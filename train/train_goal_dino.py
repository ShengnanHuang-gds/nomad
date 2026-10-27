"""Train a goal-direction head on frozen DINOv2 tokens (cached by cache_dino_features.py).

Input: the cached tokens of the current frame and of the goal frame (CLS plus
pooled patch grid each). A small Transformer reads both token sets together,
so it can compare the two views, and a GoalDirectionHead on its CLS output
predicts the goal bearing in the robot frame as (direction, kappa).

Samples match D-ft: the goal comes from the same trajectory, 3 < distance < 40
steps (action_mask), |goal| >= --min-goal-m. Each epoch draws one goal per
current frame, uniform over its valid distances (the distribution D-ft sees
after its filters). Loss weight distance / 20, --warmup-epochs of 1 - cos,
then von Mises NLL. With flip features, half of the samples use the mirrored
images of both frames and the mirrored target (y -> -y).

Validation uses D-ft's trajectory list (same 236 trajectories), one fixed goal
per current frame. The epoch with the lowest far (>= 20 steps) median bearing
error is saved as dino_dir_best.pth.

Run from train/:
    python -u train_goal_dino.py
"""

import argparse
import csv
import json
import math
import os
import pickle
import time

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from eval_by_distance import load_config
from train_goal_dir import FAR_STEPS, cos_error, direction_loss, log_i0
from yaw_traj import integrated_yaw_unit_direction, yaw_tensor_from_out
from vint_train.models.nomad.pair_token_head import PairTokenHead


def sector_labels(target_xy, mid_deg=15.0):
    """Map robot-frame goal xy to left(0) / center(1) / right(2)."""
    bearing = torch.rad2deg(torch.atan2(target_xy[:, 1], target_xy[:, 0]))
    labels = torch.ones(target_xy.shape[0], dtype=torch.long, device=target_xy.device)
    labels = torch.where(bearing > mid_deg, torch.zeros_like(labels), labels)
    labels = torch.where(bearing < -mid_deg, torch.full_like(labels, 2), labels)
    return labels, bearing.abs()


def load_head_checkpoint(head, ckpt_head):
    """Load weights; expand or shrink ``kind`` when context frame count changes."""
    current = head.state_dict()
    skipped = []
    for key, value in ckpt_head.items():
        if key not in current:
            skipped.append((key, "missing in model"))
            continue
        target = current[key]
        if target.shape == value.shape:
            current[key] = value
            continue
        if key == "kind" and value.ndim == 2 and target.ndim == 2 and value.shape[1] == target.shape[1]:
            n = min(value.shape[0], target.shape[0])
            target = target.clone()
            target[:n] = value[:n]
            current[key] = target
            print(f"partial kind load: {n}/{target.shape[0]} token kinds from checkpoint")
            continue
        skipped.append((key, f"shape {tuple(value.shape)} vs {tuple(target.shape)}"))
    head.load_state_dict(current)
    return skipped


CACHE_DIR = "logs/dino_cache/dinov2_vits14_reg"
DFT_VAL_LIST = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/val_trajectories.txt"
MIN_STEPS, MAX_STEPS = 4, 39
DEFAULT_HARD_PAIRS_CSV = "logs/revalidation/hard_pairs/hard_pairs_train.csv"


def load_hard_frame_set(csv_path, far_only=True, require_turn=False):
    """Unique (traj_name, t) from mined hard-pair CSV."""
    import csv

    keys = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if far_only and int(row["far"]) == 0:
                continue
            if require_turn and int(row["hard_turn"]) == 0:
                continue
            keys.add((row["traj_name"], int(row["t"])))
    return keys


TURN_STRICT_LAT_M = 0.30
TURN_STRICT_YAW_DEG = 45.0


def path_winding_deg(traj, t, spacing, len_pred):
    """Sum of absolute yaw step changes over len_pred future waypoints (GT train traj)."""
    yaw = traj["yaw"]
    n = len(yaw)
    idx = [min(int(t) + i * spacing, n - 1) for i in range(int(len_pred) + 1)]
    yaws = [float(np.ravel(yaw[i])[0]) for i in idx]
    total = 0.0
    for i in range(len(yaws) - 1):
        dy = yaws[i + 1] - yaws[i]
        dy = (dy + np.pi) % (2 * np.pi) - np.pi
        total += abs(np.degrees(dy))
    return total


def frame_turn_strict(traj, curr, spacing, len_pred, meters_per_unit):
    """Same rule as eval_frame_sets TURN_STRICT (0.30 m / 45 deg on 8-step horizon)."""
    pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)
    yaw_arr = traj["yaw"]
    curr = int(curr)
    t_end = min(curr + int(len_pred), len(pos) - 1)
    d = pos[t_end] - pos[curr]
    yaw0 = float(np.ravel(yaw_arr[curr])[0])
    c, s = np.cos(yaw0), np.sin(yaw0)
    lateral_m = abs(-d[0] * s + d[1] * c) * meters_per_unit
    t_yaw = min(curr + int(len_pred) * spacing, len(yaw_arr) - 1)
    y0 = float(np.ravel(yaw_arr[curr])[0])
    y1 = float(np.ravel(yaw_arr[t_yaw])[0])
    dy = (y1 - y0 + np.pi) % (2 * np.pi) - np.pi
    return (lateral_m >= TURN_STRICT_LAT_M) or (abs(np.degrees(dy)) >= TURN_STRICT_YAW_DEG)


def load_cache(cache_dir, name):
    path = os.path.join(cache_dir, name)
    with open(os.path.join(path, "keys.pkl"), "rb") as f:
        keys = pickle.load(f)
    with open(os.path.join(path, "meta.json")) as f:
        meta = json.load(f)
    return path, {key: row for row, key in enumerate(keys)}, meta


def _future_dyaw_deg(traj, curr, spacing, n_steps):
    """Per-step yaw change (degrees) for k=1..n_steps along GT trajectory."""
    yaw = traj["yaw"]
    n = len(yaw)
    out = np.zeros(n_steps, dtype=np.float32)
    curr = int(curr)
    for k in range(1, n_steps + 1):
        i0 = min(curr + (k - 1) * spacing, n - 1)
        i1 = min(curr + k * spacing, n - 1)
        y0 = float(np.ravel(yaw[i0])[0])
        y1 = float(np.ravel(yaw[i1])[0])
        dy = (y1 - y0 + np.pi) % (2 * np.pi) - np.pi
        out[k - 1] = np.degrees(dy)
    return out


def _local_bearing_step(pos, curr, c, s, step, min_goal_m):
    gi = min(int(curr) + int(step), len(pos) - 1)
    d = pos[gi] - pos[curr]
    local = np.array([d[0] * c + d[1] * s, -d[0] * s + d[1] * c], dtype=np.float32)
    if float(np.linalg.norm(local)) < min_goal_m:
        return None
    return local


def build_pairs(
    config,
    split,
    rows,
    traj_filter,
    min_goal_m,
    context=0,
    target="goal",
    multi_horizon_aux=(),
    multi_horizon_strict=False,
    hard_frame_set=None,
    yaw_aux_steps=0,
):
    """Every valid (current, goal) pair: rows into the cache, target in meters, distance in steps.

    target "goal": the goal position in the robot frame. target "endpoint": the robot position
    len_traj_pred steps ahead (the near waypoint the policy is about to reach), the same for every
    goal of a current frame; frames whose endpoint is closer than min_goal_m are dropped.
    ctx holds the rows of frames curr-1 ... curr-context (the index starts at context_size, so they exist).
    """
    horizon = int(config["len_traj_pred"])
    data_config = config["datasets"]["go_stanford"]
    index_path = os.path.join(
        data_config[split],
        f"dataset_dist_{config['distance']['min_dist_cat']}_to_{config['distance']['max_dist_cat']}"
        f"_context_{config.get('context_type', 'temporal')}_n{config['context_size']}"
        f"_slack_{data_config.get('end_slack', 0)}_pred_{config['len_traj_pred']}.pkl",
    )
    with open(index_path, "rb") as f:
        index_to_data, _goals = pickle.load(f)
    by_traj = {}
    for traj_name, curr, max_goal in index_to_data:
        if traj_filter(traj_name):
            by_traj.setdefault(traj_name, []).append((curr, max_goal))
    if context > config["context_size"]:
        raise ValueError(f"--context {context} exceeds context_size {config['context_size']}")
    spacing = int(data_config.get("waypoint_spacing", 1))
    meters_per_unit = float(data_config.get("metric_waypoint_spacing", 0.25)) * spacing
    curr_rows, goal_rows, ctx_rows, targets, steps, owner, windings, turn_flags, target_aux_rows, aux_valid_rows = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    target_yaw_rows = []
    multi_horizon_aux = tuple(int(x) for x in multi_horizon_aux)
    yaw_aux_steps = int(yaw_aux_steps)
    frame_hard_rows = []
    n_curr = 0
    for traj_name, entries in tqdm(by_traj.items(), desc=f"pairs {split}", leave=False):
        with open(os.path.join(data_config["data_folder"], traj_name, "traj_data.pkl"), "rb") as f:
            traj = pickle.load(f)
        pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)
        yaw = np.array([float(np.ravel(y)[0]) for y in traj["yaw"]])
        for curr, max_goal in entries:
            wind_frame = path_winding_deg(traj, curr, spacing, horizon)
            strict_frame = float(frame_turn_strict(traj, curr, spacing, horizon, meters_per_unit))
            k = np.arange(MIN_STEPS, min(MAX_STEPS, max_goal) + 1)
            if len(k) == 0:
                continue
            delta = pos[curr + k] - pos[curr]
            c, s = np.cos(yaw[curr]), np.sin(yaw[curr])
            local = np.stack([delta[:, 0] * c + delta[:, 1] * s, -delta[:, 0] * s + delta[:, 1] * c], axis=1)
            keep = np.linalg.norm(local, axis=1) >= min_goal_m
            if not keep.any():
                continue
            k, local = k[keep], local[keep]
            if target == "endpoint":
                d = pos[curr + horizon] - pos[curr]
                end = np.array([d[0] * c + d[1] * s, -d[0] * s + d[1] * c])
                if np.linalg.norm(end) < min_goal_m:
                    continue
                aux_stack = None
                aux_valid_stack = None
                if multi_horizon_aux:
                    aux_pts = []
                    aux_valid = []
                    for st in multi_horizon_aux:
                        loc = _local_bearing_step(pos, curr, c, s, st, min_goal_m)
                        if loc is None:
                            if multi_horizon_strict:
                                break
                            aux_pts.append(np.zeros(2, dtype=np.float32))
                            aux_valid.append(False)
                        else:
                            aux_pts.append(loc)
                            aux_valid.append(True)
                    if multi_horizon_strict and len(aux_pts) != len(multi_horizon_aux):
                        continue
                    aux_stack = np.stack(aux_pts, axis=0)
                    aux_valid_stack = np.array(aux_valid, dtype=bool)
                local = np.tile(end, (len(k), 1))
                dyaw_stack = None
                if yaw_aux_steps > 0:
                    dyaw_stack = _future_dyaw_deg(traj, curr, spacing, yaw_aux_steps)
            curr_rows.append(np.full(len(k), rows[(traj_name, curr)]))
            goal_rows.append(np.array([rows[(traj_name, curr + int(j))] for j in k]))
            past = [rows[(traj_name, curr - j)] for j in range(1, context + 1)]
            ctx_rows.append(np.tile(np.array(past, dtype=np.int64).reshape(1, context), (len(k), 1)))
            targets.append(local.astype(np.float32))
            steps.append(k)
            owner.append(np.full(len(k), n_curr))
            windings.append(np.full(len(k), wind_frame, dtype=np.float32))
            turn_flags.append(np.full(len(k), strict_frame, dtype=np.float32))
            if multi_horizon_aux:
                target_aux_rows.append(np.tile(aux_stack[None], (len(k), 1, 1)))
                aux_valid_rows.append(np.tile(aux_valid_stack[None], (len(k), 1)))
            if yaw_aux_steps > 0 and target == "endpoint":
                target_yaw_rows.append(np.tile(dyaw_stack[None], (len(k), 1)))
            frame_hard_rows.append(
                hard_frame_set is not None and (traj_name, int(curr)) in hard_frame_set
            )
            n_curr += 1
    owner = np.concatenate(owner)
    starts = np.searchsorted(owner, np.arange(n_curr))
    counts = np.diff(np.append(starts, len(owner)))
    out = {
        "curr": np.concatenate(curr_rows),
        "goal": np.concatenate(goal_rows),
        "ctx": np.concatenate(ctx_rows),
        "target": np.concatenate(targets),
        "steps": np.concatenate(steps),
        "winding": np.concatenate(windings),
        "turn_strict": np.concatenate(turn_flags),
        "starts": starts,
        "counts": counts,
    }
    if hard_frame_set is not None:
        out["frame_hard"] = np.array(frame_hard_rows, dtype=bool)
    if yaw_aux_steps > 0:
        out["target_yaw"] = np.concatenate(target_yaw_rows).astype(np.float32)
        out["yaw_aux_steps"] = yaw_aux_steps
    if multi_horizon_aux:
        out["target_aux"] = np.concatenate(target_aux_rows).astype(np.float32)
        out["aux_valid"] = np.concatenate(aux_valid_rows)
        out["multi_horizon_aux"] = np.array(multi_horizon_aux, dtype=np.int32)
        out["multi_horizon_strict"] = bool(multi_horizon_strict)
    return out


def draw(pairs, rng, frame_boost=1.0):
    """One random (current, goal) index per slot; optional oversample hard current frames."""
    n = len(pairs["starts"])
    if frame_boost > 1.0 and "frame_hard" in pairs and pairs["frame_hard"].any():
        w = np.where(pairs["frame_hard"], frame_boost, 1.0).astype(np.float64)
        w /= w.sum()
        fi = rng.choice(n, size=n, replace=True, p=w)
        return pairs["starts"][fi] + (rng.random(n) * pairs["counts"][fi]).astype(np.int64)
    return pairs["starts"] + (rng.random(n) * pairs["counts"]).astype(np.int64)


class PairBatches(Dataset):
    """Each item is a whole batch, read from the memmapped token cache with sorted fancy indexing."""

    def __init__(self, cache_path, pairs, chosen, batch_size, flip, seed, context=0):
        self.cache_path = cache_path
        self.pairs = pairs
        self.batches = [chosen[i : i + batch_size] for i in range(0, len(chosen), batch_size)]
        self.flip = flip
        self.seed = seed
        self.context = context
        self.arrays = None

    def __len__(self):
        return len(self.batches)

    def _open(self):
        self.arrays = [np.load(os.path.join(self.cache_path, "features.npy"), mmap_mode="r")]
        if self.flip:
            self.arrays.append(np.load(os.path.join(self.cache_path, "features_flip.npy"), mmap_mode="r"))

    def _read(self, array, rows):
        order = np.argsort(rows)
        out = np.empty((len(rows),) + array.shape[1:], dtype=np.float16)
        out[order] = array[rows[order]]
        return out

    def __getitem__(self, b):
        if self.arrays is None:
            self._open()
        idx = self.batches[b]
        curr_rows, goal_rows = self.pairs["curr"][idx], self.pairs["goal"][idx]
        target = self.pairs["target"][idx].copy()
        mirrored = np.zeros(len(idx), dtype=bool)
        if self.flip:
            mirrored = np.random.default_rng((self.seed, b)).random(len(idx)) < 0.5
        curr = np.empty((len(idx),) + self.arrays[0].shape[1:], dtype=np.float16)
        goal = np.empty_like(curr)
        for which, sel in ((0, ~mirrored), (1, mirrored)):
            if sel.any():
                curr[sel] = self._read(self.arrays[which], curr_rows[sel])
                goal[sel] = self._read(self.arrays[which], goal_rows[sel])
        target[mirrored, 1] *= -1.0
        batch = [torch.from_numpy(curr), torch.from_numpy(goal), torch.from_numpy(target)]
        batch.append(torch.from_numpy(self.pairs["steps"][idx]))
        if "target_aux" in self.pairs:
            aux = self.pairs["target_aux"][idx].copy()
            aux[mirrored, :, 1] *= -1.0
            batch.append(torch.from_numpy(aux))
            if "aux_valid" in self.pairs:
                batch.append(torch.from_numpy(self.pairs["aux_valid"][idx]))
        context = getattr(self, "context", 0)
        if context > 0:
            ctx_rows = self.pairs["ctx"][idx]
            ctx = np.empty((len(idx), context) + self.arrays[0].shape[1:], dtype=np.float16)
            for which, sel in ((0, ~mirrored), (1, mirrored)):
                for j in range(context):
                    if sel.any():
                        ctx[sel, j] = self._read(self.arrays[which], ctx_rows[sel, j])
            batch.append(torch.from_numpy(ctx))
        if "winding" in self.pairs:
            batch.append(torch.from_numpy(self.pairs["winding"][idx].astype(np.float32)))
        if "turn_strict" in self.pairs:
            batch.append(torch.from_numpy(self.pairs["turn_strict"][idx].astype(np.float32)))
        if "target_yaw" in self.pairs:
            yaw_t = self.pairs["target_yaw"][idx].copy()
            yaw_t[mirrored] *= -1.0
            batch.append(torch.from_numpy(yaw_t))
        return tuple(batch)


def _parse_batch(batch, device):
    curr, goal, target, steps = batch[:4]
    ctx, winding_t, turn_strict_t, target_aux, aux_valid_t, target_yaw_t = None, None, None, None, None, None
    for t in batch[4:]:
        if t.ndim == 4:
            ctx = t.to(device, non_blocking=True).float()
        elif t.ndim == 3 and t.shape[-1] == 2:
            target_aux = t.to(device, non_blocking=True).float()
        elif t.ndim == 2:
            if t.dtype == torch.bool:
                aux_valid_t = t.to(device, non_blocking=True).bool()
            else:
                target_yaw_t = t.to(device, non_blocking=True).float()
        elif t.ndim == 1:
            if winding_t is None:
                winding_t = t.to(device, non_blocking=True)
            else:
                turn_strict_t = t.to(device, non_blocking=True)
    return (
        curr.to(device, non_blocking=True).float(),
        goal.to(device, non_blocking=True).float(),
        target.to(device),
        steps.to(device),
        ctx,
        winding_t,
        turn_strict_t,
        target_aux,
        aux_valid_t,
        target_yaw_t,
    )


def loader(cache_path, pairs, chosen, batch_size, flip, seed, workers, context=0):
    return DataLoader(
        PairBatches(cache_path, pairs, chosen, batch_size, flip, seed, context),
        batch_size=None,
        shuffle=False,
        num_workers=workers,
    )



def run_epoch(
    head,
    batches,
    device,
    optimizer=None,
    scheduler=None,
    use_nll=True,
    desc="",
    hard_bearing_deg=0.0,
    hard_weight=1.0,
    hard_far_only=True,
    sector_lambda=0.0,
    sector_mid_deg=15.0,
    sector_hard_boost=2.0,
    turn_winding_deg=0.0,
    turn_weight=1.0,
    turn_strict_weight=0.0,
    curvature_q=(None, None),
    curvature_weights=(1.0, 1.5, 3.0),
    multi_horizon_lambda=0.0,
    yaw_aux_lambda=0.0,
    yaw_aux_steps=0,
    yaw_integrate_lambda=0.0,
):
    """Direction loss + optional sector CE. Sector GT from target xy (online)."""
    training = optimizer is not None
    head.train(training)
    errors, far, loss_sum, nll_sum, count = [], [], 0.0, 0.0, 0
    hard_count = 0
    sector_correct = 0
    sector_n = 0
    with torch.set_grad_enabled(training):
        for batch in tqdm(batches, desc=desc, leave=False):
            curr, goal, target, steps_dev, ctx, winding_t, turn_strict_t, target_aux, aux_valid_t, target_yaw_t = (
                _parse_batch(batch, device)
            )
            weight = steps_dev.float() / FAR_STEPS
            if training and turn_strict_weight > 1.0 and turn_strict_t is not None:
                weight = weight * torch.where(turn_strict_t > 0.5, turn_strict_weight, 1.0)
            if (
                training
                and turn_winding_deg > 0.0
                and turn_weight != 1.0
                and winding_t is not None
            ):
                weight = weight * torch.where(winding_t >= turn_winding_deg, turn_weight, 1.0)
            if training and curvature_q[0] is not None and winding_t is not None:
                q1, q2 = curvature_q
                w_low, w_mid, w_high = curvature_weights
                tier = torch.where(
                    winding_t >= q2,
                    torch.full_like(winding_t, w_high),
                    torch.where(winding_t >= q1, torch.full_like(winding_t, w_mid), torch.full_like(winding_t, w_low)),
                )
                weight = weight * tier
            if hard_bearing_deg > 0.0 and hard_weight != 1.0:
                bearing_abs = torch.rad2deg(torch.atan2(target[:, 1], target[:, 0])).abs()
                hard = bearing_abs > hard_bearing_deg
                if hard_far_only:
                    hard = hard & (steps_dev >= FAR_STEPS)
                weight = weight * torch.where(hard, hard_weight, 1.0)
                hard_count += int(hard.sum().item())
            with torch.autocast("cuda", dtype=torch.bfloat16):
                out = head(curr, goal, ctx)
            direction, kappa = out[0].float(), out[1].float()
            loss, cos_err = direction_loss(direction, kappa, target, weight, use_nll)
            if (
                training
                and multi_horizon_lambda > 0.0
                and target_aux is not None
                and len(out) > 2
                and isinstance(out[2], list)
            ):
                aux_terms = []
                for i, aux_pair in enumerate(out[2]):
                    d_aux, k_aux = aux_pair[0].float(), aux_pair[1].float()
                    if aux_valid_t is not None:
                        valid = aux_valid_t[:, i]
                        if not valid.any():
                            continue
                        la, _ = direction_loss(
                            d_aux[valid], k_aux[valid], target_aux[:, i][valid], weight[valid], use_nll=False
                        )
                    else:
                        la, _ = direction_loss(d_aux, k_aux, target_aux[:, i], weight, use_nll=False)
                    aux_terms.append(la)
                if aux_terms:
                    loss = loss + multi_horizon_lambda * (sum(aux_terms) / len(aux_terms))
            yaw_pred = yaw_tensor_from_out(head, out)
            if training and yaw_aux_lambda > 0.0 and yaw_pred is not None and target_yaw_t is not None:
                yaw_gt = torch.deg2rad(target_yaw_t)
                yaw_loss = torch.nn.functional.smooth_l1_loss(
                    yaw_pred.float(), yaw_gt, reduction="none"
                ).mean(dim=1)
                loss = loss + yaw_aux_lambda * (yaw_loss * weight).mean()
            if training and yaw_integrate_lambda > 0.0 and yaw_pred is not None:
                d_int = integrated_yaw_unit_direction(yaw_pred.float())
                li, _ = direction_loss(d_int, kappa, target, weight, use_nll=False)
                loss = loss + yaw_integrate_lambda * li
            sector_out = None
            if sector_lambda > 0.0:
                for item in out[2:]:
                    if not isinstance(item, torch.Tensor) or item.ndim != 2:
                        continue
                    if yaw_aux_steps > 0 and item.shape[1] == yaw_aux_steps:
                        continue
                    sector_out = item
                    break
            if sector_lambda > 0.0 and sector_out is not None:
                logits = sector_out.float()
                labels, bearing_abs = sector_labels(target, sector_mid_deg)
                ce = torch.nn.functional.cross_entropy(logits, labels, reduction="none")
                ce_w = torch.where(bearing_abs > 45.0, sector_hard_boost, 1.0)
                loss = loss + sector_lambda * (ce * ce_w).mean()
                sector_correct += int((logits.argmax(-1) == labels).sum().item())
                sector_n += len(labels)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(head.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
            cos_err = cos_err.detach()
            nll_sum += (-kappa.detach() * cos_err + log_i0(kappa.detach())).sum().item()
            errors.append(torch.rad2deg(torch.acos(cos_err)).cpu().numpy())
            far.append((steps_dev >= FAR_STEPS).cpu().numpy())
            loss_sum += loss.item() * len(steps_dev)
            count += len(steps_dev)
    errors, far = np.concatenate(errors), np.concatenate(far)
    out_metrics = {
        "loss": loss_sum / count,
        "median_deg": float(np.median(errors)),
        "far_median_deg": float(np.median(errors[far])),
        "far_mean_deg": float(errors[far].mean()),
        "vm_nll": nll_sum / count,
        "samples": count,
    }
    if hard_bearing_deg > 0.0 and hard_weight != 1.0 and count > 0:
        out_metrics["hard_frac"] = hard_count / count
    if sector_n > 0:
        out_metrics["sector_acc"] = sector_correct / sector_n
    return out_metrics


def main():
    parser = argparse.ArgumentParser(description="Goal-direction head on frozen DINOv2 tokens")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--val-list", default=DFT_VAL_LIST)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--warmup-epochs", type=int, default=2, help="1 - cos epochs before von Mises NLL")
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.05)
    parser.add_argument("--width", type=int, default=256)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--heads", type=int, default=8)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--context", type=int, default=0, help="Past frames added as extra token sets")
    parser.add_argument("--no-flip", action="store_true")
    parser.add_argument("--min-goal-m", type=float, default=0.3)
    parser.add_argument("--target", choices=("goal", "endpoint"), default="goal",
                        help="goal: far-goal bearing. endpoint: bearing of the position len_traj_pred steps ahead")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-batches", type=int, default=0, help="Per-epoch cap for smoke tests")
    parser.add_argument("--run-name", default="nomad_dino_dir")
    parser.add_argument(
        "--init",
        default="",
        help="Optional checkpoint (dino_dir_best.pth) to fine-tune from",
    )
    parser.add_argument(
        "--hard-bearing-deg",
        type=float,
        default=0.0,
        help="If >0, upweight samples with |goal bearing| above this (degrees)",
    )
    parser.add_argument("--hard-weight", type=float, default=2.5, help="Extra loss multiplier on hard samples")
    parser.add_argument(
        "--hard-far-only",
        action="store_true",
        default=True,
        help="Only treat far (steps>=20) large-bearing samples as hard",
    )
    parser.add_argument("--hard-all-dist", action="store_false", dest="hard_far_only")
    parser.add_argument("--n-sectors", type=int, default=0, help="0=off; 3=left/center/right")
    parser.add_argument("--sector-lambda", type=float, default=1.0)
    parser.add_argument("--sector-mid-deg", type=float, default=15.0)
    parser.add_argument("--sector-hard-boost", type=float, default=2.0)
    parser.add_argument(
        "--turn-winding-deg",
        type=float,
        default=0.0,
        help="If >0, multiply loss weight by --turn-weight when GT path winding >= this (train only)",
    )
    parser.add_argument("--turn-weight", type=float, default=2.0)
    parser.add_argument(
        "--turn-strict-weight",
        type=float,
        default=0.0,
        help="If >1, multiply loss on strict turn frames (0.30m/45deg, train only)",
    )
    parser.add_argument(
        "--curvature-tiers",
        default="",
        help="Comma weights low,mid,high; uses train frame-winding tertiles (e.g. 1,1.5,3)",
    )
    parser.add_argument("--top-k-checkpoints", type=int, default=3, help="Keep top-K val far_median checkpoints")
    parser.add_argument(
        "--multi-horizon",
        default="",
        help="Auxiliary endpoint steps (comma), e.g. 2,4 with primary step len_traj_pred (8). endpoint target only.",
    )
    parser.add_argument(
        "--multi-horizon-lambda",
        type=float,
        default=0.25,
        help="Weight on mean aux direction loss (1-cos); primary step 8 keeps full vm loss.",
    )
    parser.add_argument(
        "--multi-horizon-strict",
        action="store_true",
        help="Drop current frames unless all aux steps meet min_goal_m (legacy P4; default is masked aux on L8 for all frames).",
    )
    parser.add_argument(
        "--hard-pairs-csv",
        default="",
        help="Mined hard_pairs_*.csv; enables frame_hard for oversampling (see --hard-frame-boost).",
    )
    parser.add_argument(
        "--hard-frame-boost",
        type=float,
        default=1.0,
        help="Relative sampling weight for hard frames when --hard-pairs-csv is set (>1 oversamples).",
    )
    parser.add_argument(
        "--hard-pairs-far-only",
        action="store_true",
        default=True,
        help="Only (traj,t) with at least one far hard pair in CSV.",
    )
    parser.add_argument("--hard-pairs-all-dist", action="store_false", dest="hard_pairs_far_only")
    parser.add_argument(
        "--hard-pairs-turn-only",
        action="store_true",
        help="Only frames with hard_turn in CSV (with far filter if enabled).",
    )
    parser.add_argument(
        "--yaw-aux-steps",
        type=int,
        default=0,
        help="If >0, train-only auxiliary per-step GT dyaw (deg) along trajectory; endpoint target only.",
    )
    parser.add_argument(
        "--yaw-aux-lambda",
        type=float,
        default=0.3,
        help="Weight on smooth_l1(rad) between yaw aux head and GT step dyaw (train only).",
    )
    parser.add_argument(
        "--yaw-integrate-lambda",
        type=float,
        default=0.25,
        help="1-cos on integrated yaw polyline dir vs endpoint target (train only; matches deploy WP dir).",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda:0")
    output_dir = os.path.join("logs", "nomad_d", f"{args.run_name}_{time.strftime('%Y_%m_%d_%H_%M_%S')}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"output: {os.path.abspath(output_dir)}")
    if args.hard_bearing_deg > 0:
        print(
            f"hard weighting: |bearing|>{args.hard_bearing_deg}deg "
            f"x{args.hard_weight} far_only={args.hard_far_only} (online, no LMDB)"
        )
    if args.turn_winding_deg > 0:
        print(f"turn-aware loss: winding>={args.turn_winding_deg}deg x{args.turn_weight} (train only, GT path)")
    if args.turn_strict_weight > 1.0:
        print(f"turn-strict loss: weight x{args.turn_strict_weight} on 0.30m/45deg frames (train only)")
    curvature_weights = (1.0, 1.5, 3.0)
    curvature_q = (None, None)
    if args.curvature_tiers.strip():
        curvature_weights = tuple(float(x) for x in args.curvature_tiers.split(","))
        if len(curvature_weights) != 3:
            raise ValueError("--curvature-tiers must have 3 comma-separated weights")

    config = load_config(args.config)
    cache_path, rows, meta = load_cache(args.cache_dir, "train")
    flip = meta["flip"] and not args.no_flip
    with open(args.val_list) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    multi_aux = tuple(int(x) for x in args.multi_horizon.split(",") if x.strip()) if args.multi_horizon.strip() else ()
    if multi_aux and args.target != "endpoint":
        raise ValueError("--multi-horizon requires --target endpoint")
    if multi_aux and any(h <= 0 for h in multi_aux):
        raise ValueError(f"invalid --multi-horizon steps: {multi_aux}")
    yaw_aux_steps = int(args.yaw_aux_steps)
    if yaw_aux_steps > 0 and args.target != "endpoint":
        raise ValueError("--yaw-aux-steps requires --target endpoint")
    mh_strict = bool(args.multi_horizon_strict)
    hard_frame_set = None
    hard_csv = args.hard_pairs_csv.strip()
    if hard_csv:
        if not os.path.isfile(hard_csv):
            raise FileNotFoundError(f"--hard-pairs-csv not found: {hard_csv}")
        hard_frame_set = load_hard_frame_set(
            hard_csv, far_only=args.hard_pairs_far_only, require_turn=args.hard_pairs_turn_only
        )
        print(
            f"hard frame keys from {hard_csv}: {len(hard_frame_set)} "
            f"(far_only={args.hard_pairs_far_only} turn_only={args.hard_pairs_turn_only})"
        )
    train_pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t not in val_trajs,
        args.min_goal_m,
        args.context,
        args.target,
        multi_aux,
        mh_strict,
        hard_frame_set,
        yaw_aux_steps,
    )
    val_pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t in val_trajs,
        args.min_goal_m,
        args.context,
        args.target,
        multi_aux,
        mh_strict,
        None,
        yaw_aux_steps,
    )
    if hard_frame_set is not None and "frame_hard" in train_pairs:
        fh = train_pairs["frame_hard"]
        print(
            f"train frames marked hard: {int(fh.sum())}/{len(fh)} ({100.0 * fh.mean():.1f}%) | "
            f"oversample boost x{args.hard_frame_boost}"
        )
    if args.curvature_tiers.strip():
        frame_w = train_pairs["winding"][train_pairs["starts"]]
        q1, q2 = np.percentile(frame_w, [33.333, 66.667])
        curvature_q = (float(q1), float(q2))
        print(
            f"curvature tiers: w={curvature_weights} | train winding tertiles {q1:.1f}, {q2:.1f} deg"
        )
        with open(os.path.join(output_dir, "curvature_tiers.json"), "w") as f:
            json.dump({"q33": curvature_q[0], "q66": curvature_q[1], "weights": curvature_weights}, f)
    val_chosen = draw(val_pairs, np.random.default_rng(1234))
    print(
        f"cache {meta['model']} {meta['width']}x{meta['height']} pool {meta['pool']} -> {meta['tokens']} tokens x "
        f"{meta['dim']} | flip {flip} | context {args.context} | target {args.target}\ncurrent frames: {len(train_pairs['starts'])} train, "
        f"{len(val_pairs['starts'])} val ({len(val_trajs)} trajectories) | pairs {len(train_pairs['curr'])} train"
    )

    head = PairTokenHead(
        meta["dim"],
        meta["tokens"],
        args.width,
        args.layers,
        args.heads,
        args.dropout,
        args.context,
        n_sectors=args.n_sectors,
        aux_horizons=multi_aux,
        yaw_aux_steps=yaw_aux_steps,
    ).to(device)
    if yaw_aux_steps > 0:
        print(
            f"yaw traj: {yaw_aux_steps} step dyaw | aux lambda={args.yaw_aux_lambda} | "
            f"integrate-dir lambda={args.yaw_integrate_lambda} | deploy WP dir=integrate(yaw), kappa from vm head"
        )
    if multi_aux:
        mode = "strict drop" if mh_strict else "masked aux (L8 on all endpoint frames)"
        print(
            f"multi-horizon: primary step {config['len_traj_pred']} + aux {multi_aux} "
            f"(P0->Pk chord bearing), lambda={args.multi_horizon_lambda}, {mode}"
        )
        if not mh_strict and "aux_valid" in train_pairs:
            av = train_pairs["aux_valid"]
            all_aux = av.all(axis=1)
            print(
                f"aux mask: train pairs {len(av)} | all aux valid {int(all_aux.sum())} "
                f"({100.0 * all_aux.mean():.1f}%) | any aux valid {int((av.any(axis=1)).sum())}"
            )
    if args.init:
        ckpt = torch.load(args.init, map_location="cpu", weights_only=False)
        skipped = load_head_checkpoint(head, ckpt["head"])
        print(
            f"loaded init from {args.init} (epoch {ckpt.get('epoch', '?')}) "
            f"skipped={skipped}"
        )
    if args.n_sectors > 0:
        print(
            f"sector head: n={args.n_sectors} lambda={args.sector_lambda} "
            f"mid=+/-{args.sector_mid_deg}deg hard_boost={args.sector_hard_boost}"
        )
    print(f"head parameters: {sum(p.numel() for p in head.parameters()) / 1e6:.2f}M")
    steps_per_epoch = math.ceil(len(train_pairs["starts"]) / args.batch_size)
    if args.max_batches > 0:
        steps_per_epoch = min(steps_per_epoch, args.max_batches)
    # Fine-tunes from a strong init use a smaller LR.
    lr = args.lr if not args.init else args.lr * 0.3
    optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=args.weight_decay)
    total = steps_per_epoch * args.epochs
    warm = steps_per_epoch
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda s: (s + 1) / warm if s < warm else 0.5 * (1.0 + math.cos(math.pi * (s - warm) / max(1, total - warm))),
    )
    val_batches = loader(cache_path, val_pairs, val_chosen, 512, False, 0, 2, args.context)
    hard_kw = dict(
        hard_bearing_deg=args.hard_bearing_deg,
        hard_weight=args.hard_weight,
        hard_far_only=args.hard_far_only,
        sector_lambda=(args.sector_lambda if args.n_sectors > 0 else 0.0),
        sector_mid_deg=args.sector_mid_deg,
        sector_hard_boost=args.sector_hard_boost,
        turn_winding_deg=args.turn_winding_deg,
        turn_weight=args.turn_weight,
        turn_strict_weight=args.turn_strict_weight,
        curvature_q=curvature_q,
        curvature_weights=curvature_weights,
        multi_horizon_lambda=(args.multi_horizon_lambda if multi_aux else 0.0),
        yaw_aux_lambda=(args.yaw_aux_lambda if yaw_aux_steps > 0 else 0.0),
        yaw_aux_steps=yaw_aux_steps,
        yaw_integrate_lambda=(args.yaw_integrate_lambda if yaw_aux_steps > 0 else 0.0),
    )
    val_kw = dict(hard_kw)
    val_kw["multi_horizon_lambda"] = 0.0
    val_kw["yaw_aux_lambda"] = 0.0
    val_kw["yaw_integrate_lambda"] = 0.0
    val_kw.update(
        turn_winding_deg=0.0,
        turn_weight=1.0,
        turn_strict_weight=0.0,
        curvature_q=(None, None),
    )

    best, log_rows = math.inf, []
    top_k = []
    for epoch in range(args.epochs):
        start = time.time()
        use_nll = epoch >= args.warmup_epochs
        chosen = rng.permutation(draw(train_pairs, rng, args.hard_frame_boost))[
            : steps_per_epoch * args.batch_size
        ]
        train_batches = loader(
            cache_path, train_pairs, chosen, args.batch_size, flip, args.seed + epoch, args.num_workers, args.context
        )
        stage = "vm-nll" if use_nll else "1-cos"
        train = run_epoch(
            head, train_batches, device, optimizer, scheduler, use_nll, f"epoch {epoch} ({stage})", **hard_kw
        )
        # Validation stays unweighted so epoch selection matches the original metric.
        val = run_epoch(head, val_batches, device, use_nll=True, desc="val", **val_kw)
        state = {"epoch": epoch, "head": head.state_dict(), "args": vars(args), "meta": meta, **val}
        torch.save(state, os.path.join(output_dir, "dino_dir_last.pth"))
        selected = val["far_median_deg"] < best
        if selected:
            best = val["far_median_deg"]
            torch.save(state, os.path.join(output_dir, "dino_dir_best.pth"))
        if args.top_k_checkpoints > 0:
            top_k.append((val["far_median_deg"], epoch, state))
            top_k.sort(key=lambda x: x[0])
            top_k = top_k[: args.top_k_checkpoints]
            for rank, (score, ep, st) in enumerate(top_k, start=1):
                torch.save(st, os.path.join(output_dir, f"dino_dir_top{rank}_ep{ep}_far{score:.2f}.pth"))
        row = {
            "epoch": epoch,
            "stage": stage,
            **{f"train_{k}": v for k, v in train.items()},
            **{f"val_{k}": v for k, v in val.items()},
            "best": selected,
            "minutes": (time.time() - start) / 60,
        }
        log_rows.append(row)
        with open(os.path.join(output_dir, "train_log.csv"), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerows(log_rows)
        hard_msg = f" | hard_frac {train['hard_frac']:.2f}" if "hard_frac" in train else ""
        sec_msg = ""
        if "sector_acc" in train or "sector_acc" in val:
            sec_msg = (
                f" | sector acc train {train.get('sector_acc', float('nan')):.2f} "
                f"/ val {val.get('sector_acc', float('nan')):.2f}"
            )
        print(
            f"[epoch {epoch} {stage}] median train {train['median_deg']:.1f} / val {val['median_deg']:.1f} | "
            f"far train {train['far_median_deg']:.1f} / val {val['far_median_deg']:.1f} deg | "
            f"val NLL {val['vm_nll']:.3f}{' | best' if selected else ''}{hard_msg}{sec_msg} | {row['minutes']:.1f} min"
        )
    print(f"Best val far median {best:.1f} deg -> {os.path.join(output_dir, 'dino_dir_best.pth')}")


if __name__ == "__main__":
    main()

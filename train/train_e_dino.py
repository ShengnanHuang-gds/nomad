"""Train E with an estimated goal position: DINO direction x B distance (+ sigma).

Frozen: the policy's vision_encoder and dist_pred_net, the DINO PairTokenHead,
and B (Epoch 29), which always supplies the distance, as in the direct test.
Trainable: noise_pred_net only.

--init-from b         start from B; the new cond_encoder columns are zeroed
--init-from e_oracle  start from E-oracle (pos_dim 2), which already uses [x, y]
--true-pos-prob p     per sample, feed the true goal_pos with probability p

Appended condition (dataset units, same as goal_pos):
  [mu_x, mu_y] or [mu_x, mu_y, sigma], mu = dino_dir * b_dist_steps,
  sigma = b_dist_steps / sqrt(kappa), clipped. True-position rows get sigma 0.
When the goal is masked, the appended values are zeroed (same as E-oracle).

Run from train/:

    python -u train_e_dino.py
    python -u train_e_dino.py --config config/nomad_e_dino_mu.yaml --init-from e_oracle \
        --epochs 10 --lr 3e-5 --warmup-epochs 1
    python -u train_e_dino.py --config config/nomad_e_dino_mu.yaml --init-from e_oracle \
        --goal-pos-mode blend --epochs 10 --lr 3e-5 --warmup-epochs 1
"""

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
import numpy as np
import torch
import torch.nn.functional as F
from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from diffusers.training_utils import EMAModel
from diffusion_policy.model.diffusion.conditional_unet1d import ConditionalUnet1D
from torch.utils.data import DataLoader
from tqdm import tqdm
from warmup_scheduler import GradualWarmupScheduler

from eval_by_distance import load_config
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, meters_per_unit, normalize_images
from train_goal_dino import CACHE_DIR, PairTokenHead, load_cache
from yaw_traj import path_tensor_from_out, wp_direction_from_head


def blend_torch(g_dir, g_k, w_dir, w_k, wp_scale=1.0):
    r = g_k.unsqueeze(-1) * g_dir + (wp_scale * w_k).unsqueeze(-1) * w_dir
    return r / r.norm(dim=-1, keepdim=True).clamp(min=1e-6)


def sector_logits_from_out(head, out):
    n = int(getattr(head, "n_sectors", 0) or 0)
    if n <= 0:
        return None
    for item in out:
        if isinstance(item, torch.Tensor) and item.ndim == 2 and item.shape[1] == n:
            return item
    return None


def sector_center_dirs(sec_idx, snap_deg=30.0):
    """sec_idx [B] -> unit dirs for left(+snap)/center/right(-snap)."""
    table = torch.tensor([snap_deg, 0.0, -snap_deg], device=sec_idx.device, dtype=torch.float32)
    rad = table[sec_idx.long()] * (math.pi / 180.0)
    return torch.stack([rad.cos(), rad.sin()], dim=-1)


def dual_peak_mask(logits):
    """Match run_ambig_sector_blend: high top2 mass + small gap."""
    p = torch.softmax(logits.float(), dim=-1)
    top_vals, top_idx = p.sort(dim=-1, descending=True)
    gap = top_vals[:, 0] - top_vals[:, 1]
    dual = ((top_vals[:, 0] + top_vals[:, 1]) >= 0.75) & (gap <= 0.25)
    return dual, top_idx[:, 0], top_idx[:, 1]


def path_xy_to_width(path_xy, pos_dim):
    """path_xy [B, K, 2] -> [B, pos_dim-2], pad/crop steps as needed."""
    need = max(1, (pos_dim - 2) // 2)
    if path_xy.shape[1] < need:
        pad = need - path_xy.shape[1]
        path_xy = torch.cat([path_xy, path_xy[:, -1:, :].expand(-1, pad, -1)], dim=1)
    elif path_xy.shape[1] > need:
        path_xy = path_xy[:, :need]
    return path_xy.reshape(path_xy.shape[0], -1)


def forward_wp_head(wp_head, features, curr_rows, goal_rows, past_rows, device, wp_odom=None):
    """Frozen WP head forward with optional ctx=2 history."""
    curr = read_tokens(features, curr_rows).to(device).float()
    goal = read_tokens(features, goal_rows).to(device).float()
    ctx = None
    wp_context = int(wp_head.kind.shape[0] - 2)
    if wp_context > 0:
        if past_rows is None:
            raise ValueError(f"wp_head context={wp_context} requires past_rows")
        past = past_rows[:, :wp_context].detach().cpu().numpy()
        ctx = torch.stack(
            [read_tokens(features, past[:, j]).to(device).float() for j in range(wp_context)],
            dim=1,
        )
    if int(getattr(wp_head, "odom_dim", 0) or 0) > 0 and wp_odom is None:
        raise ValueError("wp_head odom_dim>0 requires wp_odom")
    w_out = wp_head(curr, goal, ctx, odom=wp_odom)
    w_dir, w_k = wp_direction_from_head(wp_head, w_out, "auto")
    return w_out, w_dir, w_k


def build_blend_path(
    w_dir,
    pos_dim,
    path_gate="none",
    kappa=None,
    w_k=None,
    wp_scale=1.0,
    wp_out=None,
    wp_head=None,
    path_source="ray",
    meters_per_unit=0.12,
    path_units="meters",
):
    """[B, pos_dim-2] polyline in dataset units."""
    path_steps = max(1, (pos_dim - 2) // 2)
    if path_source == "wp_poly":
        if wp_head is None or wp_out is None:
            raise ValueError("wp_poly path_source needs wp_head output")
        pred = path_tensor_from_out(wp_head, wp_out)
        if pred is None:
            raise ValueError("wp_poly requires a WP path_head (path_steps>0)")
        path = pred.float()
        if path_units == "meters":
            path = path / max(float(meters_per_unit), 1e-6)
        return path_xy_to_width(path, pos_dim)
    t = torch.arange(1, path_steps + 1, device=w_dir.device, dtype=w_dir.dtype).view(1, -1, 1)
    path = w_dir.unsqueeze(1) * t
    if path_gate == "wp_vs_goal":
        if kappa is None or w_k is None:
            raise ValueError("wp_vs_goal path_gate needs kappa and w_k")
        gate = (wp_scale * w_k) / (kappa + wp_scale * w_k + 1e-6)
        path = path * gate.view(-1, 1, 1)
    elif path_gate == "dual_ambig":
        if wp_head is None or wp_out is None:
            raise ValueError("dual_ambig path_gate needs wp_head output")
        sec = sector_logits_from_out(wp_head, wp_out)
        if sec is None:
            raise ValueError("dual_ambig requires WP sector head (n_sectors>=3)")
        dual, i0, i1 = dual_peak_mask(sec)
        if dual.any():
            half = max(1, path_steps // 2)
            t_h = torch.arange(1, half + 1, device=w_dir.device, dtype=w_dir.dtype).view(1, -1, 1)
            d0 = sector_center_dirs(i0).to(dtype=w_dir.dtype)
            d1 = sector_center_dirs(i1).to(dtype=w_dir.dtype)
            dual_path = torch.cat([d0.unsqueeze(1) * t_h, d1.unsqueeze(1) * t_h], dim=1)
            if dual_path.shape[1] < path_steps:
                pad = path_steps - dual_path.shape[1]
                dual_path = torch.cat([dual_path, dual_path[:, -1:, :].expand(-1, pad, -1)], dim=1)
            elif dual_path.shape[1] > path_steps:
                dual_path = dual_path[:, :path_steps]
            path = torch.where(dual.view(-1, 1, 1), dual_path, path)
    elif path_gate not in ("", "none"):
        raise ValueError(f"unknown path_gate: {path_gate}")
    return path.reshape(w_dir.shape[0], -1)
from vint_train.data.vint_dataset import ViNT_Dataset
from vint_train.models.nomad.nomad import DenseNetwork, NoMaD
from vint_train.models.nomad.nomad_vint import NoMaD_ViNT, replace_bn_with_gn
from vint_train.training.train_utils import (
    ACTION_STATS,
    append_goal_pos,
    get_delta,
    normalize_data,
)
from vint_train.visualizing.visualize_utils import from_numpy

DINO_BEST = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
WP_BEST = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth"
E_ORACLE_CHECKPOINT = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth"


class ViNTWithDinoRows(ViNT_Dataset):
    """Same samples as ViNT_Dataset, plus row indices into the DINO feature cache."""

    def __init__(self, *args, dino_rows=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.dino_rows = dino_rows

    def __getitem__(self, i):
        f_curr, curr_time, max_goal_dist = self.index_to_data[i]
        f_goal, goal_time, goal_is_negative = self._sample_goal(f_curr, curr_time, max_goal_dist)
        context_times = list(
            range(
                curr_time + -self.context_size * self.waypoint_spacing,
                curr_time + 1,
                self.waypoint_spacing,
            )
        )
        obs_image = torch.cat([self._load_image(f_curr, t) for t in context_times])
        goal_image = self._load_image(f_goal, goal_time)
        curr_traj_data = self._get_trajectory(f_curr)
        actions, goal_pos = self._compute_actions(curr_traj_data, curr_time, goal_time)
        if goal_is_negative:
            distance = self.max_dist_cat
        else:
            distance = (goal_time - curr_time) // self.waypoint_spacing
        action_mask = (
            (distance < self.max_action_distance)
            and (distance > self.min_action_distance)
            and (not goal_is_negative)
        )
        # Past DINO rows for waypoint heads with visual history (curr-1, curr-2, ...).
        past_rows = []
        for j in range(1, 4):
            t_past = curr_time - j * self.waypoint_spacing
            key = (f_curr, t_past)
            if t_past < 0 or key not in self.dino_rows:
                past_rows.append(int(self.dino_rows[(f_curr, curr_time)]))
            else:
                past_rows.append(int(self.dino_rows[key]))
        return (
            torch.as_tensor(obs_image, dtype=torch.float32),
            torch.as_tensor(goal_image, dtype=torch.float32),
            torch.as_tensor(actions, dtype=torch.float32),
            torch.as_tensor(distance, dtype=torch.int64),
            torch.as_tensor(goal_pos, dtype=torch.float32),
            torch.as_tensor(self.dataset_index, dtype=torch.int64),
            torch.as_tensor(action_mask, dtype=torch.float32),
            int(self.dino_rows[(f_curr, curr_time)]),
            int(self.dino_rows[(f_goal, goal_time)]),
            torch.as_tensor(past_rows, dtype=torch.int64),
        )


def build_e_model(config, pos_dim):
    vision_encoder = replace_bn_with_gn(
        NoMaD_ViNT(
            obs_encoding_size=config["encoding_size"],
            context_size=config["context_size"],
            mha_num_attention_heads=config["mha_num_attention_heads"],
            mha_num_attention_layers=config["mha_num_attention_layers"],
            mha_ff_dim_factor=config["mha_ff_dim_factor"],
        )
    )
    noise_pred_net = ConditionalUnet1D(
        input_dim=2,
        global_cond_dim=config["encoding_size"] + pos_dim,
        down_dims=config["down_dims"],
        cond_predict_scale=config["cond_predict_scale"],
    )
    model = NoMaD(
        vision_encoder=vision_encoder,
        noise_pred_net=noise_pred_net,
        dist_pred_net=DenseNetwork(embedding_dim=config["encoding_size"]),
    )
    scheduler = DDPMScheduler(
        num_train_timesteps=config["num_diffusion_iters"],
        beta_schedule="squaredcos_cap_v2",
        clip_sample=True,
        prediction_type="epsilon",
    )
    return model, scheduler


def load_b_into_e(model_e, checkpoint_b, pos_dim, device):
    """Copy B weights; zero-init the new cond_encoder columns for the appended dims."""
    state_b = torch.load(checkpoint_b, map_location="cpu", weights_only=False)
    if isinstance(state_b, dict) and "state_dict" in state_b:
        state_b = state_b["state_dict"]
    state_e = model_e.state_dict()
    loaded = {}
    zeroed = 0
    for key, value in state_b.items():
        if key not in state_e:
            raise RuntimeError(f"B key missing in E: {key}")
        target = state_e[key]
        if value.shape == target.shape:
            loaded[key] = value
        elif (
            value.ndim == 2
            and target.shape[0] == value.shape[0]
            and target.shape[1] == value.shape[1] + pos_dim
        ):
            wide = torch.zeros_like(target)
            wide[:, : value.shape[1]] = value
            loaded[key] = wide
            zeroed += 1
        else:
            raise RuntimeError(f"Shape mismatch for {key}: B {tuple(value.shape)} vs E {tuple(target.shape)}")
    missing = set(state_e) - set(loaded)
    if missing:
        raise RuntimeError(f"E keys not filled from B: {sorted(missing)[:5]}")
    model_e.load_state_dict(loaded, strict=True)
    model_e.to(device)
    print(f"Loaded B into E; zero-initialized {zeroed} cond_encoder weight matrices (+{pos_dim} cols)")
    return model_e


def load_expand_cond(model_e, checkpoint, old_pos_dim, new_pos_dim, device, label='ckpt'):
    """Load a checkpoint trained with old_pos_dim; zero-fill extra cond columns to new_pos_dim."""
    state = torch.load(checkpoint, map_location='cpu', weights_only=False)
    if isinstance(state, dict) and 'state_dict' in state:
        state = state['state_dict']
    state_e = model_e.state_dict()
    loaded = {}
    zeroed = 0
    extra = int(new_pos_dim) - int(old_pos_dim)
    if extra < 0:
        raise ValueError(f'new_pos_dim {new_pos_dim} < old_pos_dim {old_pos_dim}')
    for key, value in state.items():
        if key not in state_e:
            raise RuntimeError(f'{label} key missing in E: {key}')
        target = state_e[key]
        if value.shape == target.shape:
            loaded[key] = value
        elif (
            extra > 0
            and value.ndim == 2
            and target.shape[0] == value.shape[0]
            and target.shape[1] == value.shape[1] + extra
        ):
            wide = torch.zeros_like(target)
            wide[:, : value.shape[1]] = value
            loaded[key] = wide
            zeroed += 1
        else:
            raise RuntimeError(
                f'Shape mismatch for {key}: {label} {tuple(value.shape)} vs E {tuple(target.shape)}'
            )
    missing = set(state_e) - set(loaded)
    if missing:
        raise RuntimeError(f'E keys not filled from {label}: {sorted(missing)[:5]}')
    model_e.load_state_dict(loaded, strict=True)
    model_e.to(device)
    print(f'Loaded {label} into E; zero-initialized {zeroed} cond matrices (+{extra} cols, {old_pos_dim}->{new_pos_dim})')
    return model_e


def load_dino_head(path, device):
    state = torch.load(path, map_location=device, weights_only=False)
    meta, run_args = state["meta"], state["args"]
    context = run_args.get("context", 0)
    multi = (run_args.get("multi_horizon") or "").strip()
    aux_horizons = tuple(int(x) for x in multi.split(",") if x.strip()) if multi else ()
    yaw_aux_steps = int(run_args.get("yaw_aux_steps", 0) or 0)
    path_steps = int(run_args.get("path_steps", 0) or 0)
    path_mlp = int(run_args.get("path_mlp", 0) or 0)
    path_residual = int(run_args.get("path_residual", 0) or 0)
    path_spatial = run_args.get("path_spatial", "") or ""
    odom_dim = int(run_args.get("odom_dim", 0) or 0)
    path_rot = bool(run_args.get("path_rot", False))
    head = PairTokenHead(
        meta["dim"],
        meta["tokens"],
        run_args["width"],
        run_args["layers"],
        run_args["heads"],
        run_args["dropout"],
        context,
        n_sectors=run_args.get("n_sectors", 0),
        aux_horizons=aux_horizons,
        yaw_aux_steps=yaw_aux_steps,
        path_steps=path_steps,
        path_mlp=path_mlp,
        path_residual=path_residual,
        path_spatial=path_spatial,
        odom_dim=odom_dim,
        path_rot=path_rot,
    ).to(device)
    head.load_state_dict(state["head"], strict=True)
    head.eval()
    head.requires_grad_(False)
    print(f"DINO head epoch {state['epoch']}, val far median {state['far_median_deg']:.1f} deg ({path})")
    return head, meta


def read_tokens(features, rows):
    rows = np.asarray(rows, dtype=np.int64)
    order = np.argsort(rows)
    out = np.empty((len(rows),) + features.shape[1:], dtype=np.float16)
    out[order] = features[rows[order]]
    return torch.from_numpy(out)


@torch.no_grad()
def estimated_goal_pos(
    loc_model,
    dino_head,
    features,
    batch_obs,
    batch_goal,
    curr_rows,
    goal_rows,
    pos_dim,
    device,
    wp_head=None,
    wp_scale=1.0,
    goal_pos_mode="goal",
    past_rows=None,
    path_gate="none",
    path_source="ray",
    meters_per_unit=0.12,
    path_units="meters",
    wp_odom=None,
    wp_path_head=None,
):
    """[mu_x, mu_y] or [mu_x, mu_y, sigma] in dataset units. Masked rows are zeroed by append_goal_pos.

    Distance always comes from the frozen B distance head (loc_model), matching the direct test.
    goal_pos_mode: goal = far DINO head only; blend = kappa-weighted goal + waypoint heads.
    path_source: ray = WP dir * 1..K; wp_poly = WP path_head xy / meters_per_unit.
    past_rows: optional [B, K] cache indices for curr-1..curr-K (needed when wp_head.context > 0).
    wp_path_head: optional separate frozen head for blend_path polyline only; mu blend always uses wp_head.
    """
    no_mask = torch.zeros(len(batch_obs), dtype=torch.long, device=device)
    cond = loc_model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
    steps = loc_model("dist_pred_net", obsgoal_cond=cond).squeeze(-1).clamp(min=0.0)
    curr = read_tokens(features, curr_rows).to(device).float()
    goal = read_tokens(features, goal_rows).to(device).float()
    dino_out = dino_head(curr, goal)
    direction, kappa = dino_out[0], dino_out[1]
    w_dir = w_k = None
    w_out = None
    if goal_pos_mode in ("blend", "blend_path"):
        if wp_head is None:
            raise ValueError(f"goal_pos_mode={goal_pos_mode} requires wp_head")
        w_out, w_dir, w_k = forward_wp_head(
            wp_head, features, curr_rows, goal_rows, past_rows, device, wp_odom=wp_odom
        )
        direction = blend_torch(direction, kappa, w_dir, w_k, wp_scale=wp_scale)
    elif goal_pos_mode != "goal":
        raise ValueError(f"unknown goal_pos_mode: {goal_pos_mode}")
    mu = direction * steps.unsqueeze(-1)
    if goal_pos_mode == "blend_path":
        # Stuff guessed near direction as an 8-step straight polyline in dataset units.
        # Step length 1 matches ViNT's normalized waypoint spacing.
        # dual_ambig: on dual-peak frames, replace with two 4-step sector-center paths.
        if w_dir is None:
            raise ValueError("blend_path missing wp direction")
        path_head = wp_path_head if wp_path_head is not None else wp_head
        path_out = w_out
        if path_head is not wp_head:
            path_out, path_w_dir, _path_w_k = forward_wp_head(
                path_head, features, curr_rows, goal_rows, past_rows, device, wp_odom=wp_odom
            )
            w_dir_for_ray = path_w_dir if path_source != "wp_poly" else w_dir
        else:
            w_dir_for_ray = w_dir
        path_flat = build_blend_path(
            w_dir_for_ray,
            pos_dim,
            path_gate=path_gate,
            kappa=kappa,
            w_k=w_k,
            wp_scale=wp_scale,
            wp_out=path_out,
            wp_head=path_head,
            path_source=path_source,
            meters_per_unit=meters_per_unit,
            path_units=path_units,
        )
        out = torch.cat([mu, path_flat], dim=-1)
        if out.shape[-1] != pos_dim:
            raise ValueError(f"blend_path width {out.shape[-1]} != pos_dim {pos_dim}")
        return out
    if pos_dim == 2:
        return mu
    if pos_dim == 3:
        sigma = (steps / kappa.clamp(min=1e-3).sqrt()).clamp(max=40.0)
        return torch.cat([mu, sigma.unsqueeze(-1)], dim=-1)
    raise ValueError(f"unsupported pos_dim={pos_dim} for mode={goal_pos_mode}")


def train_one_epoch(
    model,
    loc_model,
    ema,
    dino_head,
    wp_head,
    wp_path_head,
    features,
    loader,
    optimizer,
    scheduler_noise,
    device,
    args,
    epoch,
):
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    model.noise_pred_net.train()
    dino_head.eval()
    if wp_head is not None:
        wp_head.eval()
    if wp_path_head is not None:
        wp_path_head.eval()
    loss_sum, count = 0.0, 0
    goal_mask_prob = args.goal_mask_prob
    num_batches = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    with tqdm(loader, total=num_batches, desc=f"E epoch {epoch}", leave=False) as bar:
        for i, batch in enumerate(bar):
            if i >= num_batches:
                break
            (
                obs_image,
                goal_image,
                actions,
                _distance,
                goal_pos,
                _idx,
                action_mask,
                curr_rows,
                goal_rows,
                past_rows,
            ) = batch
            batch_obs, batch_goal = normalize_images(obs_image, goal_image, device)
            action_mask = action_mask.to(device)
            b = actions.shape[0]
            goal_mask = (torch.rand(b, device=device) < goal_mask_prob).long()
            with torch.no_grad():
                obsgoal_cond = model(
                    "vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=goal_mask
                )
                est_pos = estimated_goal_pos(
                    loc_model,
                    dino_head,
                    features,
                    batch_obs,
                    batch_goal,
                    curr_rows,
                    goal_rows,
                    args.pos_dim,
                    device,
                    wp_head=wp_head,
                    wp_path_head=wp_path_head,
                    wp_scale=args.wp_scale,
                    goal_pos_mode=args.goal_pos_mode,
                    past_rows=past_rows,
                    path_gate=args.path_gate,
                    path_source=args.path_source,
                    meters_per_unit=args.meters_per_unit,
                    path_units=args.path_units,
                )
                if args.true_pos_prob > 0:
                    use_true = torch.rand(b, device=device) < args.true_pos_prob
                    if use_true.any():
                        gp = goal_pos.to(device)
                        est_pos[use_true, :2] = gp[use_true]
                        if args.goal_pos_mode == "blend_path" and args.pos_dim > 2:
                            act = actions.to(device).float()[use_true, :, :2]
                            act = act.reshape(act.shape[0], -1)
                            n = min(act.shape[-1], args.pos_dim - 2)
                            est_pos[use_true, 2 : 2 + n] = act[:, :n]
                        elif args.pos_dim == 3:
                            est_pos[use_true, 2] = 0.0
            diffusion_cond = append_goal_pos(obsgoal_cond, est_pos, goal_mask)

            deltas = get_delta(actions)
            naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
            noise = torch.randn_like(naction)
            timesteps = torch.randint(0, scheduler_noise.config.num_train_timesteps, (b,), device=device).long()
            noisy = scheduler_noise.add_noise(naction, noise, timesteps)
            pred = model("noise_pred_net", sample=noisy, timestep=timesteps, global_cond=diffusion_cond)
            per = F.mse_loss(pred, noise, reduction="none").mean(dim=list(range(1, pred.ndim)))
            loss = (per * action_mask).mean() / (action_mask.mean() + 1e-2)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if getattr(args, "grad_clip", False):
                torch.nn.utils.clip_grad_norm_(model.noise_pred_net.parameters(), float(args.max_grad_norm))
            optimizer.step()
            ema.step(model)

            n = int(action_mask.sum().item())
            loss_sum += loss.item() * max(n, 1)
            count += max(n, 1)
            bar.set_postfix(loss=f"{loss.item():.4f}")
            if args.print_every > 0 and i % args.print_every == 0:
                print(f"(epoch {epoch}) (batch {i}/{num_batches - 1}) action loss {loss.item():.4f}")
    return loss_sum / max(count, 1)


def main():
    parser = argparse.ArgumentParser(description="Train E-μσ with DINO direction + B distance")
    parser.add_argument("--config", default="config/nomad_e_dino.yaml")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--init-from", choices=("b", "e_oracle"), default="b",
                        help="b: B weights, new cond columns zeroed. e_oracle: start from E-oracle (pos_dim 2)")
    parser.add_argument("--init-ckpt", default="", help="Optional E checkpoint to load instead of B/E-oracle")
    parser.add_argument("--checkpoint-e-oracle", default=E_ORACLE_CHECKPOINT)
    parser.add_argument("--true-pos-prob", type=float, default=0.0,
                        help="Per-sample probability of feeding the true goal_pos instead of the DINO estimate")
    parser.add_argument("--warmup-epochs", type=int, default=-1, help="-1 = use config")
    parser.add_argument("--dino-head", default=DINO_BEST)
    parser.add_argument("--wp-head", default=WP_BEST, help="Waypoint DINO head (for --goal-pos-mode blend)")
    parser.add_argument(
        "--wp-path-head",
        default="",
        help="Optional separate frozen WP head for blend_path 16-d path only; mu blend always uses --wp-head",
    )
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument(
        "--exclude-val-list",
        default="",
        help="Text file of trajectory names to drop from the training index (one per line)",
    )
    parser.add_argument(
        "--val-manifest-csv",
        default="",
        help="If set, run nav ADE val on this manifest after each epoch (true_pos_prob=0)",
    )
    parser.add_argument(
        "--goal-pos-mode",
        choices=("goal", "blend", "blend_path"),
        default="goal",
        help="goal / blend / blend_path(=blend far xy + wp-dir polyline)",
    )
    parser.add_argument(
        "--path-gate",
        choices=("none", "wp_vs_goal", "dual_ambig"),
        default="none",
        help="blend_path only: none | wp_vs_goal | dual_ambig (top-2 sector paths when dual-peak)",
    )
    parser.add_argument(
        "--path-source",
        choices=("ray", "wp_poly"),
        default="ray",
        help="blend_path: ray=WP dir*1..K; wp_poly=WP path_head 8-step xy",
    )
    parser.add_argument(
        "--path-units",
        choices=("meters", "dataset"),
        default="meters",
        help="wp_poly only: meters=divide path_head by meters_per_unit; dataset=already ViNT action units",
    )
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--pos-dim", type=int, default=0, help="2=E-μ, 3=E-μσ, 18=blend+path8, 0=config goal_pos_dim")
    parser.add_argument("--epochs", type=int, default=0, help="0 = use config")
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--lr", type=float, default=0.0)
    parser.add_argument("--goal-mask-prob", type=float, default=-1.0)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--print-every", type=int, default=100)
    parser.add_argument("--max-batches", type=int, default=0)
    parser.add_argument("--start-epoch", type=int, default=0, help="First epoch index when resuming")
    parser.add_argument("--run-name", default="")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.epochs > 0:
        config["epochs"] = args.epochs
    if args.batch_size > 0:
        config["batch_size"] = args.batch_size
    if args.lr > 0:
        config["lr"] = args.lr
    if args.warmup_epochs >= 0:
        config["warmup_epochs"] = args.warmup_epochs
    args.goal_mask_prob = config["goal_mask_prob"] if args.goal_mask_prob < 0 else args.goal_mask_prob
    args.grad_clip = bool(config.get("clipping", False))
    args.max_grad_norm = float(config.get("max_norm", 1.0))
    args.pos_dim = args.pos_dim or int(config.get("goal_pos_dim", 3))
    if args.pos_dim != int(config.get("goal_pos_dim", args.pos_dim)):
        raise ValueError(f"--pos-dim {args.pos_dim} disagrees with {args.config} goal_pos_dim; eval reads the config")
    if args.init_from == "e_oracle" and args.pos_dim < 2:
        raise ValueError("E-oracle base is pos_dim 2; need pos_dim >= 2")
    if args.goal_pos_mode == "blend_path" and args.pos_dim < 4:
        raise ValueError("blend_path needs pos_dim >= 4 (far xy + at least one path point)")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    blend_tag = {"blend": "_blend", "blend_path": "_blendpath"}.get(args.goal_pos_mode, "")
    tag = f"d{args.pos_dim}_{args.init_from}_true{int(round(100 * args.true_pos_prob))}{blend_tag}"
    run_name = args.run_name or f"nomad_e_dino_{tag}_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    output_dir = os.path.join("logs", "nomad", run_name)
    os.makedirs(output_dir, exist_ok=True)
    print(
        f"device: {device}\noutput: {os.path.abspath(output_dir)}\npos_dim: {args.pos_dim} | init {args.init_from} | "
        f"true_pos_prob {args.true_pos_prob} | goal_pos_mode {args.goal_pos_mode} | "
        f"path_gate {args.path_gate} | path_source {args.path_source} | path_units {args.path_units} | wp_scale {args.wp_scale} | "
        f"init_ckpt {args.init_ckpt or args.init_from} | "
        f"lr {config['lr']} | epochs {config['epochs']} | warmup {config.get('warmup_epochs', 4)} | "
        f"grad_clip {args.grad_clip} max_norm {args.max_grad_norm} | wd 1e-4"
    )

    cache_path, rows, meta = load_cache(args.cache_dir, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    dino_head, dino_meta = load_dino_head(args.dino_head, device)
    wp_head = wp_path_head = None
    if args.goal_pos_mode in ("blend", "blend_path"):
        wp_head, wp_meta = load_dino_head(args.wp_head, device)
        for key in ("model", "width", "height", "pool"):
            if wp_meta[key] != meta[key]:
                raise RuntimeError(f"WP cache {key}={meta[key]} vs head {wp_meta[key]}")
        if args.path_source == "wp_poly" and int(getattr(wp_head, "path_steps", 0) or 0) <= 0:
            raise ValueError(f"path_source=wp_poly but WP head has no path_steps: {args.wp_head}")
        if args.wp_path_head:
            wp_path_head, wp_path_meta = load_dino_head(args.wp_path_head, device)
            for key in ("model", "width", "height", "pool"):
                if wp_path_meta[key] != meta[key]:
                    raise RuntimeError(f"WP path cache {key}={meta[key]} vs head {wp_path_meta[key]}")
            if int(getattr(wp_path_head, "path_steps", 0) or 0) <= 0:
                raise ValueError(f"--wp-path-head missing path_steps: {args.wp_path_head}")
            print(f"Decoupled cond: mu from {args.wp_head} | path from {args.wp_path_head}")
    for key in ("model", "width", "height", "pool"):
        if dino_meta[key] != meta[key]:
            raise RuntimeError(f"DINO cache {key}={meta[key]} vs head {dino_meta[key]}")

    data_config = config["datasets"]["go_stanford"]
    dataset = ViNTWithDinoRows(
        data_folder=data_config["data_folder"],
        data_split_folder=data_config["train"],
        dataset_name="go_stanford",
        image_size=config["image_size"],
        waypoint_spacing=data_config.get("waypoint_spacing", 1),
        min_dist_cat=config["distance"]["min_dist_cat"],
        max_dist_cat=config["distance"]["max_dist_cat"],
        min_action_distance=config["action"]["min_dist_cat"],
        max_action_distance=config["action"]["max_dist_cat"],
        negative_mining=data_config.get("negative_mining", True),
        len_traj_pred=config["len_traj_pred"],
        learn_angle=config["learn_angle"],
        context_size=config["context_size"],
        context_type=config.get("context_type", "temporal"),
        end_slack=data_config.get("end_slack", 0),
        goals_per_obs=data_config.get("goals_per_obs", 1),
        normalize=config["normalize"],
        goal_type=config.get("goal_type", "image"),
        dino_rows=rows,
    )
    if args.exclude_val_list:
        with open(args.exclude_val_list, encoding="utf-8") as vf:
            val_trajs = {line.strip() for line in vf if line.strip()}
        before = len(dataset.index_to_data)
        dataset.index_to_data = [x for x in dataset.index_to_data if x[0] not in val_trajs]
        dataset.dataset_index = np.arange(len(dataset.index_to_data))
        print(f"exclude_val_list: dropped {before - len(dataset.index_to_data)} / {before} train index rows")
    loader = DataLoader(
        dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=args.num_workers,
        persistent_workers=args.num_workers > 0,
        drop_last=True,
    )
    args.meters_per_unit = float(meters_per_unit(dataset))
    print(f"train samples: {len(dataset)}, meters/unit: {args.meters_per_unit:.3f}")

    model, noise_scheduler = build_e_model(config, args.pos_dim)
    if args.init_ckpt:
        state = torch.load(args.init_ckpt, map_location="cpu", weights_only=False)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state, strict=True)
        model.to(device)
        print(f"Loaded init ckpt (strict): {args.init_ckpt}")
        loc_model = load_frozen_nomad(load_config(args.config_b), args.checkpoint_b, device)
    elif args.init_from == "b":
        load_b_into_e(model, args.checkpoint_b, args.pos_dim, device)
        loc_model = model
    else:
        if args.pos_dim == 2:
            state = torch.load(args.checkpoint_e_oracle, map_location="cpu", weights_only=False)
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state, strict=True)
            model.to(device)
            print(f"Loaded E-oracle into E (strict): {args.checkpoint_e_oracle}")
        else:
            load_expand_cond(model, args.checkpoint_e_oracle, 2, args.pos_dim, device, label='e_oracle')
        loc_model = load_frozen_nomad(load_config(args.config_b), args.checkpoint_b, device)
    model.vision_encoder.requires_grad_(False)
    model.dist_pred_net.requires_grad_(False)
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    trainable = [(n, p) for n, p in model.noise_pred_net.named_parameters() if p.requires_grad]
    print(f"Trainable UNet params: {sum(p.numel() for _, p in trainable) / 1e6:.2f}M ({len(trainable)} tensors)")
    for n, p in trainable[:8]:
        print(f"  trainable: {n} {tuple(p.shape)}")
    if len(trainable) > 8:
        print(f"  ... ({len(trainable) - 8} more)")
    print(f"optimizer: AdamW lr={config['lr']} weight_decay=1e-4")

    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=float(config["lr"]), weight_decay=1e-4)
    total_epochs = int(config["epochs"])
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(total_epochs, 1))
    warmup_epochs = int(config.get("warmup_epochs", 4))
    if warmup_epochs > 0:
        lr_scheduler = GradualWarmupScheduler(
            optimizer, multiplier=1, total_epoch=warmup_epochs, after_scheduler=cosine
        )
    else:
        lr_scheduler = cosine
    ema = EMAModel(model=model, power=0.75)
    if args.start_epoch > 0 and args.init_ckpt:
        ema_state = torch.load(args.init_ckpt, map_location="cpu", weights_only=False)
        if isinstance(ema_state, dict) and "state_dict" in ema_state:
            ema_state = ema_state["state_dict"]
        ema.averaged_model.load_state_dict(ema_state, strict=True)
        print(f"Loaded EMA from resume: {args.init_ckpt}")

    log_path = os.path.join(output_dir, "train_log.csv")
    log_rows = []
    if args.start_epoch > 0 and os.path.isfile(log_path):
        log_rows = list(csv.DictReader(open(log_path, encoding="utf-8")))
    train_root = os.path.dirname(os.path.abspath(__file__))
    for _ in range(args.start_epoch):
        lr_scheduler.step()
    for epoch in range(args.start_epoch, total_epochs):
        start = time.time()
        train_loss = train_one_epoch(
            model,
            loc_model,
            ema,
            dino_head,
            wp_head,
            wp_path_head,
            features,
            loader,
            optimizer,
            noise_scheduler,
            device,
            args,
            epoch,
        )
        lr_scheduler.step()

        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, f"ema_{epoch}.pth"))
        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, "ema_latest.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, f"{epoch}.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, "latest.pth"))
        row = {
            "epoch": epoch,
            "train_action_loss": train_loss,
            "lr": optimizer.param_groups[0]["lr"],
            "minutes": (time.time() - start) / 60,
            "train_batches": len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches),
            "train_samples_index": len(dataset),
        }
        if args.val_manifest_csv:
            val_json = os.path.join(output_dir, f"val_nav_epoch{epoch}.json")
            val_cmd = [
                sys.executable,
                "-u",
                os.path.join(train_root, "eval_e_path_adapt_val.py"),
                "--checkpoint",
                os.path.join(output_dir, f"ema_{epoch}.pth"),
                "--manifest-csv",
                args.val_manifest_csv,
                "--dino-head",
                args.dino_head,
                "--wp-head",
                args.wp_head,
                "--config-e-dino",
                args.config,
                "--config-b",
                args.config_b,
                "--path-units",
                args.path_units,
                "--path-source",
                args.path_source,
                "--path-gate",
                args.path_gate,
                "--goal-pos-mode",
                args.goal_pos_mode,
                "--wp-scale",
                str(args.wp_scale),
                "--pos-dim",
                str(args.pos_dim),
                "--epoch",
                str(epoch),
                "--out-dir",
                output_dir,
                "--out-json",
                val_json,
            ]
            if args.wp_path_head:
                val_cmd.extend(["--wp-path-head", args.wp_path_head])
            env = os.environ.copy()
            dp = os.path.join(os.path.dirname(train_root), "diffusion_policy")
            env["PYTHONPATH"] = dp if not env.get("PYTHONPATH") else dp + os.pathsep + env["PYTHONPATH"]
            subprocess.run(val_cmd, cwd=train_root, check=True, env=env)
            with open(val_json, encoding="utf-8") as vf:
                val_out = json.load(vf)
            row["val_nav_ade_cm"] = val_out["nav_ade_cm"]
            row["val_nav_per_frame_csv"] = val_out.get("per_frame_csv", "")
        log_rows.append(row)
        with open(os.path.join(output_dir, "train_log.csv"), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerows(log_rows)
        print(f"[epoch {epoch}] action loss {train_loss:.4f} | lr {row['lr']:.2e} | {row['minutes']:.1f} min")

    with open(os.path.join(output_dir, "args.txt"), "w") as f:
        f.write(f"checkpoint_b={args.checkpoint_b}\ndino_head={args.dino_head}\npos_dim={args.pos_dim}\n")
        f.write(f"goal_pos_mode={args.goal_pos_mode}\npath_gate={args.path_gate}\n")
        f.write(f"path_source={args.path_source}\ninit_ckpt={args.init_ckpt}\n")
        f.write(f"wp_head={args.wp_head}\nwp_path_head={args.wp_path_head}\nwp_scale={args.wp_scale}\n")
        f.write(f"exclude_val_list={args.exclude_val_list}\nval_manifest_csv={args.val_manifest_csv}\n")
        f.write(f"cache={args.cache_dir}\ngoal_mask_prob={args.goal_mask_prob}\n")
        f.write(f"init_from={args.init_from}\ncheckpoint_e_oracle={args.checkpoint_e_oracle}\n")
        f.write(f"true_pos_prob={args.true_pos_prob}\nlr={config['lr']}\nepochs={config['epochs']}\n")
    print(f"Done. Checkpoints in {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

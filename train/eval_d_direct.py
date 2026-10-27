"""Feed D-derived goal positions to the existing E-oracle. No training.

Part 1, position error on all three distance groups against two baselines
that do not know the group:
  global mean   one position for every frame (pooled mean of the paired targets)
  B dist ahead  B distance head steps * 0.12 m, straight ahead

Part 2, far group only. The same E-oracle Epoch 29 weights, the same
diffusion noise, and one masked run. Only the appended goal_pos changes:
  clean                       true direction, true distance
  D mu                        D direction, D distance
  D dir + true dist           isolates the direction error
  true dir + D dist           isolates the distance error
  D dir + B dist              repairs distance without training
  true dir + B dist           how good B's distance head is on its own

E-oracle was trained on clean coordinates, so every D-based row is a lower
bound on what an E trained with D inputs would reach.

Run from train/:

    python -u eval_d_direct.py --head logs/nomad_d/<run>/goal_head_7.pth
"""

import argparse
import os

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import (
    B_CHECKPOINT,
    encode,
    load_frozen_nomad,
    load_head,
    make_split_dataset,
    meters_per_unit,
    normalize_images,
    write_csv,
)
from eval_position_noise import (
    boot_mean,
    diffuse,
    encode_cond,
    load_model,
    mean_ade_fde,
    subset_index,
)
from vint_train.training.train_utils import append_goal_pos

E_CHECKPOINT = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth"
GROUP_ORDER = ("4-8", "9-19", "20-40")
VARIANTS = (
    "clean",
    "D mu",
    "D dir + true dist",
    "true dir + D dist",
    "D dir + B dist",
    "true dir + B dist",
)


def unit(vectors):
    norm = np.linalg.norm(vectors, axis=1, keepdims=True)
    ahead = np.tile(np.array([[1.0, 0.0]]), (len(vectors), 1))
    return np.where(norm > 1e-6, vectors / np.maximum(norm, 1e-6), ahead)


def build_variants(target, mu, b_dist):
    """All inputs in meters. Returns name -> [N, 2] positions in meters."""
    true_dir, d_dir = unit(target), unit(mu)
    true_len = np.linalg.norm(target, axis=1, keepdims=True)
    d_len = np.linalg.norm(mu, axis=1, keepdims=True)
    b_len = b_dist[:, None]
    return {
        "clean": target,
        "D mu": mu,
        "D dir + true dist": d_dir * true_len,
        "true dir + D dist": true_dir * d_len,
        "D dir + B dist": d_dir * b_len,
        "true dir + B dist": true_dir * b_len,
    }


@torch.no_grad()
def b_and_d_predictions(model_b, head, dataset, moments, device, batch_size):
    """B distance head (meters) and D mu (meters) for every (frame, group)."""
    meters = meters_per_unit(dataset)
    items = []
    for frame_index, (traj_name, t, goals) in enumerate(moments):
        for name, _lo, _hi, _k, goal_time in goals:
            items.append((frame_index, traj_name, t, name, goal_time))
    out = {"frame_index": [], "group": [], "target": [], "mu": [], "b_dist": []}
    for start in tqdm(range(0, len(items), batch_size), desc="B + D", leave=False):
        chunk = items[start : start + batch_size]
        obs_list, goal_list, pos_list = [], [], []
        for _frame, traj_name, t, _name, goal_time in chunk:
            obs, goal, _actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
            pos_list.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        cond = encode(model_b, batch_obs, batch_goal)
        mu, _sigma = head(cond)
        steps = model_b("dist_pred_net", obsgoal_cond=cond).squeeze(-1)
        out["frame_index"] += [item[0] for item in chunk]
        out["group"] += [item[3] for item in chunk]
        out["target"].append(np.stack(pos_list) * meters)
        out["mu"].append(mu.cpu().numpy())
        out["b_dist"].append(np.clip(steps.cpu().numpy(), 0.0, None) * meters)
    return {
        "frame_index": np.array(out["frame_index"]),
        "group": np.array(out["group"]),
        "target": np.concatenate(out["target"]),
        "mu": np.concatenate(out["mu"]),
        "b_dist": np.concatenate(out["b_dist"]),
    }


def bearing_error_deg(a, b):
    diff = np.abs(np.arctan2(a[:, 1], a[:, 0]) - np.arctan2(b[:, 1], b[:, 0]))
    return np.degrees(np.minimum(diff, 2.0 * np.pi - diff))


def position_table(pred):
    global_mean = pred["target"].mean(axis=0)
    ahead = np.zeros_like(pred["target"])
    ahead[:, 0] = pred["b_dist"]
    sources = {
        "D mu": pred["mu"],
        "global mean": np.tile(global_mean, (len(pred["target"]), 1)),
        "B dist ahead": ahead,
        "D dir + B dist": unit(pred["mu"]) * pred["b_dist"][:, None],
    }
    rows = []
    for group in GROUP_ORDER:
        mask = pred["group"] == group
        target = pred["target"][mask]
        true_len = np.linalg.norm(target, axis=1)
        for name, position in sources.items():
            pos = position[mask]
            err = np.linalg.norm(pos - target, axis=1)
            pos_len = np.linalg.norm(pos, axis=1)
            rows.append(
                {
                    "group": group,
                    "source": name,
                    "n": int(mask.sum()),
                    "true_dist_m": float(true_len.mean()),
                    "pred_dist_m": float(pos_len.mean()),
                    "err_mean_m": float(err.mean()),
                    "err_median_m": float(np.median(err)),
                    "dist_ratio_median": float(np.median(pos_len / np.maximum(true_len, 1e-6))),
                    "bearing_err_median_deg": float(np.median(bearing_error_deg(pos, target))),
                }
            )
    return rows, global_mean


@torch.no_grad()
def run_e_oracle(model_e, scheduler_e, dataset, far, positions_m, device, num_samples, batch_size, variants=VARIANTS):
    meters = meters_per_unit(dataset)
    n = len(far)
    ade = {name: np.zeros(n) for name in variants}
    fde = {name: np.zeros(n) for name in variants}
    ade_mask, fde_mask = np.zeros(n), np.zeros(n)
    horizon = dataset.len_traj_pred
    for start in tqdm(range(0, n, batch_size), desc="E-oracle far", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list, gt_list, pos_list = [], [], [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
            gt_list.append(actions[:, :2])
            pos_list.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = torch.randn((len(chunk) * num_samples, horizon, 2), device=device)
        cond_goal, mask_goal = encode_cond(model_e, batch_obs, batch_goal, 0, device)
        cond_mask, mask_mask = encode_cond(model_e, batch_obs, batch_goal, 1, device)
        clean_units = torch.tensor(np.stack(pos_list), dtype=torch.float32, device=device)
        pred_mask = diffuse(
            model_e, scheduler_e, append_goal_pos(cond_mask, clean_units, mask_mask), noise, num_samples, device
        )
        preds = {}
        for name in variants:
            pos_units = torch.tensor(
                positions_m[name][start : start + len(chunk)] / meters, dtype=torch.float32, device=device
            )
            preds[name] = diffuse(
                model_e, scheduler_e, append_goal_pos(cond_goal, pos_units, mask_goal), noise, num_samples, device
            )
        for i, gt in enumerate(gt_list):
            index = start + i
            ade_mask[index], fde_mask[index] = mean_ade_fde(pred_mask[i], gt, meters)
            for name in variants:
                ade[name][index], fde[name][index] = mean_ade_fde(preds[name][i], gt, meters)
    return ade, fde, ade_mask, fde_mask


def fmt(mean, lo, hi, scale=100.0):
    return f"{scale * mean:+.2f} [{scale * lo:+.2f}, {scale * hi:+.2f}]"


def main():
    parser = argparse.ArgumentParser(description="Direct test: D-derived goal_pos into E-oracle")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e", default=E_CHECKPOINT)
    parser.add_argument("--head", required=True)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    output_dir = args.output_dir or os.path.join(os.path.dirname(args.head), "eval_direct_e_oracle")
    os.makedirs(output_dir, exist_ok=True)

    config_b = load_config(args.config_b)
    config_e = load_config(args.config_e)
    if not config_e.get("goal_pos_oracle"):
        raise RuntimeError("E-oracle config must set goal_pos_oracle: true")
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)

    model_b = load_frozen_nomad(config_b, args.checkpoint_b, device)
    head = load_head(args.head, config_b["encoding_size"], device)
    pred = b_and_d_predictions(model_b, head, dataset, moments, device, 64)

    rows, global_mean = position_table(pred)
    print(f"\nPart 1. Position error, meters. Global mean position = ({global_mean[0]:.2f}, {global_mean[1]:.2f}) m")
    print("dist ratio = median of predicted / true distance. bearing = median direction error.")
    print(f"{'group':<7}{'source':<17}{'true m':>8}{'pred m':>8}{'mean err':>10}{'median':>8}{'ratio':>7}{'bearing':>9}")
    for row in rows:
        bearing = f"{row['bearing_err_median_deg']:.1f}"
        print(
            f"{row['group']:<7}{row['source']:<17}{row['true_dist_m']:8.2f}{row['pred_dist_m']:8.2f}"
            f"{row['err_mean_m']:10.3f}{row['err_median_m']:8.3f}{row['dist_ratio_median']:7.2f}{bearing:>9}"
        )
    print("global mean and B dist ahead use a fixed direction, so their bearing error is the spread of true bearings.")
    write_csv(os.path.join(output_dir, "position_baselines.csv"), rows)

    far_mask = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far_mask], kind="stable")
    far_target = pred["target"][far_mask][order]
    far_mu = pred["mu"][far_mask][order]
    far_bdist = pred["b_dist"][far_mask][order]
    positions = build_variants(far_target, far_mu, far_bdist)
    far = []
    for traj_name, t, goals in moments:
        goal_time = [g[4] for g in goals if g[0] == "20-40"][0]
        far.append((traj_name, t, goal_time))

    model_e, scheduler_e = load_model(config_e, args.checkpoint_e, device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    ade, fde, ade_mask, fde_mask = run_e_oracle(
        model_e, scheduler_e, dataset, far, positions, device, args.num_samples, args.batch_size
    )

    rng = np.random.default_rng(args.seed + 1)
    summary = []
    print("\nPart 2. Far group (20-40), E-oracle Epoch 29, shared noise. Values in cm.")
    print("use = masked ADE - ADE with this goal_pos. vs clean = ADE(clean) - ADE(this), negative means worse.")
    for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
        if set_name not in sets:
            continue
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        clean_use = ade_mask[idx] - ade["clean"][idx]
        clean_mean = float(clean_use.mean())
        print(f"\n[{set_name}] n={len(idx)}  masked ADE {100 * ade_mask[idx].mean():.2f} cm")
        print(f"{'goal_pos':<20}{'pos err m':>10}{'ADE':>8}{'ADE use':>24}{'kept':>7}{'FDE use':>24}{'vs clean':>24}")
        for name in VARIANTS:
            use = ade_mask[idx] - ade[name][idx]
            fuse = fde_mask[idx] - fde[name][idx]
            gap = ade["clean"][idx] - ade[name][idx]
            u = boot_mean(use, boot)
            fu = boot_mean(fuse, boot)
            g = boot_mean(gap, boot)
            pos_err = float(np.linalg.norm(positions[name][idx] - far_target[idx], axis=1).mean())
            kept = u[0] / clean_mean if clean_mean > 0 else float("nan")
            print(
                f"{name:<20}{pos_err:10.2f}{100 * ade[name][idx].mean():8.2f}{fmt(*u):>24}"
                f"{100 * kept:6.0f}%{fmt(*fu):>24}{fmt(*g):>24}"
            )
            summary.append(
                {
                    "frames": set_name,
                    "goal_pos": name,
                    "n": int(len(idx)),
                    "position_error_m": pos_err,
                    "ade_m": float(ade[name][idx].mean()),
                    "ade_mask_m": float(ade_mask[idx].mean()),
                    "ade_use_m": u[0],
                    "ade_use_lo": u[1],
                    "ade_use_hi": u[2],
                    "kept_fraction": kept,
                    "fde_use_m": fu[0],
                    "fde_use_lo": fu[1],
                    "fde_use_hi": fu[2],
                    "ade_gap_vs_clean_m": g[0],
                    "ade_gap_lo": g[1],
                    "ade_gap_hi": g[2],
                }
            )
    write_csv(os.path.join(output_dir, "direct_test.csv"), summary)
    np.savez_compressed(
        os.path.join(output_dir, "per_frame.npz"),
        target=far_target,
        mu=far_mu,
        b_dist=far_bdist,
        ade_mask=ade_mask,
        fde_mask=fde_mask,
        **{f"ade_{i}": ade[name] for i, name in enumerate(VARIANTS)},
        **{f"fde_{i}": fde[name] for i, name in enumerate(VARIANTS)},
        variants=np.array(VARIANTS),
    )
    print(f"\nSaved to {os.path.abspath(output_dir)}")
    print("E-oracle saw only clean coordinates in training, so D-based rows are a lower bound for a trained E.")


if __name__ == "__main__":
    main()

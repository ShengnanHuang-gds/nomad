"""Evaluate D-ft on the locked paired frames, then feed it to E-oracle.

Part 1, bearing error (degrees) by goal distance and on the fixed frame sets,
for D-ft, the frozen D (GoalPosHead on B features), and straight ahead.
Part 2, kappa calibration on the far group.
Part 3, far group into E-oracle Epoch 29 with shared noise. Distance always
comes from B's distance head except where a row says true distance.

Run from train/:

    python -u eval_goal_dir.py --run-dir logs/nomad_d/<dft run>
"""

import argparse
import os

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT, run_e_oracle, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import (
    B_CHECKPOINT,
    encode,
    load_frozen_nomad,
    load_head,
    make_split_dataset,
    meters_per_unit,
    normalize_images,
    spearman,
    write_csv,
)
from eval_position_noise import boot_mean, load_model, subset_index
from train_goal_dir import encode_d
from vint_train.models.nomad.nomad import GoalDirectionHead

FROZEN_D = "logs/nomad_d/nomad_d_2026_10_13_13_51_35/goal_head_7.pth"
GROUP_ORDER = ("4-8", "9-19", "20-40")
E_VARIANTS = (
    "clean",
    "D-ft dir + B dist",
    "D-ft dir + true dist",
    "frozen D dir + B dist",
    "true dir + B dist",
)


def load_dft(config, checkpoint_b, path, device):
    nomad = load_frozen_nomad(config, checkpoint_b, device)
    encoder = nomad.vision_encoder
    del nomad
    state = torch.load(path, map_location=device, weights_only=False)
    encoder.load_state_dict(state["vision_encoder"])
    head = GoalDirectionHead(config["encoding_size"])
    head.load_state_dict(state["head"])
    print(f"D-ft loaded: {path} (epoch {state['epoch']}, val far median {state['val_far_median_deg']:.1f} deg)")
    return encoder.eval(), head.to(device).eval(), state["epoch"]


def bearing_deg(xy):
    return np.degrees(np.arctan2(xy[:, 1], xy[:, 0]))


def angle_diff_deg(a, b):
    diff = np.abs(a - b) % 360.0
    return np.minimum(diff, 360.0 - diff)


@torch.no_grad()
def predict(model_b, frozen_head, encoder_d, head_d, dataset, moments, device, batch_size):
    meters = meters_per_unit(dataset)
    items = []
    for frame_index, (traj_name, t, goals) in enumerate(moments):
        for name, _lo, _hi, _k, goal_time in goals:
            items.append((frame_index, traj_name, t, name, goal_time))
    out = {key: [] for key in ("target", "dft_dir", "kappa", "frozen_mu", "b_dist")}
    for start in tqdm(range(0, len(items), batch_size), desc="B + D + D-ft", leave=False):
        chunk = items[start : start + batch_size]
        obs_list, goal_list, pos_list = [], [], []
        for _frame, traj_name, t, _name, goal_time in chunk:
            obs, goal, _actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
            pos_list.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        cond_b = encode(model_b, batch_obs, batch_goal)
        frozen_mu, _sigma = frozen_head(cond_b)
        steps = model_b("dist_pred_net", obsgoal_cond=cond_b).squeeze(-1)
        direction, kappa = head_d(encode_d(encoder_d, batch_obs, batch_goal))
        out["target"].append(np.stack(pos_list) * meters)
        out["frozen_mu"].append(frozen_mu.cpu().numpy())
        out["b_dist"].append(np.clip(steps.cpu().numpy(), 0.0, None) * meters)
        out["dft_dir"].append(direction.cpu().numpy())
        out["kappa"].append(kappa.cpu().numpy())
    pred = {key: np.concatenate(value) for key, value in out.items()}
    pred["frame_index"] = np.array([item[0] for item in items])
    pred["group"] = np.array([item[3] for item in items])
    return pred


def bearing_table(pred, sets):
    true_bearing = bearing_deg(pred["target"])
    sources = {
        "D-ft": angle_diff_deg(bearing_deg(pred["dft_dir"]), true_bearing),
        "frozen D": angle_diff_deg(bearing_deg(pred["frozen_mu"]), true_bearing),
        "straight ahead": np.abs(true_bearing),
    }
    rows = []
    for group in GROUP_ORDER:
        in_group = pred["group"] == group
        for set_name, frame_mask in sets.items():
            if group != "20-40" and set_name != "all":
                continue
            mask = in_group & frame_mask[pred["frame_index"]]
            for source, err in sources.items():
                rows.append(
                    {
                        "group": group,
                        "frames": set_name,
                        "source": source,
                        "n": int(mask.sum()),
                        "median_deg": float(np.median(err[mask])),
                        "mean_deg": float(err[mask].mean()),
                        "within_15deg": float((err[mask] <= 15.0).mean()),
                    }
                )
    return rows


def kappa_bins(pred, bins=5):
    mask = pred["group"] == "20-40"
    err = angle_diff_deg(bearing_deg(pred["dft_dir"][mask]), bearing_deg(pred["target"][mask]))
    kappa = pred["kappa"][mask]
    edges = np.quantile(kappa, np.linspace(0.0, 1.0, bins + 1))
    which = np.clip(np.searchsorted(edges, kappa, side="right") - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        sel = which == b
        rows.append(
            {
                "bin": b,
                "n": int(sel.sum()),
                "kappa_mean": float(kappa[sel].mean()),
                "implied_std_deg": float(np.degrees(1.0 / np.sqrt(kappa[sel].mean()))),
                "median_err_deg": float(np.median(err[sel])),
                "mean_err_deg": float(err[sel].mean()),
            }
        )
    return rows, spearman(kappa, err)


def fmt(stats):
    mean, lo, hi = stats
    return f"{100 * mean:+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}]"


def main():
    parser = argparse.ArgumentParser(description="Evaluate D-ft and feed it to E-oracle")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e", default=E_CHECKPOINT)
    parser.add_argument("--frozen-head", default=FROZEN_D)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="goal_dir_best.pth", help="File inside --run-dir")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_e = load_config(args.config_e)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)
    output_dir = os.path.join(args.run_dir, f"eval_{os.path.splitext(args.checkpoint)[0]}")
    os.makedirs(output_dir, exist_ok=True)

    model_b = load_frozen_nomad(config_b, args.checkpoint_b, device)
    frozen_head = load_head(args.frozen_head, config_b["encoding_size"], device)
    encoder_d, head_d, epoch = load_dft(config_b, args.checkpoint_b, os.path.join(args.run_dir, args.checkpoint), device)
    pred = predict(model_b, frozen_head, encoder_d, head_d, dataset, moments, device, 64)
    del encoder_d
    torch.cuda.empty_cache()

    rows = bearing_table(pred, sets)
    print(f"\nPart 1. Bearing error on the locked frames (D-ft epoch {epoch}), degrees.")
    print(f"{'group':<7}{'frames':<28}{'source':<16}{'n':>6}{'median':>8}{'mean':>8}{'<=15deg':>9}")
    for row in rows:
        print(
            f"{row['group']:<7}{row['frames']:<28}{row['source']:<16}{row['n']:>6}"
            f"{row['median_deg']:8.1f}{row['mean_deg']:8.1f}{100 * row['within_15deg']:8.0f}%"
        )
    write_csv(os.path.join(output_dir, "bearing_error.csv"), rows)

    calib, rho = kappa_bins(pred)
    print(f"\nPart 2. Far kappa calibration (Spearman kappa vs error {rho:+.2f}; negative is good).")
    print(f"{'bin':>4}{'n':>6}{'kappa':>9}{'~std deg':>10}{'median err':>12}{'mean err':>10}")
    for row in calib:
        print(
            f"{row['bin']:>4}{row['n']:>6}{row['kappa_mean']:9.2f}{row['implied_std_deg']:10.1f}"
            f"{row['median_err_deg']:12.1f}{row['mean_err_deg']:10.1f}"
        )
    write_csv(os.path.join(output_dir, "kappa_calibration_far.csv"), calib)

    far_mask = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far_mask], kind="stable")
    target = pred["target"][far_mask][order]
    dft_dir = pred["dft_dir"][far_mask][order]
    frozen_dir = unit(pred["frozen_mu"][far_mask][order])
    b_len = pred["b_dist"][far_mask][order][:, None]
    true_len = np.linalg.norm(target, axis=1, keepdims=True)
    positions = {
        "clean": target,
        "D-ft dir + B dist": dft_dir * b_len,
        "D-ft dir + true dist": dft_dir * true_len,
        "frozen D dir + B dist": frozen_dir * b_len,
        "true dir + B dist": unit(target) * b_len,
    }
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]

    model_e, scheduler_e = load_model(config_e, args.checkpoint_e, device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    ade, fde, ade_mask, fde_mask = run_e_oracle(
        model_e, scheduler_e, dataset, far, positions, device, args.num_samples, args.batch_size, E_VARIANTS
    )

    rng = np.random.default_rng(args.seed + 1)
    summary = []
    print("\nPart 3. Far group into E-oracle Epoch 29, shared noise. cm. use = masked ADE - ADE.")
    for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
        if set_name not in sets:
            continue
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        clean_use = float((ade_mask[idx] - ade["clean"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}  masked ADE {100 * ade_mask[idx].mean():.2f} cm")
        print(f"{'goal_pos':<24}{'ADE':>8}{'ADE use':>24}{'kept':>7}{'FDE use':>24}")
        for name in E_VARIANTS:
            use = boot_mean(ade_mask[idx] - ade[name][idx], boot)
            fuse = boot_mean(fde_mask[idx] - fde[name][idx], boot)
            kept = use[0] / clean_use if clean_use > 0 else float("nan")
            print(f"{name:<24}{100 * ade[name][idx].mean():8.2f}{fmt(use):>24}{100 * kept:6.0f}%{fmt(fuse):>24}")
            summary.append(
                {
                    "frames": set_name,
                    "goal_pos": name,
                    "n": int(len(idx)),
                    "ade_m": float(ade[name][idx].mean()),
                    "ade_use_m": use[0],
                    "ade_use_lo": use[1],
                    "ade_use_hi": use[2],
                    "kept_fraction": kept,
                    "fde_use_m": fuse[0],
                    "fde_use_lo": fuse[1],
                    "fde_use_hi": fuse[2],
                }
            )
    write_csv(os.path.join(output_dir, "e_oracle_direct.csv"), summary)
    np.savez_compressed(os.path.join(output_dir, "predictions.npz"), **pred)
    print(f"\nSaved to {os.path.abspath(output_dir)}")
    print("E-oracle saw only clean coordinates in training, so D-ft rows are a lower bound for a trained E.")


if __name__ == "__main__":
    main()

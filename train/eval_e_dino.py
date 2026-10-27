"""Paired far-group eval of E-dino (DINO dir + B dist, optional sigma) vs B and E-oracle.

Uses the locked 1000 frames, shared diffusion noise, N=8. The appended condition
for E-dino is [mu_x, mu_y] or [mu_x, mu_y, sigma] in dataset units from the
frozen DINO head and B distance head (same recipe as training). E-oracle gets
clean [x, y]; E-oracle+DINO is the untrained direct test with the DINO [x, y].

Run from train/:

    python -u eval_e_dino.py --run-dir logs/nomad/<e_dino run> --checkpoint ema_29.pth
"""

import argparse
import os

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dino import DFT_PREDICTIONS
from eval_goal_head import B_CHECKPOINT, make_split_dataset, meters_per_unit, normalize_images, write_csv
from eval_position_noise import boot_mean, diffuse, encode_cond, load_model, mean_ade_fde, subset_index
from eval_waypoint_head import blend, head_predict
from train_e_dino import DINO_BEST, WP_BEST, load_dino_head
from train_goal_dino import CACHE_DIR, load_cache
from revalidate import CACHE_ROOT
from vint_train.training.train_utils import append_goal_pos

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")


@torch.no_grad()
def run_models(models, dataset, far, cond_pos, device, num_samples, batch_size):
    """cond_pos: dict model_name -> [N, pos_dim] in dataset units (or None for B)."""
    meters = meters_per_unit(dataset)
    n = len(far)
    ade = {name: np.zeros(n) for name in models}
    fde = {name: np.zeros(n) for name in models}
    ade_mask = {name: np.zeros(n) for name in models}
    fde_mask = {name: np.zeros(n) for name in models}
    horizon = dataset.len_traj_pred
    names = list(models)
    for start in tqdm(range(0, n, batch_size), desc="paired far", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list, gt_list = [], [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, actions, _goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
            gt_list.append(actions[:, :2])
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = torch.randn((len(chunk) * num_samples, horizon, 2), device=device)
        for name in names:
            model, scheduler, pos_dim = models[name]
            cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
            cond_mask, mask_mask = encode_cond(model, batch_obs, batch_goal, 1, device)
            if pos_dim > 0:
                pos = torch.tensor(cond_pos[name][start : start + len(chunk)], dtype=torch.float32, device=device)
                zeros = torch.zeros_like(pos)
                cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
                cond_mask = append_goal_pos(cond_mask, zeros, mask_mask)
            pred_goal = diffuse(model, scheduler, cond_goal, noise, num_samples, device)
            pred_mask = diffuse(model, scheduler, cond_mask, noise, num_samples, device)
            for i, gt in enumerate(gt_list):
                index = start + i
                ade[name][index], fde[name][index] = mean_ade_fde(pred_goal[i], gt, meters)
                ade_mask[name][index], fde_mask[name][index] = mean_ade_fde(pred_mask[i], gt, meters)
    return ade, fde, ade_mask, fde_mask


def fmt(stats):
    mean, lo, hi = stats
    return f"{100 * mean:+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}]"


def main():
    parser = argparse.ArgumentParser(description="Evaluate E-dino on locked far frames")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--config-e-dino", default="config/nomad_e_dino.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e-oracle", default=E_CHECKPOINT)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="ema_latest.pth")
    parser.add_argument("--dino-head", default=DINO_BEST)
    parser.add_argument("--goal-pos-mode", choices=("goal", "blend"), default="")
    parser.add_argument("--wp-head", default=WP_BEST)
    parser.add_argument("--wp-run-dir", default="logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument("--dino-predictions", default="", help="Optional predictions.npz with dino_dir/dino_kappa")
    parser.add_argument("--dft-predictions", default=DFT_PREDICTIONS)
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_eo = load_config(args.config_e_oracle)
    config_ed = load_config(args.config_e_dino)
    pos_dim = int(config_ed.get("goal_pos_dim", 3))
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]
    output_dir = os.path.join(args.run_dir, f"eval_{os.path.splitext(args.checkpoint)[0]}")
    os.makedirs(output_dir, exist_ok=True)

    # Positions from saved DINO predictions (preferred) or recompute.
    pred_path = args.dino_predictions or os.path.join(
        "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"
    )
    if os.path.exists(pred_path):
        pred = dict(np.load(pred_path))
        far_mask = pred["group"] == "20-40"
        order = np.argsort(pred["frame_index"][far_mask], kind="stable")
        dino_dir = pred["dino_dir"][far_mask][order]
        kappa = pred["dino_kappa"][far_mask][order]
        b_dist_m = pred["b_dist"][far_mask][order]
        target_m = pred["target"][far_mask][order]
        print(f"Loaded DINO predictions from {pred_path}")
    else:
        raise FileNotFoundError(f"Need DINO predictions at {pred_path}; run eval_goal_dino.py first")

    b_steps = b_dist_m / meters
    goal_pos_mode = args.goal_pos_mode
    if not goal_pos_mode:
        args_path = os.path.join(args.run_dir, "args.txt")
        if os.path.isfile(args_path):
            with open(args_path) as f:
                for line in f:
                    if line.startswith("goal_pos_mode="):
                        goal_pos_mode = line.strip().split("=", 1)[1]
        goal_pos_mode = goal_pos_mode or "goal"
    if goal_pos_mode == "blend":
        cache_npz = os.path.join(args.wp_run_dir, "eval_waypoint", "locked_per_frame.npz")
        if os.path.isfile(cache_npz):
            cached = np.load(cache_npz)
            wp_dir, wp_kappa = cached["wp_dir"].astype(np.float32), cached["wp_kappa"].astype(np.float32)
        else:
            _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
            feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
            wp_head, _ = load_dino_head(args.wp_head, device)
            wp_dir, wp_kappa = head_predict(wp_head, far, rows, feats, device)
        direction = blend(dino_dir, kappa, wp_dir, wp_kappa, wp_scale=args.wp_scale)
        print(f"E-dino inference: kappa blend (wp_scale={args.wp_scale})")
    else:
        direction = dino_dir
    mu_units = (direction * b_steps[:, None]).astype(np.float32)
    sigma_units = (b_steps / np.maximum(np.sqrt(kappa), 1e-3)).clip(max=40.0).astype(np.float32)
    if pos_dim == 3:
        e_dino_pos = np.concatenate([mu_units, sigma_units[:, None]], axis=1)
    else:
        e_dino_pos = mu_units
    clean_units = (target_m / meters).astype(np.float32)

    model_b, sched_b = load_model(config_b, args.checkpoint_b, device)
    model_eo, sched_eo = load_model(config_eo, args.checkpoint_e_oracle, device)
    model_ed, sched_ed = load_model(config_ed, os.path.join(args.run_dir, args.checkpoint), device)
    models = {
        "B": (model_b, sched_b, 0),
        "E-oracle": (model_eo, sched_eo, 2),
        "E-oracle+DINO": (model_eo, sched_eo, 2),
        "E-dino": (model_ed, sched_ed, pos_dim),
    }
    cond_pos = {
        "B": None,
        "E-oracle": clean_units,
        "E-oracle+DINO": mu_units,
        "E-dino": e_dino_pos,
    }

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    ade, fde, ade_mask, fde_mask = run_models(
        models, dataset, far, cond_pos, device, args.num_samples, args.batch_size
    )

    rng = np.random.default_rng(args.seed + 1)
    rows = []
    print("\nFar group. use = masked ADE - ADE (cm). kept = use / E-oracle use on the same frames.")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        oracle_use = float((ade_mask["E-oracle"][idx] - ade["E-oracle"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}")
        print(f"{'model':<16}{'ADE':>8}{'ADE use':>24}{'kept':>7}{'FDE use':>24}")
        for name in models:
            use = boot_mean(ade_mask[name][idx] - ade[name][idx], boot)
            fuse = boot_mean(fde_mask[name][idx] - fde[name][idx], boot)
            kept = use[0] / oracle_use if oracle_use > 0 else float("nan")
            print(f"{name:<16}{100 * ade[name][idx].mean():8.2f}{fmt(use):>24}{100 * kept:6.0f}%{fmt(fuse):>24}")
            rows.append(
                {
                    "frames": set_name,
                    "model": name,
                    "n": int(len(idx)),
                    "ade_m": float(ade[name][idx].mean()),
                    "ade_use_m": use[0],
                    "ade_use_lo": use[1],
                    "ade_use_hi": use[2],
                    "kept_vs_oracle": kept,
                    "fde_use_m": fuse[0],
                    "fde_use_lo": fuse[1],
                    "fde_use_hi": fuse[2],
                }
            )
    write_csv(os.path.join(output_dir, "paired_far.csv"), rows)
    np.savez_compressed(
        os.path.join(output_dir, "per_frame.npz"),
        **{f"ade_{name}": ade[name] for name in models},
        **{f"ade_mask_{name}": ade_mask[name] for name in models},
    )
    print(f"\nSaved to {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

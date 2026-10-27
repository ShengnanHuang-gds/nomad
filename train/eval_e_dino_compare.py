"""Compare E-dino runs (goal vs kappa-blend goal_pos) on locked far frames + turn/spread."""

import argparse
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_e_dino import SET_NAMES, fmt, run_models
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, make_split_dataset, meters_per_unit
from eval_position_noise import boot_mean, load_model, subset_index
from eval_waypoint_head import blend, head_predict
from train_e_dino import WP_BEST, load_dino_head
from train_goal_dino import load_cache
from revalidate import CACHE_ROOT


def read_run_args(run_dir):
    path = os.path.join(run_dir, "args.txt")
    out = {}
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    out[k] = v
    return out


def far_mu(mode, dino_dir, goal_kappa, b_steps, pos_dim, wp_dir=None, wp_kappa=None, wp_scale=1.0):
    if mode == "blend":
        direction = blend(dino_dir, goal_kappa, wp_dir, wp_kappa, wp_scale=wp_scale)
    else:
        direction = dino_dir
    mu = (direction * b_steps[:, None]).astype(np.float32)
    if pos_dim == 3:
        sigma = (b_steps / np.maximum(np.sqrt(goal_kappa), 1e-3)).clip(max=40.0).astype(np.float32)
        return np.concatenate([mu, sigma[:, None]], axis=1)
    return mu


def load_wp_on_far(far, wp_run_dir, device):
    cache_npz = os.path.join(wp_run_dir, "eval_waypoint", "locked_per_frame.npz")
    if os.path.isfile(cache_npz):
        c = np.load(cache_npz)
        return c["wp_dir"].astype(np.float32), c["wp_kappa"].astype(np.float32)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    ckpt = os.path.join(wp_run_dir, "dino_dir_best.pth")
    if not os.path.isfile(ckpt):
        ckpt = WP_BEST
    wp_head, _ = load_dino_head(ckpt, device)
    return head_predict(wp_head, far, rows, feats, device)


def main():
    parser = argparse.ArgumentParser(description="Compare E-dino goal vs kappa-blend training")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--config-e-dino", default="config/nomad_e_dino_mu.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e-oracle", default=E_CHECKPOINT)
    parser.add_argument("--run-goal", required=True)
    parser.add_argument("--run-blend", required=True)
    parser.add_argument("--checkpoint", default="ema_latest.pth")
    parser.add_argument("--wp-run-dir", default="logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument(
        "--dino-predictions",
        default="logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz",
    )
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
    pos_dim = int(config_ed.get("goal_pos_dim", 2))
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]

    pred = dict(np.load(args.dino_predictions))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    dino_dir = pred["dino_dir"][fm][order]
    goal_kappa = pred["dino_kappa"][fm][order]
    b_steps = (pred["b_dist"][fm][order] / meters).astype(np.float32)
    clean = (pred["target"][fm][order] / meters).astype(np.float32)
    mu_goal_only = (dino_dir * b_steps[:, None]).astype(np.float32)

    mode_g = read_run_args(args.run_goal).get("goal_pos_mode", "goal")
    blend_args = read_run_args(args.run_blend)
    mode_b = blend_args.get("goal_pos_mode", "blend")
    wp_scale = float(blend_args.get("wp_scale", args.wp_scale))
    wp_dir, wp_kappa = load_wp_on_far(far, args.wp_run_dir, device)

    pos_g = far_mu(mode_g, dino_dir, goal_kappa, b_steps, pos_dim)
    pos_b = far_mu(mode_b, dino_dir, goal_kappa, b_steps, pos_dim, wp_dir, wp_kappa, wp_scale)

    model_b, sched_b = load_model(config_b, args.checkpoint_b, device)
    model_eo, sched_eo = load_model(config_eo, args.checkpoint_e_oracle, device)
    model_eg, sched_eg = load_model(config_ed, os.path.join(args.run_goal, args.checkpoint), device)
    model_eb, sched_eb = load_model(config_ed, os.path.join(args.run_blend, args.checkpoint), device)

    label_g = f"E-dino ({mode_g})"
    label_b = f"E-dino blend ({mode_b})"
    models = {
        "B": (model_b, sched_b, 0),
        "E-oracle": (model_eo, sched_eo, 2),
        "E-oracle+DINO": (model_eo, sched_eo, 2),
        label_g: (model_eg, sched_eg, pos_dim),
        label_b: (model_eb, sched_eb, pos_dim),
    }
    cond_pos = {
        "B": None,
        "E-oracle": clean,
        "E-oracle+DINO": mu_goal_only,
        label_g: pos_g,
        label_b: pos_b,
    }

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    ade, fde, ade_mask, fde_mask = run_models(
        models, dataset, far, cond_pos, device, args.num_samples, args.batch_size
    )

    rng = np.random.default_rng(args.seed + 1)
    boot_all = subset_index(len(far), args.bootstrap, rng)
    print(f"\nCompare {args.checkpoint}: goal={args.run_goal} blend={args.run_blend}\n")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        oracle_use = float((ade_mask["E-oracle"][idx] - ade["E-oracle"][idx]).mean())
        print(f"[{set_name}] n={len(idx)}")
        for name in (label_g, label_b, "E-oracle+DINO"):
            use = boot_mean(ade_mask[name][idx] - ade[name][idx], boot)
            kept = use[0] / oracle_use if oracle_use > 0 else float("nan")
            print(f"  {name:<24} use {fmt(use)} cm  kept {100 * kept:.0f}%")
        dlt = boot_mean(
            (ade_mask[label_b][idx] - ade[label_b][idx]) - (ade_mask[label_g][idx] - ade[label_g][idx]),
            boot,
        )
        print(f"  paired blend - goal: {fmt(dlt)} cm\n")

    dlt_all = boot_mean(
        (ade_mask[label_b] - ade[label_b]) - (ade_mask[label_g] - ade[label_g]),
        boot_all,
    )
    print(f"[all far] paired blend - goal: {fmt(dlt_all)} cm")


if __name__ == "__main__":
    main()
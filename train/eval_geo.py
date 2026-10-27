"""Locked far-frame eval of NoMaD-Geo against B, E-oracle and the untrained direct test.

Same 1000 frames, shared diffusion noise, N=8. Rows:
  B               no position
  E-oracle        true [x, y]
  E-oracle+DINO   untrained direct test: DINO bearing x B distance (saved predictions)
  Geo             NoMaD-Geo with its own estimate [x, y, std] (own distance head + own bearing head)
  Geo+true        NoMaD-Geo with the true [x, y] and std 0 (its ceiling)
kept = goal use / E-oracle goal use on the same frames. Also reports Geo bearing error.

Run from train/:
    python -u eval_geo.py --run-dir logs/nomad_geo/<run> --checkpoint ema_best.pth
"""

import argparse
import json
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_e_dino import SET_NAMES, fmt, run_models
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, make_split_dataset, meters_per_unit, normalize_images, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from train_e_dino import read_tokens
from train_geo import build_geo
from train_goal_dino import CACHE_DIR, load_cache

DINO_PREDICTIONS = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"


@torch.no_grad()
def geo_estimates(model, dataset, far, rows, features, device, batch_size=32):
    pos_all, std_all, dir_all, steps_all = [], [], [], []
    for start in range(0, len(far), batch_size):
        chunk = far[start : start + batch_size]
        obs_l, goal_l = [], []
        for traj_name, t, g in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, g)
            obs_l.append(obs)
            goal_l.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
        no_mask = torch.zeros(len(chunk), dtype=torch.long, device=device)
        cond = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
        curr = read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        pos, std, direction, _kappa, steps = model.estimate_goal(cond, curr, goal)
        pos_all.append(pos.cpu().numpy())
        std_all.append(std.cpu().numpy())
        dir_all.append(direction.cpu().numpy())
        steps_all.append(steps.cpu().numpy())
    return np.concatenate(pos_all), np.concatenate(std_all), np.concatenate(dir_all), np.concatenate(steps_all)


def bearing_deg(xy):
    return np.degrees(np.arctan2(xy[:, 1], xy[:, 0]))


def angle_err(a, b):
    return np.abs((bearing_deg(a) - bearing_deg(b) + 180.0) % 360.0 - 180.0)


def main():
    parser = argparse.ArgumentParser(description="Evaluate NoMaD-Geo on locked far frames")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e-oracle", default=E_CHECKPOINT)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="ema_best.pth")
    parser.add_argument("--dino-predictions", default=DINO_PREDICTIONS)
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda:0")
    config_b = load_config(args.config_b)
    config_eo = load_config(args.config_e_oracle)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]
    output_dir = os.path.join(args.run_dir, f"eval_{os.path.splitext(args.checkpoint)[0]}")
    os.makedirs(output_dir, exist_ok=True)

    pred = dict(np.load(args.dino_predictions))
    far_mask = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far_mask], kind="stable")
    target_m = pred["target"][far_mask][order]
    dino_dir = pred["dino_dir"][far_mask][order]
    b_steps = pred["b_dist"][far_mask][order] / meters
    clean_units = (target_m / meters).astype(np.float32)
    direct_units = (dino_dir * b_steps[:, None]).astype(np.float32)

    with open(os.path.join(args.run_dir, "geo_meta.json")) as f:
        geo_meta = json.load(f)
    head_state = {"meta": geo_meta["head_meta"], "args": geo_meta["head_args"]}
    model_geo, sched_geo = build_geo(config_eo, head_state)
    state = torch.load(os.path.join(args.run_dir, args.checkpoint), map_location="cpu", weights_only=False)
    model_geo.load_state_dict(state, strict=True)
    model_geo.to(device).eval()
    print(f"NoMaD-Geo loaded (strict): {os.path.join(args.run_dir, args.checkpoint)}")

    cache_path, rows, cache_meta = load_cache(args.cache_dir, "test_paired")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    geo_pos, geo_std, geo_dir, geo_steps = geo_estimates(model_geo, dataset, far, rows, features, device)
    if not np.allclose(np.linalg.norm(clean_units, axis=1) * meters, np.linalg.norm(target_m, axis=1)):
        raise RuntimeError("target mismatch")
    geo_err = angle_err(geo_dir, target_m)
    dino_err = angle_err(dino_dir, target_m)
    true_steps = np.linalg.norm(clean_units, axis=1)
    print(
        f"Far bearing error median: Geo head {np.median(geo_err):.1f} deg vs original DINO head {np.median(dino_err):.1f} deg | "
        f"distance / true median: Geo {np.median(geo_steps / true_steps):.2f}, B {np.median(b_steps / true_steps):.2f}"
    )

    model_b, sched_b = load_model(config_b, args.checkpoint_b, device)
    model_eo, sched_eo = load_model(config_eo, args.checkpoint_e_oracle, device)
    models = {
        "B": (model_b, sched_b, 0),
        "E-oracle": (model_eo, sched_eo, 2),
        "E-oracle+DINO": (model_eo, sched_eo, 2),
        "Geo": (model_geo, sched_geo, 3),
        "Geo+true": (model_geo, sched_geo, 3),
    }
    cond_pos = {
        "B": None,
        "E-oracle": clean_units,
        "E-oracle+DINO": direct_units,
        "Geo": np.concatenate([geo_pos, geo_std[:, None]], axis=1).astype(np.float32),
        "Geo+true": np.concatenate([clean_units, np.zeros((len(far), 1), np.float32)], axis=1),
    }
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    ade, fde, ade_mask, fde_mask = run_models(models, dataset, far, cond_pos, device, args.num_samples, args.batch_size)

    rng = np.random.default_rng(args.seed + 1)
    rows_out = []
    print("\nFar group. use = masked ADE - ADE (cm). kept = use / E-oracle use on the same frames.")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        oracle_use = float((ade_mask["E-oracle"][idx] - ade["E-oracle"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}")
        print(f"{'model':<15}{'ADE':>8}{'ADE use':>24}{'kept':>7}{'FDE use':>24}")
        for name in models:
            use = boot_mean(ade_mask[name][idx] - ade[name][idx], boot)
            fuse = boot_mean(fde_mask[name][idx] - fde[name][idx], boot)
            kept = use[0] / oracle_use if oracle_use > 0 else float("nan")
            print(f"{name:<15}{100 * ade[name][idx].mean():8.2f}{fmt(use):>24}{100 * kept:6.0f}%{fmt(fuse):>24}")
            rows_out.append(
                {
                    "frames": set_name, "model": name, "n": int(len(idx)), "ade_m": float(ade[name][idx].mean()),
                    "ade_use_m": use[0], "ade_use_lo": use[1], "ade_use_hi": use[2], "kept_vs_oracle": kept,
                    "fde_use_m": fuse[0], "fde_use_lo": fuse[1], "fde_use_hi": fuse[2],
                }
            )
    boot_all = subset_index(len(far), args.bootstrap, rng)
    diff = (ade_mask["Geo"] - ade["Geo"]) - (ade_mask["E-oracle+DINO"] - ade["E-oracle+DINO"])
    print(f"\nPaired: Geo use - direct test use = {fmt(boot_mean(diff, boot_all))} cm")
    write_csv(os.path.join(output_dir, "paired_far.csv"), rows_out)
    np.savez_compressed(
        os.path.join(output_dir, "per_frame.npz"),
        geo_pos=geo_pos, geo_std=geo_std, geo_dir=geo_dir, geo_steps=geo_steps, geo_bearing_err=geo_err,
        **{f"ade_{n}": ade[n] for n in models}, **{f"ade_mask_{n}": ade_mask[n] for n in models},
    )
    print(f"Saved to {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

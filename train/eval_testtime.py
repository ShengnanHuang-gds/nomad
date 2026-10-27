"""Test-time transforms of the DINO goal estimate fed to E-oracle. No training.

Each config maps (direction, kappa, B distance) to the position E-oracle sees:
  source  plain DINO direction, or the flip test-time average (tta)
  a, c    bearing shrink toward straight ahead: theta' = theta * a * kappa / (kappa + c)
          (c = 0 means no kappa dependence)
  m       distance scale: d' = d * m
Tuning: a grid on far goals (20-39 steps) from the held-out D-ft trajectories,
scored by goal use = masked ADE - ADE with that position. E-oracle trained on these
trajectories, so the absolute val numbers are optimistic; only the ranking is used.
The best config is then run once on the locked 1000 test frames next to the plain
direct test, E-oracle with true positions and B. Every config shares the same
initial noise and the same per-step DDPM noise (the RNG is reseeded per batch).

Run from train/:
    python -u eval_testtime.py
"""

import argparse
import itertools
import json
import os

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dino import combine_flip
from eval_goal_head import B_CHECKPOINT, encode, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images, write_csv
from eval_position_noise import boot_mean, diffuse, encode_cond, load_model, mean_ade_fde, subset_index
from train_e_dino import DINO_BEST, load_dino_head, read_tokens
from train_goal_dino import CACHE_DIR, DFT_VAL_LIST, load_cache
from vint_train.training.train_utils import append_goal_pos

DINO_TEST_PREDICTIONS = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"
OUTPUT_DIR = "logs/nomad_d/testtime"
FAR_MIN, FAR_MAX = 20, 39
SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")


def transform(direction, kappa, steps, a, c, m):
    theta = np.arctan2(direction[:, 1], direction[:, 0])
    gain = a * (kappa / (kappa + c) if c > 0 else np.ones_like(kappa))
    theta = theta * gain
    d = steps * m
    return np.stack([d * np.cos(theta), d * np.sin(theta)], axis=1).astype(np.float32)


def config_name(src, a, c, m):
    return f"{src} a={a:g} c={c:g} m={m:g}"


@torch.no_grad()
def rollout(model, scheduler, dataset, items, positions, device, num_samples, batch_size, seed, desc):
    """positions: name -> [N, 2] waypoint units, or None for a no-position model (goal image only).

    Returns per-frame masked ADE and ADE per name (meters).
    """
    meters = meters_per_unit(dataset)
    n = len(items)
    ade = {name: np.zeros(n) for name in positions}
    ade_mask = np.zeros(n)
    pos_dims = {v.shape[1] for v in positions.values() if v is not None}
    if len(pos_dims) > 1:
        raise ValueError(f"positions for one model must share a width, got {pos_dims}")
    takes_pos = bool(pos_dims)
    pos_dim = pos_dims.pop() if takes_pos else 0
    for b_idx, start in enumerate(tqdm(range(0, n, batch_size), desc=desc, leave=False)):
        chunk = items[start : start + batch_size]
        obs_l, goal_l, gt_l = [], [], []
        for traj_name, t, g in chunk:
            obs, goal, actions, _p = load_observation(dataset, traj_name, t, g)
            obs_l.append(obs)
            goal_l.append(goal)
            gt_l.append(actions[:, :2])
        batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
        b = len(chunk)
        gen = torch.Generator(device=device).manual_seed(seed * 100003 + b_idx)
        noise = torch.randn((b * num_samples, dataset.len_traj_pred, 2), device=device, generator=gen)
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        cond_mask, mask_mask = encode_cond(model, batch_obs, batch_goal, 1, device)
        if takes_pos:
            cond_mask = append_goal_pos(cond_mask, torch.zeros((b, pos_dim), device=device), mask_mask)
        torch.manual_seed(seed * 7919 + b_idx)
        pred = diffuse(model, scheduler, cond_mask, noise, num_samples, device)
        for i, gt in enumerate(gt_l):
            ade_mask[start + i] = mean_ade_fde(pred[i], gt, meters)[0]
        for name, pos in positions.items():
            cond = cond_goal
            if pos is not None:
                cond = append_goal_pos(cond_goal, torch.tensor(pos[start : start + b], device=device), mask_goal)
            torch.manual_seed(seed * 7919 + b_idx)
            pred = diffuse(model, scheduler, cond, noise, num_samples, device)
            for i, gt in enumerate(gt_l):
                ade[name][start + i] = mean_ade_fde(pred[i], gt, meters)[0]
    return ade_mask, ade


def val_items(index_to_data, val_trajs, n, seed):
    rng = np.random.default_rng(seed)
    entries = [e for e in index_to_data if e[0] in val_trajs and e[2] >= FAR_MIN]
    pick = rng.choice(len(entries), size=min(n, len(entries)), replace=False)
    items = []
    for i in sorted(pick):
        traj_name, t, max_goal = entries[i]
        items.append((traj_name, t, t + int(rng.integers(FAR_MIN, min(FAR_MAX, max_goal) + 1))))
    return items


@torch.no_grad()
def val_estimates(items, dataset, model_b, head, rows, features, features_flip, device, batch_size=64):
    out = {k: [] for k in ("dir", "kappa", "dir_flip", "kappa_flip", "steps", "target")}
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        obs_l, goal_l, pos_l = [], [], []
        for traj_name, t, g in chunk:
            obs, goal, _a, goal_pos = load_observation(dataset, traj_name, t, g)
            obs_l.append(obs)
            goal_l.append(goal)
            pos_l.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
        steps = model_b("dist_pred_net", obsgoal_cond=encode(model_b, batch_obs, batch_goal)).squeeze(-1).clamp(min=0)
        curr_rows = [rows[(c[0], c[1])] for c in chunk]
        goal_rows = [rows[(c[0], c[2])] for c in chunk]
        for suffix, feats in (("", features), ("_flip", features_flip)):
            d, k = head(read_tokens(feats, curr_rows).to(device).float(), read_tokens(feats, goal_rows).to(device).float())
            out["dir" + suffix].append(d.cpu().numpy())
            out["kappa" + suffix].append(k.cpu().numpy())
        out["steps"].append(steps.cpu().numpy())
        out["target"].append(np.stack(pos_l))
    return {k: np.concatenate(v) for k, v in out.items()}


def angle_err(direction, target):
    a = np.degrees(np.arctan2(direction[:, 1], direction[:, 0]))
    b = np.degrees(np.arctan2(target[:, 1], target[:, 0]))
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


def main():
    parser = argparse.ArgumentParser(description="Tune test-time transforms of the DINO estimate on val, test once")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e-oracle", default=E_CHECKPOINT)
    parser.add_argument("--dino-head", default=DINO_BEST)
    parser.add_argument("--test-predictions", default=DINO_TEST_PREDICTIONS)
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--val-list", default=DFT_VAL_LIST)
    parser.add_argument("--val-frames", type=int, default=600)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--skip-test", action="store_true", help="Tune on val only (smoke tests)")
    args = parser.parse_args()

    device = torch.device("cuda:0")
    os.makedirs(args.output_dir, exist_ok=True)
    config_b = load_config(args.config_b)
    config_eo = load_config(args.config_e_oracle)
    model_eo, sched_eo = load_model(config_eo, args.checkpoint_e_oracle, device)

    # ---- validation tuning ----
    train_set = make_split_dataset(config_b, "train")
    with open(args.val_list) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    items = val_items(train_set.index_to_data, val_trajs, args.val_frames, seed=4321)
    cache_path, rows, _meta = load_cache(args.cache_dir, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    features_flip = np.load(os.path.join(cache_path, "features_flip.npy"), mmap_mode="r")
    head, _hm = load_dino_head(args.dino_head, device)
    model_b = load_frozen_nomad(config_b, args.checkpoint_b, device)
    est = val_estimates(items, train_set, model_b, head, rows, features, features_flip, device)
    del model_b
    torch.cuda.empty_cache()
    tta_dir, tta_kappa = combine_flip(est["dir"], est["kappa"], est["dir_flip"], est["kappa_flip"])
    sources = {"plain": (est["dir"], est["kappa"]), "tta": (tta_dir, tta_kappa)}
    print(
        f"val far frames {len(items)} | bearing median plain {np.median(angle_err(est['dir'], est['target'])):.1f}, "
        f"tta {np.median(angle_err(tta_dir, est['target'])):.1f} deg | B dist ratio "
        f"{np.median(est['steps'] / np.linalg.norm(est['target'], axis=1)):.2f}"
    )

    grid = list(itertools.product(("plain", "tta"), (1.0, 0.85, 0.7), (0.0, 1.0, 3.0, 10.0), (1.0, 0.85, 0.7)))
    positions = {config_name(*g): transform(*sources[g[0]], est["steps"], *g[1:]) for g in grid}
    positions["true"] = est["target"].astype(np.float32)
    ade_mask, ade = rollout(model_eo, sched_eo, train_set, items, positions, device, args.num_samples, args.batch_size, args.seed, "val grid")
    rows_val = []
    for g in grid:
        name = config_name(*g)
        rows_val.append({"config": name, "source": g[0], "a": g[1], "c": g[2], "m": g[3],
                         "val_use_cm": 100 * float((ade_mask - ade[name]).mean())})
    true_use = 100 * float((ade_mask - ade["true"]).mean())
    rows_val.sort(key=lambda r: -r["val_use_cm"])
    base = next(r for r in rows_val if r["config"] == config_name("plain", 1.0, 0.0, 1.0))
    print(f"\nVal far use (cm), true position {true_use:+.2f}, plain direct test {base['val_use_cm']:+.2f}. Top 10:")
    for r in rows_val[:10]:
        print(f"  {r['config']:<28} {r['val_use_cm']:+.2f}  ({100 * r['val_use_cm'] / true_use:.0f}% of true)")
    write_csv(os.path.join(args.output_dir, "val_grid.csv"), rows_val)
    best = rows_val[0]
    with open(os.path.join(args.output_dir, "best_config.json"), "w") as f:
        json.dump({**best, "val_true_use_cm": true_use, "val_plain_use_cm": base["val_use_cm"]}, f, indent=2)
    if args.skip_test:
        return

    # ---- locked test, run once ----
    test_set = make_split_dataset(config_b, "test")
    meters = meters_per_unit(test_set)
    moments = load_paired_frames(args.frames)
    sets, _lat, _yaw = frame_sets(test_set, moments, meters, args.spread)
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]
    pred = dict(np.load(args.test_predictions))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    steps = take("b_dist") / meters
    test_sources = {"plain": (take("dino_dir"), take("dino_kappa")), "tta": (take("dino_tta_dir"), take("dino_tta_kappa"))}
    test_pos = {
        "true": (take("target") / meters).astype(np.float32),
        "direct (plain)": transform(*test_sources["plain"], steps, 1.0, 0.0, 1.0),
        "direct (tta)": transform(*test_sources["tta"], steps, 1.0, 0.0, 1.0),
        f"best: {best['config']}": transform(*test_sources[best["source"]], steps, best["a"], best["c"], best["m"]),
    }
    ade_mask_t, ade_t = rollout(model_eo, sched_eo, test_set, far, test_pos, device, args.num_samples, 8, args.seed + 1, "test")
    model_b, sched_b = load_model(config_b, args.checkpoint_b, device)
    ade_mask_b, ade_b = rollout(model_b, sched_b, test_set, far, {"B": None}, device, args.num_samples, 8, args.seed + 1, "test B")

    rng = np.random.default_rng(args.seed + 2)
    out_rows = []
    print("\nLocked far frames. use = masked ADE - ADE (cm); kept vs E-oracle with the true position.")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        true_use_t = float((ade_mask_t[idx] - ade_t["true"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}")
        entries = [("B", ade_mask_b, ade_b["B"])] + [(k, ade_mask_t, ade_t[k]) for k in test_pos]
        for name, am, a in entries:
            u = boot_mean(am[idx] - a[idx], boot)
            print(f"  {name:<36} use {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  kept {100 * u[0] / true_use_t:4.0f}%")
            out_rows.append({"frames": set_name, "model": name, "use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2],
                             "kept": u[0] / true_use_t})
    boot_all = subset_index(len(far), args.bootstrap, rng)
    for k in list(test_pos)[2:]:
        d = (ade_mask_t - ade_t[k]) - (ade_mask_t - ade_t["direct (plain)"])
        u = boot_mean(d, boot_all)
        print(f"Paired: {k} - direct (plain) = {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}] cm")
    write_csv(os.path.join(args.output_dir, "test_results.csv"), out_rows)
    np.savez_compressed(os.path.join(args.output_dir, "test_per_frame.npz"), ade_mask=ade_mask_t,
                        **{f"ade_{i}": ade_t[k] for i, k in enumerate(test_pos)}, names=np.array(list(test_pos)))
    print(f"Saved to {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()

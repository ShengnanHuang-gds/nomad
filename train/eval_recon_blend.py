"""Cross-dataset smoke: kappa blend vs goal-head direct on RECON (GNM-format).

Uses GoStanford-trained heads / B / E-oracle zero-shot on RECON trajectories.
Online DINOv2 (no feature cache). Samples far goals (20-40 steps) from test trajs.

Run from train/ after downloading recon_gnm/recon:
    python -u eval_recon_blend.py --data-folder C:/Users/61078/Desktop/nomad/recon_gnm/recon
"""

from __future__ import annotations

import argparse
import csv
import json
import os

import cv2  # noqa: F401 — load before torch on Windows (nomad_train)

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import DISTANCE_GROUPS, load_config, load_observation
from eval_goal_head import meters_per_unit, normalize_images
from eval_position_noise import boot_mean, subset_index
from eval_testtime import angle_err, rollout
from adaptive_blend import angle_between_deg, blend_suppress, suppress_from_wp_turn
from infer_kappa_blend import WP_BEST, KappaBlendNavigator, _context_times, _load_pils
from train_e_dino import DINO_BEST
from vint_train.data.vint_dataset import ViNT_Dataset


def _traj_complete(data_folder, name, min_len=20):
    import pickle

    folder = os.path.join(data_folder, name)
    pkl = os.path.join(folder, "traj_data.pkl")
    if not os.path.isfile(pkl):
        return False
    with open(pkl, "rb") as f:
        n = len(pickle.load(f)["position"])
    if n < min_len:
        return False
    jpgs = {int(f[:-4]) for f in os.listdir(folder) if f.endswith(".jpg") and f[:-4].isdigit()}
    return all(i in jpgs for i in range(n))


def write_split(data_folder, split_root, test_frac=0.3, seed=0):
    trajs = sorted(
        d
        for d in os.listdir(data_folder)
        if os.path.isdir(os.path.join(data_folder, d))
        and not d.startswith(".")
        and _traj_complete(data_folder, d)
    )
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(trajs))
    n_test = max(1, int(round(len(trajs) * test_frac)))
    test = [trajs[i] for i in order[:n_test]]
    train = [trajs[i] for i in order[n_test:]]
    for name, names in (("train", train), ("test", test)):
        out = os.path.join(split_root, name)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "traj_names.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(names) + ("\n" if names else ""))
    return train, test


def make_recon_dataset(config, data_folder, split_folder, dataset_name="recon"):
    return ViNT_Dataset(
        data_folder=data_folder,
        data_split_folder=split_folder,
        dataset_name=dataset_name,
        image_size=config["image_size"],
        waypoint_spacing=1,
        min_dist_cat=config["distance"]["min_dist_cat"],
        max_dist_cat=config["distance"]["max_dist_cat"],
        min_action_distance=config["action"]["min_dist_cat"],
        max_action_distance=config["action"]["max_dist_cat"],
        negative_mining=True,
        len_traj_pred=config["len_traj_pred"],
        learn_angle=config["learn_angle"],
        context_size=config["context_size"],
        context_type=config.get("context_type", "temporal"),
        end_slack=0,
        goals_per_obs=1,
        normalize=config["normalize"],
        goal_type=config.get("goal_type", "image"),
    )


def _frame_loadable(dataset, traj_name, t, g):
    try:
        load_observation(dataset, traj_name, t, g)
        return True
    except (TypeError, OSError, FileNotFoundError):
        return False


def sample_far_items(dataset, n, seed, far_lo=20, far_hi=40):
    rng = np.random.default_rng(seed)
    cand = []
    for traj_name, t, max_goal in dataset.index_to_data:
        if max_goal < far_lo:
            continue
        g_hi = min(far_hi, max_goal)
        g = t + far_lo
        if g > g_hi:
            continue
        if _frame_loadable(dataset, traj_name, t, g):
            cand.append((traj_name, t, max_goal))
    if not cand:
        raise RuntimeError("No frames with far goals; need longer trajectories")
    pick = rng.choice(len(cand), size=min(n, len(cand)), replace=False)
    items = []
    for i in sorted(pick):
        traj_name, t, max_goal = cand[i]
        for _ in range(8):
            g = t + int(rng.integers(far_lo, min(far_hi, max_goal) + 1))
            if _frame_loadable(dataset, traj_name, t, g):
                items.append((traj_name, t, g))
                break
    return items


@torch.no_grad()
def estimate_positions(nav, dataset, items):
    """Online DINO + dual heads + B distance → goal_pos variants (dataset units)."""
    device = nav.device
    out = {k: [] for k in ("true", "goal_head", "waypoint_head", "kappa_blend", "goal_dir", "wp_dir", "goal_kappa", "wp_kappa", "steps")}
    for traj_name, t, g in tqdm(items, desc="estimate"):
        obs, goal, _a, true_pos = load_observation(dataset, traj_name, t, g)
        batch_obs, batch_goal = normalize_images(obs.unsqueeze(0), goal.unsqueeze(0), device)
        ctx = _load_pils(dataset, traj_name, _context_times(dataset, t))
        goal_pil = _load_pils(dataset, traj_name, [g])[0]
        curr_tok = nav.encode_dino(ctx[-1])
        goal_tok = nav.encode_dino(goal_pil)
        steps = nav.b_steps(batch_obs, batch_goal)
        pos, aux = nav.blend_goal_pos(curr_tok, goal_tok, steps)
        g_dir, g_k = aux["goal_dir"], aux["goal_kappa"]
        w_dir, w_k = aux["wp_dir"], aux["wp_kappa"]
        s = steps.unsqueeze(-1)
        out["true"].append(np.asarray(true_pos[:2], dtype=np.float32))
        out["goal_head"].append((g_dir * s)[0].cpu().numpy())
        out["waypoint_head"].append((w_dir * s)[0].cpu().numpy())
        out["kappa_blend"].append(pos[0].cpu().numpy())
        out["goal_dir"].append(g_dir[0].cpu().numpy())
        out["wp_dir"].append(w_dir[0].cpu().numpy())
        out["goal_kappa"].append(float(g_k[0].cpu()))
        out["wp_kappa"].append(float(w_k[0].cpu()))
        out["steps"].append(float(steps[0].cpu()))
    return {k: np.stack(v) if k != "steps" else np.asarray(v, dtype=np.float32) for k, v in out.items()}


def main():
    parser = argparse.ArgumentParser(description="RECON zero-shot kappa-blend validation")
    parser.add_argument("--data-folder", default="C:/Users/61078/Desktop/nomad/recon_gnm/recon")
    parser.add_argument("--dataset-name", default="recon", help="key in data_config.yaml (recon|seattle|scand|...)")
    parser.add_argument("--split-root", default=None)
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--n-frames", type=int, default=200)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--out-dir", default="logs/revalidation/recon_blend")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument("--gate-wp-lo", type=float, default=90.0)
    parser.add_argument("--gate-wp-hi", type=float, default=90.0)
    parser.add_argument(
        "--with-kappa-suppress",
        action="store_true",
        help="Also report kappa suppress (oracle wp vs endpoint + deploy goal-wp disagree w35-55)",
    )
    args = parser.parse_args()
    if args.split_root is None:
        args.split_root = f"vint_train/data/data_splits/{args.dataset_name}"

    os.makedirs(args.out_dir, exist_ok=True)
    config = load_config(args.config_b)
    # Zero-shot: put all usable trajs in test.
    train_names, test_names = write_split(args.data_folder, args.split_root, test_frac=1.0, seed=args.seed)
    print(f"{args.dataset_name} trajs: train={len(train_names)} test={len(test_names)} folder={args.data_folder}")

    dataset = make_recon_dataset(
        config, args.data_folder, os.path.join(args.split_root, "test"), dataset_name=args.dataset_name
    )
    meters = meters_per_unit(dataset)
    print(f"meters_per_unit={meters:.4f} (metric_waypoint_spacing={dataset.data_config['metric_waypoint_spacing']})")

    items = sample_far_items(dataset, args.n_frames, seed=args.seed + 1)
    print(f"sampled far frames: {len(items)}")

    nav = KappaBlendNavigator(
        device=args.device,
        wp_scale=args.wp_scale,
        gate_wp_lo=args.gate_wp_lo,
        gate_wp_hi=args.gate_wp_hi,
        load_dino=True,
        dino_half=True,
    )
    # Point heads explicitly (defaults already correct)
    _ = DINO_BEST, WP_BEST

    est = estimate_positions(nav, dataset, items)
    end = np.stack([load_observation(dataset, n, t, g)[2][-1, :2] for n, t, g in items]).astype(np.float32)
    print(
        f"bearing medians (deg): goal vs true goal {np.median(angle_err(est['goal_dir'], est['true'])):.1f} | "
        f"wp vs endpoint {np.median(angle_err(est['wp_dir'], end)):.1f} | "
        f"goal vs endpoint {np.median(angle_err(est['goal_dir'], end)):.1f}"
    )

    positions = {
        "true goal": est["true"],
        "goal head (direct)": est["goal_head"],
        "waypoint head": est["waypoint_head"],
        "kappa blend": est["kappa_blend"],
    }
    if args.with_kappa_suppress:
        g_dir = est["goal_dir"]
        w_dir = est["wp_dir"]
        gk = est["goal_kappa"].astype(np.float32)
        wk = est["wp_kappa"].astype(np.float32)
        steps = est["steps"][:, None]
        wp_err_gt = angle_err(w_dir, end).astype(np.float32)
        wp_err_dis = angle_between_deg(g_dir, w_dir).astype(np.float32)
        turn0 = np.zeros(len(g_dir), dtype=np.float32)
        for label, wp_err, lo, hi in (
            ("kappa suppress (oracle w35-55)", wp_err_gt, 35.0, 55.0),
            ("kappa suppress (deploy w35-55)", wp_err_dis, 35.0, 55.0),
        ):
            sup = suppress_from_wp_turn(wp_err, turn0, wp_lo=lo, wp_hi=hi, turn_weight=0.0, cap=1.0)
            d = blend_suppress(g_dir, gk, w_dir, wk, sup)
            positions[label] = (d * steps).astype(np.float32)
    tag = f"{args.dataset_name}-far"
    am, ade = rollout(
        nav.model_e,
        nav.scheduler,
        dataset,
        items,
        positions,
        nav.device,
        args.num_samples,
        8,
        args.seed + 2,
        tag,
    )

    rng = np.random.default_rng(args.seed + 3)
    boot = subset_index(len(items), args.bootstrap, rng)
    ref = float((am - ade["true goal"]).mean())
    rows = []
    print(f"\n[{args.dataset_name} far] n={len(items)} use (cm) [95% CI] and share of true-goal use:")
    for k in positions:
        u = boot_mean(am - ade[k], boot)
        vs = (u[0] / ref) if abs(ref) > 1e-9 else float("nan")
        print(f"  {k:<22} {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  ({100 * vs:.0f}%)")
        rows.append({"condition": k, "use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2], "vs_true_goal": vs})
    dlt = boot_mean((am - ade["kappa blend"]) - (am - ade["goal head (direct)"]), boot)
    print(f"  blend - direct         {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
    rows.append({"condition": "blend - direct", "use_cm": 100 * dlt[0], "lo": 100 * dlt[1], "hi": 100 * dlt[2], "vs_true_goal": float("nan")})
    if args.with_kappa_suppress:
        for name in ("kappa suppress (oracle w35-55)", "kappa suppress (deploy w35-55)"):
            dlt = boot_mean((am - ade[name]) - (am - ade["goal head (direct)"]), boot)
            print(f"  {name} - direct   {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
            rows.append({"condition": f"{name} - direct", "use_cm": 100 * dlt[0], "lo": 100 * dlt[1], "hi": 100 * dlt[2], "vs_true_goal": float("nan")})
        dlt = boot_mean((am - ade["kappa suppress (oracle w35-55)"]) - (am - ade["kappa blend"]), boot)
        print(f"  suppress(oracle) - blend {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")

    csv_path = os.path.join(args.out_dir, f"{args.dataset_name}_blend.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    meta = {
        "n_frames": len(items),
        "n_test_trajs": len(test_names),
        "n_train_trajs": len(train_names),
        "meters_per_unit": meters,
        "data_folder": args.data_folder,
        "dataset_name": args.dataset_name,
        "note": f"zero-shot GoStanford heads/B/E on HF reconstructed {args.dataset_name}; images 128x128",
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    np.savez_compressed(
        os.path.join(args.out_dir, "per_frame.npz"),
        ade_mask=am,
        traj=np.array([n for n, _t, _g in items]),
        **{f"ade_{i}": ade[k] for i, k in enumerate(positions)},
        names=np.array(list(positions)),
    )
    print(f"Saved {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()

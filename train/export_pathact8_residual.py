"""Export pathact8 WP 8-pt path, E-dino nav samples, and GT for residual ADE diagnosis.

Standalone script (does not modify eval_e_dino.py). Defaults match deploy audit eval_command.txt.
"""
import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone

import cv2  # noqa: F401
import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_e_dino import head_predict_wp_path
from eval_frame_sets import PAIRED_FRAMES
from eval_goal_head import make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import diffuse, encode_cond, load_model, mean_ade_fde
from eval_waypoint_head import blend
from revalidate import CACHE_ROOT
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from vint_train.training.train_utils import append_goal_pos

DEFAULT_RUN_DIR = "logs/nomad/nomad_e_ft_pathact8"
DEFAULT_CKPT = "ema_latest.pth"
DEFAULT_CONFIG_E = "config/nomad_e_dino_path.yaml"
DEFAULT_CONFIG_B = "config/nomad_b40.yaml"
DEFAULT_CKPT_B = "logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth"
DEFAULT_DINO_PRED = (
    "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"
)
DEFAULT_WP_HEAD = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
DEFAULT_FRAMES_CSV = "logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv"
DEFAULT_OUT = "logs/revalidation/pathact8_residual_export"

PREFLIGHT_PATHS = (
    ("run_ckpt", os.path.join(DEFAULT_RUN_DIR, DEFAULT_CKPT)),
    ("config_e", DEFAULT_CONFIG_E),
    ("config_b", DEFAULT_CONFIG_B),
    ("checkpoint_b", DEFAULT_CKPT_B),
    ("dino_pred", DEFAULT_DINO_PRED),
    ("wp_head", DEFAULT_WP_HEAD),
    ("frames_csv", DEFAULT_FRAMES_CSV),
    ("dino_features", os.path.join(CACHE_ROOT, "test_paired", "features.npy")),
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_frames_csv(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append((row["traj_name"], int(row["t"]), int(row["goal_time"])))
    return rows


def verify_frames_vs_locked(far):
    moments = load_paired_frames(PAIRED_FRAMES)
    locked = [
        (name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments
    ]
    if len(far) > len(locked):
        raise ValueError(f"frames csv has {len(far)} rows > locked far {len(locked)}")
    for i, (a, b) in enumerate(zip(far, locked)):
        if a != b:
            raise ValueError(f"frame row {i} differs from locked far: csv={a} locked={b}")


def load_dino_far_slice(pred_path, n_frames):
    pred = dict(np.load(pred_path))
    far_mask = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far_mask], kind="stable")
    idx = np.flatnonzero(far_mask)[order][:n_frames]
    return {
        "dino_dir": pred["dino_dir"][idx].astype(np.float32),
        "dino_kappa": pred["dino_kappa"][idx].astype(np.float32),
        "b_dist_m": pred["b_dist"][idx].astype(np.float32),
        "target_m": pred["target"][idx].astype(np.float32),
        "frame_index": pred["frame_index"][idx].astype(np.int32),
    }


def build_blend_path_cond(
    dino_dir,
    kappa,
    b_dist_m,
    wp_dir,
    wp_kappa,
    wp_path_xy,
    meters,
    pos_dim,
    path_units,
    wp_scale=1.0,
):
    b_steps = b_dist_m / meters
    direction = blend(dino_dir, kappa, wp_dir, wp_kappa, wp_scale=wp_scale)
    mu_units = (direction * b_steps[:, None]).astype(np.float32)
    path_steps = max(1, (pos_dim - 2) // 2)
    path = wp_path_xy.astype(np.float32)
    if path_units == "meters":
        path = path / max(float(meters), 1e-6)
    if path.shape[1] < path_steps:
        pad = path_steps - path.shape[1]
        path = np.concatenate([path, np.repeat(path[:, -1:, :], pad, axis=1)], axis=1)
    elif path.shape[1] > path_steps:
        path = path[:, :path_steps]
    e_dino_pos = np.concatenate([mu_units, path.reshape(len(mu_units), -1)], axis=1).astype(np.float32)
    if e_dino_pos.shape[1] != pos_dim:
        raise ValueError(f"blend_path pos width {e_dino_pos.shape[1]} != {pos_dim}")
    return mu_units, direction, path, e_dino_pos


def load_gt_actions(dataset, far, horizon):
    gt = []
    for traj_name, t, goal_time in far:
        _o, _g, actions, _p = load_observation(dataset, traj_name, t, goal_time)
        xy = np.asarray(actions, dtype=np.float32)[:, :2]
        if xy.shape[0] < horizon:
            xy = np.concatenate([xy, np.repeat(xy[-1:, :], horizon - xy.shape[0], axis=0)], axis=0)
        gt.append(xy[:horizon])
    return np.stack(gt, axis=0)


@torch.no_grad()
def sample_edino_nav(model, scheduler, dataset, far, e_dino_pos, device, num_samples, batch_size, seed):
    horizon = dataset.len_traj_pred
    n = len(far)
    pos_dim = e_dino_pos.shape[1]
    preds = np.zeros((n, num_samples, horizon, 2), dtype=np.float32)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    for start in tqdm(range(0, n, batch_size), desc="E-dino nav", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = torch.randn((len(chunk) * num_samples, horizon, 2), device=device)
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        pos = torch.tensor(e_dino_pos[start : start + len(chunk)], dtype=torch.float32, device=device)
        cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
        pred_goal = diffuse(model, scheduler, cond_goal, noise, num_samples, device)
        preds[start : start + len(chunk)] = pred_goal[..., :2].detach().cpu().numpy()
    return preds


def preflight(args):
    missing = []
    checks = list(PREFLIGHT_PATHS)
    checks.append(("run_ckpt", os.path.join(args.run_dir, args.checkpoint)))
    if args.frames_csv != DEFAULT_FRAMES_CSV:
        checks.append(("frames_csv", args.frames_csv))
    seen = set()
    for name, path in checks:
        if path in seen:
            continue
        seen.add(path)
        ok = os.path.isfile(path)
        if not ok:
            missing.append((name, path))
        size = os.path.getsize(path) if ok else 0
        digest = sha256_file(path)[:16] if ok and size < 200_000_000 else ("n/a" if not ok else "large")
        print(f"  [{name}] {'OK' if ok else 'MISSING'} {path} ({size} bytes, sha256={digest})")
    if missing:
        raise FileNotFoundError("Preflight failed: " + ", ".join(f"{n}={p}" for n, p in missing))
    return True


def main():
    parser = argparse.ArgumentParser(description="Export pathact8 residual diagnostics (WP path + nav + GT)")
    parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", default=DEFAULT_CKPT)
    parser.add_argument("--config-e-dino", default=DEFAULT_CONFIG_E)
    parser.add_argument("--config-b", default=DEFAULT_CONFIG_B)
    parser.add_argument("--checkpoint-b", default=DEFAULT_CKPT_B)
    parser.add_argument("--dino-predictions", default=DEFAULT_DINO_PRED)
    parser.add_argument("--wp-head", default=DEFAULT_WP_HEAD)
    parser.add_argument("--path-units", choices=("meters", "dataset"), default="dataset")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument("--frames-csv", default=DEFAULT_FRAMES_CSV)
    parser.add_argument("--max-frames", type=int, default=0, help="0 = all rows in frames csv")
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", help="Preflight + frame list only; no GPU export")
    args = parser.parse_args()

    print("Preflight (pathact8 deploy stack):")
    preflight(args)

    far = load_frames_csv(args.frames_csv)
    verify_frames_vs_locked(far)
    if args.max_frames > 0:
        far = far[: args.max_frames]
    print(f"Export frames: n={len(far)} from {args.frames_csv}")

    if args.dry_run:
        print("Dry-run OK — re-run without --dry-run to write NPZ (after smoke check).")
        return

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_ed = load_config(args.config_e_dino)
    pos_dim = int(config_ed.get("goal_pos_dim", 18))
    dataset = make_split_dataset(config_b, "test")
    meters = float(meters_per_unit(dataset))
    horizon = int(dataset.len_traj_pred)
    n = len(far)

    dino = load_dino_far_slice(args.dino_predictions, n)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    wp_head, _ = load_dino_head(args.wp_head, device)
    wp_dir, wp_kappa, wp_path_raw = head_predict_wp_path(wp_head, far, rows, feats, device)

    mu_units, blend_dir, path_dataset, e_dino_pos = build_blend_path_cond(
        dino["dino_dir"],
        dino["dino_kappa"],
        dino["b_dist_m"],
        wp_dir,
        wp_kappa,
        wp_path_raw,
        meters,
        pos_dim,
        args.path_units,
        wp_scale=args.wp_scale,
    )

    gt = load_gt_actions(dataset, far, horizon)
    ckpt_path = os.path.join(args.run_dir, args.checkpoint)
    model_ed, sched_ed = load_model(config_ed, ckpt_path, device)
    nav_samples = sample_edino_nav(
        model_ed, sched_ed, dataset, far, e_dino_pos, device, args.num_samples, args.batch_size, args.seed
    )
    nav_mean = nav_samples.mean(axis=1)
    ade_m = np.zeros(n, dtype=np.float32)
    for i in range(n):
        ade_m[i], _ = mean_ade_fde(nav_samples[i], gt[i], meters)

    wp_path_m = wp_path_raw.astype(np.float32)
    path_ade_cm = (
        np.linalg.norm(path_dataset - gt, axis=-1).mean(axis=1) * meters * 100
    ).astype(np.float32)

    os.makedirs(args.out_dir, exist_ok=True)
    traj = np.array([f[0] for f in far], dtype=object)
    t_arr = np.array([f[1] for f in far], dtype=np.int32)
    goal_t = np.array([f[2] for f in far], dtype=np.int32)

    npz_path = os.path.join(args.out_dir, "residual_export.npz")
    np.savez_compressed(
        npz_path,
        traj_name=traj,
        t=t_arr,
        goal_time=goal_t,
        frame_index=dino["frame_index"],
        gt_actions=gt,
        wp_path_raw_m=wp_path_m,
        wp_path_dataset=path_dataset,
        wp_dir=wp_dir,
        wp_kappa=wp_kappa,
        dino_dir=dino["dino_dir"],
        dino_kappa=dino["dino_kappa"],
        blend_dir=blend_dir,
        mu_units=mu_units,
        e_dino_pos=e_dino_pos,
        nav_pred_samples=nav_samples,
        nav_pred_mean=nav_mean,
        ade_edino_m=ade_m,
        path_ade_vs_gt_cm=path_ade_cm,
        meters_per_unit=np.float32(meters),
    )

    frames_csv_out = os.path.join(args.out_dir, "frames.csv")
    with open(frames_csv_out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "traj_name", "t", "goal_time", "frame_index", "ade_edino_cm", "path_ade_cm"])
        for i in range(n):
            w.writerow(
                [
                    i,
                    far[i][0],
                    far[i][1],
                    far[i][2],
                    int(dino["frame_index"][i]),
                    float(ade_m[i] * 100),
                    float(path_ade_cm[i]),
                ]
            )

    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "export_pathact8_residual.py",
        "goal_pos_mode": "blend_path",
        "path_source": "wp_poly",
        "path_gate": "none",
        "path_units": args.path_units,
        "wp_scale": args.wp_scale,
        "num_samples": args.num_samples,
        "seed": args.seed,
        "n_frames": n,
        "horizon": horizon,
        "pos_dim": pos_dim,
        "run_dir": args.run_dir,
        "checkpoint": args.checkpoint,
        "checkpoint_sha256": sha256_file(ckpt_path),
        "wp_head": args.wp_head,
        "wp_head_sha256": sha256_file(args.wp_head),
        "frames_csv": args.frames_csv,
        "mean_ade_edino_cm": float(ade_m.mean() * 100),
        "mean_path_ade_cm": float(path_ade_cm.mean()),
        "note": "Historical pure-far baselines may lack checkpoints; this export is pathact8-only.",
    }
    meta_path = os.path.join(args.out_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    print(f"mean E-dino ADE {100 * ade_m.mean():.2f} cm | mean path-head ADE vs GT {path_ade_cm.mean():.2f} cm")
    print(f"Wrote {os.path.abspath(npz_path)}")
    print(f"Wrote {os.path.abspath(meta_path)}")


if __name__ == "__main__":
    main()

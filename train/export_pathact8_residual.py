"""Export pathact8 WP path, E-dino nav samples, and GT for residual ADE diagnosis.

Standalone — does not modify eval_e_dino.py / train code. Defaults match deploy audit eval.
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

import cv2  # noqa: F401
import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import ade_fde, load_config, load_observation, load_paired_frames
from eval_e_dino import head_predict_wp_path
from eval_frame_sets import (
    PAIRED_FRAMES,
    TURN_LOOSE,
    TURN_STRICT,
    frame_motion,
    turning_mask,
)
from eval_goal_head import make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import diffuse, encode_cond, load_model, mean_ade_fde
from eval_waypoint_head import blend
from revalidate import CACHE_ROOT
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from vint_train.training.train_utils import append_goal_pos

# pathact8 WP path head targets are ViNT action / dataset units (see audit path_units_notes.md).
HEAD_PATH_OUTPUT_UNITS = "dataset"

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
DEFAULT_OUT = "logs/revalidation/pathact8_residual_export/smoke20"

SCORE_DEFINITION = {
    "ade_edino_m": (
        "eval_position_noise.mean_ade_fde: for each frame, mean L2 step error in meters "
        "averaged over horizon, then averaged over num_samples diffusion draws. "
        "pred [S,H,2] and gt [H,2] in dataset units; scaled by meters_per_unit (eval_by_distance.ade_fde)."
    ),
    "per_step_consistency": (
        "mean_k(mean_s L2(s,k)) == mean_s(mean_k L2(s,k)) == ade (linearity of mean)."
    ),
    "gt_in_condition": (
        "False: E-dino cond is encode_cond(images) + append_goal_pos(e_dino_pos); "
        "e_dino_pos = [mu_x, mu_y, path_flat] from DINO/WP/B only, not GT actions."
    ),
    "path_cond": (
        "Same as eval_e_dino blend_path + wp_poly: kappa-blend dir * b_steps, wp_poly path "
        "with path_units flag (dataset=use head xy; meters=divide head xy by meters_per_unit "
        "when head outputs meters — pathact8 head outputs dataset units)."
    ),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_commit_short():
    root = Path(__file__).resolve().parent
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def file_meta(path):
    if not os.path.isfile(path):
        return {"path": path, "exists": False}
    return {
        "path": path,
        "exists": True,
        "bytes": os.path.getsize(path),
        "sha256": sha256_file(path),
    }


def load_frames_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
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


def moment_indices(moments, far):
    idx_by_nt = {(name, t): i for i, (name, t, _goals) in enumerate(moments)}
    out = []
    for traj_name, t, _goal_time in far:
        key = (traj_name, t)
        if key not in idx_by_nt:
            raise KeyError(f"no PAIRED_FRAMES moment for {key}")
        out.append(idx_by_nt[key])
    return np.asarray(out, dtype=np.int32)


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


def align_path_steps(path_xy, path_steps):
    path = path_xy.astype(np.float32)
    if path.shape[1] < path_steps:
        pad = path_steps - path.shape[1]
        path = np.concatenate([path, np.repeat(path[:, -1:, :], pad, axis=1)], axis=1)
    elif path.shape[1] > path_steps:
        path = path[:, :path_steps]
    return path


def path_for_eval_cond(wp_path_head, meters, path_steps, path_units):
    """Match eval_e_dino.py wp_poly branch (path_gate=none)."""
    path = align_path_steps(wp_path_head, path_steps)
    if path_units == "meters":
        path = path / max(float(meters), 1e-6)
    return path


def build_blend_path_cond(
    dino_dir,
    dino_kappa,
    b_dist_m,
    wp_dir,
    wp_kappa,
    wp_path_head,
    meters,
    pos_dim,
    path_units,
    wp_scale=1.0,
):
    b_steps = b_dist_m / meters
    direction = blend(dino_dir, dino_kappa, wp_dir, wp_kappa, wp_scale=wp_scale)
    mu_units = (direction * b_steps[:, None]).astype(np.float32)
    path_steps = max(1, (pos_dim - 2) // 2)
    path_cond = path_for_eval_cond(wp_path_head, meters, path_steps, path_units)
    e_dino_pos = np.concatenate([mu_units, path_cond.reshape(len(mu_units), -1)], axis=1).astype(
        np.float32
    )
    if e_dino_pos.shape[1] != pos_dim:
        raise ValueError(f"blend_path pos width {e_dino_pos.shape[1]} != {pos_dim}")
    wp_path_m = wp_path_head.astype(np.float32) * float(meters)
    wp_path_dataset = align_path_steps(wp_path_head, path_steps)
    return mu_units, direction, path_cond, wp_path_dataset, wp_path_m, e_dino_pos


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
    paths = [
        ("pathact8_ckpt", os.path.join(args.run_dir, args.checkpoint)),
        ("config_e_dino", args.config_e_dino),
        ("config_b", args.config_b),
        ("checkpoint_b", args.checkpoint_b),
        ("dino_predictions", args.dino_predictions),
        ("wp_head", args.wp_head),
        ("frames_csv", args.frames_csv),
        ("dino_features", os.path.join(CACHE_ROOT, "test_paired", "features.npy")),
    ]
    missing = []
    for name, path in paths:
        ok = os.path.isfile(path)
        if not ok:
            missing.append((name, path))
        size = os.path.getsize(path) if ok else 0
        digest = sha256_file(path)[:16] if ok and size < 250_000_000 else ("n/a" if not ok else "large")
        print(f"  [{name}] {'OK' if ok else 'MISSING'} {path} ({size} B, sha256={digest})")
    if missing:
        raise FileNotFoundError("Preflight failed: " + ", ".join(f"{n}={p}" for n, p in missing))


def run_post_export_checks(
    far,
    gt,
    nav_samples,
    ade_m,
    e_dino_pos,
    mu_units,
    path_cond,
    path_cond_flat,
    meters,
    dino,
    traj,
    t_arr,
    goal_t,
):
    n = len(far)
    report = {"ok": True, "checks": []}

    def add(name, ok, detail):
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["ok"] = False

    for i in range(n):
        if (traj[i], int(t_arr[i]), int(goal_t[i])) != far[i]:
            add("sample_id_row", False, f"row {i} mismatch")
            break
    else:
        add("sample_id_row", True, f"n={n} traj/t/goal_time align with far list")

    ade_re = np.zeros(n, dtype=np.float64)
    per_step_via_mean = np.zeros(n, dtype=np.float64)
    for i in range(n):
        ade_re[i], _ = mean_ade_fde(nav_samples[i], gt[i], meters)
        dist_s_k, _ = ade_fde(nav_samples[i], gt[i], meters)
        per_step_via_mean[i] = float(dist_s_k.mean(axis=0).mean())

    max_ade_diff = float(np.max(np.abs(ade_re - ade_m)))
    add(
        "ade_recompute_mean_ade_fde",
        max_ade_diff < 1e-5,
        f"max |ade_re - ade_m| = {max_ade_diff:.2e} m",
    )
    max_step_diff = float(np.max(np.abs(per_step_via_mean - ade_m)))
    add(
        "per_step_mean_equals_ade",
        max_step_diff < 1e-5,
        f"max |mean_k(mean_s err) - ade_m| = {max_step_diff:.2e} m",
    )

    rebuilt = np.concatenate([mu_units, path_cond.reshape(n, -1)], axis=1)
    pos_diff = float(np.max(np.abs(rebuilt - e_dino_pos)))
    add(
        "path_cond_matches_e_dino_pos",
        pos_diff < 1e-6,
        f"max |rebuild e_dino_pos - stored| = {pos_diff:.2e} (dataset units)",
    )

    gt_flat = gt.reshape(n, -1)
    path_flat = path_cond.reshape(n, -1)
    gt_vs_path = float(np.linalg.norm(gt_flat - path_flat, axis=1).mean())
    add(
        "gt_not_used_as_path_cond",
        gt_vs_path > 1e-4 or n > 0,
        f"mean L2(path_cond vs gt) in dataset units = {gt_vs_path:.4f} (should differ; GT not copied into cond)",
    )

    if not np.all(dino["frame_index"] == dino["frame_index"][0] + np.arange(n)):
        add("frame_index_order", True, "frame_index from DINO npz (sorted far slice)")
    add("target_m_shape", dino["target_m"].shape == (n, 2), str(dino["target_m"].shape))

    return report


def main():
    parser = argparse.ArgumentParser(description="Export pathact8 residual diagnostics")
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
    parser.add_argument("--max-frames", type=int, default=20)
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Preflight (actual CLI paths):")
    preflight(args)

    far = load_frames_csv(args.frames_csv)
    verify_frames_vs_locked(far)
    if args.max_frames > 0:
        far = far[: args.max_frames]
    print(f"Export frames: n={len(far)} from {args.frames_csv}")

    if args.dry_run:
        print("Dry-run OK — no GPU export.")
        return

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_ed = load_config(args.config_e_dino)
    pos_dim = int(config_ed.get("goal_pos_dim", 18))
    path_steps = max(1, (pos_dim - 2) // 2)
    dataset = make_split_dataset(config_b, "test")
    meters = float(meters_per_unit(dataset))
    horizon = int(dataset.len_traj_pred)
    n = len(far)

    moments = load_paired_frames(PAIRED_FRAMES)
    mom_idx = moment_indices(moments, far)
    lateral, yaw = frame_motion(dataset, moments, meters)
    strict_turn = turning_mask(lateral, yaw, TURN_STRICT)[mom_idx]
    loose_turn = turning_mask(lateral, yaw, TURN_LOOSE)[mom_idx]

    dino = load_dino_far_slice(args.dino_predictions, n)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    wp_head, _ = load_dino_head(args.wp_head, device)
    wp_dir, wp_kappa, wp_path_head = head_predict_wp_path(wp_head, far, rows, feats, device)

    mu_units, blend_dir, path_cond, wp_path_dataset, wp_path_m, e_dino_pos = build_blend_path_cond(
        dino["dino_dir"],
        dino["dino_kappa"],
        dino["b_dist_m"],
        wp_dir,
        wp_kappa,
        wp_path_head,
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

    path_ade_cm = (
        np.linalg.norm(path_cond - gt[:, : path_cond.shape[1]], axis=-1).mean(axis=1) * meters * 100
    ).astype(np.float32)

    os.makedirs(args.out_dir, exist_ok=True)
    traj = np.array([f[0] for f in far], dtype=object)
    t_arr = np.array([f[1] for f in far], dtype=np.int32)
    goal_t = np.array([f[2] for f in far], dtype=np.int32)

    array_units = {
        "gt_actions": "dataset (ViNT action units, same as eval load_observation)",
        "wp_path_head": HEAD_PATH_OUTPUT_UNITS + " (raw WP path_head output)",
        "wp_path_dataset": "dataset (aligned to path_steps)",
        "wp_path_meters": "meters (wp_path_head * meters_per_unit)",
        "path_cond": f"dataset (fed to E-dino; eval path_units={args.path_units})",
        "mu_units": "dataset (blend dir * b_steps)",
        "e_dino_pos": "dataset (mu + flat path_cond)",
        "nav_pred_samples": "dataset",
        "nav_pred_mean": "dataset",
        "target_m": "meters (from DINO predictions.npz)",
        "b_dist_m": "meters",
    }

    npz_path = os.path.join(args.out_dir, "residual_export.npz")
    np.savez_compressed(
        npz_path,
        traj_name=traj,
        t=t_arr,
        goal_time=goal_t,
        frame_index=dino["frame_index"],
        moment_index=mom_idx,
        strict_turn=strict_turn.astype(np.bool_),
        loose_turn=loose_turn.astype(np.bool_),
        target_m=dino["target_m"],
        b_dist_m=dino["b_dist_m"],
        gt_actions=gt,
        wp_path_head=wp_path_head.astype(np.float32),
        wp_path_dataset=wp_path_dataset,
        wp_path_meters=wp_path_m,
        path_cond=path_cond,
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
        path_units_flag=np.array(args.path_units),
        head_path_output_units=np.array(HEAD_PATH_OUTPUT_UNITS),
    )

    frames_csv_out = os.path.join(args.out_dir, "frames.csv")
    with open(frames_csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "row",
                "traj_name",
                "t",
                "goal_time",
                "frame_index",
                "moment_index",
                "strict_turn",
                "loose_turn",
                "ade_edino_cm",
                "path_ade_cm",
            ]
        )
        for i in range(n):
            w.writerow(
                [
                    i,
                    far[i][0],
                    far[i][1],
                    far[i][2],
                    int(dino["frame_index"][i]),
                    int(mom_idx[i]),
                    int(strict_turn[i]),
                    int(loose_turn[i]),
                    float(ade_m[i] * 100),
                    float(path_ade_cm[i]),
                ]
            )

    check_report = run_post_export_checks(
        far,
        gt,
        nav_samples,
        ade_m,
        e_dino_pos,
        mu_units,
        path_cond,
        path_cond.reshape(n, -1),
        meters,
        dino,
        traj,
        t_arr,
        goal_t,
    )

    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "export_pathact8_residual.py",
        "git_commit": git_commit_short(),
        "argv": sys.argv,
        "args": vars(args),
        "deploy": {
            "goal_pos_mode": "blend_path",
            "path_source": "wp_poly",
            "path_gate": "none",
            "path_units": args.path_units,
            "wp_scale": args.wp_scale,
        },
        "num_samples": args.num_samples,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "n_frames": n,
        "horizon": horizon,
        "path_steps": path_steps,
        "pos_dim": pos_dim,
        "meters_per_unit": meters,
        "array_units": array_units,
        "score_definition": SCORE_DEFINITION,
        "files": {
            "pathact8_ckpt": file_meta(ckpt_path),
            "wp_head": file_meta(args.wp_head),
            "dino_predictions": file_meta(args.dino_predictions),
            "config_e_dino": file_meta(args.config_e_dino),
            "config_b": file_meta(args.config_b),
            "checkpoint_b": file_meta(args.checkpoint_b),
            "frames_csv": file_meta(args.frames_csv),
        },
        "mean_ade_edino_cm": float(ade_m.mean() * 100),
        "mean_path_cond_ade_cm": float(path_ade_cm.mean()),
        "post_export_checks": check_report,
        "note": "Does not restore missing historical baseline checkpoints.",
    }
    meta_path = os.path.join(args.out_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    checks_path = os.path.join(args.out_dir, "checks.json")
    with open(checks_path, "w", encoding="utf-8") as f:
        json.dump(check_report, f, indent=2)
        f.write("\n")

    print(f"mean E-dino ADE {100 * ade_m.mean():.2f} cm | path_cond vs GT {path_ade_cm.mean():.2f} cm")
    print(f"post-export checks ok={check_report['ok']}")
    for c in check_report["checks"]:
        print(f"  [{'PASS' if c['ok'] else 'FAIL'}] {c['name']}: {c['detail']}")
    print(f"Wrote {os.path.abspath(npz_path)}")
    print(f"Wrote {os.path.abspath(meta_path)}")


if __name__ == "__main__":
    main()

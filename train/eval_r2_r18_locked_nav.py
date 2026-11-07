"""Locked 1000-frame test: fair R2 (2D mu) vs R18 (mu + pathact8 path), fixed checkpoints.

Shared diffusion initial noise and per-chunk generator seeds across models; no training.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2  # noqa: F401
import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_e_path_adapt_val import (
    chunk_seed,
    diffuse_shared,
    nav_ade_cm_decomposed_per_frame,
    past_rows_batch,
    pregenerate_noise,
)
from eval_frame_sets import PAIRED_FRAMES, TURN_LOOSE, TURN_STRICT, frame_motion, turning_mask
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import encode_cond, mean_ade_fde
from export_pathact8_residual import verify_frames_vs_locked
from eval_path_readout_a_locked_nav import (
    git_commit_short,
    load_frames_csv,
    moment_indices,
    run_diffusion_replay_check,
)
from revalidate import CACHE_ROOT
from r2_r18_common import bootstrap_traj_pooled_pairs
from train_e_dino import (
    E_ORACLE_CHECKPOINT,
    build_e_model,
    estimated_goal_pos,
    load_dino_head,
    load_expand_cond,
)
from train_goal_dino import load_cache
from vint_train.training.train_utils import append_goal_pos, get_action

DEFAULT_OUT = "logs/revalidation/r2_r18_locked_2026-11-07"
DEFAULT_FRAMES = "logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv"
DEFAULT_CONFIG_B = "config/nomad_b40.yaml"
CONFIG_R2 = "config/nomad_e_dino_r2_r18.yaml"
CONFIG_R18 = "config/nomad_e_dino_r18.yaml"
CKPT_R2 = "logs/nomad/nomad_e_r2_fair_20261107/ema_4.pth"
CKPT_R18 = "logs/nomad/nomad_e_r18_fair_20261107/ema_1.pth"
SHA_R2 = "bcd2ef1e69eb8e4f649395a11873988b98992a8a4e5cf67b07771be507928b9b"
SHA_R18 = "53d5f5606f3aaccab5f5b208edf9e01ed6f680efdd1279fca1dfd7f7d99a072a"
DINO = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
PATHACT8 = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
BOOT_N = 10000
BOOT_SEED = 20261107
NUM_SAMPLES = 8
BATCH_SIZE = 8
EVAL_SEED = 0

TIME_SLICE = slice(0, 256)
VISION_SLICE = slice(256, 512)
MU_SLICE = slice(512, 514)
PATH_SLICE = slice(514, 530)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_checkpoint(path: str, expected_sha: str) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    got = sha256_file(path)
    if got != expected_sha:
        raise RuntimeError(f"checkpoint sha256 mismatch for {path}: expected {expected_sha}, got {got}")
    return {"path": path, "sha256": got}


def load_e_checkpoint(config: dict, pos_dim: int, ckpt_path: str, device: torch.device):
    model, scheduler = build_e_model(config, pos_dim)
    st = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    if isinstance(st, dict) and "state_dict" in st:
        st = st["state_dict"]
    model.load_state_dict(st, strict=True)
    model.to(device).eval()
    return model, scheduler


def cond_slices_report(pos_dim: int, diffusion_step_embed_dim: int = 256, encoding_size: int = 256) -> dict:
    cond_dim = diffusion_step_embed_dim + encoding_size + pos_dim
    path_stop = diffusion_step_embed_dim + encoding_size + pos_dim
    path_start = diffusion_step_embed_dim + encoding_size + 2
    return {
        "diffusion_step_embed_dim": diffusion_step_embed_dim,
        "encoding_size": encoding_size,
        "pos_dim": pos_dim,
        "cond_dim": cond_dim,
        "slices": {
            "time": f"[0:{diffusion_step_embed_dim})",
            "vision": f"[{diffusion_step_embed_dim}:{diffusion_step_embed_dim + encoding_size})",
            "mu": f"[{diffusion_step_embed_dim + encoding_size}:{diffusion_step_embed_dim + encoding_size + 2})",
            "path": f"[{path_start}:{path_stop})" if pos_dim > 2 else None,
        },
    }


def audit_path_cond_columns(
    config_r18: dict,
    model_r18: torch.nn.Module,
    e_oracle_ckpt: str,
    device: torch.device,
) -> dict:
    pos_dim = 18
    meta = cond_slices_report(
        pos_dim,
        diffusion_step_embed_dim=256,
        encoding_size=int(config_r18.get("encoding_size", 256)),
    )
    model_ref, _ = build_e_model(config_r18, pos_dim)
    load_expand_cond(model_ref, e_oracle_ckpt, 2, pos_dim, device, label="e_oracle")
    model_ref.eval()

    layers = []
    path_delta_max = 0.0
    ref_sd = model_ref.state_dict()
    trained_sd = model_r18.state_dict()
    for key in sorted(trained_sd):
        if not key.startswith("noise_pred_net.") or not key.endswith("cond_encoder.1.weight"):
            continue
        w_train = trained_sd[key]
        w_ref = ref_sd.get(key)
        if w_ref is None or w_ref.shape != w_train.shape:
            continue
        entry = {
            "name": key,
            "shape": [int(x) for x in w_train.shape],
            "slices": meta["slices"],
        }
        if w_train.shape[1] >= PATH_SLICE.stop:
            d = (
                w_train[:, PATH_SLICE].detach().cpu().float()
                - w_ref[:, PATH_SLICE].detach().cpu().float()
            ).abs().max().item()
            entry["path_slice"] = f"[{PATH_SLICE.start}:{PATH_SLICE.stop})"
            entry["max_abs_delta_path_vs_oracle_expand"] = float(d)
            path_delta_max = max(path_delta_max, float(d))
        layers.append(entry)

    meta["cond_encoder_layers"] = layers
    meta["path_cols_max_abs_delta_vs_e_oracle_zero_init"] = path_delta_max
    meta["e_oracle_checkpoint"] = e_oracle_ckpt
    meta["e_oracle_sha256"] = sha256_file(e_oracle_ckpt) if os.path.isfile(e_oracle_ckpt) else None
    return meta


@torch.no_grad()
def assert_wp_path_context2(path_head, far, rows, feats, device, batch_size=8):
    context = max(0, int(path_head.kind.shape[0]) - 2)
    if context != 2:
        raise RuntimeError(f"expected WP path context=2, head reports {context}")
    from train_e_dino import read_tokens

    chunk = far[: min(batch_size, len(far))]
    curr = read_tokens(feats, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
    goal = read_tokens(feats, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
    past = [
        read_tokens(feats, [rows[(c[0], c[1] - j)] for c in chunk]).to(device).float()
        for j in range(1, context + 1)
    ]
    ctx = torch.stack(past, dim=1)
    if ctx.shape[1] != 2:
        raise RuntimeError(f"ctx batch missing 2 history frames: {tuple(ctx.shape)}")
    _ = path_head(curr, goal, ctx)
    return {"context_frames": 2, "batch_size_checked": int(ctx.shape[0]), "ctx_shape": [int(x) for x in ctx.shape]}


@torch.no_grad()
def build_est_pos_batch(
    chunk,
    rows,
    features,
    dataset,
    loc_model,
    dino_head,
    path_head,
    device,
    pos_dim,
    goal_pos_mode,
    meters,
):
    obs_list, goal_list = [], []
    traj_names, curr_ts = [], []
    curr_rows, goal_rows = [], []
    for traj_name, t, goal_time in chunk:
        obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
        obs_list.append(obs)
        goal_list.append(goal)
        traj_names.append(traj_name)
        curr_ts.append(t)
        curr_rows.append(int(rows[(traj_name, t)]))
        goal_rows.append(int(rows[(traj_name, goal_time)]))
    batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
    past = past_rows_batch(traj_names, curr_ts, rows, dataset.waypoint_spacing)
    cr = np.array(curr_rows, dtype=np.int64)
    gr = np.array(goal_rows, dtype=np.int64)
    kw = dict(
        loc_model=loc_model,
        dino_head=dino_head,
        features=features,
        batch_obs=batch_obs,
        batch_goal=batch_goal,
        curr_rows=cr,
        goal_rows=gr,
        device=device,
        past_rows=past,
        path_gate="none",
        path_source="wp_poly",
        meters_per_unit=meters,
        path_units="dataset",
        wp_scale=1.0,
        wp_head=None,
    )
    if goal_pos_mode == "goal_path":
        return estimated_goal_pos(**kw, pos_dim=pos_dim, goal_pos_mode="goal_path", wp_path_head=path_head)
    return estimated_goal_pos(**kw, pos_dim=pos_dim, goal_pos_mode="goal", wp_path_head=None)


@torch.no_grad()
def sample_nav_shared_r2_r18(
    model_r2,
    model_r18,
    sched_r2,
    sched_r18,
    dataset,
    far,
    rows,
    features,
    loc_model,
    dino_head,
    path_head,
    device,
    num_samples,
    batch_size,
    noise_chunks,
    base_seed,
    meters,
    mu_match_max,
):
    horizon = int(dataset.len_traj_pred)
    n = len(far)
    nav_r2 = np.zeros((n, num_samples, horizon, 2), dtype=np.float32)
    nav_r18 = np.zeros((n, num_samples, horizon, 2), dtype=np.float32)
    est_r2_store = np.zeros((n, 2), dtype=np.float32)
    est_r18_store = np.zeros((n, 18), dtype=np.float32)

    for chunk_index, start in enumerate(tqdm(range(0, n, batch_size), desc="nav R2/R18", leave=False)):
        chunk = far[start : start + batch_size]
        est_r2 = build_est_pos_batch(
            chunk, rows, features, dataset, loc_model, dino_head, None, device, 2, "goal", meters
        )
        est_r18 = build_est_pos_batch(
            chunk, rows, features, dataset, loc_model, dino_head, path_head, device, 18, "goal_path", meters
        )
        mu_diff = float(torch.max(torch.abs(est_r2 - est_r18[:, :2])).item())
        mu_match_max[0] = max(mu_match_max[0], mu_diff)
        if mu_diff > 1e-5:
            raise RuntimeError(f"batch {chunk_index}: mu R2 vs R18[:,:2] max diff {mu_diff}")
        est_r2_store[start : start + len(chunk)] = est_r2.detach().cpu().numpy()
        est_r18_store[start : start + len(chunk)] = est_r18.detach().cpu().numpy()

        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        init_noise = noise_chunks[chunk_index].clone()
        seed = chunk_seed(base_seed, chunk_index)
        mask = torch.zeros(len(chunk), dtype=torch.long, device=device)

        for model, sched, est, out in (
            (model_r2, sched_r2, est_r2, nav_r2),
            (model_r18, sched_r18, est_r18, nav_r18),
        ):
            gen = torch.Generator(device=device)
            gen.manual_seed(seed)
            cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
            cond_goal = append_goal_pos(cond_goal, est, mask_goal if mask_goal is not None else mask)
            pred = diffuse_shared(model, sched, cond_goal, init_noise.clone(), num_samples, device, gen)
            out[start : start + len(chunk)] = pred[..., :2].detach().cpu().numpy()

    return nav_r2, nav_r18, est_r2_store, est_r18_store


@torch.no_grad()
def replay_model_twice(model, sched, dataset, far, rows, features, loc_model, dino_head, path_head, device, num_samples, batch_size, noise_chunks, base_seed, meters, use_r18):
    n = min(batch_size, len(far))
    chunk = far[:n]
    est = build_est_pos_batch(
        chunk,
        rows,
        features,
        dataset,
        loc_model,
        dino_head,
        path_head if use_r18 else None,
        device,
        18 if use_r18 else 2,
        "goal_path" if use_r18 else "goal",
        meters,
    )
    obs_list, goal_list = [], []
    for traj_name, t, goal_time in chunk:
        obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
        obs_list.append(obs)
        goal_list.append(goal)
    batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
    noise = noise_chunks[0].clone()
    seed = chunk_seed(base_seed, 0)
    mask = torch.zeros(len(chunk), dtype=torch.long, device=device)

    def once():
        gen = torch.Generator(device=device)
        gen.manual_seed(seed)
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        cond_goal = append_goal_pos(cond_goal, est, mask_goal if mask_goal is not None else mask)
        return diffuse_shared(model, sched, cond_goal, noise.clone(), num_samples, device, gen)

    a = once().detach().cpu().numpy()
    b = once().detach().cpu().numpy()
    return float(np.max(np.abs(a - b)))


def load_gt_nav(dataset, far, horizon):
    gt = []
    for traj_name, t, goal_time in far:
        _o, _g, actions, _p = load_observation(dataset, traj_name, t, goal_time)
        gt.append(np.asarray(actions, dtype=np.float32)[:, :2])
    return np.stack(gt, axis=0)


def per_step_mean_err_cm(nav, gt, meters):
    err = np.linalg.norm(nav - gt[:, None, :, :], axis=-1).mean(axis=(1, 2))
    return (err * meters * 100.0).astype(np.float32)


def json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return str(o)


def write_conclusion_zh(out_dir, ade_r2, ade_r18, delta_mean, boot, n_strict, turn_r2, turn_r18):
    lines = [
        "# R2 vs R18 Locked Far 1000",
        "",
        f"- R2 (2D mu): nav ADE {ade_r2:.4f} cm",
        f"- R18 (mu + pathact8 16D): nav ADE {ade_r18:.4f} cm",
        f"- paired delta R2-R18 (positive => R18 better): {delta_mean:+.4f} cm",
        "",
        f"Bootstrap traj-pooled n={BOOT_N} seed={BOOT_SEED}: "
        f"mean {boot['mean_improvement_cm']:+.4f} cm, "
        f"95% CI [{boot['ci95_lo_cm']:+.4f}, {boot['ci95_hi_cm']:+.4f}]",
        "",
        f"Strict turn subset n={n_strict}: R2 {turn_r2:.4f} cm, R18 {turn_r18:.4f} cm",
        "",
        "Fixed checkpoints, shared diffusion noise; estimated_goal_pos only (true_pos_prob=0).",
        "",
    ]
    with open(os.path.join(out_dir, "CONCLUSION_zh.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--frames", default=DEFAULT_FRAMES)
    ap.add_argument("--smoke-check", action="store_true")
    ap.add_argument("--max-frames", type=int, default=0, help="0 = full 1000")
    ap.add_argument("--seed", type=int, default=EVAL_SEED)
    ap.add_argument("--num-samples", type=int, default=NUM_SAMPLES)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = ap.parse_args()

    far = load_frames_csv(args.frames)
    verify_frames_vs_locked(far)
    if args.max_frames > 0:
        far = far[: args.max_frames]

    os.makedirs(args.out_dir, exist_ok=True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    ckpt_r2_rec = verify_checkpoint(CKPT_R2, SHA_R2)
    ckpt_r18_rec = verify_checkpoint(CKPT_R18, SHA_R18)

    config_b = load_config(DEFAULT_CONFIG_B)
    config_r2 = load_config(CONFIG_R2)
    config_r18 = load_config(CONFIG_R18)
    dataset = make_split_dataset(config_b, "test")
    meters = float(meters_per_unit(dataset))
    horizon = int(dataset.len_traj_pred)
    n = len(far)

    moments = load_paired_frames(PAIRED_FRAMES)
    mom_idx = moment_indices(moments, far)
    lateral, yaw = frame_motion(dataset, moments, meters)
    strict_turn = turning_mask(lateral, yaw, TURN_STRICT)[mom_idx]
    loose_turn = turning_mask(lateral, yaw, TURN_LOOSE)[mom_idx]
    turning = strict_turn.astype(bool)

    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    features = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(DINO, device)
    path_head, _ = load_dino_head(PATHACT8, device)
    loc_model = load_frozen_nomad(config_b, B_CHECKPOINT, device)

    ctx_info = assert_wp_path_context2(path_head, far, rows, features, device, args.batch_size)

    model_r2, sched_r2 = load_e_checkpoint(config_r2, 2, CKPT_R2, device)
    model_r18, sched_r18 = load_e_checkpoint(config_r18, 18, CKPT_R18, device)

    e_oracle_path = os.path.join(Path(__file__).resolve().parent, E_ORACLE_CHECKPOINT)
    path_cond_audit = audit_path_cond_columns(config_r18, model_r18, e_oracle_path, device)

    noise_chunks = pregenerate_noise(n, args.num_samples, horizon, args.batch_size, device, args.seed)
    mu_match_max = [0.0]
    nav_r2, nav_r18, est_r2, est_r18 = sample_nav_shared_r2_r18(
        model_r2,
        model_r18,
        sched_r2,
        sched_r18,
        dataset,
        far,
        rows,
        features,
        loc_model,
        dino_head,
        path_head,
        device,
        args.num_samples,
        args.batch_size,
        noise_chunks,
        args.seed,
        meters,
        mu_match_max,
    )

    gt_nav = load_gt_nav(dataset, far, horizon)
    ade_r2, f4_r2, b4_r2 = nav_ade_cm_decomposed_per_frame(nav_r2, gt_nav, meters)
    ade_r18, f4_r18, b4_r18 = nav_ade_cm_decomposed_per_frame(nav_r18, gt_nav, meters)
    delta = ade_r2 - ade_r18
    traj_names = np.array([f[0] for f in far], object)

    smoke = None
    if args.smoke_check or n <= 16:
        replay_max = replay_model_twice(
            model_r18,
            sched_r18,
            dataset,
            far,
            rows,
            features,
            loc_model,
            dino_head,
            path_head,
            device,
            args.num_samples,
            args.batch_size,
            noise_chunks,
            args.seed,
            meters,
            use_r18=True,
        )
        n_chunks = (n + args.batch_size - 1) // args.batch_size
        replay_ok = True
        replay_diffs = []
        for ci in range(n_chunks):
            ok_ci, diff_ci = run_diffusion_replay_check(
                model_r18,
                sched_r18,
                dataset,
                far,
                est_r18,
                device,
                args.num_samples,
                args.batch_size,
                noise_chunks,
                ci,
                args.seed,
            )
            replay_ok = replay_ok and ok_ci
            replay_diffs.append(diff_ci)
        replay_max_diff = float(max(replay_diffs)) if replay_diffs else 0.0
        path_nnz = float(np.max(np.abs(est_r18[:, 2:])))
        smoke = {
            "max_replay_same_model_twice": replay_max,
            "max_diffusion_replay_diff": replay_max_diff,
            "mu_r2_r18_max_diff": float(mu_match_max[0]),
            "est_r2_shape": list(est_r2.shape),
            "est_r18_shape": list(est_r18.shape),
            "path_portion_max_abs_r18": path_nnz,
            "ctx_check": ctx_info,
            "ok_replay_twice": bool(replay_max < 1e-5),
            "ok_diffusion_replay": bool(replay_ok),
            "ok_mu_match": bool(mu_match_max[0] < 1e-5),
            "ok_shapes": est_r2.shape[1] == 2 and est_r18.shape[1] == 18,
            "ok_context_2": int(ctx_info.get("context_frames", 0)) == 2,
            "ok_path_nonzero": path_nnz > 1e-6,
            "passed": (
                replay_max < 1e-5
                and replay_ok
                and mu_match_max[0] < 1e-5
                and est_r2.shape[1] == 2
                and est_r18.shape[1] == 18
                and ctx_info.get("context_frames") == 2
                and path_nnz > 1e-6
            ),
        }
        with open(os.path.join(args.out_dir, "smoke_check.json"), "w", encoding="utf-8") as f:
            json.dump(smoke, f, indent=2)

    if smoke is not None and not smoke.get("passed", False):
        print("SMOKE_CHECK_FAILED", json.dumps(smoke, indent=2))
        sys.exit(1)
    if args.smoke_check:
        print("smoke_check", json.dumps(smoke, indent=2))
        sys.exit(0)

    boot_mean, boot_lo, boot_hi = bootstrap_traj_pooled_pairs(delta, traj_names, n_boot=BOOT_N, seed=BOOT_SEED)
    boot = {
        "delta_r2_minus_r18_cm_mean": boot_mean,
        "ci95_lo_cm": boot_lo,
        "ci95_hi_cm": boot_hi,
        "n_boot": BOOT_N,
        "boot_seed": BOOT_SEED,
        "resample_unit": "trajectory (pool all frames from drawn trajs)",
        "interpretation": "positive => R18 lower ADE than R2",
    }

    mean_r2 = float(ade_r2.mean())
    mean_r18 = float(ade_r18.mean())
    main_table = [
        {
            "model": "R2",
            "cond_dim": 2,
            "nav_ade_cm": mean_r2,
            "ade_front4_cm": float(f4_r2.mean()),
            "ade_back4_cm": float(b4_r2.mean()),
            "nav_ade_turn_strict_cm": float(ade_r2[turning].mean()) if turning.any() else float("nan"),
            "checkpoint": CKPT_R2,
            "checkpoint_sha256": ckpt_r2_rec["sha256"],
        },
        {
            "model": "R18",
            "cond_dim": 18,
            "nav_ade_cm": mean_r18,
            "ade_front4_cm": float(f4_r18.mean()),
            "ade_back4_cm": float(b4_r18.mean()),
            "nav_ade_turn_strict_cm": float(ade_r18[turning].mean()) if turning.any() else float("nan"),
            "checkpoint": CKPT_R18,
            "checkpoint_sha256": ckpt_r18_rec["sha256"],
        },
    ]

    per_step = {
        "R2": per_step_mean_err_cm(nav_r2, gt_nav, meters),
        "R18": per_step_mean_err_cm(nav_r18, gt_nav, meters),
    }
    np.savez_compressed(
        os.path.join(args.out_dir, "per_step_mean_err.npz"),
        R2=per_step["R2"],
        R18=per_step["R18"],
    )

    with open(os.path.join(args.out_dir, "main_table.csv"), "w", newline="", encoding="utf-8") as cf:
        w = csv.DictWriter(cf, fieldnames=list(main_table[0].keys()))
        w.writeheader()
        w.writerows(main_table)

    with open(os.path.join(args.out_dir, "per_frame.csv"), "w", newline="", encoding="utf-8") as cf:
        w = csv.DictWriter(
            cf,
            fieldnames=[
                "traj_name",
                "t",
                "goal_time",
                "strict_turn",
                "nav_ade_cm_R2",
                "nav_ade_cm_R18",
                "delta_r2_minus_r18_cm",
                "ade_front4_cm_R2",
                "ade_front4_cm_R18",
                "ade_back4_cm_R2",
                "ade_back4_cm_R18",
            ],
        )
        w.writeheader()
        for i in range(n):
            w.writerow(
                {
                    "traj_name": far[i][0],
                    "t": far[i][1],
                    "goal_time": far[i][2],
                    "strict_turn": int(strict_turn[i]),
                    "nav_ade_cm_R2": float(ade_r2[i]),
                    "nav_ade_cm_R18": float(ade_r18[i]),
                    "delta_r2_minus_r18_cm": float(delta[i]),
                    "ade_front4_cm_R2": float(f4_r2[i]),
                    "ade_front4_cm_R18": float(f4_r18[i]),
                    "ade_back4_cm_R2": float(b4_r2[i]),
                    "ade_back4_cm_R18": float(b4_r18[i]),
                }
            )

    with open(os.path.join(args.out_dir, "paired_delta.csv"), "w", newline="", encoding="utf-8") as cf:
        w = csv.DictWriter(
            cf,
            fieldnames=["traj_name", "t", "goal_time", "delta_r2_minus_r18_cm", "improvement_for_R18"],
        )
        w.writeheader()
        for i in range(n):
            w.writerow(
                {
                    "traj_name": far[i][0],
                    "t": far[i][1],
                    "goal_time": far[i][2],
                    "delta_r2_minus_r18_cm": float(delta[i]),
                    "improvement_for_R18": float(delta[i] > 0),
                }
            )

    cmd = " ".join([sys.executable, os.path.basename(__file__)] + sys.argv[1:])
    with open(os.path.join(args.out_dir, "eval_command.txt"), "w", encoding="utf-8") as f:
        f.write(cmd + "\n")
        f.write("PYTHONPATH=../diffusion_policy (cwd=train)\n")

    with open(os.path.join(args.out_dir, "path_cond_audit.json"), "w", encoding="utf-8") as f:
        json.dump(path_cond_audit, f, indent=2)

    summary = {
        "nav_ade_cm": {"R2": mean_r2, "R18": mean_r18},
        "delta_r2_minus_r18_cm_mean": float(delta.mean()),
        "bootstrap_delta_r2_minus_r18": boot,
        "main_table": main_table,
        "strict_turn_n": int(turning.sum()),
        "path_cond_audit_path_delta_max": path_cond_audit.get("path_cols_max_abs_delta_vs_e_oracle_zero_init"),
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=json_default)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit_short(),
        "frames_csv": args.frames,
        "n_frames": n,
        "seed": args.seed,
        "num_samples": args.num_samples,
        "batch_size": args.batch_size,
        "horizon": horizon,
        "shared_noise_across_R2_R18": True,
        "paired_step_noise_note": "Shared initial noise chunks; each model resets torch.Generator per chunk to seed+10007*chunk_index.",
        "estimated_goal_pos": {
            "R2": {"goal_pos_mode": "goal", "pos_dim": 2, "true_pos_prob": 0},
            "R18": {
                "goal_pos_mode": "goal_path",
                "pos_dim": 18,
                "wp_path_head": PATHACT8,
                "path_source": "wp_poly",
                "path_units": "dataset",
                "true_pos_prob": 0,
            },
        },
        "checkpoints": {"R2": ckpt_r2_rec, "R18": ckpt_r18_rec},
        "dino_head": {"path": DINO, "sha256": sha256_file(DINO) if os.path.isfile(DINO) else None},
        "pathact8_head": {"path": PATHACT8, "sha256": sha256_file(PATHACT8) if os.path.isfile(PATHACT8) else None},
        "configs": {"R2": CONFIG_R2, "R18": CONFIG_R18, "nomad_b40": DEFAULT_CONFIG_B},
        "cache": {"root": CACHE_ROOT, "split": "test_paired"},
        "mu_match_max_abs": float(mu_match_max[0]),
        "smoke_check": smoke,
        "summary": summary,
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=json_default)

    write_conclusion_zh(
        args.out_dir,
        mean_r2,
        mean_r18,
        float(delta.mean()),
        {
            "mean_improvement_cm": boot_mean,
            "ci95_lo_cm": boot_lo,
            "ci95_hi_cm": boot_hi,
        },
        int(turning.sum()),
        float(ade_r2[turning].mean()) if turning.any() else float("nan"),
        float(ade_r18[turning].mean()) if turning.any() else float("nan"),
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

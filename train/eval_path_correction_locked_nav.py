"""Locked far eval for path correction A/B vs pathact8 baseline.

Protocols (--mu-protocol):
  fixed_mu     — baseline deploy mu_units for every variant; only swap 16-d path in e_dino_pos.
  deploy_blend — blend_path + wp_poly: mu from blend(dino_dir, dino_kappa, wp_dir, wp_kappa)
                 with wp_dir = normalize(corrected path step-8); kappa from frozen WP head (not recalibrated).

All variants in one run share the same far frame order, E checkpoint, and pregenerated diffusion noise.
"""

import argparse
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
from eval_e_dino import head_predict_wp_path
from eval_frame_sets import PAIRED_FRAMES, turning_mask, frame_motion
from eval_goal_head import make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import encode_cond, load_model, mean_ade_fde
from vint_train.training.train_utils import get_action
from eval_waypoint_head import blend
from export_pathact8_residual import (
    load_dino_far_slice,
    load_gt_actions,
    path_for_eval_cond,
    verify_frames_vs_locked,
)
from path_correction_ab import FrozenPathAct8WithCorrection
from revalidate import CACHE_ROOT
from eval_frame_sets import TURN_LOOSE, TURN_STRICT
from train_e_dino import load_dino_head, read_tokens
from train_goal_dino import CACHE_DIR, load_cache, load_head_checkpoint
from vint_train.models.nomad.pair_token_head import PairTokenHead
from vint_train.training.train_utils import append_goal_pos
from yaw_traj import path_tensor_from_out

DEFAULT_WP_BASE = (
    "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
)
DEFAULT_E_RUN = "logs/nomad/nomad_e_ft_pathact8"
DEFAULT_E_CKPT = "ema_latest.pth"
DEFAULT_CONFIG_E = "config/nomad_e_dino_path.yaml"
DEFAULT_CONFIG_B = "config/nomad_b40.yaml"
DEFAULT_FRAMES = "logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv"
DEFAULT_DINO_PRED = (
    "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"
)
BOOT_SEED = 20261103
BOOT_N = 10000


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_commit_short():
    root = Path(__file__).resolve().parent
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_frames_csv(path):
    import csv

    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.append((row["traj_name"], int(row["t"]), int(row["goal_time"])))
    return out


def moment_indices(moments, far):
    idx_by_nt = {(name, t): i for i, (name, t, _goals) in enumerate(moments)}
    out = []
    for traj_name, t, _goal_time in far:
        key = (traj_name, t)
        if key not in idx_by_nt:
            raise KeyError(f"no PAIRED_FRAMES moment for {key}")
        out.append(idx_by_nt[key])
    return np.asarray(out, dtype=np.int32)


def build_model(init_path, correction_ckpt, correction_mode, device):
    ckpt = torch.load(init_path, map_location="cpu", weights_only=False)
    args = ckpt.get("args", {})
    cache_path, _rows, cache_meta = load_cache(CACHE_DIR, "train")
    base = PairTokenHead(
        cache_meta["dim"],
        cache_meta["tokens"],
        int(args.get("width", 256)),
        int(args.get("layers", 4)),
        int(args.get("heads", 8)),
        float(args.get("dropout", 0.1)),
        int(args.get("context", 2)),
        n_sectors=0,
        path_steps=int(args.get("path_steps", 8)),
        path_mlp=int(args.get("path_mlp", 0)),
        path_residual=int(args.get("path_residual", 0)),
        path_spatial=str(args.get("path_spatial", "") or ""),
        odom_dim=int(args.get("odom_dim", 0)),
        path_rot=bool(args.get("path_rot", False)),
    )
    load_head_checkpoint(base, ckpt["head"])
    mode = correction_mode or "dist"
    model = FrozenPathAct8WithCorrection(base, mode).to(device)
    if correction_ckpt:
        st = torch.load(correction_ckpt, map_location="cpu", weights_only=False)
        model.correction.load_state_dict(st["correction"])
        mode = st.get("correction_mode", mode)
    model.eval()
    return model, mode


@torch.no_grad()
def predict_paths_wp(model, far, rows, feats, device, batch_size=128):
    """Paths [N,8,2] dataset units from correction wrapper."""
    context = max(0, int(model.base.kind.shape[0]) - 2)
    paths = []
    for start in range(0, len(far), batch_size):
        chunk = far[start : start + batch_size]
        curr = read_tokens(feats, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(feats, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        ctx = None
        if context > 0:
            past = [
                read_tokens(feats, [rows[(c[0], c[1] - j)] for c in chunk]).to(device).float()
                for j in range(1, context + 1)
            ]
            ctx = torch.stack(past, dim=1)
        p_corr, _p_base, _raw = model(curr, goal, ctx)
        paths.append(p_corr.float().cpu().numpy())
    return np.concatenate(paths, axis=0).astype(np.float32)


def wp_dir_from_path(path_n_h_2):
    v = np.asarray(path_n_h_2[:, -1, :], dtype=np.float64)
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n = np.maximum(n, 1e-12)
    return (v / n).astype(np.float32)


def deploy_mu_units(dino_dir, dino_kappa, b_dist_m, wp_dir, wp_kappa, meters, wp_scale=1.0):
    b_steps = (b_dist_m / meters).astype(np.float32)
    direction = blend(dino_dir, dino_kappa, wp_dir, wp_kappa, wp_scale=wp_scale)
    return (direction * b_steps[:, None]).astype(np.float32)


def build_e_dino_pos(mu_units, wp_path, meters, pos_dim, path_units="dataset"):
    path_steps = max(1, (pos_dim - 2) // 2)
    path_cond = path_for_eval_cond(wp_path, meters, path_steps, path_units)
    flat = path_cond.reshape(len(mu_units), -1)
    return np.concatenate([mu_units.astype(np.float32), flat.astype(np.float32)], axis=1)


def path_ade_cm(pred_n_h_2, gt_h_2, meters):
    k = min(pred_n_h_2.shape[1], gt_h_2.shape[1])
    err = np.linalg.norm(pred_n_h_2[:, :k] - gt_h_2[:, :k], axis=-1)
    return err.mean(axis=1) * float(meters) * 100.0


def path_ade_front_back_cm(pred, gt, meters):
    k = pred.shape[1]
    mid = k // 2
    f = path_ade_cm(pred[:, :mid], gt[:, :mid], meters)
    b = path_ade_cm(pred[:, mid:], gt[:, mid:], meters)
    return f, b


def pregenerate_noise(n, num_samples, horizon, batch_size, device, seed):
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    chunks = []
    for start in range(0, n, batch_size):
        bs = min(batch_size, n - start)
        chunks.append(torch.randn((bs * num_samples, horizon, 2), device=device))
    return chunks


@torch.no_grad()

def diffuse_shared(model, scheduler, cond, noise, num_samples, device, generator):
    """Reverse diffusion with explicit generator for every scheduler.step variance draw."""
    cond = cond.repeat_interleave(num_samples, dim=0)
    sample = noise.clone()
    for k in scheduler.timesteps:
        noise_pred = model(
            "noise_pred_net",
            sample=sample,
            timestep=k.unsqueeze(-1).repeat(sample.shape[0]).to(device),
            global_cond=cond,
        )
        sample = scheduler.step(
            model_output=noise_pred,
            timestep=k,
            sample=sample,
            generator=generator,
        ).prev_sample
    actions = get_action(sample)
    return actions.reshape(noise.shape[0] // num_samples, num_samples, -1, noise.shape[-1])


def chunk_seed(base_seed, chunk_index):
    return int(base_seed + chunk_index * 10007)


def run_diffusion_replay_check(model, scheduler, dataset, far, e_dino_pos, device, num_samples, batch_size, noise_chunks, chunk_index, base_seed, atol=1e-5):
    """Same inputs + same generator seed -> identical nav samples."""
    start = chunk_index * batch_size
    if start >= len(far):
        return True, 0.0
    chunk = far[start : start + batch_size]
    obs_list, goal_list = [], []
    for traj_name, t, goal_time in chunk:
        obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
        obs_list.append(obs)
        goal_list.append(goal)
    batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
    noise = noise_chunks[chunk_index].clone()
    seed = chunk_seed(base_seed, chunk_index)

    def once():
        gen = torch.Generator(device=device)
        gen.manual_seed(seed)
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        pos = torch.tensor(e_dino_pos[start : start + len(chunk)], dtype=torch.float32, device=device)
        cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
        return diffuse_shared(model, scheduler, cond_goal, noise.clone(), num_samples, device, gen)

    a = once().detach().cpu().numpy()
    b = once().detach().cpu().numpy()
    diff = float(np.max(np.abs(a - b)))
    return diff <= atol, diff


@torch.no_grad()
def sample_nav_paired_variants(
    model,
    scheduler,
    dataset,
    far,
    variant_e_dino,
    device,
    num_samples,
    batch_size,
    noise_chunks,
    base_seed,
    variant_keys,
):
    """For each batch: shared initial noise; each variant resets Generator to the same chunk seed."""
    horizon = dataset.len_traj_pred
    n = len(far)
    out = {k: np.zeros((n, num_samples, horizon, 2), dtype=np.float32) for k in variant_keys}
    for chunk_index, start in enumerate(range(0, n, batch_size)):
        chunk = far[start : start + batch_size]
        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        init_noise = noise_chunks[chunk_index].clone()
        seed = chunk_seed(base_seed, chunk_index)
        for vkey in variant_keys:
            gen = torch.Generator(device=device)
            gen.manual_seed(seed)
            cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
            pos = torch.tensor(
                variant_e_dino[vkey][start : start + len(chunk)], dtype=torch.float32, device=device
            )
            cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
            pred = diffuse_shared(
                model, scheduler, cond_goal, init_noise.clone(), num_samples, device, gen
            )
            out[vkey][start : start + len(chunk)] = pred[..., :2].detach().cpu().numpy()
    return out


def bootstrap_by_trajectory(delta_cm, traj_names, n_boot=BOOT_N, seed=BOOT_SEED):
    traj_names = np.asarray(traj_names)
    uniq = np.unique(traj_names)
    per_traj = np.array([delta_cm[traj_names == u].mean() for u in uniq], dtype=np.float64)
    if per_traj.size < 2:
        m = float(per_traj.mean()) if per_traj.size else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, per_traj.size, size=(n_boot, per_traj.size))
    boots = per_traj[idx].mean(axis=1)
    return float(per_traj.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def sample_nav_shared_noise(model, scheduler, dataset, far, e_dino_pos, device, num_samples, batch_size, noise_chunks):
    horizon = dataset.len_traj_pred
    n = len(far)
    preds = np.zeros((n, num_samples, horizon, 2), dtype=np.float32)
    chunk_idx = 0
    for start in tqdm(range(0, n, batch_size), desc="E-dino nav", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = noise_chunks[chunk_idx]
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        pos = torch.tensor(e_dino_pos[start : start + len(chunk)], dtype=torch.float32, device=device)
        cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
        gen = torch.Generator(device=device)
        gen.manual_seed(chunk_seed(0, chunk_idx))
        chunk_idx += 1
        pred_goal = diffuse_shared(model, scheduler, cond_goal, noise, num_samples, device, gen)
        preds[start : start + len(chunk)] = pred_goal[..., :2].detach().cpu().numpy()
    return preds


def nav_ade_cm_per_frame(nav_samples, gt, meters):
    out = np.zeros(len(gt), dtype=np.float64)
    for i in range(len(gt)):
        ade_m, _ = mean_ade_fde(nav_samples[i], gt[i], meters)
        out[i] = ade_m * 100.0
    return out


def bootstrap_paired_ci(delta_cm, n_boot=BOOT_N, seed=BOOT_SEED):
    v = np.asarray(delta_cm, dtype=np.float64)
    if v.size < 2:
        m = float(v.mean()) if v.size else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    boots = v[idx].mean(axis=1)
    return float(v.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def run_smoke_checks(
    path_base,
    path_zero,
    mu_base,
    e_base,
    e_zero,
    nav_base,
    nav_replay,
    replay_ok,
    replay_max_diff,
    mu_baseline_deploy,
    mu_a_deploy,
    nav_fixed,
    nav_deploy,
):
    pd = np.abs(path_base - path_zero).max()
    ed = np.abs(e_base - e_zero).max()
    nd = np.abs(nav_base - nav_replay).max()
    mu_a_vs_base = float(np.max(np.abs(mu_a_deploy - mu_baseline_deploy))) if mu_a_deploy is not None else float("nan")
    nd_proto = float(np.max(np.abs(nav_fixed - nav_deploy))) if nav_fixed is not None and nav_deploy is not None else float("nan")
    ok_path = bool(pd < 1e-4)
    ok_edino = bool(ed < 1e-4)
    ok_nav = bool(nd < 1e-5)
    ok_replay = bool(replay_ok)
    ok_mu_a_deploy = bool(mu_a_vs_base < 1e-4) if mu_a_deploy is not None else True
    ok_same_mu_nav = bool(nd_proto < 1e-5) if nav_fixed is not None and nav_deploy is not None else True
    ok = ok_path and ok_edino and ok_nav and ok_replay and ok_mu_a_deploy and ok_same_mu_nav
    return {
        "max_path_diff_units": float(pd),
        "max_edino_pos_diff": float(ed),
        "max_nav_sample_diff_vs_replay": float(nd),
        "max_diffusion_replay_diff": float(replay_max_diff),
        "max_mu_A_deploy_minus_baseline_deploy": mu_a_vs_base,
        "max_nav_diff_baseline_fixed_vs_deploy_when_same_mu": nd_proto,
        "ok_zero_path": ok_path,
        "ok_zero_edino_fixed_mu": ok_edino,
        "ok_zero_nav_paired_noise": ok_nav,
        "ok_diffusion_replay_twice": ok_replay,
        "ok_A_deploy_mu_matches_baseline": ok_mu_a_deploy,
        "ok_baseline_fixed_vs_deploy_nav_when_mu_shared": ok_same_mu_nav,
        "passed": ok,
        "note": "program check only, not performance",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wp-base", default=DEFAULT_WP_BASE)
    ap.add_argument("--wp-corr-a", default="", help="Distance correction dino_dir_best.pth")
    ap.add_argument("--wp-corr-b", default="", help="Direction correction dino_dir_best.pth")
    ap.add_argument("--e-run", default=DEFAULT_E_RUN)
    ap.add_argument("--e-checkpoint", default=DEFAULT_E_CKPT)
    ap.add_argument("--config-e-dino", default=DEFAULT_CONFIG_E)
    ap.add_argument("--config-b", default=DEFAULT_CONFIG_B)
    ap.add_argument("--dino-predictions", default=DEFAULT_DINO_PRED)
    ap.add_argument("--frames", default=DEFAULT_FRAMES)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--num-samples", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--path-units", choices=("dataset", "meters"), default="dataset")
    ap.add_argument("--wp-scale", type=float, default=1.0)
    ap.add_argument("--max-frames", type=int, default=0)
    ap.add_argument("--smoke-check", action="store_true", help="Run zero-correction consistency checks only")
    args = ap.parse_args()

    far = load_frames_csv(args.frames)
    verify_frames_vs_locked(far)
    if args.max_frames > 0:
        far = far[: args.max_frames]

    os.makedirs(args.out_dir, exist_ok=True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_ed = load_config(args.config_e_dino)
    pos_dim = int(config_ed.get("goal_pos_dim", 18))
    dataset = make_split_dataset(config_b, "test")
    meters = float(meters_per_unit(dataset))
    horizon = int(dataset.len_traj_pred)
    n = len(far)

    moments = load_paired_frames(PAIRED_FRAMES)
    mom_idx = moment_indices(moments, far)
    lateral, yaw = frame_motion(dataset, moments, meters)
    strict_turn = turning_mask(lateral, yaw, TURN_STRICT)[mom_idx]
    loose_turn = turning_mask(lateral, yaw, TURN_LOOSE)[mom_idx]
    straight = (~loose_turn).astype(bool)
    turning = strict_turn.astype(bool)

    dino = load_dino_far_slice(args.dino_predictions, n)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")

    wp_head, _ = load_dino_head(args.wp_base, device)
    _wd, wp_kappa, _wp_path_head = head_predict_wp_path(wp_head, far, rows, feats, device)

    model_base, _ = build_model(args.wp_base, None, "dist", device)
    path_base = predict_paths_wp(model_base, far, rows, feats, device, args.batch_size)

    paths = {"baseline": path_base}
    best_epoch = {"baseline": None}
    ckpt_sha = {"baseline": sha256_file(args.wp_base) if os.path.isfile(args.wp_base) else None}

    for tag, ckpt, mode in (
        ("A_dist", args.wp_corr_a, "dist"),
        ("B_dir", args.wp_corr_b, "dir"),
    ):
        if not ckpt:
            continue
        m, _ = build_model(args.wp_base, ckpt, mode, device)
        paths[tag] = predict_paths_wp(m, far, rows, feats, device, args.batch_size)
        ckpt_sha[tag] = sha256_file(ckpt)
        st = torch.load(ckpt, map_location="cpu", weights_only=False)
        best_epoch[tag] = int(st.get("epoch", -1))

    gt_nav = load_gt_actions(dataset, far, horizon)
    gt_path = gt_nav[:, : path_base.shape[1], :]

    mu_baseline = deploy_mu_units(
        dino["dino_dir"],
        dino["dino_kappa"],
        dino["b_dist_m"],
        wp_dir_from_path(path_base),
        wp_kappa,
        meters,
        wp_scale=args.wp_scale,
    )

    e_pos = {}
    mu_used = {}
    for name, path in paths.items():
        mu_used[(name, "fixed_mu")] = mu_baseline
        wp_d = wp_dir_from_path(path)
        mu_used[(name, "deploy_blend")] = deploy_mu_units(
            dino["dino_dir"],
            dino["dino_kappa"],
            dino["b_dist_m"],
            wp_d,
            wp_kappa,
            meters,
            wp_scale=args.wp_scale,
        )
        for proto in ("fixed_mu", "deploy_blend"):
            e_pos[(name, proto)] = build_e_dino_pos(
                mu_used[(name, proto)], path, meters, pos_dim, args.path_units
            )

    ckpt_e = os.path.join(args.e_run, args.e_checkpoint)
    model_ed, sched_ed = load_model(config_ed, ckpt_e, device)
    noise_chunks = pregenerate_noise(n, args.num_samples, horizon, args.batch_size, device, args.seed)

    variant_keys = [f"{name}|{proto}" for name in paths for proto in ("fixed_mu", "deploy_blend")]
    variant_e_dino = {k: e_pos[(k.split("|")[0], k.split("|")[1])] for k in variant_keys}
    nav = sample_nav_paired_variants(
        model_ed,
        sched_ed,
        dataset,
        far,
        variant_e_dino,
        device,
        args.num_samples,
        args.batch_size,
        noise_chunks,
        args.seed,
        variant_keys,
    )
    nav_ade = {k: nav_ade_cm_per_frame(nav[k], gt_nav, meters) for k in variant_keys}

    path_metrics = {}
    for name, path in paths.items():
        ade = path_ade_cm(path, gt_path, meters)
        f4, b4 = path_ade_front_back_cm(path, gt_path, meters)
        path_metrics[name] = {
            "path_ade_cm_mean": float(ade.mean()),
            "path_ade_front4_cm_mean": float(f4.mean()),
            "path_ade_back4_cm_mean": float(b4.mean()),
            "path_ade_cm_per_frame": ade.astype(np.float32),
            "straight_path_ade_cm_mean": float(ade[straight].mean()) if straight.any() else float("nan"),
            "turning_path_ade_cm_mean": float(ade[turning].mean()) if turning.any() else float("nan"),
        }

    smoke = None
    if args.smoke_check or n <= 8:
        path_z = path_base.copy()
        e_fix_b = e_pos[("baseline", "fixed_mu")]
        e_fix_z = build_e_dino_pos(mu_baseline, path_z, meters, pos_dim, args.path_units)
        nav_b = nav["baseline|fixed_mu"]
        replay_keys = ["baseline|fixed_mu", "__replay_baseline_fixed_mu__"]
        replay_e = {
            "baseline|fixed_mu": e_fix_b,
            "__replay_baseline_fixed_mu__": e_fix_b,
        }
        nav_replay_pair = sample_nav_paired_variants(
            model_ed,
            sched_ed,
            dataset,
            far,
            replay_e,
            device,
            args.num_samples,
            args.batch_size,
            noise_chunks,
            args.seed,
            replay_keys,
        )
        nav_replay = nav_replay_pair["__replay_baseline_fixed_mu__"]
        n_chunks = (n + args.batch_size - 1) // args.batch_size
        replay_ok = True
        replay_diffs = []
        for ci in range(n_chunks):
            ok_ci, diff_ci = run_diffusion_replay_check(
                model_ed,
                sched_ed,
                dataset,
                far,
                e_fix_b,
                device,
                args.num_samples,
                args.batch_size,
                noise_chunks,
                ci,
                args.seed,
            )
            replay_ok = replay_ok and ok_ci
            replay_diffs.append(diff_ci)
        replay_max = float(max(replay_diffs)) if replay_diffs else 0.0
        mu_a_dep = mu_used.get(("A_dist", "deploy_blend"))
        smoke = run_smoke_checks(
            path_base,
            path_z,
            mu_baseline,
            e_fix_b,
            e_fix_z,
            nav_b,
            nav_replay,
            replay_ok,
            replay_max,
            mu_a_dep,
            mu_used.get(("baseline", "deploy_blend")),
            nav.get("baseline|fixed_mu"),
            nav.get("baseline|deploy_blend"),
        )

    if smoke is not None and not smoke.get("passed", False):
        print("SMOKE_CHECK_FAILED", json.dumps(smoke, indent=2))
        if args.smoke_check:
            sys.exit(1)
    if args.smoke_check:
        print("smoke_check", json.dumps(smoke, indent=2))
        sys.exit(0)

    base_nav_fixed = nav_ade["baseline|fixed_mu"]
    base_nav_deploy = nav_ade["baseline|deploy_blend"]
    summary_rows = []
    for name in paths:
        for proto, base_nav in (
            ("fixed_mu", base_nav_fixed),
            ("deploy_blend", base_nav_deploy),
        ):
            key = f"{name}|{proto}"
            delta = nav_ade[key] - base_nav if name != "baseline" else nav_ade[key] * 0.0
            summary_rows.append(
                {
                    "variant": name,
                    "mu_protocol": proto,
                    "nav_ade_cm_mean": float(nav_ade[key].mean()),
                    "delta_vs_baseline_same_protocol_cm_mean": float(delta.mean()),
                }
            )

    per_frame_traj_names = np.array([f[0] for f in far], object)

    boot = {}
    for name in paths:
        if name == "baseline":
            continue
        for proto in ("fixed_mu", "deploy_blend"):
            base = base_nav_fixed if proto == "fixed_mu" else base_nav_deploy
            d = nav_ade[f"{name}|{proto}"] - base
            label = f"{name}_{proto}_minus_baseline"
            m, lo, hi = bootstrap_by_trajectory(d, per_frame_traj_names)
            boot[label] = {
                "mean_cm": m,
                "ci95_lo_cm": lo,
                "ci95_hi_cm": hi,
                "resample_unit": "trajectory (bootstrap over per-traj mean delta, n_boot=10000)",
            }

    per_frame = {
        "traj_name": np.array([f[0] for f in far], object),
        "t": np.array([f[1] for f in far], np.int32),
        "goal_time": np.array([f[2] for f in far], np.int32),
        "strict_turn": strict_turn.astype(np.int8),
        "loose_turn": loose_turn.astype(np.int8),
        "gt_path": gt_path.astype(np.float32),
        "gt_nav_horizon": gt_nav.astype(np.float32),
    }
    for name, path in paths.items():
        per_frame[f"path_{name}"] = path.astype(np.float32)
        for proto in ("fixed_mu", "deploy_blend"):
            key = f"{name}|{proto}"
            per_frame[f"nav_ade_cm_{key}"] = nav_ade[key].astype(np.float32)
            per_frame[f"mu_{key}"] = mu_used[(name, proto)].astype(np.float32)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit_short(),
        "frames_csv": args.frames,
        "n_frames": n,
        "seed": args.seed,
        "num_samples": args.num_samples,
        "batch_size": args.batch_size,
        "shared_noise_across_variants": True,
        "paired_step_noise": True,
        "paired_step_noise_note": "Initial noise chunks shared; each variant resets torch.Generator per batch chunk to base_seed+10007*chunk_index before reverse diffusion.",
        "path_units": args.path_units,
        "wp_scale": args.wp_scale,
        "deploy_blend_sources": {
            "far_goal_direction": "dino_dir from frozen DINO predictions.npz",
            "wp_direction": "normalize(corrected 8-point path last step), dataset units",
            "kappa": "wp_kappa from frozen pathact8 WP head (head_predict_wp_path), not recalibrated",
            "distance_scale": "b_dist_m from predictions.npz -> b_steps = b_dist_m / meters_per_unit",
            "blend": "eval_waypoint_head.blend(dino_dir, dino_kappa, wp_dir, wp_kappa, wp_scale)",
        },
        "fixed_mu_note": "mu_units frozen to baseline deploy_blend mu for all variants",
        "checkpoints": {
            "wp_base": args.wp_base,
            "wp_base_sha256": ckpt_sha.get("baseline"),
            "wp_corr_a": args.wp_corr_a or None,
            "wp_corr_a_sha256": ckpt_sha.get("A_dist"),
            "wp_corr_b": args.wp_corr_b or None,
            "wp_corr_b_sha256": ckpt_sha.get("B_dir"),
            "e_checkpoint": ckpt_e,
            "e_checkpoint_sha256": sha256_file(ckpt_e) if os.path.isfile(ckpt_e) else None,
        },
        "best_epoch_from_ckpt": best_epoch,
        "path_metrics": {k: {kk: vv for kk, vv in v.items() if not kk.endswith("_per_frame")} for k, v in path_metrics.items()},
        "primary_comparison_keys": [
            "baseline|fixed_mu",
            "A_dist|fixed_mu",
            "B_dir|fixed_mu",
            "B_dir|deploy_blend",
        ],
        "mu_max_abs_diff_A_deploy_vs_baseline_deploy": float(
            np.max(np.abs(mu_used.get(("A_dist", "deploy_blend"), mu_baseline) - mu_used.get(("baseline", "deploy_blend"), mu_baseline)))
        ) if "A_dist" in paths else None,
        "historical_eval_note": "logs/revalidation/path_correction_ab/locked_eval/ is v1 (step noise not fully paired); do not compare directly.",
        "nav_summary": summary_rows,
        "bootstrap_nav_delta": boot,
        "smoke_check": smoke,
    }

    cmd = " ".join([sys.executable, os.path.basename(__file__)] + sys.argv[1:])
    with open(os.path.join(args.out_dir, "eval_command.txt"), "w", encoding="utf-8") as f:
        f.write(cmd + "\n")
        f.write("PYTHONPATH=../diffusion_policy (cwd=train)\n")

    np.savez_compressed(os.path.join(args.out_dir, "per_frame_eval.npz"), **per_frame)
    csv_path = os.path.join(args.out_dir, "per_frame_nav_ade.csv")
    import csv

    csv_cols = ["traj_name", "t", "goal_time"] + [f"nav_ade_cm_{k}" for k in variant_keys]
    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        w = csv.DictWriter(cf, fieldnames=csv_cols)
        w.writeheader()
        for i in range(n):
            row = {
                "traj_name": far[i][0],
                "t": far[i][1],
                "goal_time": far[i][2],
            }
            for k in variant_keys:
                row[f"nav_ade_cm_{k}"] = float(nav_ade[k][i])
            w.writerow(row)
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=lambda o: bool(o) if isinstance(o, (np.bool_,)) else (float(o) if isinstance(o, (np.floating,)) else (int(o) if isinstance(o, (np.integer,)) else str(o))))
    path_summary = {
        k: {kk: vv for kk, vv in v.items() if kk != "path_ade_cm_per_frame"}
        for k, v in path_metrics.items()
    }
    _json_default = lambda o: bool(o) if isinstance(o, (np.bool_,)) else (
        float(o) if isinstance(o, (np.floating,)) else (
            int(o) if isinstance(o, (np.integer,)) else str(o)
        )
    )
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"path_metrics": path_summary, "primary_comparison_keys": [
            "baseline|fixed_mu",
            "A_dist|fixed_mu",
            "B_dir|fixed_mu",
            "B_dir|deploy_blend",
        ],
        "mu_max_abs_diff_A_deploy_vs_baseline_deploy": float(
            np.max(np.abs(mu_used.get(("A_dist", "deploy_blend"), mu_baseline) - mu_used.get(("baseline", "deploy_blend"), mu_baseline)))
        ) if "A_dist" in paths else None,
        "historical_eval_note": "logs/revalidation/path_correction_ab/locked_eval/ is v1 (step noise not fully paired); do not compare directly.",
        "nav_summary": summary_rows, "bootstrap": boot}, f, indent=2, default=_json_default)

    if smoke:
        print("smoke_check", json.dumps(smoke, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()

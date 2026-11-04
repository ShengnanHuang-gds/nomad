"""Locked Far 1000-frame downstream nav: O / F / D for CLS path-readout A vs pathact8 deploy.

  O — pathact8 8-point path + deploy mu (normal stack).
  F — A_cls path + mu frozen to O (only last 16 cond dims change).
  D — A_cls path + deploy mu recomputed (wp_dir from A path; wp_kappa from A_cls head forward).

Shared initial and per-step diffusion noise across O/F/D; no retrain or B-group eval.
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
from vint_train.training.train_utils import append_goal_pos, get_action
from eval_waypoint_head import blend
from export_pathact8_residual import (
    load_dino_far_slice,
    load_gt_actions,
    path_for_eval_cond,
    verify_frames_vs_locked,
)
from revalidate import CACHE_ROOT
from eval_frame_sets import TURN_LOOSE, TURN_STRICT
from train_e_dino import load_dino_head, read_tokens
from train_goal_dino import load_cache

DEFAULT_WP_O = (
    "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
)
DEFAULT_WP_A = (
    "logs/nomad_d/nomad_dino_wp_ctx2_pathreadout_A_cls_2026_11_03_23_38_31/dino_dir_best.pth"
)
DEFAULT_CKPT_MANIFEST = "logs/revalidation/path_readout_ab_v2/checkpoints.json"
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


def wp_checkpoint_record(path, manifest_path=DEFAULT_CKPT_MANIFEST):
    rec = {"path": path, "sha256": sha256_file(path) if os.path.isfile(path) else None}
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as mf:
            man = json.load(mf)
        norm = os.path.normpath(path).replace("\\", "/")
        for item in man.get("checkpoints", []):
            ip = os.path.normpath(item.get("path", "")).replace("\\", "/")
            if ip.endswith(norm) or norm.endswith(ip.split("/")[-2] + "/" + os.path.basename(norm)):
                rec.update({k: item[k] for k in ("label", "epoch", "context", "path_spatial", "sha256") if k in item})
                break
    st = torch.load(path, map_location="cpu", weights_only=False)
    rec["epoch_from_ckpt"] = int(st.get("epoch", -1))
    rec["args"] = {k: st.get("args", {}).get(k) for k in ("context", "path_steps", "path_spatial", "freeze_dir")}
    return rec


@torch.no_grad()
def assert_wp_head_context2(head, far, rows, feats, device, batch_size=8):
    """Smoke: WP forward must stack two past frames (ctx=2)."""
    context = max(0, int(head.kind.shape[0]) - 2)
    if context != 2:
        raise RuntimeError(f"expected WP context=2, head reports {context}")
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
    _ = head(curr, goal, ctx)
    return {"context_frames": 2, "batch_size_checked": int(ctx.shape[0]), "ctx_shape": [int(x) for x in ctx.shape]}


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


def bootstrap_trajectory_pooled(delta_cm, traj_names, n_boot=BOOT_N, seed=BOOT_SEED):
    """Resample trajectories with replacement; mean delta over all frames in drawn trajs."""
    delta_cm = np.asarray(delta_cm, dtype=np.float64)
    traj_names = np.asarray(traj_names)
    uniq = np.unique(traj_names)
    by_traj = {u: delta_cm[traj_names == u] for u in uniq}
    if len(uniq) < 2:
        m = float(delta_cm.mean()) if delta_cm.size else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        boots[b] = np.concatenate([by_traj[t] for t in pick]).mean()
    return float(delta_cm.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


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
    mu_o,
    mu_f,
    e_o,
    e_o_rebuild,
    nav_o,
    nav_replay,
    replay_ok,
    replay_max_diff,
    nav_o_dup_branch,
    ctx_info,
):
    mu_f_diff = float(np.max(np.abs(mu_f - mu_o)))
    ed = float(np.max(np.abs(e_o - e_o_rebuild)))
    nd = float(np.max(np.abs(nav_o - nav_replay)))
    nd_dup = (
        float(np.max(np.abs(nav_o - nav_o_dup_branch)))
        if nav_o_dup_branch is not None
        else float("nan")
    )
    ok_mu_f = bool(mu_f_diff < 1e-4)
    ok_edino = bool(ed < 1e-5)
    ok_nav = bool(nd < 1e-5)
    ok_replay = bool(replay_ok)
    ok_dup = bool(nd_dup < 1e-5) if nav_o_dup_branch is not None else True
    ok_ctx = int(ctx_info.get("context_frames", 0)) == 2
    ok = ok_mu_f and ok_edino and ok_nav and ok_replay and ok_dup and ok_ctx
    return {
        "max_mu_F_minus_O": mu_f_diff,
        "max_edino_pos_rebuild_diff": ed,
        "max_nav_sample_diff_vs_replay": nd,
        "max_diffusion_replay_diff": float(replay_max_diff),
        "max_nav_diff_O_vs_duplicate_cond_branch": nd_dup,
        "ctx_check": ctx_info,
        "ok_F_mu_matches_O": ok_mu_f,
        "ok_edino_pos_rebuild": ok_edino,
        "ok_nav_paired_noise_replay": ok_nav,
        "ok_diffusion_replay_twice": ok_replay,
        "ok_same_cond_two_branches": ok_dup,
        "ok_context_2": ok_ctx,
        "passed": ok,
        "note": "program check only, not performance",
    }


def write_report_zh(out_dir, summary_table, boot, strict_turn_stats, paired_stats, historical_ref_cm):
    lines = [
        "# A组 CLS 续训 — Locked Far 1000 下游导航验证（O/F/D）",
        "",
        "## 主表（导航 ADE，cm）",
        "",
        "| 条件 | μ 来源 | 路径来源 | 绝对 ADE | 相对 O 改善 (O−cond) | 相对下降比例 |",
        "|------|--------|----------|----------|----------------------|--------------|",
    ]
    for row in summary_table:
        lines.append(
            f"| {row['condition']} | {row['mu_source']} | {row['path_source']} | "
            f"{row['nav_ade_cm']:.4f} | {row['improvement_vs_O_cm']:+.4f} | {row['relative_drop_pct']:.3f}% |"
        )
    lines.extend(["", "## 严格转弯子集", ""])
    for row in strict_turn_stats:
        lines.append(f"- **{row['condition']}**: ADE={row['nav_ade_cm']:.4f} cm, n={row['n']}")
    lines.extend(["", "## 配对差值（均值，cm；正值表示相对 O 导航 ADE 降低）", ""])
    for k, v in paired_stats.items():
        lines.append(f"- {k}: mean={v['mean_cm']:.4f}, improve_frac={v['improve_frac']:.3f}")
    lines.extend(["", "## Bootstrap（轨迹重采样，10000 次，seed={})".format(BOOT_SEED), ""])
    for label, b in boot.items():
        lines.append(
            f"- **{label}**: mean={b['mean_improvement_cm']:.4f}, "
            f"95% CI [{b['ci95_lo_cm']:.4f}, {b['ci95_hi_cm']:.4f}]"
        )
    lines.extend([
        "",
        "## 说明",
        "- 改善量定义：ADE_O − ADE_condition；Bootstrap 对帧级配对差值做轨迹池化重采样。",
        "- 历史参考 ADE（~17.75 cm）未参与本轮相减；O 在本轮同协议重算。",
        f"- 历史参考（只读）：{historical_ref_cm}",
        "- D 的 μ 含远目标 κ 与 WP κ 的 blend；WP κ 来自 **A_cls** 头前向（同路径预测一次 forward），"
        "  非 pathact8 κ；共享 Transformer 更新后 κ 数值可与 pathact8 不同，D−F 不能全归因于末点方向。",
        "",
    ])
    path = os.path.join(out_dir, "REPORT_zh.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wp-o", default=DEFAULT_WP_O, help="pathact8 deploy WP checkpoint")
    ap.add_argument("--wp-a", default=DEFAULT_WP_A, help="A_cls path-readout checkpoint")
    ap.add_argument("--ckpt-manifest", default=DEFAULT_CKPT_MANIFEST)
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
    ap.add_argument("--smoke-check", action="store_true", help="Run consistency checks and exit")
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

    wp_head_o, _ = load_dino_head(args.wp_o, device)
    wp_head_a, _ = load_dino_head(args.wp_a, device)
    ctx_o = assert_wp_head_context2(wp_head_o, far, rows, feats, device, args.batch_size)
    ctx_a = assert_wp_head_context2(wp_head_a, far, rows, feats, device, args.batch_size)
    ctx_info = {"pathact8": ctx_o, "A_cls": ctx_a}

    _wd_o, wp_kappa_o, path_o = head_predict_wp_path(
        wp_head_o, far, rows, feats, device, batch_size=args.batch_size
    )
    _wd_a, wp_kappa_a, path_a = head_predict_wp_path(
        wp_head_a, far, rows, feats, device, batch_size=args.batch_size
    )

    gt_nav = load_gt_actions(dataset, far, horizon)
    gt_path = gt_nav[:, : path_o.shape[1], :]

    mu_o = deploy_mu_units(
        dino["dino_dir"],
        dino["dino_kappa"],
        dino["b_dist_m"],
        wp_dir_from_path(path_o),
        wp_kappa_o,
        meters,
        wp_scale=args.wp_scale,
    )
    mu_f = mu_o.copy()
    mu_d = deploy_mu_units(
        dino["dino_dir"],
        dino["dino_kappa"],
        dino["b_dist_m"],
        wp_dir_from_path(path_a),
        wp_kappa_a,
        meters,
        wp_scale=args.wp_scale,
    )

    e_pos = {
        "O": build_e_dino_pos(mu_o, path_o, meters, pos_dim, args.path_units),
        "F": build_e_dino_pos(mu_f, path_a, meters, pos_dim, args.path_units),
        "D": build_e_dino_pos(mu_d, path_a, meters, pos_dim, args.path_units),
    }
    mu_used = {"O": mu_o, "F": mu_f, "D": mu_d}
    paths = {"O": path_o, "A": path_a}

    ckpt_e = os.path.join(args.e_run, args.e_checkpoint)
    model_ed, sched_ed = load_model(config_ed, ckpt_e, device)
    noise_chunks = pregenerate_noise(n, args.num_samples, horizon, args.batch_size, device, args.seed)

    variant_keys = ["O", "F", "D"]
    nav = sample_nav_paired_variants(
        model_ed,
        sched_ed,
        dataset,
        far,
        e_pos,
        device,
        args.num_samples,
        args.batch_size,
        noise_chunks,
        args.seed,
        variant_keys,
    )
    nav_ade = {k: nav_ade_cm_per_frame(nav[k], gt_nav, meters) for k in variant_keys}

    path_metrics = {}
    for label, path in (("pathact8", path_o), ("A_cls", path_a)):
        ade = path_ade_cm(path, gt_path, meters)
        f4, b4 = path_ade_front_back_cm(path, gt_path, meters)
        path_metrics[label] = {
            "path_ade_cm_mean": float(ade.mean()),
            "path_ade_front4_cm_mean": float(f4.mean()),
            "path_ade_back4_cm_mean": float(b4.mean()),
            "path_ade_cm_per_frame": ade.astype(np.float32),
            "straight_path_ade_cm_mean": float(ade[straight].mean()) if straight.any() else float("nan"),
            "turning_path_ade_cm_mean": float(ade[turning].mean()) if turning.any() else float("nan"),
        }

    per_step_err = {}
    for cond in variant_keys:
        pred = nav[cond]
        err = np.linalg.norm(pred - gt_nav[:, None, :, :], axis=-1).mean(axis=(1, 2))
        per_step_err[cond] = (err * meters * 100.0).astype(np.float32)

    smoke = None
    if args.smoke_check or n <= 16:
        e_o_rebuild = build_e_dino_pos(mu_o, path_o, meters, pos_dim, args.path_units)
        replay_keys = ["O", "__replay_O__"]
        replay_e = {"O": e_pos["O"], "__replay_O__": e_pos["O"]}
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
        nav_replay = nav_replay_pair["__replay_O__"]
        n_chunks = (n + args.batch_size - 1) // args.batch_size
        replay_ok = True
        replay_diffs = []
        for ci in range(n_chunks):
            ok_ci, diff_ci = run_diffusion_replay_check(
                model_ed,
                sched_ed,
                dataset,
                far,
                e_pos["O"],
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
        dup_keys = ["O", "__O_dup__"]
        dup_e = {"O": e_pos["O"], "__O_dup__": e_pos["O"].copy()}
        nav_dup = sample_nav_paired_variants(
            model_ed,
            sched_ed,
            dataset,
            far,
            dup_e,
            device,
            args.num_samples,
            args.batch_size,
            noise_chunks,
            args.seed,
            dup_keys,
        )["__O_dup__"]
        smoke = run_smoke_checks(
            mu_o,
            mu_f,
            e_pos["O"],
            e_o_rebuild,
            nav["O"],
            nav_replay,
            replay_ok,
            replay_max,
            nav_dup,
            ctx_info["pathact8"],
        )
        smoke["ctx_check_full"] = ctx_info

    if smoke is not None and not smoke.get("passed", False):
        print("SMOKE_CHECK_FAILED", json.dumps(smoke, indent=2))
        sys.exit(1)
    if args.smoke_check:
        print("smoke_check", json.dumps(smoke, indent=2))
        sys.exit(0)

    ade_o = float(nav_ade["O"].mean())
    summary_table = []
    mu_sources = {
        "O": "deploy blend: dino_dir/kappa + b_dist + wp_dir(pathact8末点) + wp_kappa(pathact8头)",
        "F": "与 O 完全相同（逐样本复制 mu_units）",
        "D": "deploy blend: dino_dir/kappa + b_dist + wp_dir(A末点) + wp_kappa(A_cls头前向)",
    }
    path_sources = {"O": "pathact8 WP head 8点", "F": "A_cls WP head 8点", "D": "A_cls WP head 8点"}
    summary_rows = []
    for cond in variant_keys:
        ade_c = float(nav_ade[cond].mean())
        imp = ade_o - ade_c
        rel = 100.0 * imp / ade_o if ade_o > 0 else float("nan")
        row = {
            "condition": cond,
            "mu_source": mu_sources[cond],
            "path_source": path_sources[cond],
            "nav_ade_cm": ade_c,
            "improvement_vs_O_cm": imp,
            "relative_drop_pct": rel,
        }
        summary_table.append(row)
        summary_rows.append(row)

    per_frame_traj_names = np.array([f[0] for f in far], object)
    paired_stats = {}
    for label, delta in (
        ("F_minus_O_nav_ade", nav_ade["F"] - nav_ade["O"]),
        ("D_minus_O_nav_ade", nav_ade["D"] - nav_ade["O"]),
        ("D_minus_F_nav_ade", nav_ade["D"] - nav_ade["F"]),
        ("improvement_F_vs_O", nav_ade["O"] - nav_ade["F"]),
        ("improvement_D_vs_O", nav_ade["O"] - nav_ade["D"]),
        ("improvement_D_vs_F", nav_ade["F"] - nav_ade["D"]),
    ):
        paired_stats[label] = {
            "mean_cm": float(delta.mean()),
            "improve_frac": float((delta > 0).mean()) if "improvement" in label else float((delta < 0).mean()),
        }

    boot = {}
    for label, imp_series in (
        ("improvement_F_vs_O", nav_ade["O"] - nav_ade["F"]),
        ("improvement_D_vs_O", nav_ade["O"] - nav_ade["D"]),
        ("improvement_D_vs_F", nav_ade["F"] - nav_ade["D"]),
    ):
        m, lo, hi = bootstrap_trajectory_pooled(imp_series, per_frame_traj_names)
        boot[label] = {
            "mean_improvement_cm": m,
            "ci95_lo_cm": lo,
            "ci95_hi_cm": hi,
            "n_boot": BOOT_N,
            "boot_seed": BOOT_SEED,
            "resample_unit": "trajectory (pool all frames from drawn trajs)",
        }

    strict_turn_stats = []
    n_strict = int(strict_turn.sum())
    for cond in variant_keys:
        sub = nav_ade[cond][turning] if turning.any() else np.array([], dtype=np.float64)
        strict_turn_stats.append(
            {
                "condition": cond,
                "nav_ade_cm": float(sub.mean()) if sub.size else float("nan"),
                "n": n_strict,
                "subset": "TURN_STRICT via eval_frame_sets",
            }
        )

    wp_rec_o = wp_checkpoint_record(args.wp_o, args.ckpt_manifest)
    wp_rec_a = wp_checkpoint_record(args.wp_a, args.ckpt_manifest)

    per_frame = {
        "traj_name": np.array([f[0] for f in far], object),
        "t": np.array([f[1] for f in far], np.int32),
        "goal_time": np.array([f[2] for f in far], np.int32),
        "strict_turn": strict_turn.astype(np.int8),
        "loose_turn": loose_turn.astype(np.int8),
        "gt_path": gt_path.astype(np.float32),
        "gt_nav_horizon": gt_nav.astype(np.float32),
        "path_pathact8": path_o.astype(np.float32),
        "path_A_cls": path_a.astype(np.float32),
    }
    for cond in variant_keys:
        per_frame[f"nav_ade_cm_{cond}"] = nav_ade[cond].astype(np.float32)
        per_frame[f"mu_{cond}"] = mu_used[cond].astype(np.float32)
        per_frame[f"per_step_mean_pos_err_cm_{cond}"] = per_step_err[cond]

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
        "conditions": {
            "O": {"mu": mu_sources["O"], "path": path_sources["O"]},
            "F": {"mu": mu_sources["F"], "path": path_sources["F"]},
            "D": {"mu": mu_sources["D"], "path": path_sources["D"]},
        },
        "deploy_blend_note": "Far dino_dir/dino_kappa and b_dist_m frozen from predictions.npz; no kappa recalibration.",
        "D_wp_kappa_source": "A_cls PairTokenHead forward (same pass as path_a); shared trunk may differ from pathact8 kappa outputs.",
        "checkpoints": {
            "wp_pathact8": wp_rec_o,
            "wp_A_cls": wp_rec_a,
            "e_run": args.e_run,
            "e_checkpoint": args.e_checkpoint,
            "e_checkpoint_sha256": sha256_file(ckpt_e) if os.path.isfile(ckpt_e) else None,
            "dino_predictions": args.dino_predictions,
        },
        "ctx_check": ctx_info,
        "path_metrics": {k: {kk: vv for kk, vv in v.items() if not kk.endswith("_per_frame")} for k, v in path_metrics.items()},
        "nav_summary_table": summary_table,
        "strict_turn_subset": strict_turn_stats,
        "paired_frame_stats": paired_stats,
        "bootstrap_improvement": boot,
        "historical_reference_only_cm": "~17.75 (prior locked run; not subtracted this round)",
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
        json.dump(
            {
                "path_metrics": path_summary,
                "nav_summary_table": summary_table,
                "strict_turn_subset": strict_turn_stats,
                "paired_frame_stats": paired_stats,
                "bootstrap_improvement": boot,
            },
            f,
            indent=2,
            default=_json_default,
        )

    write_report_zh(
        args.out_dir,
        summary_table,
        boot,
        strict_turn_stats,
        paired_stats,
        meta["historical_reference_only_cm"],
    )
    with open(os.path.join(args.out_dir, "ctx_check.json"), "w", encoding="utf-8") as f:
        json.dump(ctx_info, f, indent=2)
    if smoke:
        with open(os.path.join(args.out_dir, "smoke_check.json"), "w", encoding="utf-8") as f:
            json.dump(smoke, f, indent=2)

    if smoke:
        print("smoke_check", json.dumps(smoke, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()

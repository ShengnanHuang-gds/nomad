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

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
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
from train_e_dino import DINO_BEST, WP_BEST, load_dino_head, read_tokens
from train_goal_dino import CACHE_DIR, load_cache
from revalidate import CACHE_ROOT
from vint_train.training.train_utils import append_goal_pos
from yaw_traj import path_tensor_from_out, wp_direction_from_head

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
_SECTOR_SNAP = 30.0


def _sector_center_np(sec, snap=_SECTOR_SNAP):
    deg = np.array([snap, 0.0, -snap], dtype=np.float32)[sec]
    rad = np.deg2rad(deg)
    return np.stack([np.cos(rad), np.sin(rad)], axis=1).astype(np.float32)


def _dual_peak_np(logits):
    x = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(x)
    p = e / np.maximum(e.sum(axis=1, keepdims=True), 1e-6)
    order = np.argsort(p, axis=1)[:, ::-1]
    top = np.take_along_axis(p, order, axis=1)
    gap = top[:, 0] - top[:, 1]
    dual = ((top[:, 0] + top[:, 1]) >= 0.75) & (gap <= 0.25)
    return dual, order[:, 0], order[:, 1]


@torch.no_grad()
def head_predict_wp_path(head, items, rows, features, device, batch_size=256, odom_feats=None):
    context = max(0, int(head.kind.shape[0]) - 2)
    odom_dim = int(getattr(head, "odom_dim", 0) or 0)
    dirs, kappas, paths = [], [], []
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        curr = read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        ctx = None
        if context > 0:
            past = [
                read_tokens(features, [rows[(c[0], c[1] - j)] for c in chunk]).to(device).float()
                for j in range(1, context + 1)
            ]
            ctx = torch.stack(past, dim=1)
        odom = None
        if odom_dim > 0:
            if odom_feats is None:
                raise ValueError("WP head odom_dim>0 needs odom_feats")
            odom = torch.from_numpy(np.asarray(odom_feats[start : start + batch_size], np.float32)).to(device)
        out = head(curr, goal, ctx, odom=odom)
        d, k = wp_direction_from_head(head, out, "auto")
        pred = path_tensor_from_out(head, out)
        if pred is None:
            raise RuntimeError("WP head missing path_head for path_source=wp_poly")
        dirs.append(d.cpu().numpy())
        kappas.append(k.cpu().numpy())
        paths.append(pred.float().cpu().numpy())
    return (
        np.concatenate(dirs).astype(np.float32),
        np.concatenate(kappas).astype(np.float32),
        np.concatenate(paths).astype(np.float32),
    )


@torch.no_grad()
def head_predict_wp_sector(head, items, rows, features, device, batch_size=256):
    context = max(0, int(head.kind.shape[0]) - 2)
    dirs, kappas, logits = [], [], []
    n_sec = int(getattr(head, "n_sectors", 0) or 0)
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        curr = read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        ctx = None
        if context > 0:
            past = [
                read_tokens(features, [rows[(c[0], c[1] - j)] for c in chunk]).to(device).float()
                for j in range(1, context + 1)
            ]
            ctx = torch.stack(past, dim=1)
        out = head(curr, goal, ctx)
        d, k = wp_direction_from_head(head, out, "auto")
        sec = None
        for item in out[2:]:
            if isinstance(item, torch.Tensor) and item.ndim == 2 and item.shape[1] == n_sec:
                sec = item
                break
        if sec is None:
            raise RuntimeError("WP head missing sector logits for dual_ambig")
        dirs.append(d.cpu().numpy())
        kappas.append(k.cpu().numpy())
        logits.append(sec.cpu().numpy())
    return (
        np.concatenate(dirs).astype(np.float32),
        np.concatenate(kappas).astype(np.float32),
        np.concatenate(logits).astype(np.float32),
    )


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


@torch.no_grad()
def precompute_b_paths(model_b, sched_b, dataset, far, device, num_samples, batch_size):
    """Mean B 8-step xy in dataset units, goal-conditioned."""
    horizon = dataset.len_traj_pred
    n = len(far)
    paths = np.zeros((n, horizon, 2), dtype=np.float32)
    for start in tqdm(range(0, n, batch_size), desc="B path", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = torch.randn((len(chunk) * num_samples, horizon, 2), device=device)
        cond_goal, _m = encode_cond(model_b, batch_obs, batch_goal, 0, device)
        pred = diffuse(model_b, sched_b, cond_goal, noise, num_samples, device)
        mean = pred.mean(dim=1)[..., :2]
        paths[start : start + len(chunk)] = mean.detach().cpu().numpy()
    return paths


def fmt(stats):
    mean, lo, hi = stats
    return f"{100 * mean:+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}]"


def _path_stats(name, xy, gt, meters):
    k = min(xy.shape[1], gt.shape[1])
    ade = float(np.linalg.norm(xy[:, :k] - gt[:, :k], axis=-1).mean() * meters * 100)
    if k < 3:
        print(f"probe {name}: ADE vs GT {ade:.1f} cm")
        return ade
    d = np.diff(xy[:, :k], axis=1)
    u = d / np.maximum(np.linalg.norm(d, axis=-1, keepdims=True), 1e-6)
    c = np.clip((u[:, :-1] * u[:, 1:]).sum(-1), -1, 1)
    turn = float(np.degrees(np.arccos(c)).sum(axis=1).mean())
    print(f"probe {name}: ADE vs GT {ade:.1f} cm | mean turn {turn:.1f} deg")
    return ade


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
    parser.add_argument("--goal-pos-mode", choices=("goal", "blend", "blend_path"), default="")
    parser.add_argument("--path-gate", choices=("none", "wp_vs_goal", "dual_ambig"), default="")
    parser.add_argument("--path-source", choices=("ray", "wp_poly"), default="")
    parser.add_argument(
        "--path-units",
        choices=("meters", "dataset"),
        default="meters",
        help="wp_poly only: meters=path_head in meters; dataset=ViNT action units",
    )
    parser.add_argument(
        "--probe-gt-path",
        action="store_true",
        help="Also eval the same E-dino weights with GT 8-step actions as path (keep guessed far xy)",
    )
    parser.add_argument(
        "--probe-b-path",
        action="store_true",
        help="Also eval the same E-dino weights with B's mean 8-step as path (keep guessed far xy)",
    )
    parser.add_argument(
        "--probe-arc-parts",
        action="store_true",
        help="Ablate which GT-path slice E uses: first2 / last / heading-ray / full GT / B path",
    )
    parser.add_argument(
        "--probe-sign-bhead",
        action="store_true",
        help="Oracle: force GT sign on pred heading (keep |pred|) as ray; B last-pt heading as ray",
    )
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
    eval_tag = os.path.splitext(args.checkpoint)[0]
    if args.probe_arc_parts:
        eval_tag = f"{eval_tag}_arcparts"
    elif args.probe_sign_bhead:
        eval_tag = f"{eval_tag}_signb"
    elif args.probe_gt_path:
        eval_tag = f"{eval_tag}_gtpath"
    elif args.probe_b_path:
        eval_tag = f"{eval_tag}_bpath"
    output_dir = os.path.join(args.run_dir, f"eval_{eval_tag}")
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
    path_gate = args.path_gate
    path_source = args.path_source
    if not goal_pos_mode or not path_gate or not path_source:
        args_path = os.path.join(args.run_dir, "args.txt")
        if os.path.isfile(args_path):
            with open(args_path) as f:
                for line in f:
                    if not goal_pos_mode and line.startswith("goal_pos_mode="):
                        goal_pos_mode = line.strip().split("=", 1)[1]
                    if not path_gate and line.startswith("path_gate="):
                        path_gate = line.strip().split("=", 1)[1]
                    if not path_source and line.startswith("path_source="):
                        path_source = line.strip().split("=", 1)[1]
        goal_pos_mode = goal_pos_mode or "goal"
        path_gate = path_gate or "none"
        path_source = path_source or "ray"
    wp_dir = wp_kappa = None
    sector_logits = None
    wp_path_xy = None
    if goal_pos_mode in ("blend", "blend_path"):
        _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
        feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
        wp_head, _ = load_dino_head(args.wp_head, device)
        if path_source == "wp_poly":
            wp_dir, wp_kappa, wp_path_xy = head_predict_wp_path(wp_head, far, rows, feats, device)
        elif path_gate == "dual_ambig":
            wp_dir, wp_kappa, sector_logits = head_predict_wp_sector(wp_head, far, rows, feats, device)
        else:
            cache_npz = os.path.join(args.wp_run_dir, "eval_waypoint", "locked_per_frame.npz")
            if os.path.isfile(cache_npz):
                cached = np.load(cache_npz)
                wp_dir, wp_kappa = cached["wp_dir"].astype(np.float32), cached["wp_kappa"].astype(np.float32)
            else:
                wp_dir, wp_kappa = head_predict(wp_head, far, rows, feats, device)
        direction = blend(dino_dir, kappa, wp_dir, wp_kappa, wp_scale=args.wp_scale)
        print(
            f"E-dino inference: {goal_pos_mode} path_source={path_source} "
            f"path_gate={path_gate} (wp_scale={args.wp_scale})"
        )
    else:
        direction = dino_dir
    mu_units = (direction * b_steps[:, None]).astype(np.float32)
    sigma_units = (b_steps / np.maximum(np.sqrt(kappa), 1e-3)).clip(max=40.0).astype(np.float32)
    if goal_pos_mode == "blend_path":
        path_steps = max(1, (pos_dim - 2) // 2)
        if path_source == "wp_poly":
            path = wp_path_xy.astype(np.float32)
            if args.path_units == "meters":
                path = path / max(float(meters), 1e-6)
            if path.shape[1] < path_steps:
                pad = path_steps - path.shape[1]
                path = np.concatenate([path, np.repeat(path[:, -1:, :], pad, axis=1)], axis=1)
            elif path.shape[1] > path_steps:
                path = path[:, :path_steps]
            print(f"wp_poly path: {path.shape} units={args.path_units} meters_per_unit={meters:.3f}")
        else:
            t = (np.arange(1, path_steps + 1, dtype=np.float32))[None, :, None]
            path = wp_dir[:, None, :] * t
        if path_gate == "wp_vs_goal":
            gate = (args.wp_scale * wp_kappa) / (kappa + args.wp_scale * wp_kappa + 1e-6)
            path = path * gate[:, None, None]
        elif path_gate == "dual_ambig":
            dual, i0, i1 = _dual_peak_np(sector_logits)
            half = max(1, path_steps // 2)
            t_h = (np.arange(1, half + 1, dtype=np.float32))[None, :, None]
            d0 = _sector_center_np(i0)
            d1 = _sector_center_np(i1)
            dual_path = np.concatenate([d0[:, None, :] * t_h, d1[:, None, :] * t_h], axis=1)
            if dual_path.shape[1] < path_steps:
                pad = path_steps - dual_path.shape[1]
                dual_path = np.concatenate(
                    [dual_path, np.repeat(dual_path[:, -1:, :], pad, axis=1)], axis=1
                )
            elif dual_path.shape[1] > path_steps:
                dual_path = dual_path[:, :path_steps]
            path = np.where(dual[:, None, None], dual_path, path)
            print(f"dual_ambig frames: {int(dual.sum())}/{len(dual)} ({100.0 * dual.mean():.1f}%)")
        elif path_gate not in ("", "none"):
            raise ValueError(f"unknown path_gate: {path_gate}")
        e_dino_pos = np.concatenate([mu_units, path.reshape(len(mu_units), -1)], axis=1).astype(np.float32)
        if e_dino_pos.shape[1] != pos_dim:
            raise ValueError(f"blend_path pos width {e_dino_pos.shape[1]} != {pos_dim}")
    elif pos_dim == 3:
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
    def _load_gt_xy(path_steps):
        rows = []
        for traj_name, t, goal_time in far:
            _o, _g, actions, _p = load_observation(dataset, traj_name, t, goal_time)
            xy = np.asarray(actions, dtype=np.float32)[:, :2]
            if xy.shape[0] < path_steps:
                xy = np.concatenate([xy, np.repeat(xy[-1:, :], path_steps - xy.shape[0], axis=0)], axis=0)
            rows.append(xy[:path_steps])
        return np.stack(rows, axis=0)

    def _add_path_probe(name, path_xy, path_w, gt_xy=None):
        flat = path_xy.reshape(len(path_xy), -1)
        if flat.shape[1] < path_w:
            flat = np.pad(flat, ((0, 0), (0, path_w - flat.shape[1])))
        cond_pos[name] = np.concatenate([mu_units, flat[:, :path_w]], axis=1).astype(np.float32)
        models[name] = (model_ed, sched_ed, pos_dim)
        if gt_xy is not None:
            _path_stats(name, path_xy, gt_xy, meters)

    if args.probe_gt_path or args.probe_arc_parts:
        if goal_pos_mode != "blend_path" or pos_dim < 4:
            raise ValueError("GT path probes need blend_path pos_dim>=4")
        path_w = pos_dim - 2
        path_steps = max(1, path_w // 2)
        gt_xy = _load_gt_xy(path_steps)
        if "E-dino+GT path" not in models:
            _add_path_probe("E-dino+GT path", gt_xy, path_w, gt_xy)
            print(f"probe GT path: swapped {path_w} path dims, far xy still blend")
        if args.probe_arc_parts:
            pred_xy = e_dino_pos[:, 2 : 2 + path_w].reshape(-1, path_steps, 2).copy()
            _path_stats("E-dino pred", pred_xy, gt_xy, meters)
            first2 = pred_xy.copy()
            k2 = min(2, path_steps)
            first2[:, :k2] = gt_xy[:, :k2]
            last = pred_xy.copy()
            last[:, -1] = gt_xy[:, -1]
            t = np.arange(1, path_steps + 1, dtype=np.float32)[None, :, None]
            heading = unit(gt_xy[:, -1])[:, None, :] * t
            _add_path_probe("E-dino+GT first2", first2, path_w, gt_xy)
            _add_path_probe("E-dino+GT last", last, path_w, gt_xy)
            _add_path_probe("E-dino+GT heading", heading, path_w, gt_xy)
    if args.probe_sign_bhead:
        if goal_pos_mode != "blend_path" or pos_dim < 4:
            raise ValueError("--probe-sign-bhead needs blend_path pos_dim>=4")
        path_w = pos_dim - 2
        path_steps = max(1, path_w // 2)
        gt_xy = gt_xy if "gt_xy" in locals() else _load_gt_xy(path_steps)
        pred_xy = e_dino_pos[:, 2 : 2 + path_w].reshape(-1, path_steps, 2).copy()
        gb = np.arctan2(gt_xy[:, -1, 1], gt_xy[:, -1, 0])
        pb = np.arctan2(pred_xy[:, -1, 1], pred_xy[:, -1, 0])
        dead = np.deg2rad(15.0)
        nb = np.where(np.abs(gb) >= dead, np.sign(gb) * np.abs(pb), pb)
        t = np.arange(1, path_steps + 1, dtype=np.float32)[None, :, None]
        sign_ray = np.stack([np.cos(nb), np.sin(nb)], axis=-1)[:, None, :] * t
        _add_path_probe("E-dino+GT sign ray", sign_ray, path_w, gt_xy)
        torch.manual_seed(args.seed + 7)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(args.seed + 7)
        b_xy = precompute_b_paths(
            model_b, sched_b, dataset, far, device, args.num_samples, args.batch_size
        )
        b_ray = unit(b_xy[:, -1])[:, None, :] * t
        _add_path_probe("E-dino+B heading", b_ray, path_w, gt_xy)
        b_ang = np.degrees(
            np.arccos(np.clip((unit(b_xy[:, -1]) * unit(gt_xy[:, -1])).sum(-1), -1, 1))
        )
        print(
            f"B last-pt heading err median {np.median(b_ang):.1f} mean {b_ang.mean():.1f}"
        )
    if args.probe_b_path or args.probe_arc_parts:
        if goal_pos_mode != "blend_path" or pos_dim < 4:
            raise ValueError("--probe-b-path needs blend_path pos_dim>=4")
        path_w = pos_dim - 2
        path_steps = max(1, path_w // 2)
        torch.manual_seed(args.seed + 7)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(args.seed + 7)
        b_xy = precompute_b_paths(
            model_b, sched_b, dataset, far, device, args.num_samples, args.batch_size
        )
        gt_xy = gt_xy if "gt_xy" in locals() else _load_gt_xy(path_steps)
        _add_path_probe("E-dino+B path", b_xy, path_w, gt_xy)

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

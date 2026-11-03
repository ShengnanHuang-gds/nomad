"""2x2 on E-path: DINO direction head (mu) x WP 8-step path head (poly), locked far."""
from __future__ import annotations

import argparse
import os

import cv2  # noqa: F401
import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_e_dino import head_predict_wp_path
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, rollout
from eval_waypoint_head import blend
from revalidate import CACHE_ROOT
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from yaw_traj import odom_feats_for_items

WP_PATHACT8 = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
E_RUN = "logs/nomad/nomad_e_ft_pathact8"
E_CKPT = "ema_latest.pth"

CELLS = (
    ("PP", "P", "P"),
    ("PG", "P", "G"),
    ("GP", "G", "P"),
    ("GG", "G", "G"),
)


def unit(x):
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return (x / np.maximum(n, 1e-6)).astype(np.float32)


def path_flat(path_xy):
    return path_xy.reshape(path_xy.shape[0], -1).astype(np.float32)


def pack(mu, path_xy, pos_dim):
    flat = path_flat(path_xy)
    need = pos_dim - 2
    if flat.shape[1] < need:
        pad = need - flat.shape[1]
        flat = np.concatenate([flat, np.repeat(flat[:, -2:], pad // 2, axis=1)], axis=1)
    elif flat.shape[1] > need:
        flat = flat[:, :need]
    return np.concatenate([mu.astype(np.float32), flat], axis=1)


def main():
    p = argparse.ArgumentParser(description="Direction x 8-step path 2x2 on E-path")
    p.add_argument("--config-e-dino", default="config/nomad_e_dino_path.yaml")
    p.add_argument("--run-dir", default=E_RUN)
    p.add_argument("--checkpoint", default=E_CKPT)
    p.add_argument("--wp-head", default=WP_PATHACT8)
    p.add_argument("--dino-predictions", default=DINO_TEST_PREDICTIONS)
    p.add_argument("--out-dir", default="logs/revalidation/dir_path_2x2_pathact8")
    p.add_argument("--num-samples", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--path-units", choices=("dataset", "meters"), default="dataset")
    args = p.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() or "cpu" not in args.device else "cpu")
    os.makedirs(args.out_dir, exist_ok=True)
    config = load_config(args.config_e_dino)
    pos_dim = int(config.get("goal_pos_dim", 18))
    path_steps = (pos_dim - 2) // 2

    dataset = make_split_dataset(load_config("config/nomad_b40.yaml"), "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(PAIRED_FRAMES)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    n = len(far)

    pred = dict(np.load(args.dino_predictions))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    dino_dir = take("dino_dir").astype(np.float32)
    dino_k = take("dino_kappa").astype(np.float32)
    steps_b = (take("b_dist") / meters).astype(np.float32)
    goal_pos = (take("target") / meters).astype(np.float32)
    sb = steps_b[:, None]

    mu_p = (dino_dir * sb).astype(np.float32)
    mu_g = (unit(goal_pos) * sb).astype(np.float32)

    gt_path = np.stack(
        [np.asarray(load_observation(dataset, a, t, g)[2], np.float32)[:, :2] for a, t, g in far]
    )
    if gt_path.shape[1] > path_steps:
        gt_path = gt_path[:, :path_steps]
    elif gt_path.shape[1] < path_steps:
        pad = path_steps - gt_path.shape[1]
        gt_path = np.concatenate([gt_path, np.repeat(gt_path[:, -1:, :], pad, axis=1)], axis=1)

    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    wp_head, _ = load_dino_head(args.wp_head, device)
    odom = odom_feats_for_items(dataset, far) if int(getattr(wp_head, "odom_dim", 0) or 0) > 0 else None
    _wd, _wk, poly = head_predict_wp_path(wp_head, far, rows, feats, device, odom_feats=odom)
    if args.path_units == "meters":
        poly = poly / max(float(meters), 1e-6)
    if poly.shape[1] > path_steps:
        poly = poly[:, :path_steps]
    elif poly.shape[1] < path_steps:
        pad = path_steps - poly.shape[1]
        poly = np.concatenate([poly, np.repeat(poly[:, -1:, :], pad, axis=1)], axis=1)

    wp_dir = _wd
    mu_deploy = (blend(dino_dir, dino_k, wp_dir, _wk) * sb).astype(np.float32)

    positions = {}
    for name, gk, wk in CELLS:
        mu = mu_p if gk == "P" else mu_g
        path = poly if wk == "P" else gt_path
        positions[name] = pack(mu, path, pos_dim)
    positions["deploy_blend"] = pack(mu_deploy, poly, pos_dim)

    ckpt = os.path.join(args.run_dir, args.checkpoint)
    model, sched = load_model(config, ckpt, device)
    am, ade = rollout(
        model,
        sched,
        dataset,
        far,
        positions,
        device,
        args.num_samples,
        args.batch_size,
        args.seed + 3,
        "dir x path 2x2",
    )

    rng = np.random.default_rng(args.seed + 4)
    boot = subset_index(n, args.bootstrap, rng)
    use = {c: am - ade[c] for c, _, _ in CELLS}
    use["deploy_blend"] = am - ade["deploy_blend"]
    fmt = lambda u: f"{100*u[0]:+.2f} [{100*u[1]:+.2f}, {100*u[2]:+.2f}]"

    print("\n=== E-path 2x2: direction head (mu) x 8-step path head ===")
    print(f"n={n} locked far 20-40 | model={ckpt} | wp={args.wp_head}")
    print("mu: P=dino_dir*B_steps  G=unit(GT goal_pos)*B_steps")
    print("path: P=wp_poly  G=GT 8-step actions (dataset units)")
    print(f"pos_dim={pos_dim}  path_steps={path_steps}  meters/unit={meters:.3f}\n")
    print("use = -(ADE-ADE_mask) cm  (higher better)\n")
    print("              path_P (pred 8-step)    path_G (GT 8-step)")
    for g_lab, g_key in (("dir_P", "P"), ("dir_G", "G")):
        row = []
        for w_key in ("P", "G"):
            cname = next(c for c, gg, ww in CELLS if gg == g_key and ww == w_key)
            u = boot_mean(use[cname], boot)
            row.append(fmt(u))
        print(f"  {g_lab:<8}  {row[0]:>24}  {row[1]:>24}")

    u_pp, u_pg, u_gp, u_gg = (use[c] for c, _, _ in CELLS)
    interact = u_gg - u_gp - u_pg + u_pp
    ui = boot_mean(interact, boot)
    print(f"\n  interaction I = U_GG - U_GP - U_PG + U_PP: {fmt(ui)} cm")
    u_dep = boot_mean(use["deploy_blend"], boot)
    print(f"  deploy (kappa-blend mu + pred path): {fmt(u_dep)} cm")

    rows_out = []
    for c in list(positions.keys()):
        u = boot_mean(use[c], boot)
        rows_out.append({"cell": c, "use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2]})
    rows_out.append({"cell": "interaction_I", "use_cm": 100 * ui[0], "lo": 100 * ui[1], "hi": 100 * ui[2]})
    write_csv(os.path.join(args.out_dir, "factorial_use.csv"), rows_out)
    np.savez_compressed(
        os.path.join(args.out_dir, "per_frame.npz"),
        ade_mask=am,
        **{f"ade_{c}": ade[c] for c in positions},
    )
    sets, _, _ = frame_sets(dataset, moments, meters, SPREAD_NPZ)
    print("\nBy subset (use cm, no bootstrap):")
    for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
        idx = np.arange(n) if set_name == "all" else np.flatnonzero(sets.get(set_name, []))
        if len(idx) == 0:
            continue
        line = f"  [{set_name}] n={len(idx)}"
        for c, _, _ in CELLS:
            line += f"  {c}={100*(am[idx]-ade[c][idx]).mean():+.2f}"
        print(line)
    print(f"\nSaved {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()
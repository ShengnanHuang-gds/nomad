"""Ablation: waypoint head vs kappa weighting on locked far frames.

Conditions (all × B distance, except true goal):
  goal head (direct)   only far-goal DINO head
  waypoint head        only near-endpoint DINO head
  equal blend          normalize(d_goal + d_wp)          — no kappa
  kappa blend          normalize(k_g*d_g + k_w*d_wp)   — current method
  true goal / true endpoint dir  references

Reuses cached waypoint dirs from eval_waypoint/locked_per_frame.npz when present.

Run from train/:
    python -u eval_blend_ablation.py --run-dir logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32
"""

import argparse
import csv
import os

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
import numpy as np
import torch

from adaptive_blend import angle_between_deg, blend_suppress, suppress_from_wp_turn
from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, angle_err, rollout
from eval_waypoint_head import blend, endpoints, head_predict
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from revalidate import CACHE_ROOT

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
ATTR_NPZ = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
SUPPRESS_ORACLE = (35.0, 55.0, 1.0, 0.0)
SUPPRESS_DEPLOY = (35.0, 55.0, 1.0, 0.0)


def equal_blend(d1, d2):
    r = d1 + d2
    return (r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Ablate waypoint head vs kappa blend")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="dino_dir_best.pth")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--with-kappa-suppress",
        action="store_true",
        help="Add kappa suppress (oracle GT wp_err + deploy goal-wp disagree), same rollout as kappa blend",
    )
    parser.add_argument("--attr-npz", default=ATTR_NPZ)
    args = parser.parse_args()

    device = torch.device(args.device)
    out_dir = os.path.join(args.run_dir, "eval_blend_ablation")
    os.makedirs(out_dir, exist_ok=True)

    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]

    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    goal_dir = take("dino_dir").astype(np.float32)
    goal_kappa = take("dino_kappa").astype(np.float32)
    steps = (take("b_dist") / meters).astype(np.float32)
    goal = (take("target") / meters).astype(np.float32)

    cache_npz = os.path.join(args.run_dir, "eval_waypoint", "locked_per_frame.npz")
    if os.path.isfile(cache_npz):
        cached = np.load(cache_npz)
        wp_dir = cached["wp_dir"].astype(np.float32)
        wp_kappa = cached["wp_kappa"].astype(np.float32)
        end = cached["endpoint"].astype(np.float32)
        print(f"Reused waypoint dirs from {cache_npz}")
        assert len(wp_dir) == len(far), (len(wp_dir), len(far))
    else:
        wp_head, _ = load_dino_head(os.path.join(args.run_dir, args.checkpoint), device)
        _p, rows_t, _meta = load_cache(CACHE_ROOT, "test_paired")
        feats_t = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
        wp_dir, wp_kappa = head_predict(wp_head, far, rows_t, feats_t, device)
        end = endpoints(dataset, far)

    print(
        f"[locked far] bearing medians deg: goal vs true goal {np.median(angle_err(goal_dir, goal)):.1f} | "
        f"wp vs endpoint {np.median(angle_err(wp_dir, end)):.1f} | "
        f"goal vs endpoint {np.median(angle_err(goal_dir, end)):.1f}"
    )
    # How often kappa prefers waypoint
    prefer_wp = wp_kappa > goal_kappa
    print(
        f"kappa: median goal {np.median(goal_kappa):.1f} / wp {np.median(wp_kappa):.1f} | "
        f"wp kappa > goal kappa on {100 * prefer_wp.mean():.0f}% frames"
    )

    s = steps[:, None]
    eq = equal_blend(goal_dir, wp_dir)
    kap = blend(goal_dir, goal_kappa, wp_dir, wp_kappa)
    pos = {
        "true goal": goal,
        "true endpoint dir": (unit(end) * s).astype(np.float32),
        "goal head (direct)": (goal_dir * s).astype(np.float32),
        "waypoint head": (wp_dir * s).astype(np.float32),
        "equal blend": (eq * s).astype(np.float32),
        "kappa blend": (kap * s).astype(np.float32),
    }
    if args.with_kappa_suppress:
        attr = np.load(args.attr_npz)
        turn_strict = attr["turn_strict"].astype(bool)
        wp_err_gt = attr["wp_bearing_err_deg"].astype(np.float32)
        wp_err_dis = angle_between_deg(goal_dir, wp_dir).astype(np.float32)
        for label, wp_err, lo, hi, cap, tw in (
            ("kappa suppress (oracle w35-55)", wp_err_gt, *SUPPRESS_ORACLE),
            ("kappa suppress (deploy w35-55)", wp_err_dis, *SUPPRESS_DEPLOY),
        ):
            sup = suppress_from_wp_turn(wp_err, turn_strict, wp_lo=lo, wp_hi=hi, turn_weight=tw, cap=cap)
            d = blend_suppress(goal_dir, goal_kappa, wp_dir, wp_kappa, sup)
            pos[label] = (d * s).astype(np.float32)

    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    am, ade = rollout(
        model_eo, sched_eo, dataset, far, pos, device, args.num_samples, 8, args.seed + 1, "ablation-far"
    )

    rng = np.random.default_rng(args.seed + 7)
    rows = []
    print("\n[ablation locked far] use (cm) [95% CI]:")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        ref = float((am[idx] - ade["true goal"][idx]).mean())
        print(f"  [{set_name}] n={len(idx)}  true-goal use={100 * ref:.2f} cm")
        for k in pos:
            u = boot_mean(am[idx] - ade[k][idx], boot)
            vs = (u[0] / ref) if abs(ref) > 1e-9 else float("nan")
            print(f"    {k:<22} {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  ({100 * vs:.0f}%)")
            rows.append(
                {
                    "frames": set_name,
                    "condition": k,
                    "use_cm": 100 * u[0],
                    "lo": 100 * u[1],
                    "hi": 100 * u[2],
                    "vs_true_goal": vs,
                    "ade_cm": 100 * float(ade[k][idx].mean()),
                }
            )
        # paired deltas vs goal head
        for name in ("waypoint head", "equal blend", "kappa blend"):
            if name not in ade:
                continue
            dlt = boot_mean((am[idx] - ade[name][idx]) - (am[idx] - ade["goal head (direct)"][idx]), boot)
            print(f"    {name} - goal head   {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
        if args.with_kappa_suppress:
            for name in ("kappa suppress (oracle w35-55)", "kappa suppress (deploy w35-55)"):
                dlt = boot_mean((am[idx] - ade[name][idx]) - (am[idx] - ade["goal head (direct)"][idx]), boot)
                print(f"    {name} - goal head   {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
                rows.append(
                    {
                        "frames": set_name,
                        "condition": f"{name} - goal head",
                        "use_cm": 100 * dlt[0],
                        "lo": 100 * dlt[1],
                        "hi": 100 * dlt[2],
                        "vs_true_goal": float("nan"),
                        "ade_cm": float("nan"),
                    }
                )
            dlt = boot_mean(
                (am[idx] - ade["kappa suppress (oracle w35-55)"][idx]) - (am[idx] - ade["kappa blend"][idx]),
                boot,
            )
            print(f"    kappa suppress (oracle) - kappa blend  {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
            rows.append(
                {
                    "frames": set_name,
                    "condition": "kappa suppress (oracle) - kappa blend",
                    "use_cm": 100 * dlt[0],
                    "lo": 100 * dlt[1],
                    "hi": 100 * dlt[2],
                    "vs_true_goal": float("nan"),
                    "ade_cm": float("nan"),
                }
            )
            rows.append(
                {
                    "frames": set_name,
                    "condition": f"{name} - goal head",
                    "use_cm": 100 * dlt[0],
                    "lo": 100 * dlt[1],
                    "hi": 100 * dlt[2],
                    "vs_true_goal": float("nan"),
                    "ade_cm": float("nan"),
                }
            )
        # kappa vs equal
        dlt = boot_mean((am[idx] - ade["kappa blend"][idx]) - (am[idx] - ade["equal blend"][idx]), boot)
        print(f"    kappa - equal blend  {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
        rows.append(
            {
                "frames": set_name,
                "condition": "kappa - equal blend",
                "use_cm": 100 * dlt[0],
                "lo": 100 * dlt[1],
                "hi": 100 * dlt[2],
                "vs_true_goal": float("nan"),
                "ade_cm": float("nan"),
            }
        )

    csv_path = os.path.join(out_dir, "ablation.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(
        os.path.join(out_dir, "ablation_per_frame.npz"),
        ade_mask=am,
        names=np.array(list(pos)),
        traj=np.array([n for n, _t, _g in far]),
        goal_dir=goal_dir,
        goal_kappa=goal_kappa,
        wp_dir=wp_dir,
        wp_kappa=wp_kappa,
        **{f"ade_{i}": ade[k] for i, k in enumerate(pos)},
    )
    print(f"Saved {os.path.abspath(out_dir)}")


if __name__ == "__main__":
    main()

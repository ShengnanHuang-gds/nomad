"""Next steps after kappa blend: near/mid check, then kappa-scale tune.

Modes (run one at a time from train/):
  python -u eval_blend_next.py --mode groups --run-dir logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32
  python -u eval_blend_next.py --mode scale  --run-dir logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32

groups: kappa blend vs goal-head direct on locked near / mid / far (same 1000 frames).
scale:  pick waypoint-kappa scale on the clean tuning set; compare best vs last WP
        checkpoint; one locked-far eval with the winning (ckpt, scale).
"""

import argparse
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, angle_err, rollout
from eval_waypoint_head import blend, endpoints, head_predict, print_bearings
from revalidate import CACHE_ROOT, dino_and_b, tune_items
from train_e_dino import DINO_BEST, load_dino_head, read_tokens
from train_goal_dino import load_cache

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
GROUPS = ("4-8", "9-19", "20-40")
GROUP_LABEL = {"4-8": "near", "9-19": "mid", "20-40": "far"}
# Candidate multipliers for waypoint kappa in the blend. 1.0 = current fixed rule.
SCALE_GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)


def build_positions(goal_dir, goal_kappa, wp_dir, wp_kappa, steps, end, goal, wp_scale=1.0):
    s = steps[:, None].astype(np.float32)
    return {
        "true goal": goal.astype(np.float32),
        "true endpoint dir": (unit(end) * s).astype(np.float32),
        "goal head (direct)": (goal_dir * s).astype(np.float32),
        "waypoint head": (wp_dir * s).astype(np.float32),
        "kappa blend": blend(goal_dir, goal_kappa, wp_dir, wp_scale * wp_kappa) * s,
    }


def locked_items_for_group(moments, group):
    return [(n, t, [g[4] for g in goals if g[0] == group][0]) for n, t, goals in moments]


def dino_slice(pred, group, meters):
    fm = pred["group"] == group
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    return {
        "dir": take("dino_dir"),
        "kappa": take("dino_kappa"),
        "steps": take("b_dist") / meters,
        "goal": (take("target") / meters).astype(np.float32),
        "frame_index": take("frame_index"),
    }


def run_groups(args, device, out_dir):
    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    wp_head, _ = load_dino_head(os.path.join(args.run_dir, args.checkpoint), device)
    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    _p, rows_t, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats_t = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    rng = np.random.default_rng(args.seed + 3)
    rows_out = []

    for group in GROUPS:
        items = locked_items_for_group(moments, group)
        d = dino_slice(pred, group, meters)
        assert len(items) == len(d["dir"]), (group, len(items), len(d["dir"]))
        wp_dir, wp_kappa = head_predict(wp_head, items, rows_t, feats_t, device)
        end = endpoints(dataset, items)
        print_bearings(f"locked {GROUP_LABEL[group]}", d["dir"], wp_dir, end, d["goal"])
        pos = build_positions(d["dir"], d["kappa"], wp_dir, wp_kappa, d["steps"], end, d["goal"])
        # Keep conditions light: direct, blend, true goal (ref). Full set only on far.
        keep = ("true goal", "goal head (direct)", "kappa blend")
        if group == "20-40":
            keep = tuple(pos)
        pos = {k: pos[k] for k in keep}
        am, ade = rollout(
            model_eo, sched_eo, dataset, items, pos, device, args.num_samples, 8, args.seed + 10, f"locked-{GROUP_LABEL[group]}"
        )
        print(f"\n[locked {GROUP_LABEL[group]} {group}] use (cm) [95% CI] and share of true-goal use:")
        for set_name in SET_NAMES:
            idx = np.flatnonzero(sets[set_name])
            boot = subset_index(len(idx), args.bootstrap, rng)
            ref = float((am[idx] - ade["true goal"][idx]).mean())
            print(f"  [{set_name}] n={len(idx)}")
            for k in pos:
                u = boot_mean(am[idx] - ade[k][idx], boot)
                vs = (u[0] / ref) if abs(ref) > 1e-9 else float("nan")
                print(f"    {k:<20} {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  ({100 * vs:.0f}%)")
                rows_out.append(
                    {
                        "group": group,
                        "label": GROUP_LABEL[group],
                        "frames": set_name,
                        "condition": k,
                        "use_cm": 100 * u[0],
                        "lo": 100 * u[1],
                        "hi": 100 * u[2],
                        "vs_true_goal": vs,
                    }
                )
            if "kappa blend" in pos and "goal head (direct)" in pos:
                dlt = boot_mean((am[idx] - ade["kappa blend"][idx]) - (am[idx] - ade["goal head (direct)"][idx]), boot)
                print(f"    blend - direct       {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")
                rows_out.append(
                    {
                        "group": group,
                        "label": GROUP_LABEL[group],
                        "frames": set_name,
                        "condition": "blend - direct",
                        "use_cm": 100 * dlt[0],
                        "lo": 100 * dlt[1],
                        "hi": 100 * dlt[2],
                        "vs_true_goal": float("nan"),
                    }
                )
        np.savez_compressed(
            os.path.join(out_dir, f"groups_{GROUP_LABEL[group]}_per_frame.npz"),
            ade_mask=am,
            names=np.array(list(pos)),
            traj=np.array([n for n, _t, _g in items]),
            wp_dir=wp_dir,
            wp_kappa=wp_kappa,
            endpoint=end,
            **{f"ade_{i}": ade[k] for i, k in enumerate(pos)},
        )

    write_csv(os.path.join(out_dir, "groups_eval.csv"), rows_out)
    print(f"Saved to {os.path.abspath(out_dir)}")


def _use_vs_true(am, ade, key):
    ref = float((am - ade["true goal"]).mean())
    u = float((am - ade[key]).mean())
    return u, (u / ref) if abs(ref) > 1e-9 else float("nan")


def run_scale(args, device, out_dir):
    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    rng = np.random.default_rng(args.seed + 4)
    rows_out = []

    # ---- clean tuning set: best vs last, then scale grid on the winner's outputs ----
    items = tune_items(dataset, {t for t, _, _ in moments}, args.n_tune, seed=2468)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test")
    feats = np.load(os.path.join(CACHE_ROOT, "test", "features.npy"), mmap_mode="r")
    goal_head, _ = load_dino_head(DINO_BEST, device)
    b_frozen = load_frozen_nomad(config_b, B_CHECKPOINT, device)
    est = dino_and_b(items, dataset, b_frozen, goal_head, rows, feats, device)
    del b_frozen, goal_head
    end = endpoints(dataset, items)

    ckpt_scores = {}
    wp_cache = {}
    for tag, ckpt in (("best", "dino_dir_best.pth"), ("last", "dino_dir_last.pth")):
        head, _ = load_dino_head(os.path.join(args.run_dir, ckpt), device)
        wp_dir, wp_kappa = head_predict(head, items, rows, feats, device)
        del head
        wp_cache[tag] = (wp_dir, wp_kappa)
        print_bearings(f"tuning/{tag}", est["dir"], wp_dir, end, est["target"])
        pos = build_positions(est["dir"], est["kappa"], wp_dir, wp_kappa, est["steps"], end, est["target"], wp_scale=1.0)
        # Only need true goal + blend for ckpt pick; include direct for reporting.
        pos_ckpt = {k: pos[k] for k in ("true goal", "goal head (direct)", "kappa blend")}
        am, ade = rollout(
            model_eo, sched_eo, dataset, items, pos_ckpt, device, args.num_samples, 16, args.seed, f"tune-ckpt-{tag}"
        )
        u, vs = _use_vs_true(am, ade, "kappa blend")
        u_d, vs_d = _use_vs_true(am, ade, "goal head (direct)")
        ckpt_scores[tag] = vs
        print(
            f"[tuning ckpt={tag}] blend use {100 * u:+.2f} cm ({100 * vs:.0f}% of true) | "
            f"direct {100 * u_d:+.2f} cm ({100 * vs_d:.0f}%)"
        )
        rows_out.append({"phase": "ckpt", "ckpt": tag, "scale": 1.0, "condition": "kappa blend", "use_cm": 100 * u, "vs_true_goal": vs})
        rows_out.append({"phase": "ckpt", "ckpt": tag, "scale": 1.0, "condition": "goal head (direct)", "use_cm": 100 * u_d, "vs_true_goal": vs_d})

    winner = max(ckpt_scores, key=ckpt_scores.get)
    print(f"\n[ckpt pick] winner={winner} (blend vs true: {100 * ckpt_scores[winner]:.0f}%)")
    wp_dir, wp_kappa = wp_cache[winner]

    # One rollout with all scale variants as named positions (same noise → fair compare).
    s = est["steps"][:, None].astype(np.float32)
    pos_scale = {
        "true goal": est["target"].astype(np.float32),
        "goal head (direct)": (est["dir"] * s).astype(np.float32),
    }
    for sc in SCALE_GRID:
        pos_scale[f"blend@{sc:g}"] = blend(est["dir"], est["kappa"], wp_dir, sc * wp_kappa) * s
    am, ade = rollout(
        model_eo, sched_eo, dataset, items, pos_scale, device, args.num_samples, 16, args.seed + 5, "tune-scale"
    )
    ref = float((am - ade["true goal"]).mean())
    print("\n[tuning scale grid] use (cm) and share of true-goal use:")
    best_sc, best_vs = None, -1e9
    for sc in SCALE_GRID:
        key = f"blend@{sc:g}"
        u = float((am - ade[key]).mean())
        vs = u / ref
        print(f"  scale={sc:<4g} {100 * u:+.2f}  ({100 * vs:.0f}%)")
        rows_out.append({"phase": "scale", "ckpt": winner, "scale": sc, "condition": "kappa blend", "use_cm": 100 * u, "vs_true_goal": vs})
        if vs > best_vs:
            best_sc, best_vs = sc, vs
    u_d = float((am - ade["goal head (direct)"]).mean())
    print(f"  direct     {100 * u_d:+.2f}  ({100 * u_d / ref:.0f}%)")
    print(f"[scale pick] best scale={best_sc:g} ({100 * best_vs:.0f}% of true)")

    # ---- locked far with winning (ckpt, scale) ----
    far = locked_items_for_group(moments, "20-40")
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    d = dino_slice(pred, "20-40", meters)
    _p, rows_t, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats_t = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    head, _ = load_dino_head(os.path.join(args.run_dir, f"dino_dir_{winner}.pth"), device)
    wp_dir_t, wp_kappa_t = head_predict(head, far, rows_t, feats_t, device)
    del head
    end_t = endpoints(dataset, far)
    print_bearings(f"locked/{winner}@scale{best_sc:g}", d["dir"], wp_dir_t, end_t, d["goal"])
    pos_t = build_positions(d["dir"], d["kappa"], wp_dir_t, wp_kappa_t, d["steps"], end_t, d["goal"], wp_scale=best_sc)
    # Also report scale=1.0 for paired comparison if different.
    if abs(best_sc - 1.0) > 1e-9:
        pos_t["kappa blend@1"] = blend(d["dir"], d["kappa"], wp_dir_t, wp_kappa_t) * d["steps"][:, None].astype(np.float32)
    am, ade = rollout(model_eo, sched_eo, dataset, far, pos_t, device, args.num_samples, 8, args.seed + 1, "locked-scale")
    print(f"\n[locked far | ckpt={winner} scale={best_sc:g}] use (cm) [95% CI]:")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        ref = float((am[idx] - ade["true goal"][idx]).mean())
        print(f"  [{set_name}] n={len(idx)}")
        for k in pos_t:
            u = boot_mean(am[idx] - ade[k][idx], boot)
            vs = (u[0] / ref) if abs(ref) > 1e-9 else float("nan")
            print(f"    {k:<22} {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  ({100 * vs:.0f}%)")
            rows_out.append(
                {
                    "phase": "locked",
                    "ckpt": winner,
                    "scale": best_sc if k == "kappa blend" else (1.0 if k == "kappa blend@1" else float("nan")),
                    "frames": set_name,
                    "condition": k,
                    "use_cm": 100 * u[0],
                    "lo": 100 * u[1],
                    "hi": 100 * u[2],
                    "vs_true_goal": vs,
                }
            )
        dlt = boot_mean((am[idx] - ade["kappa blend"][idx]) - (am[idx] - ade["goal head (direct)"][idx]), boot)
        print(f"    blend - direct         {100 * dlt[0]:+.2f} [{100 * dlt[1]:+.2f}, {100 * dlt[2]:+.2f}] cm")

    write_csv(os.path.join(out_dir, "scale_eval.csv"), rows_out)
    with open(os.path.join(out_dir, "scale_pick.txt"), "w", encoding="utf-8") as f:
        f.write(f"winner_ckpt={winner}\nbest_scale={best_sc}\ntune_vs_true={best_vs}\n")
    np.savez_compressed(
        os.path.join(out_dir, "locked_scale_per_frame.npz"),
        ade_mask=am,
        names=np.array(list(pos_t)),
        traj=np.array([n for n, _t, _g in far]),
        winner_ckpt=np.array(winner),
        best_scale=np.array(best_sc),
        wp_dir=wp_dir_t,
        wp_kappa=wp_kappa_t,
        endpoint=end_t,
        **{f"ade_{i}": ade[k] for i, k in enumerate(pos_t)},
    )
    print(f"Saved to {os.path.abspath(out_dir)}")


def main():
    parser = argparse.ArgumentParser(description="Near/mid check and kappa-scale tune")
    parser.add_argument("--mode", choices=("groups", "scale"), required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="dino_dir_best.pth")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--n-tune", type=int, default=600)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    device = torch.device(args.device)
    out_dir = os.path.join(args.run_dir, "eval_blend_next")
    os.makedirs(out_dir, exist_ok=True)
    if args.mode == "groups":
        run_groups(args, device, out_dir)
    else:
        run_scale(args, device, out_dir)


if __name__ == "__main__":
    main()

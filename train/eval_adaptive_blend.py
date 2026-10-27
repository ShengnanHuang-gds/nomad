"""Eval adaptive (gated) kappa blend on locked far frames vs plain kappa blend."""
import argparse, csv, json, os

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
import numpy as np
import torch
from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, rollout
from eval_waypoint_head import blend, endpoints, head_predict
from adaptive_blend import (
    angle_between_deg,
    blend_gated,
    blend_suppress,
    combine_gates,
    gate_from_disagree,
    gate_from_dyaw,
    gate_from_orb,
    suppress_from_wp_turn,
)
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from revalidate import CACHE_ROOT

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
YAW_CSV = "logs/revalidation/yaw_overlap_analysis/per_frame_yaw_overlap.csv"
CTX2_RUN = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44"
WP_RUN = CTX2_RUN
ATTR_NPZ = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"


def load_far_yaw():
    abs_dyaw = []
    orb = []
    with open(YAW_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["group"] != "20-40":
                continue
            abs_dyaw.append(abs(float(row["endpoint_dyaw_deg"])))
            orb.append(int(row["orb"]))
    return np.array(abs_dyaw, dtype=np.float32), np.array(orb, dtype=np.int32)


def report(name, am, ade, idx, boot):
    u = boot_mean(am[idx] - ade[name][idx], boot)
    print(f"    {name:<28} {100*u[0]:+.2f} [{100*u[1]:+.2f}, {100*u[2]:+.2f}] cm")


def build_suppress_grid(quick):
    rows = [
        {"kind": "baseline", "name": "kappa blend"},
        {"kind": "baseline", "name": "goal head (direct)"},
    ]
    for ws in ([0.85, 0.9, 0.95] if quick else [0.8, 0.85, 0.9, 0.95]):
        rows.append({"kind": "wp_scale", "name": f"wp_scale={ws:.2f}", "wp_scale": ws})
    wp_pairs = [(35, 55), (40, 60), (45, 65)] if quick else [(30, 50), (35, 55), (40, 60), (45, 65), (40, 70)]
    caps = [0.85, 1.0] if quick else [0.75, 0.85, 0.95, 1.0]
    turn_ws = [0.0, 0.75, 1.0] if quick else [0.0, 0.5, 0.75, 1.0]
    for wp_lo, wp_hi in wp_pairs:
        for cap in caps:
            for tw in turn_ws:
                rows.append(
                    {
                        "kind": "suppress",
                        "name": f"sup_w{wp_lo:.0f}_{wp_hi:.0f}_c{cap:.2f}_t{tw:.2f}",
                        "wp_lo": wp_lo,
                        "wp_hi": wp_hi,
                        "cap": cap,
                        "turn_weight": tw,
                    }
                )
    return rows


def dir_for_suppress_row(row, goal_dir, goal_k, wp_dir, wp_k, wp_err, turn_strict):
    if row["kind"] == "baseline" and row["name"] == "goal head (direct)":
        return goal_dir
    if row["kind"] == "wp_scale":
        return blend(goal_dir, goal_k, wp_dir, wp_k, wp_scale=row["wp_scale"])
    if row["kind"] == "baseline":
        return blend(goal_dir, goal_k, wp_dir, wp_k)
    sup = suppress_from_wp_turn(
        wp_err, turn_strict, wp_lo=row["wp_lo"], wp_hi=row["wp_hi"],
        turn_weight=row["turn_weight"], cap=row["cap"],
    )
    return blend_suppress(goal_dir, goal_k, wp_dir, wp_k, sup)


def run_suppress_sweep(args):
    device = torch.device(args.device)
    out_dir = args.sweep_out_dir or "logs/revalidation/kappa_gate_sweep"
    os.makedirs(out_dir, exist_ok=True)

    config_b = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(PAIRED_FRAMES)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]

    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    goal_dir = take("dino_dir").astype(np.float32)
    goal_k = take("dino_kappa").astype(np.float32)
    steps = (take("b_dist") / meters).astype(np.float32)

    cached = np.load(os.path.join(args.run_dir, "eval_waypoint", "locked_per_frame.npz"))
    wp_dir = cached["wp_dir"].astype(np.float32)
    wp_k = cached["wp_kappa"].astype(np.float32)

    attr = np.load(args.attr_npz)
    turn_strict = attr["turn_strict"].astype(bool)
    if args.gate_wp_field == "bearing_gt":
        wp_err = attr["wp_bearing_err_deg"].astype(np.float32)
    else:
        wp_err = angle_between_deg(goal_dir, wp_dir).astype(np.float32)
    hard = wp_err >= 45.0

    s = steps[:, None]
    grid = build_suppress_grid(args.quick)
    pos = {row["name"]: (dir_for_suppress_row(row, goal_dir, goal_k, wp_dir, wp_k, wp_err, turn_strict) * s).astype(np.float32) for row in grid}

    model_eo, sched_eo = load_model(load_config("config/nomad_e_oracle.yaml"), E_CHECKPOINT, device)
    am, ade = rollout(model_eo, sched_eo, dataset, far, pos, device, 8, 8, args.seed + 1, "suppress-sweep")

    rng = np.random.default_rng(args.seed + 3)
    boot_all = subset_index(len(am), args.bootstrap, rng)
    idx_hard = np.flatnonzero(hard)
    boot_hard = subset_index(len(idx_hard), args.bootstrap, rng)

    results = []
    print(f"\n[suppress sweep] n={len(am)} hard45={len(idx_hard)} wp={args.gate_wp_field}")
    print(f"{'name':<36} {'all':>8} {'hard':>8} {'hard_k-g':>8}")
    for row in grid:
        name = row["name"]
        use_all = boot_mean(am - ade[name], boot_all)
        use_hard = boot_mean(am[idx_hard] - ade[name][idx_hard], boot_hard)
        kg = boot_mean(
            (am[idx_hard] - ade[name][idx_hard]) - (am[idx_hard] - ade["goal head (direct)"][idx_hard]),
            boot_hard,
        )
        rec = {
            **row,
            "all_use_cm": 100 * use_all[0],
            "hard_use_cm": 100 * use_hard[0],
            "hard_kappa_minus_goal_cm": 100 * kg[0],
        }
        results.append(rec)
        print(f"{name:<36} {rec['all_use_cm']:+.2f}   {rec['hard_use_cm']:+.2f}   {rec['hard_kappa_minus_goal_cm']:+.2f}")

    ref_all = 100 * boot_mean(am - ade["kappa blend"], boot_all)[0]
    ref_kg = 100 * boot_mean(
        (am[idx_hard] - ade["kappa blend"][idx_hard]) - (am[idx_hard] - ade["goal head (direct)"][idx_hard]),
        boot_hard,
    )[0]
    print(f"\nRef kappa blend: all {ref_all:+.2f} cm | hard k-g {ref_kg:+.2f} cm")
    gated = [r for r in results if r["kind"] == "suppress"]
    best = max(gated, key=lambda r: (r["all_use_cm"] >= 2.80 - 1e-6, r["all_use_cm"], r["hard_kappa_minus_goal_cm"]))
    print("Best suppress:", json.dumps(best, indent=2))

    fields = sorted({k for r in results for k in r})
    with open(os.path.join(out_dir, "sweep.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    with open(os.path.join(out_dir, "best.json"), "w", encoding="utf-8") as f:
        json.dump({"best": best, "baseline_all_cm": ref_all, "baseline_hard_kg_cm": ref_kg}, f, indent=2)
    print("Saved", os.path.abspath(out_dir))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", default=WP_RUN)
    p.add_argument("--dyaw-lo", type=float, default=30.0)
    p.add_argument("--dyaw-hi", type=float, default=90.0)
    p.add_argument("--dis-lo", type=float, default=25.0)
    p.add_argument("--dis-hi", type=float, default=55.0)
    p.add_argument("--orb-ref", type=float, default=20.0)
    p.add_argument("--wp-boost", type=float, default=1.0)
    p.add_argument("--orb-gate", action="store_true", help="Include ORB in deploy gate (needs tuned --orb-ref)")
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--suppress-sweep", action="store_true", help="Grid WP suppression gates (turn / wp_err)")
    p.add_argument("--attr-npz", default=ATTR_NPZ)
    p.add_argument("--gate-wp-field", choices=("bearing_gt", "disagree"), default="bearing_gt")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--sweep-out-dir", default=None)
    args = p.parse_args()

    if args.suppress_sweep:
        run_suppress_sweep(args)
        return

    device = torch.device(args.device)
    out_dir = os.path.join(args.run_dir, "eval_adaptive_blend")
    os.makedirs(out_dir, exist_ok=True)

    config_b = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(PAIRED_FRAMES)
    sets, _, _ = frame_sets(dataset, moments, meters, SPREAD_NPZ)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]

    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    goal_dir = take("dino_dir").astype(np.float32)
    goal_k = take("dino_kappa").astype(np.float32)
    steps = (take("b_dist") / meters).astype(np.float32)
    goal = (take("target") / meters).astype(np.float32)

    cache_npz = os.path.join(args.run_dir, "eval_waypoint", "locked_per_frame.npz")
    cached = np.load(cache_npz)
    wp_dir = cached["wp_dir"].astype(np.float32)
    wp_k = cached["wp_kappa"].astype(np.float32)
    end = cached["endpoint"].astype(np.float32)

    abs_dyaw, orb = load_far_yaw()
    assert len(abs_dyaw) == len(far)

    kap = blend(goal_dir, goal_k, wp_dir, wp_k)
    g_oracle = gate_from_dyaw(abs_dyaw, args.dyaw_lo, args.dyaw_hi)
    g_dis = gate_from_disagree(goal_dir, wp_dir, args.dis_lo, args.dis_hi)
    g_orb = gate_from_orb(orb, args.orb_ref)
    g_deploy = g_dis if not args.orb_gate else combine_gates(g_dis, g_orb, mode="max")
    g_both = combine_gates(g_oracle, g_deploy, mode="max")

    s = steps[:, None]
    pos = {
        "kappa blend": (kap * s).astype(np.float32),
        "gated oracle dyaw": (blend_gated(goal_dir, goal_k, wp_dir, wp_k, g_oracle, wp_boost=args.wp_boost) * s),
        "gated deploy dis+orb": (blend_gated(goal_dir, goal_k, wp_dir, wp_k, g_deploy, wp_boost=args.wp_boost) * s),
        "gated max(oracle,deploy)": (blend_gated(goal_dir, goal_k, wp_dir, wp_k, g_both, wp_boost=args.wp_boost) * s),
        "goal head (direct)": (goal_dir * s).astype(np.float32),
        "true goal": goal.astype(np.float32),
    }

    print(f"gate means: oracle {g_oracle.mean():.2f} deploy {g_deploy.mean():.2f}")
    print(f"gate>0.5: oracle {100*(g_oracle>0.5).mean():.1f}% deploy {100*(g_deploy>0.5).mean():.1f}%")

    model_eo, sched_eo = load_model(load_config("config/nomad_e_oracle.yaml"), E_CHECKPOINT, device)
    am, ade = rollout(model_eo, sched_eo, dataset, far, pos, device, 8, 8, args.seed + 1, "adapt-far")

    rng = np.random.default_rng(args.seed + 3)
    rows = []
    print("\n[locked far] use (cm):")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        print(f"  [{set_name}] n={len(idx)}")
        for k in pos:
            report(k, am, ade, idx, boot)
        for name in ("gated deploy dis+orb", "gated oracle dyaw"):
            dlt = boot_mean((am[idx]-ade[name][idx]) - (am[idx]-ade["kappa blend"][idx]), boot)
            print(f"    {name} - kappa blend  {100*dlt[0]:+.2f} [{100*dlt[1]:+.2f}, {100*dlt[2]:+.2f}] cm")
    np.savez_compressed(os.path.join(out_dir, "gates.npz"), g_oracle=g_oracle, g_deploy=g_deploy, abs_dyaw=abs_dyaw, orb=orb)
    print("Saved", os.path.abspath(out_dir))

if __name__ == "__main__":
    main()

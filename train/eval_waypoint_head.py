"""Near-waypoint bearing head fed to E-oracle. No policy training.

The waypoint head (train_goal_dino.py --target endpoint) predicts the bearing of the
robot position len_traj_pred steps ahead from the current and goal frames. E-oracle
gets one of these positions (all times B's goal distance, except "true goal"):
  goal head (direct)   the far-goal DINO head: today's deployable direct test
  waypoint head        the new near-waypoint head
  kappa blend          normalize(kappa_g * d_goal + kappa_w * d_waypoint), fixed rule, no tuning
  true endpoint dir    ceiling (uses the label of the trajectory being scored)
  true goal            E-oracle's training condition; the 100% reference
Reported on the clean tuning set (test-split trajectories unused by the locked frames)
and on the locked far frames, with bearing errors and paired differences.

Run from train/:
    python -u eval_waypoint_head.py --run-dir logs/nomad_d/<waypoint head run>
    python -u eval_waypoint_head.py --run-dir logs/nomad_d/<wp run> --oracle-factorial --skip-tune
"""

import argparse
import csv
import os
import pickle

import cv2  # noqa: F401 — before torch on Windows (nomad_train)
import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, angle_err, rollout
from revalidate import CACHE_ROOT, dino_and_b, tune_items
from train_e_dino import DINO_BEST, load_dino_head, read_tokens
from yaw_traj import wp_direction_from_head
from train_goal_dino import load_cache
from vint_train.data.data_utils import get_data_path

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
YAW_CSV_ORACLE = "logs/revalidation/yaw_overlap_analysis/per_frame_yaw_overlap.csv"
ORACLE_CONDITIONS = (
    "Dgt_dg_GT",
    "Db_dg_GT",
    "Dgt_dg_pred",
    "Db_dg_pred",
    "Db_d_blend",  # blend PP: pred goal + pred wp
    "Db_blend_dgp_dwGT",  # blend PG
    "Db_blend_dgGT_dwp",  # blend GP
    "Db_blend_dgGT_dwGT",  # blend GG (kappa pred; dirs GT)
)

# 2x2 blend cells (goal x wp: P=pred direction, G=GT unit direction); distance always B.
BLEND_2X2 = (
    ("Db_d_blend", "P", "P"),
    ("Db_blend_dgp_dwGT", "P", "G"),
    ("Db_blend_dgGT_dwp", "G", "P"),
    ("Db_blend_dgGT_dwGT", "G", "G"),
)


def _head_context(head):
    return max(0, int(head.kind.shape[0]) - 2)


@torch.no_grad()
def head_predict(head, items, rows, features, device, batch_size=256, wp_dir_mode="auto"):
    context = _head_context(head)
    dirs, kappas = [], []
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        curr = read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        ctx = None
        if context > 0:
            past = []
            for j in range(1, context + 1):
                past.append(
                    read_tokens(features, [rows[(c[0], c[1] - j)] for c in chunk]).to(device).float()
                )
            ctx = torch.stack(past, dim=1)
        out = head(curr, goal, ctx)
        d, k = wp_direction_from_head(head, out, wp_dir_mode)
        dirs.append(d.cpu().numpy())
        kappas.append(k.cpu().numpy())
    return np.concatenate(dirs), np.concatenate(kappas)


def endpoints(dataset, items):
    return np.stack([load_observation(dataset, n, t, g)[2][-1, :2] for n, t, g in items]).astype(np.float32)


def blend(d1, k1, d2, k2, wp_scale=1.0):
    r = k1[:, None] * d1 + (wp_scale * k2)[:, None] * d2
    return (r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)).astype(np.float32)


def blend_torch(g_dir, g_k, w_dir, w_k, wp_scale=1.0):
    """Unit direction; g_dir/w_dir are [B, 2], kappas [B]."""
    r = g_k.unsqueeze(-1) * g_dir + (wp_scale * w_k).unsqueeze(-1) * w_dir
    return r / r.norm(dim=-1, keepdim=True).clamp(min=1e-6)


def build_positions(goal_dir, goal_kappa, wp_dir, wp_kappa, steps, end, goal):
    s = steps[:, None].astype(np.float32)
    return {
        "true goal": goal.astype(np.float32),
        "true endpoint dir": (unit(end) * s).astype(np.float32),
        "goal head (direct)": (goal_dir * s).astype(np.float32),
        "waypoint head": (wp_dir * s).astype(np.float32),
        "kappa blend": blend(goal_dir, goal_kappa, wp_dir, wp_kappa) * s,
    }


def _yaw_scalar(y, i):
    return float(np.ravel(y[i])[0])


def _endpoint_dyaw_deg(yaw_arr, t, g):
    d = _yaw_scalar(yaw_arr, g) - _yaw_scalar(yaw_arr, t)
    d = (d + np.pi) % (2 * np.pi) - np.pi
    return float(np.degrees(d))


def load_endpoint_dyaw_oracle(dataset, items, csv_path=YAW_CSV_ORACLE):
    n = len(items)
    if os.path.isfile(csv_path):
        rows = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("group") == "20-40":
                    rows.append(abs(float(row["endpoint_dyaw_deg"])))
        if len(rows) == n:
            return np.array(rows, dtype=np.float32)
    cache = {}
    out = np.zeros(n, dtype=np.float32)
    for i, (traj, t, g) in enumerate(items):
        if traj not in cache:
            with open(get_data_path(dataset.data_folder, traj, "traj_data.pkl"), "rb") as f:
                cache[traj] = pickle.load(f)["yaw"]
        out[i] = abs(_endpoint_dyaw_deg(cache[traj], t, g))
    return out


def build_factorial(goal_pos, goal_dir, goal_kappa, wp_dir, wp_kappa, steps_b, end_gt):
    d_g_gt = unit(goal_pos)
    d_gt = np.linalg.norm(goal_pos, axis=1).astype(np.float32)
    d_w_gt = unit(end_gt)
    sb = steps_b[:, None].astype(np.float32)
    blend_pp = blend(goal_dir, goal_kappa, wp_dir, wp_kappa)
    blend_pg = blend(goal_dir, goal_kappa, d_w_gt, wp_kappa)
    blend_gp = blend(d_g_gt, goal_kappa, wp_dir, wp_kappa)
    blend_gg = blend(d_g_gt, goal_kappa, d_w_gt, wp_kappa)
    return {
        "Dgt_dg_GT": goal_pos.astype(np.float32),
        "Db_dg_GT": (d_g_gt * sb).astype(np.float32),
        "Dgt_dg_pred": (goal_dir * d_gt[:, None]).astype(np.float32),
        "Db_dg_pred": (goal_dir * sb).astype(np.float32),
        "Db_d_blend": (blend_pp * sb).astype(np.float32),
        "Db_blend_dgp_dwGT": (blend_pg * sb).astype(np.float32),
        "Db_blend_dgGT_dwp": (blend_gp * sb).astype(np.float32),
        "Db_blend_dgGT_dwGT": (blend_gg * sb).astype(np.float32),
    }


def run_oracle_factorial(args, device, dataset, meters, moments, wp_head):
    out_dir = getattr(args, "oracle_out_dir", None) or "logs/revalidation/oracle_factorial"
    os.makedirs(out_dir, exist_ok=True)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    goal_dir = take("dino_dir").astype(np.float32)
    goal_kappa = take("dino_kappa").astype(np.float32)
    steps_b = (take("b_dist") / meters).astype(np.float32)
    goal_t = (take("target") / meters).astype(np.float32)
    _p, rows_t, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats_t = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    wp_dir, wp_kappa = head_predict(wp_head, far, rows_t, feats_t, device)
    end_t = endpoints(dataset, far)
    pos_t = build_factorial(goal_t, goal_dir, goal_kappa, wp_dir, wp_kappa, steps_b, end_t)
    bear_gap = angle_err(goal_dir, unit(goal_t))
    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    am, ade = rollout(
        model_eo, sched_eo, dataset, far, pos_t, device, args.num_samples, 8, args.seed + 3, "oracle factorial"
    )
    abs_dyaw = load_endpoint_dyaw_oracle(dataset, far)
    dyaw_sets = {
        "|dyaw|>=45": abs_dyaw >= 45,
        "|dyaw|>=60": abs_dyaw >= 60,
        "|dyaw| 90-180": (abs_dyaw >= 90) & (abs_dyaw <= 180),
    }
    rng = np.random.default_rng(args.seed + 4)
    rows_out = []
    fmt = lambda u: f"{100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]"
    print("\n=== Oracle factorial (frozen E-oracle) ===\n")
    for set_name in list(SET_NAMES) + list(dyaw_sets.keys()):
        if set_name == "all":
            idx = np.arange(len(far))
        elif set_name in sets:
            idx = np.flatnonzero(sets[set_name])
        else:
            idx = np.flatnonzero(dyaw_sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        ref = float((am[idx] - ade["Dgt_dg_GT"][idx]).mean())
        print(f"[{set_name}] n={len(idx)}")
        for c in ORACLE_CONDITIONS:
            u = boot_mean(am[idx] - ade[c][idx], boot)
            print(f"  {c:<22} {fmt(u)} cm  ({100 * u[0] / ref:.0f}% of Dgt_dg_GT)")
            rows_out.append(
                {"subset": set_name, "n": len(idx), "condition": c, "use_cm": 100 * u[0],
                 "lo": 100 * u[1], "hi": 100 * u[2], "vs_Dgt_dg_GT": u[0] / ref if ref else float("nan")}
            )
        if len(idx) > 20:
            print(f"  median goal_pred vs GT bearing: {np.median(bear_gap[idx]):.1f} deg\n")
    boot_all = subset_index(len(far), args.bootstrap, rng)
    print("Paired vs Db_dg_pred:")
    blend_cells = [c for c, _g, _w in BLEND_2X2]
    for c in ("Db_dg_GT", "Dgt_dg_pred", *blend_cells):
        d = boot_mean((am - ade[c]) - (am - ade["Db_dg_pred"]), boot_all)
        print(f"  {c}: {fmt(d)} cm")
    use = {c: am - ade[c] for c, _g, _w in BLEND_2X2}
    u_pp, u_pg, u_gp, u_gg = (use[c] for c, _g, _w in BLEND_2X2)
    interact = u_gg - u_gp - u_pg + u_pp
    ui = boot_mean(interact, boot_all)
    print("\n2x2 kappa-blend (use cm, all far; goal/wp: P=pred dir G=GT dir; kappa pred; dist B):")
    print("              wp_P          wp_G")
    for g_lab, g_key in (("goal_P", "P"), ("goal_G", "G")):
        row = []
        for w_key in ("P", "G"):
            name = next(c for c, gg, ww in BLEND_2X2 if gg == g_key and ww == w_key)
            u = boot_mean(use[name], boot_all)
            row.append(f"{fmt(u)}")
        print(f"  {g_lab:<8}  {row[0]:>22}  {row[1]:>22}")
    print(f"  interaction I = U_GG - U_GP - U_PG + U_PP: {fmt(ui)} cm")
    print("  (normalize blend: I is diagnostic non-additivity, not independent head causal effects)\n")
    rows_out.append(
        {
            "subset": "all",
            "n": len(far),
            "condition": "blend_interaction_I",
            "use_cm": 100 * ui[0],
            "lo": 100 * ui[1],
            "hi": 100 * ui[2],
            "vs_Dgt_dg_GT": float("nan"),
        }
    )
    write_csv(os.path.join(out_dir, "factorial_use.csv"), rows_out)
    np.savez_compressed(
        os.path.join(out_dir, "per_frame.npz"),
        ade_mask=am,
        abs_endpoint_dyaw=abs_dyaw,
        bearing_err_pred_vs_gt=bear_gap,
        **{f"ade_{c}": ade[c] for c in ORACLE_CONDITIONS},
    )
    print(f"Saved to {os.path.abspath(out_dir)}")


def print_bearings(tag, goal_dir, wp_dir, end, goal):
    print(
        f"[{tag}] bearing medians: waypoint head vs true endpoint {np.median(angle_err(wp_dir, end)):.1f} deg | "
        f"goal head vs true endpoint {np.median(angle_err(goal_dir, end)):.1f} | goal head vs true goal "
        f"{np.median(angle_err(goal_dir, goal)):.1f} | true goal vs true endpoint {np.median(angle_err(goal, end)):.1f} | "
        f"waypoint head >45 deg from endpoint {100 * (angle_err(wp_dir, end) > 45).mean():.0f}%"
    )


def main():
    parser = argparse.ArgumentParser(description="Near-waypoint bearing head into E-oracle")
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
    parser.add_argument("--skip-locked", action="store_true", help="Smoke tests: tuning set only")
    parser.add_argument("--skip-tune", action="store_true", help="Locked frames only (the tuning set is already reported)")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--oracle-factorial", action="store_true", help="P0: distance x bearing factorial on locked far")
    parser.add_argument("--oracle-out-dir", default="logs/revalidation/oracle_factorial")
    parser.add_argument(
        "--wp-dir-mode",
        choices=("auto", "vm", "yaw_integrated"),
        default="auto",
        help="WP unit direction: vm=out[0]; yaw_integrated=integrate(yaw); auto=yaw if head has yaw_aux",
    )
    parser.add_argument(
        "--eval-subdir",
        default="eval_waypoint",
        help="Under run-dir for csv/npz (use eval_waypoint_wpvm vs eval_waypoint_wpyaw for ablations)",
    )
    args = parser.parse_args()

    device = torch.device(args.device)
    out_dir = os.path.join(args.run_dir, args.eval_subdir)
    os.makedirs(out_dir, exist_ok=True)
    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    wp_head, _m = load_dino_head(os.path.join(args.run_dir, args.checkpoint), device)
    if args.oracle_factorial:
        run_oracle_factorial(args, device, dataset, meters, moments, wp_head)
        return
    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    rng = np.random.default_rng(args.seed + 2)
    rows_out = []

    # ---- clean tuning set ----
    if not args.skip_tune:
        items = tune_items(dataset, {t for t, _, _ in moments}, args.n_tune, seed=2468)
        _p, rows, _meta = load_cache(CACHE_ROOT, "test")
        feats = np.load(os.path.join(CACHE_ROOT, "test", "features.npy"), mmap_mode="r")
        goal_head, _gm = load_dino_head(DINO_BEST, device)
        b_frozen = load_frozen_nomad(config_b, B_CHECKPOINT, device)
        est = dino_and_b(items, dataset, b_frozen, goal_head, rows, feats, device)
        del b_frozen, goal_head
        wp_dir, wp_kappa = head_predict(wp_head, items, rows, feats, device, wp_dir_mode=args.wp_dir_mode)
        end = endpoints(dataset, items)
        print_bearings("tuning", est["dir"], wp_dir, end, est["target"])
        pos = build_positions(est["dir"], est["kappa"], wp_dir, wp_kappa, est["steps"], end, est["target"])
        am, ade = rollout(model_eo, sched_eo, dataset, items, pos, device, args.num_samples, 16, args.seed, "tuning")
        ref = float((am - ade["true goal"]).mean())
        print("[tuning] use (cm) and share of the true-goal use:")
        for k in pos:
            u = float((am - ade[k]).mean())
            print(f"  {k:<20} {100 * u:+.2f}  ({100 * u / ref:.0f}%)")
            rows_out.append({"set": "tuning", "frames": "all", "condition": k, "use_cm": 100 * u, "vs_true_goal": u / ref})
    if args.skip_locked:
        write_csv(os.path.join(out_dir, "waypoint_eval.csv"), rows_out)
        return

    # ---- locked far frames ----
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    _p, rows_t, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats_t = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")
    wp_dir_t, wp_kappa_t = head_predict(wp_head, far, rows_t, feats_t, device, wp_dir_mode=args.wp_dir_mode)
    end_t = endpoints(dataset, far)
    goal_t = (take("target") / meters).astype(np.float32)
    print_bearings("locked", take("dino_dir"), wp_dir_t, end_t, goal_t)
    pos_t = build_positions(take("dino_dir"), take("dino_kappa"), wp_dir_t, wp_kappa_t, take("b_dist") / meters, end_t, goal_t)
    am, ade = rollout(model_eo, sched_eo, dataset, far, pos_t, device, args.num_samples, 8, args.seed + 1, "locked")
    print("\n[locked] use (cm) [95% CI] and share of the true-goal use:")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        ref = float((am[idx] - ade["true goal"][idx]).mean())
        print(f"  [{set_name}] n={len(idx)}")
        for k in pos_t:
            u = boot_mean(am[idx] - ade[k][idx], boot)
            print(f"    {k:<20} {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  ({100 * u[0] / ref:.0f}%)")
            rows_out.append({"set": "locked", "frames": set_name, "condition": k, "use_cm": 100 * u[0],
                             "lo": 100 * u[1], "hi": 100 * u[2], "vs_true_goal": u[0] / ref})
    boot_all = subset_index(len(far), args.bootstrap, rng)
    for k in ("waypoint head", "kappa blend"):
        d = boot_mean((am - ade[k]) - (am - ade["goal head (direct)"]), boot_all)
        print(f"  paired {k} - goal head (direct): {100 * d[0]:+.2f} [{100 * d[1]:+.2f}, {100 * d[2]:+.2f}] cm")
    if not args.skip_tune:
        write_csv(os.path.join(out_dir, "waypoint_eval.csv"), rows_out)
    np.savez_compressed(
        os.path.join(out_dir, "locked_per_frame.npz"),
        ade_mask=am, names=np.array(list(pos_t)), traj=np.array([n for n, _t, _g in far]),
        wp_dir=wp_dir_t, wp_kappa=wp_kappa_t, endpoint=end_t,
        **{f"ade_{i}": ade[k] for i, k in enumerate(pos_t)},
    )
    print(f"Saved to {os.path.abspath(out_dir)}")


if __name__ == "__main__":
    main()

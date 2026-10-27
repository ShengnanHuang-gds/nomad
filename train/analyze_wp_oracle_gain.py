"""P1: Waypoint oracle gain attribution (no training).

Per locked far frame, oracle wp gain from the 2x2 factorial:
  delta_ade_m = ADE(PP) - ADE(PG)   # >0 when GT wp direction helps
  delta_use_cm = 100 * delta_ade_m  # same frame, shared mask + noise

Relates delta_* to wp bearing error, kappa_w, |endpoint dyaw|, turn/spread.

Run from train/:
    python -u analyze_wp_oracle_gain.py
"""

import argparse
import csv
import os

import numpy as np

from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_testtime import angle_err

ORACLE_NPZ = "logs/revalidation/oracle_factorial/per_frame.npz"
WP_NPZ = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/eval_waypoint/locked_per_frame.npz"
OUT_DIR = "logs/revalidation/wp_oracle_attribution"

ADE_PP = "ade_Db_d_blend"
ADE_PG = "ade_Db_blend_dgp_dwGT"


def pearson(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def concentration_top_frac(gain, top=0.1):
    g = np.maximum(gain, 0.0)
    total = g.sum()
    if total <= 0:
        return float("nan"), 0
    order = np.argsort(-g, kind="stable")
    k = max(1, int(np.ceil(top * len(g))))
    return float(g[order[:k]].sum() / total), k


def main():
    parser = argparse.ArgumentParser(description="Waypoint oracle gain attribution")
    parser.add_argument("--oracle-npz", default=ORACLE_NPZ)
    parser.add_argument("--wp-npz", default=WP_NPZ)
    parser.add_argument("--out-dir", default=OUT_DIR)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    args = parser.parse_args()

    o = np.load(args.oracle_npz)
    w = np.load(args.wp_npz)
    n = o[ADE_PP].shape[0]
    if w["wp_dir"].shape[0] != n:
        raise SystemExit(f"oracle n={n} vs wp n={w['wp_dir'].shape[0]}")

    ade_pp = o[ADE_PP].astype(np.float64)
    ade_pg = o[ADE_PG].astype(np.float64)
    delta_ade = ade_pp - ade_pg
    delta_use_cm = 100 * delta_ade

    end = w["endpoint"].astype(np.float32)
    wp_dir = w["wp_dir"].astype(np.float32)
    wp_kappa = w["wp_kappa"].astype(np.float64)
    wp_err = angle_err(wp_dir, unit(end)).astype(np.float64)
    abs_dyaw = o["abs_endpoint_dyaw"].astype(np.float64)
    goal_bear_err = o["bearing_err_pred_vs_gt"].astype(np.float64)

    config = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    if len(moments) != n:
        raise SystemExit(f"paired frames {len(moments)} != oracle {n}")
    sets, lateral, yaw8 = frame_sets(dataset, moments, meters, args.spread)
    turn_strict = sets["turn 0.30m/45deg"]
    turn_loose = sets["turn 0.15m/20deg"]
    spread = sets.get("B masked spread")

    os.makedirs(args.out_dir, exist_ok=True)
    per_frame = {
        "delta_ade_m": delta_ade,
        "delta_use_cm": delta_use_cm,
        "wp_bearing_err_deg": wp_err,
        "wp_kappa": wp_kappa,
        "goal_bearing_err_deg": goal_bear_err,
        "abs_endpoint_dyaw_deg": abs_dyaw,
        "turn_strict": turn_strict,
        "turn_loose": turn_loose,
        "endpoint_lateral_m": lateral,
        "yaw8_deg": yaw8,
    }
    if spread is not None:
        per_frame["spread"] = spread
    np.savez_compressed(os.path.join(args.out_dir, "attribution_per_frame.npz"), **per_frame)

    pos_gain = np.maximum(delta_ade, 0.0)
    top10_share, top10_k = concentration_top_frac(pos_gain, 0.10)
    top5_share, top5_k = concentration_top_frac(pos_gain, 0.05)

    lines = []
    lines.append("=== Waypoint oracle gain attribution (PP -> PG) ===\n")
    lines.append(f"n={n} locked far frames")
    lines.append(f"mean delta_use_cm {delta_use_cm.mean():+.3f} (sum {delta_use_cm.sum():+.1f})")
    lines.append(f"mean delta_ade_m {delta_ade.mean()*100:+.3f} cm")
    lines.append(f"frames with PG better (delta_ade>0): {(delta_ade > 0).mean()*100:.1f}%")
    lines.append(f"pearson(wp_err_deg, delta_use_cm): {pearson(wp_err, delta_use_cm):+.3f}")
    lines.append(f"pearson(wp_err_deg, delta_ade_m): {pearson(wp_err, delta_ade):+.3f}")
    lines.append(f"pearson(|dyaw|, delta_use_cm): {pearson(abs_dyaw, delta_use_cm):+.3f}")
    lines.append(f"top 10% frames ({top10_k}) hold {100*top10_share:.1f}% of positive gain")
    lines.append(f"top 5% frames ({top5_k}) hold {100*top5_share:.1f}% of positive gain\n")

    q_edges = np.percentile(wp_err, [0, 20, 40, 60, 80, 100])
    quint_rows = []
    for qi in range(5):
        lo, hi = q_edges[qi], q_edges[qi + 1]
        if qi < 4:
            m = (wp_err >= lo) & (wp_err < hi)
        else:
            m = (wp_err >= lo) & (wp_err <= hi)
        idx = np.flatnonzero(m)
        quint_rows.append(
            {
                "quintile": qi + 1,
                "wp_err_lo": lo,
                "wp_err_hi": hi,
                "n": len(idx),
                "mean_wp_err": float(wp_err[idx].mean()) if len(idx) else float("nan"),
                "mean_delta_use_cm": float(delta_use_cm[idx].mean()) if len(idx) else float("nan"),
                "sum_delta_use_cm": float(delta_use_cm[idx].sum()) if len(idx) else float("nan"),
                "frac_total_gain": float(delta_ade[idx].sum() / max(delta_ade.sum(), 1e-12)),
            }
        )
    write_csv(
        os.path.join(args.out_dir, "by_wp_err_quintile.csv"),
        quint_rows,
        list(quint_rows[0].keys()),
    )

    bin_rows = []
    bins = [
        ("wp_err <15", wp_err < 15),
        ("15-30", (wp_err >= 15) & (wp_err < 30)),
        ("30-45", (wp_err >= 30) & (wp_err < 45)),
        ("wp_err >=45", wp_err >= 45),
        ("turn strict", turn_strict),
        ("not turn strict", ~turn_strict),
        ("|dyaw|>=45", abs_dyaw >= 45),
        ("|dyaw| 90-180", (abs_dyaw >= 90) & (abs_dyaw <= 180)),
        ("high kappa, wp_err>=30", (wp_kappa >= np.median(wp_kappa)) & (wp_err >= 30)),
        ("high kappa, wp_err<15", (wp_kappa >= np.median(wp_kappa)) & (wp_err < 15)),
    ]
    if spread is not None:
        bins.append(("B masked spread", spread))
    for label, mask in bins:
        idx = np.flatnonzero(mask)
        if len(idx) == 0:
            continue
        r = pearson(wp_err[idx], delta_use_cm[idx]) if len(idx) > 2 else float("nan")
        bin_rows.append(
            {
                "bin": label,
                "n": len(idx),
                "median_wp_err_deg": float(np.median(wp_err[idx])),
                "mean_delta_use_cm": float(delta_use_cm[idx].mean()),
                "sum_delta_use_cm": float(delta_use_cm[idx].sum()),
                "frac_total_gain": float(delta_ade[idx].sum() / max(delta_ade.sum(), 1e-12)),
                "pct_frames_pg_wins": float((delta_ade[idx] > 0).mean() * 100),
                "pearson_wp_err_vs_gain_in_bin": r,
            }
        )
    write_csv(
        os.path.join(args.out_dir, "by_scene_bin.csv"),
        bin_rows,
        list(bin_rows[0].keys()),
    )

    turn_rows = []
    for name, mask in (
        ("turn 0.30m/45deg", turn_strict),
        ("straight (not 0.15m/20deg)", sets["straight (not 0.15m/20deg)"]),
    ):
        idx = np.flatnonzero(mask)
        t_share, t_k = concentration_top_frac(pos_gain[idx], 0.10)
        turn_rows.append(
            {
                "subset": name,
                "n": len(idx),
                "median_wp_err_deg": float(np.median(wp_err[idx])),
                "pct_wp_err_gt45": float((wp_err[idx] > 45).mean() * 100),
                "mean_delta_use_cm": float(delta_use_cm[idx].mean()),
                "sum_delta_use_cm": float(delta_use_cm[idx].sum()),
                "frac_all_gain": float(delta_ade[idx].sum() / max(delta_ade.sum(), 1e-12)),
                "top10pct_share_within_subset": float(t_share),
                "top10pct_k": t_k,
            }
        )
    write_csv(
        os.path.join(args.out_dir, "turn_vs_straight.csv"),
        turn_rows,
        list(turn_rows[0].keys()),
    )

    lines.append("--- turn vs straight ---")
    for row in turn_rows:
        lines.append(
            f"  {row['subset']}: n={row['n']} median_wp_err={row['median_wp_err_deg']:.1f} deg "
            f">45 deg {row['pct_wp_err_gt45']:.0f}% mean_duse={row['mean_delta_use_cm']:+.2f}cm "
            f"share_of_total_gain={100*row['frac_all_gain']:.0f}% "
            f"top10pct_within_subset={100*row['top10pct_share_within_subset']:.0f}%"
        )

    lines.append("\n--- wp error quintiles (mean delta_use_cm) ---")
    for row in quint_rows:
        lines.append(
            f"  Q{row['quintile']} [{row['wp_err_lo']:.1f},{row['wp_err_hi']:.1f}] deg "
            f"n={row['n']} mean={row['mean_delta_use_cm']:+.2f} frac_total={100*row['frac_total_gain']:.0f}%"
        )

    report = "\n".join(lines) + "\n"
    print(report)
    with open(os.path.join(args.out_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Saved CSV + npz under {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()
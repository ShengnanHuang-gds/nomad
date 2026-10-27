"""P1b: Characterize wp_err>=45 deg frames (hard120) vs controls."""

import argparse
import csv
import json
import os
import pickle

import numpy as np

from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_testtime import angle_err

ATTR_NPZ = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
WP_NPZ = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/eval_waypoint/locked_per_frame.npz"
YAW_CSV = "logs/revalidation/yaw_overlap_analysis/per_frame_yaw_overlap.csv"
OUT_DIR = "logs/revalidation/wp_hard120"


def yaw_scalar(yaw_arr, i):
    return float(np.ravel(yaw_arr[i])[0])


def wrap_rad(d):
    return (d + np.pi) % (2 * np.pi) - np.pi


def pearson(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def cohens_d(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    pooled = ((len(a) - 1) * v1 + (len(b) - 1) * v2) / (len(a) + len(b) - 2)
    if pooled <= 0:
        return 0.0
    return float((a.mean() - b.mean()) / np.sqrt(pooled))


def write_csv(path, rows, fieldnames=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not rows:
        return
    if fieldnames is None:
        keys = []
        seen = set()
        for row in rows:
            for k in row:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        fieldnames = keys
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def path_kinematics(traj_data, t, goal_time, spacing, len_pred):
    yaw = traj_data["yaw"]
    pos = traj_data["position"]
    n_yaw = len(yaw)
    idx = [min(t + i * spacing, n_yaw - 1) for i in range(len_pred + 1)]
    yaws = [yaw_scalar(yaw, i) for i in idx]
    step_dyaw = [
        abs(np.degrees(wrap_rad(yaws[i + 1] - yaws[i]))) for i in range(len(yaws) - 1)
    ]
    path_winding_8 = float(np.sum(step_dyaw))
    max_step_yaw = float(np.max(step_dyaw)) if step_dyaw else 0.0

    pts = np.array([pos[min(i, len(pos) - 1)][:2] for i in idx], dtype=np.float64)
    chord = float(np.linalg.norm(pts[-1] - pts[0]))
    arc = float(sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)))
    chord_arc_ratio = arc / max(chord, 1e-6)

    path_dyaw = 0.0
    g = min(goal_time, n_yaw - 1)
    cur = t
    while cur < g:
        nxt = min(cur + spacing, g)
        path_dyaw += abs(np.degrees(wrap_rad(yaw_scalar(yaw, nxt) - yaw_scalar(yaw, cur))))
        cur = nxt

    past = []
    for k in range(1, 4):
        t0 = t - k * spacing
        t1 = t - (k - 1) * spacing
        if t0 < 0:
            break
        past.append(abs(np.degrees(wrap_rad(yaw_scalar(yaw, t1) - yaw_scalar(yaw, t0)))))
    past_yaw_rate = float(np.mean(past)) if past else 0.0
    past_winding_3 = float(np.sum(past)) if past else 0.0

    return {
        "path_winding_8": path_winding_8,
        "max_step_yaw_deg": max_step_yaw,
        "chord_arc_ratio": chord_arc_ratio,
        "path_dyaw_t_to_g": float(path_dyaw),
        "past_yaw_rate": past_yaw_rate,
        "past_winding_3": past_winding_3,
    }


def load_yaw_far_csv(path, moments, goal_times):
    lookup = {}
    if not os.path.isfile(path):
        return lookup
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("group") != "20-40":
                continue
            key = (row["traj"], int(row["t"]), int(row["goal_time"]))
            lookup[key] = {
                "endpoint_dyaw_csv": float(row["endpoint_dyaw_deg"]),
                "path_dyaw_csv": float(row["path_dyaw_deg"]),
                "orb_matches": int(row["orb"]) if row["orb"] != "-1" else -1,
            }
    return lookup


def match_control(hard_mask, turn_strict, rng, n=None):
    n_h = int(hard_mask.sum())
    if n is None:
        n = n_h
    pool = np.flatnonzero(~hard_mask)
    if len(pool) < n:
        return pool
    rate = float(turn_strict[hard_mask].mean()) if n_h else 0.5
    n_turn = int(round(n * rate))
    n_str = n - n_turn
    turn_pool = pool[turn_strict[pool]]
    straight_pool = pool[~turn_strict[pool]]
    sel = []
    if len(turn_pool) and n_turn:
        sel.extend(rng.choice(turn_pool, min(n_turn, len(turn_pool)), replace=False))
    rem = n - len(sel)
    if rem > 0 and len(straight_pool):
        sel.extend(rng.choice(straight_pool, min(rem, len(straight_pool)), replace=False))
    if len(sel) < n:
        rest = np.setdiff1d(pool, sel)
        if len(rest):
            sel.extend(rng.choice(rest, n - len(sel), replace=False))
    return np.asarray(sel, dtype=int)


def _as_mask(n, sel):
    if isinstance(sel, np.ndarray) and sel.dtype == bool:
        return sel
    m = np.zeros(n, dtype=bool)
    m[np.asarray(sel, dtype=int)] = True
    return m


def enrichment_table(features, names, mask_h, mask_c, label_c):
    rows = []
    mh = _as_mask(len(next(iter(features.values()))), mask_h)
    mc = _as_mask(len(next(iter(features.values()))), mask_c)
    for name in names:
        a = features[name][mh]
        b = features[name][mc]
        row = {
            "feature": name,
            "control": label_c,
            "n_H": int(mh.sum()),
            "n_C": int(mc.sum()),
            "median_H": float(np.median(a)),
            "median_C": float(np.median(b)),
            "mean_H": float(a.mean()),
            "mean_C": float(b.mean()),
            "cohens_d": cohens_d(a, b),
        }
        if name in (
            "turn_strict",
            "turn_loose",
            "hidden_turn",
            "goal_low_wp_high",
        ):
            row["pct_H"] = float(100 * a.mean())
            row["pct_C"] = float(100 * b.mean())
        rows.append(row)
    return rows


def max_run_same_traj(items):
    """items: list of (traj, t) sorted by traj, t."""
    if not items:
        return 0
    best = cur = 1
    for i in range(1, len(items)):
        same = items[i][0] == items[i - 1][0] and items[i][1] - items[i - 1][1] <= 5
        cur = cur + 1 if same else 1
        best = max(best, cur)
    return best


def main():
    parser = argparse.ArgumentParser(description="WP hard120 characterization")
    parser.add_argument("--attr-npz", default=ATTR_NPZ)
    parser.add_argument("--wp-npz", default=WP_NPZ)
    parser.add_argument("--yaw-csv", default=YAW_CSV)
    parser.add_argument("--out-dir", default=OUT_DIR)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    a = dict(np.load(args.attr_npz))
    w = np.load(args.wp_npz)
    n = a["delta_ade_m"].shape[0]

    delta_ade = a["delta_ade_m"].astype(np.float64)
    delta_use = a["delta_use_cm"].astype(np.float64)
    wp_err = a["wp_bearing_err_deg"].astype(np.float64)
    wp_kappa = a["wp_kappa"].astype(np.float64)
    goal_err = a["goal_bearing_err_deg"].astype(np.float64)
    abs_dyaw = a["abs_endpoint_dyaw_deg"].astype(np.float64)
    turn_strict = a["turn_strict"].astype(bool)
    turn_loose = a["turn_loose"].astype(bool)
    lateral = a["endpoint_lateral_m"].astype(np.float64)
    yaw8 = a["yaw8_deg"].astype(np.float64)
    spread = a["spread"].astype(bool) if "spread" in a else np.zeros(n, dtype=bool)

    config = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config, "test")
    spacing = dataset.waypoint_spacing
    len_pred = dataset.len_traj_pred
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    if len(moments) != n:
        raise SystemExit(f"moments {len(moments)} != n {n}")

    goal_times = np.array(
        [[g[4] for g in goals if g[0] == "20-40"][0] for _t, _t2, goals in moments],
        dtype=np.int32,
    )
    trajs = [m[0] for m in moments]
    ts = np.array([m[1] for m in moments], dtype=np.int32)

    yaw_lookup = load_yaw_far_csv(args.yaw_csv, moments, goal_times)

    cache = {}
    path_winding = np.zeros(n)
    max_step = np.zeros(n)
    chord_arc = np.ones(n)
    path_dyaw_tg = np.zeros(n)
    past_rate = np.zeros(n)
    past_w3 = np.zeros(n)
    orb = np.full(n, -1, dtype=np.int32)

    for i, (traj, t, g) in enumerate(zip(trajs, ts, goal_times)):
        if traj not in cache:
            pkl = os.path.join(dataset.data_folder, traj, "traj_data.pkl")
            with open(pkl, "rb") as f:
                cache[traj] = pickle.load(f)
        kin = path_kinematics(cache[traj], int(t), int(g), spacing, len_pred)
        path_winding[i] = kin["path_winding_8"]
        max_step[i] = kin["max_step_yaw_deg"]
        chord_arc[i] = kin["chord_arc_ratio"]
        path_dyaw_tg[i] = kin["path_dyaw_t_to_g"]
        past_rate[i] = kin["past_yaw_rate"]
        past_w3[i] = kin["past_winding_3"]
        key = (traj, int(t), int(g))
        if key in yaw_lookup:
            orb[i] = yaw_lookup[key]["orb_matches"]

    hard = wp_err >= 45.0
    top_gain = delta_ade >= np.percentile(delta_ade, 90)
    hard_gain = hard & top_gain
    med_wind = float(np.median(path_winding))
    hidden_turn = (~turn_loose) & (path_winding >= med_wind)
    goal_low_wp_high = (goal_err < 15.0) & (wp_err >= 45.0)

    rng = np.random.default_rng(args.seed)
    c_match = match_control(hard, turn_strict, rng)
    c_all = np.flatnonzero(~hard)

    features = {
        "wp_bearing_err_deg": wp_err,
        "delta_use_cm": delta_use,
        "goal_bearing_err_deg": goal_err,
        "abs_endpoint_dyaw_deg": abs_dyaw,
        "path_dyaw_t_to_g": path_dyaw_tg,
        "endpoint_lateral_m": lateral,
        "yaw8_deg": np.abs(yaw8),
        "path_winding_8": path_winding,
        "max_step_yaw_deg": max_step,
        "chord_arc_ratio": chord_arc,
        "past_yaw_rate": past_rate,
        "past_winding_3": past_w3,
        "wp_kappa": wp_kappa,
        "turn_strict": turn_strict.astype(np.float64),
        "turn_loose": turn_loose.astype(np.float64),
        "hidden_turn": hidden_turn.astype(np.float64),
        "goal_low_wp_high": goal_low_wp_high.astype(np.float64),
        "spread": spread.astype(np.float64),
    }
    if (orb >= 0).any():
        features["orb_matches"] = orb.astype(np.float64)

    feat_names = list(features.keys())
    rows = enrichment_table(features, feat_names, hard, c_match, "C_match")
    rows += enrichment_table(features, feat_names, hard, c_all, "C_all")

    os.makedirs(args.out_dir, exist_ok=True)
    write_csv(os.path.join(args.out_dir, "enrichment_H_vs_control.csv"), rows)

    # Logistic (optional sklearn)
    logit_out = {}
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        X_cols = [
            "turn_strict",
            "path_winding_8",
            "abs_endpoint_dyaw_deg",
            "past_yaw_rate",
            "goal_bearing_err_deg",
            "chord_arc_ratio",
            "hidden_turn",
        ]
        X = np.column_stack([features[c] for c in X_cols])
        y = hard.astype(np.int32)
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf.fit(Xs, y)
        coefs = {c: float(v) for c, v in zip(X_cols, clf.coef_[0])}
        logit_out = {"intercept": float(clf.intercept_[0]), "coef": coefs, "train_acc": float(clf.score(Xs, y))}
        with open(os.path.join(args.out_dir, "logistic_is_hard.json"), "w", encoding="utf-8") as f:
            json.dump(logit_out, f, indent=2)
    except Exception as e:
        logit_out = {"error": str(e)}

    # Trajectory clustering on H
    h_idx = np.flatnonzero(hard)
    h_items = sorted([(trajs[i], int(ts[i]), i) for i in h_idx])
    runs = []
    run_len = 1
    for j in range(1, len(h_items)):
        if h_items[j][0] == h_items[j - 1][0] and h_items[j][1] - h_items[j - 1][1] <= spacing * 2:
            run_len += 1
        else:
            runs.append(run_len)
            run_len = 1
    runs.append(run_len)
    cluster_stats = {
        "n_hard": int(hard.sum()),
        "n_hard_intersect_top_gain": int(hard_gain.sum()),
        "max_consecutive_same_traj": int(max(runs) if runs else 0),
        "mean_run_len": float(np.mean(runs)) if runs else 0.0,
        "pct_hard_in_turn_strict": float(100 * turn_strict[hard].mean()),
        "pct_hard_hidden_turn": float(100 * hidden_turn[hard].mean()),
        "pct_hard_goal_low_wp_high": float(100 * goal_low_wp_high[hard].mean()),
    }

    # Top 50 manifest within H by delta_ade
    order_h = h_idx[np.argsort(-delta_ade[h_idx], kind="stable")[:50]]
    manifest = []
    for rank, i in enumerate(order_h, 1):
        manifest.append(
            {
                "rank": rank,
                "traj": trajs[i],
                "t": int(ts[i]),
                "goal_time": int(goal_times[i]),
                "wp_err_deg": float(wp_err[i]),
                "goal_err_deg": float(goal_err[i]),
                "delta_use_cm": float(delta_use[i]),
                "turn_strict": int(turn_strict[i]),
                "path_winding_8": float(path_winding[i]),
                "abs_endpoint_dyaw": float(abs_dyaw[i]),
                "past_yaw_rate": float(past_rate[i]),
                "hidden_turn": int(hidden_turn[i]),
            }
        )
    write_csv(os.path.join(args.out_dir, "hard_top50_manifest.csv"), manifest)

    pack = dict(features)
    pack["orb_matches"] = orb.astype(np.float64)
    np.savez_compressed(
        os.path.join(args.out_dir, "hard120_features.npz"),
        hard=hard,
        hard_gain=hard_gain,
        c_match_idx=c_match,
        **pack,
    )

    lines = [
        "=== P1b WP hard120 (wp_err>=45) ===",
        f"n_hard={cluster_stats['n_hard']}  n_H&G_top10%={cluster_stats['n_hard_intersect_top_gain']}",
        f"pct in turn_strict: {cluster_stats['pct_hard_in_turn_strict']:.1f}%",
        f"pct hidden_turn (not loose but high winding): {cluster_stats['pct_hard_hidden_turn']:.1f}%",
        f"pct goal_err<15 & wp>=45: {cluster_stats['pct_hard_goal_low_wp_high']:.1f}%",
        f"max consecutive hard frames same traj: {cluster_stats['max_consecutive_same_traj']}",
        "",
        "--- Enrichment vs C_match (Cohen d, top |d|) ---",
    ]
    sub = [r for r in rows if r["control"] == "C_match"]
    sub.sort(key=lambda r: -abs(r["cohens_d"]) if r["cohens_d"] == r["cohens_d"] else 0)
    for r in sub[:12]:
        lines.append(
            f"  {r['feature']:<28} d={r['cohens_d']:+.2f}  "
            f"med_H={r['median_H']:.2f} med_C={r['median_C']:.2f}"
        )
    if logit_out and "coef" in logit_out:
        lines.append("")
        lines.append("--- Logistic is_hard (std features) ---")
        for k, v in sorted(logit_out["coef"].items(), key=lambda x: -abs(x[1])):
            lines.append(f"  {k}: {v:+.3f}")
    report = "\n".join(lines) + "\n"
    print(report)
    with open(os.path.join(args.out_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(report)
        f.write("\n" + json.dumps(cluster_stats, indent=2) + "\n")
    print(f"Saved under {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()
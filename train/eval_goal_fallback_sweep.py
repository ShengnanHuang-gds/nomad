"""P5b: predict harmful kappa blend without GT wp_err; counterfactual goal vs blend."""
import csv, json, os
import cv2  # noqa: F401
import numpy as np
from scipy.optimize import minimize
from adaptive_blend import angle_between_deg
from eval_testtime import DINO_TEST_PREDICTIONS

ORACLE = "logs/revalidation/oracle_factorial/per_frame.npz"
ATTR = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
WP_CACHE = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/eval_waypoint/locked_per_frame.npz"
OUT = "logs/revalidation/goal_fallback_sweep"
FEATURES = (
    "theta_deg",
    "r_w",
    "log_kw",
    "log_kg",
    "turn_strict",
    "yaw8_deg",
    "spread",
    "turn_loose",
    "endpoint_lateral_m",
)


def load_arrays():
    o, a = np.load(ORACLE), np.load(ATTR)
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    traj = np.load(WP_CACHE)["traj"]
    ade_mask = o["ade_mask"].astype(np.float64)
    ade_b = o["ade_Db_d_blend"].astype(np.float64)
    ade_g = o["ade_Db_dg_pred"].astype(np.float64)
    gk = take("dino_kappa").astype(np.float64)
    wk = a["wp_kappa"].astype(np.float64)
    gd = take("dino_dir").astype(np.float32)
    wd = np.load(WP_CACHE)["wp_dir"].astype(np.float32)
    theta = angle_between_deg(gd, wd).astype(np.float64)
    rw = wk / np.maximum(wk + gk, 1e-6)
    harmful = (ade_b - ade_g) > 0
    wp_err = a["wp_bearing_err_deg"].astype(np.float64)
    X = np.column_stack(
        [
            theta,
            rw,
            np.log1p(wk),
            np.log1p(gk),
            a["turn_strict"].astype(np.float64),
            a["yaw8_deg"].astype(np.float64),
            a["spread"].astype(np.float64),
            a["turn_loose"].astype(np.float64),
            a["endpoint_lateral_m"].astype(np.float64),
        ]
    )
    return ade_mask, ade_b, ade_g, harmful, wp_err, traj, X



KW_GRID = (5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 22.0, 28.0, 35.0, 9999.0)
THETA_GRID = (15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 9999.0)

def rule_kw_theta(wk, theta, tk, tt, mode="and"):
    a, b = wk < tk, theta > tt
    if mode == "and":
        return a & b
    if mode == "kw_only":
        return a
    if mode == "theta_only":
        return b
    raise ValueError(mode)

def sweep_kw_theta(ade_mask, ade_b, ade_g, wk, theta, hard_mask, lam=3.0):
    best, rows = None, []
    for mode in ("and", "kw_only", "theta_only"):
        for tk in KW_GRID:
            for tt in THETA_GRID:
                pick = rule_kw_theta(wk, theta, tk, tt, mode)
                ade = pick_ade(ade_b, ade_g, pick)
                ua = use_cm(ade_mask, ade)
                uh = use_cm(ade_mask[hard_mask], ade[hard_mask]) if hard_mask.any() else float("nan")
                sc = ua + lam * uh
                row = dict(mode=mode, tau_kw=tk, tau_theta=tt, frac_goal=float(pick.mean()), use_all=ua, use_hard=uh, score=sc)
                rows.append(row)
                if best is None or sc > best["score"]:
                    best = row
    return rows, best

def use_cm(ade_mask, ade):
    return 100.0 * (ade_mask - ade).mean()


def pick_ade(ade_b, ade_g, pick_goal):
    return np.where(pick_goal, ade_g, ade_b)


def auc_score(y, p):
    y = y.astype(np.int32)
    order = np.argsort(p)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(p))
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum = ranks[pos].sum()
    return float((rank_sum - n_pos * (n_pos - 1) / 2) / (n_pos * n_neg))


def fit_logistic(X, y, l2=1.0):
    n, d = X.shape
    X1 = np.concatenate([np.ones((n, 1)), X], axis=1)

    def loss(w):
        z = X1 @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        ll = y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12)
        reg = 0.5 * l2 * np.sum(w[1:] ** 2)
        return -ll.sum() + reg

    w0 = np.zeros(d + 1)
    res = minimize(loss, w0, method="L-BFGS-B")
    w = res.x

    def predict_proba(Xt):
        X1t = np.concatenate([np.ones((len(Xt), 1)), Xt], axis=1)
        z = X1t @ w
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    return w, predict_proba


def group_folds(traj, k=5, seed=0):
    uniq = np.array(sorted(set(traj.tolist())))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    folds = []
    for i in range(k):
        folds.append(set(uniq[i::k].tolist()))
    return folds



def main():
    import argparse
    from eval_by_distance import load_config, load_paired_frames
    from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
    from eval_goal_head import make_split_dataset, meters_per_unit
    from eval_position_noise import boot_mean, subset_index
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambda-hard", type=float, default=3.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    ade_mask, ade_b, ade_g, harmful, wp_err, traj, X = load_arrays()
    theta, wk = X[:, 0], np.expm1(X[:, 2])
    tune_rows, best = sweep_kw_theta(ade_mask, ade_b, ade_g, wk, theta, wp_err >= 45.0, args.lambda_hard)
    pick = rule_kw_theta(wk, theta, best["tau_kw"], best["tau_theta"], best["mode"])
    ade_pol = pick_ade(ade_b, ade_g, pick)
    k_u, g_u, p_u = use_cm(ade_mask, ade_b), use_cm(ade_mask, ade_g), use_cm(ade_mask, ade_pol)
    dataset = make_split_dataset(load_config("config/nomad_b40.yaml"), "test")
    sets, _, _ = frame_sets(dataset, load_paired_frames(PAIRED_FRAMES), meters_per_unit(dataset), SPREAD_NPZ)
    hard45 = wp_err >= 45.0
    rng = np.random.default_rng(7)
    lines = ["=== Goal fallback kw/theta ===", str(best), "ALL kappa %+.2f goal %+.2f policy %+.2f" % (k_u, g_u, p_u)]
    for sn in ("all", "turn 0.30m/45deg", "B masked spread"):
        idx = np.flatnonzero(sets[sn])
        u_p = boot_mean(ade_mask[idx] - ade_pol[idx], subset_index(len(idx), 1000, rng))
        lines.append("[%s] policy %+.2f" % (sn, 100 * u_p[0]))
    ih = np.flatnonzero(hard45)
    uk = boot_mean(ade_mask[ih] - ade_b[ih], subset_index(len(ih), 1000, rng))
    ug = boot_mean(ade_mask[ih] - ade_g[ih], subset_index(len(ih), 1000, rng))
    up = boot_mean(ade_mask[ih] - ade_pol[ih], subset_index(len(ih), 1000, rng))
    lines.append("[hard45] kappa %+.2f goal %+.2f policy %+.2f" % (100 * uk[0], 100 * ug[0], 100 * up[0]))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(os.path.join(OUT, "tune_sweep.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tune_rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(tune_rows, key=lambda r: -r["score"]))
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write(text)
    json.dump({"best": best, "locked": {"kappa": k_u, "policy": p_u}}, open(os.path.join(OUT, "best.json"), "w"), indent=2)
    print("Saved", os.path.abspath(OUT))

if __name__ == "__main__":
    main()
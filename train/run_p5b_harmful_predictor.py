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
OUT = "logs/revalidation/p5b_harmful_predictor"
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
    os.makedirs(OUT, exist_ok=True)
    ade_mask, ade_b, ade_g, harmful, wp_err, traj, X = load_arrays()
    n = len(ade_mask)
    folds = group_folds(traj, k=5, seed=42)
    oof_p = np.zeros(n)
    fold_aucs = []

    for fi, test_trajs in enumerate(folds):
        te = np.array([t in test_trajs for t in traj])
        tr = ~te
        mu = X[tr].mean(0)
        sig = X[tr].std(0)
        sig[sig < 1e-6] = 1.0
        Xn = (X - mu) / sig
        w, pred_fn = fit_logistic(Xn[tr], harmful[tr].astype(np.float64), l2=2.0)
        oof_p[te] = pred_fn(Xn[te])
        fold_aucs.append(auc_score(harmful[te], oof_p[te]))

    oof_auc = auc_score(harmful, oof_p)
    baselines = {
        "kappa_blend": use_cm(ade_mask, ade_b),
        "goal_only": use_cm(ade_mask, ade_g),
        "oracle_pick": use_cm(ade_mask, pick_ade(ade_b, ade_g, harmful)),
    }

    sweep = []
    best = None
    for thr in np.linspace(0.05, 0.95, 19):
        pick_g = oof_p >= thr
        u = use_cm(ade_mask, pick_ade(ade_b, ade_g, pick_g))
        frac_goal = pick_g.mean()
        sweep.append({"thr": float(thr), "use_cm": u, "frac_goal": float(frac_goal)})
        if best is None or u > best["use_cm"]:
            best = {"thr": float(thr), "use_cm": u, "frac_goal": float(frac_goal)}

    theta = X[:, 0]
    oof_theta_policy = np.zeros(n, dtype=bool)
    for fi, test_trajs in enumerate(folds):
        te = np.array([t in test_trajs for t in traj])
        tr = ~te
        best_u, best_t = -1e9, None
        for thr in np.linspace(20, 80, 25):
            pick_tr = theta[tr] >= thr
            u_tr = use_cm(ade_mask[tr], pick_ade(ade_b[tr], ade_g[tr], pick_tr))
            if u_tr > best_u:
                best_u, best_t = u_tr, thr
        oof_theta_policy[te] = theta[te] >= best_t

    theta_rule_use = use_cm(ade_mask, pick_ade(ade_b, ade_g, oof_theta_policy))
    theta_rule_frac = float(oof_theta_policy.mean())

    # turn & theta conjunctive rule (OOF per fold)
    turn = X[:, 4] > 0.5
    oof_tt = np.zeros(n, dtype=bool)
    for fi, test_trajs in enumerate(folds):
        te = np.array([t in test_trajs for t in traj])
        tr = ~te
        best_u, best_t = -1e9, 30.0
        for thr in np.linspace(15, 70, 24):
            pick_tr = turn[tr] & (theta[tr] >= thr)
            u_tr = use_cm(ade_mask[tr], pick_ade(ade_b[tr], ade_g[tr], pick_tr))
            if u_tr > best_u:
                best_u, best_t = u_tr, thr
        oof_tt[te] = turn[te] & (theta[te] >= best_t)
    turn_theta_use = use_cm(ade_mask, pick_ade(ade_b, ade_g, oof_tt))

    hard45 = wp_err >= 45
    pick_best = oof_p >= best["thr"]
    hard_stats = {
        "n": int(hard45.sum()),
        "kappa_use": use_cm(ade_mask[hard45], ade_b[hard45]),
        "goal_use": use_cm(ade_mask[hard45], ade_g[hard45]),
        "policy_use": use_cm(ade_mask[hard45], pick_ade(ade_b[hard45], ade_g[hard45], pick_best[hard45])),
        "oracle_use": use_cm(ade_mask[hard45], pick_ade(ade_b[hard45], ade_g[hard45], harmful[hard45])),
    }

    lines = [
        "=== P5b harmful-blend predictor (no GT wp_err in features) ===",
        f"n={n} harmful={int(harmful.sum())} ({100*harmful.mean():.1f}%)",
        f"GroupKFold by traj (5 folds) OOF AUC={oof_auc:.3f} folds={[round(x,3) for x in fold_aucs]}",
        "",
        "Baselines (cm use):",
        f"  kappa blend     {baselines['kappa_blend']:+.2f}",
        f"  goal only       {baselines['goal_only']:+.2f}",
        f"  oracle pick     {baselines['oracle_pick']:+.2f}  (know true harmful)",
        "",
        f"Best OOF logistic thr={best['thr']:.2f} frac_goal={best['frac_goal']:.2f} use={best['use_cm']:+.2f}",
        f"OOF theta>=thr (per-fold tune) frac_goal={theta_rule_frac:.2f} use={theta_rule_use:+.2f}",
        f"OOF turn & theta>=thr (per-fold tune) use={turn_theta_use:+.2f}",
        "",
        "hard45 subset:",
        f"  kappa {hard_stats['kappa_use']:+.2f} goal {hard_stats['goal_use']:+.2f} "
        f"policy {hard_stats['policy_use']:+.2f} oracle {hard_stats['oracle_use']:+.2f}",
        "",
        "Features: " + ", ".join(FEATURES),
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write(text)
    with open(os.path.join(OUT, "threshold_sweep.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in sweep for k in r}))
        w.writeheader()
        w.writerows(sweep)
    meta = {
        "oof_auc": oof_auc,
        "fold_aucs": fold_aucs,
        "baselines": baselines,
        "best_oof": best,
        "theta_rule_use_cm": theta_rule_use,
        "turn_theta_rule_use_cm": turn_theta_use,
        "hard45": hard_stats,
        "features": FEATURES,
    }
    json.dump(meta, open(os.path.join(OUT, "summary.json"), "w"), indent=2)
    np.savez_compressed(
        os.path.join(OUT, "oof.npz"),
        oof_p=oof_p.astype(np.float32),
        harmful=harmful,
        pick_best=pick_best,
        wp_err=wp_err.astype(np.float32),
    )
    print("Saved", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
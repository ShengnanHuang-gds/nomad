"""P5c: OOF learn continuous trust tau (suppress WP kappa); locked rollout eval."""
import csv, json, os
import cv2  # noqa: F401
import numpy as np
import torch
from adaptive_blend import blend_suppress
from adaptive_blend import angle_between_deg
from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, rollout

ORACLE = "logs/revalidation/oracle_factorial/per_frame.npz"
ATTR = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
WP_CACHE = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/eval_waypoint/locked_per_frame.npz"
YAW_CSV = "logs/revalidation/yaw_overlap_analysis/per_frame_yaw_overlap.csv"
OUT = "logs/revalidation/p5c_trust"
GRID_S = np.linspace(0.0, 1.0, 21)


def load_yaw_orb(moments):
    lookup = {}
    if os.path.isfile(YAW_CSV):
        with open(YAW_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("group") != "20-40":
                    continue
                key = (row["traj"], int(row["t"]), int(row["goal_time"]))
                lookup[key] = int(row["orb"]) if row["orb"] != "-1" else 20
    orb = []
    for n, t, goals in moments:
        g = [x[4] for x in goals if x[0] == "20-40"][0]
        orb.append(float(lookup.get((n, t, g), 20.0)))
    return np.asarray(orb, dtype=np.float64)


def load_all():
    o, a = np.load(ORACLE), np.load(ATTR)
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    moments = load_paired_frames(PAIRED_FRAMES)
    traj = np.load(WP_CACHE)["traj"]
    ade_mask = o["ade_mask"].astype(np.float64)
    ade_b = o["ade_Db_d_blend"].astype(np.float64)
    ade_g = o["ade_Db_dg_pred"].astype(np.float64)
    gk = take("dino_kappa").astype(np.float64)
    wk = a["wp_kappa"].astype(np.float64)
    gd = take("dino_dir").astype(np.float32)
    wd = np.load(WP_CACHE)["wp_dir"].astype(np.float32)
    steps = (take("b_dist").astype(np.float64))
    theta = angle_between_deg(gd, wd).astype(np.float64)
    rw = wk / np.maximum(wk + gk, 1e-6)
    wp_err = a["wp_bearing_err_deg"].astype(np.float64)
    orb = load_yaw_orb(moments)
    orb_feat = 1.0 - np.clip(orb / 20.0, 0.0, 1.0)
    X = np.column_stack(
        [
            theta / 90.0,
            rw,
            np.log1p(wk) / 5.0,
            np.log1p(gk) / 5.0,
            a["turn_strict"].astype(np.float64),
            a["yaw8_deg"].astype(np.float64) / 180.0,
            a["spread"].astype(np.float64),
            a["turn_loose"].astype(np.float64),
            a["endpoint_lateral_m"].astype(np.float64),
            orb_feat,
        ]
    )
    names = (
        "theta_n", "r_w", "log_kw_n", "log_kg_n", "turn_strict", "yaw8_n",
        "spread", "turn_loose", "lat_m", "orb_low",
    )
    return dict(
        ade_mask=ade_mask, ade_b=ade_b, ade_g=ade_g, gk=gk, wk=wk, gd=gd, wd=wd,
        steps=steps, traj=traj, wp_err=wp_err, X=X, names=names, moments=moments,
    )


def optimal_s_surrogate(ade_b, ade_g):
    """Per frame s in [0,1]: 0=blend, 1=goal; minimize linear ADE interp."""
    best_s = np.zeros(len(ade_b))
    for s in GRID_S:
        ade = (1.0 - s) * ade_b + s * ade_g
        if s == 0:
            best_ade = ade.copy()
            best_s[:] = 0.0
            continue
        better = ade < best_ade
        best_ade = np.where(better, ade, best_ade)
        best_s = np.where(better, s, best_s)
    return best_s.astype(np.float32)


def group_folds(traj, k=5, seed=42):
    uniq = np.array(sorted(set(traj.tolist())))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    return [set(uniq[i::k].tolist()) for i in range(k)]


def fit_ridge_predict(Xtr, ytr, Xte, lam=1.0):
    mu = Xtr.mean(0)
    sig = Xtr.std(0)
    sig[sig < 1e-6] = 1.0
    A = (Xtr - mu) / sig
    Ate = (Xte - mu) / sig
    n, d = A.shape
    w = np.linalg.solve(A.T @ A + lam * np.eye(d), A.T @ ytr)
    pred = Ate @ w
    return np.clip(pred, 0.0, 1.0), w, mu, sig


def use_cm(mask, ade):
    return 100.0 * (mask - ade).mean()


def main():
    os.makedirs(OUT, exist_ok=True)
    d = load_all()
    n = len(d["ade_mask"])
    s_star = optimal_s_surrogate(d["ade_b"], d["ade_g"])
    folds = group_folds(d["traj"])
    s_hat = np.zeros(n, dtype=np.float32)
    weights = []
    for fi, test_trajs in enumerate(folds):
        te = np.array([t in test_trajs for t in d["traj"]])
        tr = ~te
        pred, w, mu, sig = fit_ridge_predict(d["X"][tr], s_star[tr], d["X"][te], lam=2.0)
        s_hat[te] = pred
        weights.append({"w": w.tolist(), "mu": mu.tolist(), "sig": sig.tolist()})

    # surrogate use on OOF tau
    ade_proxy = (1.0 - s_hat) * d["ade_b"] + s_hat * d["ade_g"]
    sur_use = use_cm(d["ade_mask"], ade_proxy)
    sur_oracle = use_cm(d["ade_mask"], (1.0 - s_star) * d["ade_b"] + s_star * d["ade_g"])

    config_b = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = d["moments"]
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    st = (d["steps"] / meters).astype(np.float32)[:, None]
    pos_tau = (blend_suppress(d["gd"], d["gk"], d["wd"], d["wk"], s_hat) * st).astype(np.float32)
    pos_orc = (blend_suppress(d["gd"], d["gk"], d["wd"], d["wk"], s_star) * st).astype(np.float32)
    pos_k = (blend_suppress(d["gd"], d["gk"], d["wd"], d["wk"], np.zeros(n)) * st).astype(np.float32)
    pos_g = (d["gd"] * st).astype(np.float32)
    # oracle GT wp_err ramp 35-55
    from adaptive_blend import suppress_from_wp_turn
    sup_gt = suppress_from_wp_turn(d["wp_err"], d["X"][:, 4] > 0.5, wp_lo=35, wp_hi=55, turn_weight=0, cap=1)
    pos_gt = (blend_suppress(d["gd"], d["gk"], d["wd"], d["wk"], sup_gt) * st).astype(np.float32)

    pos = {
        "kappa blend": pos_k,
        "goal head (direct)": pos_g,
        "trust OOF ridge": pos_tau,
        "trust surrogate-oracle s*": pos_orc,
        "suppress oracle w35-55": pos_gt,
    }
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_eo, sched_eo = load_model(load_config("config/nomad_e_oracle.yaml"), E_CHECKPOINT, device)
    am, ade = rollout(model_eo, sched_eo, dataset, far, pos, device, 8, 8, 1, "p5c-trust")

    sets, _, _ = frame_sets(dataset, moments, meters, SPREAD_NPZ)
    hard45 = d["wp_err"] >= 45
    rng = np.random.default_rng(0)
    boot = subset_index(n, 1000, rng)
    lines = [
        "=== P5c trust tau (OOF ridge -> blend_suppress) ===",
        f"n={n} mean s_hat={s_hat.mean():.3f} s*_surrogate={s_star.mean():.3f}",
        f"Surrogate use: OOF tau {sur_use:+.2f} cm | oracle s* {sur_oracle:+.2f} cm",
        "",
        "Rollout use_cm [95% CI] all:",
    ]
    results = {}
    for name in pos:
        u = boot_mean(am - ade[name], boot)
        results[name] = {"use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2]}
        lines.append(f"  {name:<28} {100*u[0]:+.2f} [{100*u[1]:+.2f}, {100*u[2]:+.2f}]")
    lines.append("")
    for label, mask in [("hard45", hard45), ("turn", sets["turn 0.30m/45deg"].astype(bool))]:
        idx = np.flatnonzero(mask)
        b2 = subset_index(len(idx), 1000, rng)
        lines.append(f"[{label}] n={len(idx)}")
        for name in ("kappa blend", "trust OOF ridge", "suppress oracle w35-55"):
            u = boot_mean(am[idx] - ade[name][idx], b2)
            lines.append(f"  {name:<28} {100*u[0]:+.2f} [{100*u[1]:+.2f}, {100*u[2]:+.2f}]")
    text = "\n".join(lines) + "\n"
    print(text)
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write(text)
    json.dump({"surrogate": {"oof": sur_use, "oracle_s": sur_oracle}, "rollout": results, "weights": weights},
              open(os.path.join(OUT, "summary.json"), "w"), indent=2)
    np.savez_compressed(os.path.join(OUT, "tau.npz"), s_hat=s_hat, s_star=s_star, wp_err=d["wp_err"])
    print("Saved", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
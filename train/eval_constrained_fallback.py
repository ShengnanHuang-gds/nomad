"""Goal fallback with constraint: policy use_all must beat kappa blend."""
import csv
import json
import os

import cv2  # noqa: F401
import numpy as np
from eval_goal_fallback_sweep import (
    KW_GRID,
    THETA_GRID,
    load_arrays,
    pick_ade,
    rule_kw_theta,
    sweep_kw_theta,
    use_cm,
)

OUT = "logs/revalidation/afternoon_2026_10_26/constrained_fallback"


def sweep_constrained(ade_mask, ade_b, ade_g, wk, theta, hard_mask, k_u, margin=0.0):
    best_feasible = None
    rows = []
    for mode in ("and", "kw_only", "theta_only"):
        for tk in KW_GRID:
            for tt in THETA_GRID:
                pick = rule_kw_theta(wk, theta, tk, tt, mode)
                ade = pick_ade(ade_b, ade_g, pick)
                ua = use_cm(ade_mask, ade)
                uh = use_cm(ade_mask[hard_mask], ade[hard_mask]) if hard_mask.any() else float("nan")
                feasible = ua >= k_u - margin
                row = {
                    "mode": mode,
                    "tau_kw": tk,
                    "tau_theta": tt,
                    "frac_goal": float(pick.mean()),
                    "use_all": ua,
                    "use_hard": uh,
                    "feasible": bool(feasible),
                }
                rows.append(row)
                if feasible and (best_feasible is None or ua > best_feasible["use_all"]):
                    best_feasible = row
    return rows, best_feasible


def main():
    os.makedirs(OUT, exist_ok=True)
    ade_mask, ade_b, ade_g, harmful, wp_err, traj, X = load_arrays()
    theta, wk = X[:, 0], np.expm1(X[:, 2])
    hard = wp_err >= 45.0
    k_u = use_cm(ade_mask, ade_b)
    g_u = use_cm(ade_mask, ade_g)
    _, best_uncon = sweep_kw_theta(ade_mask, ade_b, ade_g, wk, theta, hard, lam=3.0)
    rows, best = sweep_constrained(ade_mask, ade_b, ade_g, wk, theta, hard, k_u, margin=0.02)
    lines = [
        "=== Constrained goal fallback (use_all >= kappa - 0.02) ===",
        "kappa %.2f goal %.2f" % (k_u, g_u),
        "unconstrained best: %s" % best_uncon,
        "feasible best: %s" % best,
    ]
    if best:
        pick = rule_kw_theta(wk, theta, best["tau_kw"], best["tau_theta"], best["mode"])
        lines.append("feasible policy use_all %.2f hard %.2f frac_goal %.2f" % (
            best["use_all"], best["use_hard"], best["frac_goal"]))
    else:
        lines.append("No feasible policy; keep kappa blend.")
    text = "\n".join(lines) + "\n"
    print(text)
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write(text)
    with open(os.path.join(OUT, "sweep.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json.dump({"kappa": k_u, "unconstrained": best_uncon, "feasible": best}, open(os.path.join(OUT, "best.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
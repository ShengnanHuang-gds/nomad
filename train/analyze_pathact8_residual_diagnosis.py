"""Post-process full1000 residual_export.npz: independent ADE checks + diagnosis tables.



Does not modify eval/train. Run after export_pathact8_residual.py.

"""

import argparse

import csv

import json

import os

from datetime import datetime, timezone



import numpy as np

from scipy import stats



AUDIT_NPZ = "logs/revalidation/eval_audit_pathact8_far/per_frame.npz"

SMOKE_META = "logs/revalidation/pathact8_residual_export/smoke20/meta.json"





def ade_from_samples(pred_s_h_2, gt_h_2, meters):

    """pred [S,H,2], gt [H,2] dataset units -> per-sample ADE meters [S]."""

    dist = np.linalg.norm((pred_s_h_2 - gt_h_2[None]) * meters, axis=-1)

    return dist.mean(axis=1)





def frame_ade_mean_ade_fde(pred_s_h_2, gt_h_2, meters):

    ades = ade_from_samples(pred_s_h_2, gt_h_2, meters)

    return float(ades.mean())





def dist_n_s_k(pred, gt, meters):
    """pred [N,S,H,2], gt [N,H,2] -> [N,S,H] meters."""
    return np.linalg.norm((pred - gt[:, None, :, :]) * meters, axis=-1)





def bootstrap_ci(values, n_boot=2000, seed=1):

    rng = np.random.default_rng(seed)

    v = np.asarray(values, dtype=np.float64)

    if v.size < 3:

        return float("nan"), float("nan"), float("nan")

    boots = rng.choice(v, size=(n_boot, v.size), replace=True).mean(axis=1)

    return float(v.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))





def corr_bootstrap(x, y, n_boot=2000, seed=2):

    x = np.asarray(x, dtype=np.float64)

    y = np.asarray(y, dtype=np.float64)

    mask = np.isfinite(x) & np.isfinite(y)

    x, y = x[mask], y[mask]

    if len(x) < 5:

        return {}

    pear = float(np.corrcoef(x, y)[0, 1])

    spear = float(stats.spearmanr(x, y).correlation)

    rng = np.random.default_rng(seed)

    n = len(x)

    p_boot, s_boot = [], []

    for _ in range(n_boot):

        idx = rng.integers(0, n, size=n)

        if np.std(x[idx]) < 1e-12 or np.std(y[idx]) < 1e-12:

            continue

        p_boot.append(np.corrcoef(x[idx], y[idx])[0, 1])

        s_boot.append(stats.spearmanr(x[idx], y[idx]).correlation)

    p_lo, p_hi = np.quantile(p_boot, [0.025, 0.975]) if p_boot else (np.nan, np.nan)

    s_lo, s_hi = np.quantile(s_boot, [0.025, 0.975]) if s_boot else (np.nan, np.nan)

    return {

        "pearson_r": pear,

        "pearson_ci95_lo": float(p_lo),

        "pearson_ci95_hi": float(p_hi),

        "spearman_r": spear,

        "spearman_ci95_lo": float(s_lo),

        "spearman_ci95_hi": float(s_hi),

        "n": int(n),

    }





def scene_bucket(strict_turn, loose_turn):

    st = bool(strict_turn)

    lo = bool(loose_turn)

    if st:

        return "strict_turn"

    if not lo:

        return "strict_straight"

    return "middle"





def verify_npz(d, meta_path):

    report = {"ok": True, "items": []}

    n = d["gt_actions"].shape[0]

    m = float(d["meters_per_unit"])

    S, H = d["nav_pred_samples"].shape[1:3]



    def add(name, ok, detail):

        report["items"].append({"name": name, "ok": bool(ok), "detail": detail})

        if not ok:

            report["ok"] = False



    add("n_frames", n == 1000, f"n={n}")

    add("horizon", H == 8, f"H={H}")

    add("num_samples", S == 8, f"S={S}")

    add("finite_nav", np.isfinite(d["nav_pred_samples"]).all(), "nav finite")

    add("finite_gt", np.isfinite(d["gt_actions"]).all(), "gt finite")

    add("finite_path", np.isfinite(d["path_cond"]).all(), "path_cond finite")



    max_d = 0.0

    for i in range(min(n, 100)):

        got = frame_ade_mean_ade_fde(d["nav_pred_samples"][i], d["gt_actions"][i], m)

        saved = float(d["ade_edino_m"][i])

        max_d = max(max_d, abs(got - saved))

    for i in range(n):

        got = frame_ade_mean_ade_fde(d["nav_pred_samples"][i], d["gt_actions"][i], m)

        saved = float(d["ade_edino_m"][i])

        max_d = max(max_d, abs(got - saved))

    add("ade_recompute", max_d < 1e-5, f"max |recompute - ade_edino_m| = {max_d:.2e} m")



    dist = dist_n_s_k(d["nav_pred_samples"], d["gt_actions"], m)

    via_sk = float(dist.mean(axis=(1, 2)).mean())

    via_ks = float(dist.mean(axis=2).mean(axis=1).mean())

    mean_saved = float(d["ade_edino_m"].mean())

    add(

        "mean_s_mean_k",

        abs(via_sk - mean_saved) < 1e-5 and abs(via_ks - mean_saved) < 1e-5,

        f"mean_s(mean_k dist)={via_sk:.6f} mean_k(mean_s dist)={via_ks:.6f} saved_mean={mean_saved:.6f}",

    )



    per_step_mean = dist.mean(axis=(0, 1))

    overall_from_steps = float(per_step_mean.mean())

    add(

        "per_step_then_mean",

        abs(overall_from_steps - mean_saved) < 1e-5,

        f"mean_k(per_step_mean_s)={overall_from_steps:.6f}",

    )



    if os.path.isfile(meta_path):

        with open(meta_path, encoding="utf-8") as f:

            meta = json.load(f)

        files = meta.get("files", {})

        if os.path.isfile(SMOKE_META):

            with open(SMOKE_META, encoding="utf-8") as f:

                smoke = json.load(f)

            for key in ("pathact8_ckpt", "wp_head"):

                a = files.get(key, {}).get("sha256")

                b = smoke.get("files", {}).get(key, {}).get("sha256")

                add(f"hash_{key}", a == b, f"full={a} smoke={b}")



    rebuilt = np.concatenate(

        [d["mu_units"], d["path_cond"].reshape(n, -1)], axis=1

    )

    add(

        "e_dino_pos_rebuild",

        np.max(np.abs(rebuilt - d["e_dino_pos"])) < 1e-5,

        "mu+path_cond matches e_dino_pos",

    )

    gt_flat = d["gt_actions"].reshape(n, -1)

    path_flat = d["path_cond"].reshape(n, -1)

    add(

        "path_cond_not_copy_gt",

        not np.allclose(path_flat, gt_flat, atol=1e-4),

        f"mean L2(path_cond, gt) dataset units = {np.linalg.norm(path_flat-gt_flat,axis=1).mean():.4f}",

    )

    return report





def path_head_ade_cm(path_cond, gt, meters):

    k = min(path_cond.shape[1], gt.shape[1])

    return np.linalg.norm(path_cond[:, :k] - gt[:, :k], axis=-1).mean(axis=1) * meters * 100





def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(

        "--export-dir",

        default="logs/revalidation/pathact8_residual_export/full1000",

    )

    parser.add_argument("--smoke-meta", default=SMOKE_META)

    args = parser.parse_args()



    npz_path = os.path.join(args.export_dir, "residual_export.npz")

    meta_path = os.path.join(args.export_dir, "meta.json")

    d = dict(np.load(npz_path, allow_pickle=True))
    meta = {}
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

    meters = float(d["meters_per_unit"])

    n = d["gt_actions"].shape[0]

    nav = d["nav_pred_samples"]

    gt = d["gt_actions"]

    path_cond = d["path_cond"]



    verify = verify_npz(d, meta_path)



    dist = dist_n_s_k(nav, gt, meters)

    per_step_nav_cm = dist.mean(axis=0).mean(axis=1) * 100

    path_dist_k = np.linalg.norm((path_cond - gt) * meters, axis=-1)

    per_step_path_cm = path_dist_k.mean(axis=0) * 100



    rows_step = []

    for k in range(8):

        nav_k = dist[:, :, k].mean() * 100

        path_k = path_dist_k[:, k].mean() * 100

        rows_step.append(

            {

                "step": k + 1,

                "nav_mean_cm": nav_k,

                "nav_median_cm": float(np.median(dist[:, :, k]) * 100),

                "nav_p90_cm": float(np.quantile(dist[:, :, k], 0.9) * 100),

                "path_head_mean_cm": path_k,

                "path_head_median_cm": float(np.median(path_dist_k[:, k]) * 100),

                "path_head_p90_cm": float(np.quantile(path_dist_k[:, k], 0.9) * 100),

            }

        )



    step_means_cm = dist.mean(axis=(0, 1)) * 100
    first4_nav = float(step_means_cm[:4].mean())
    last4_nav = float(step_means_cm[4:].mean())
    total_nav = float(step_means_cm.mean())
    last4_share = float(step_means_cm[4:].sum() / max(step_means_cm.sum(), 1e-9))



    per_step_csv = os.path.join(args.export_dir, "per_step_stats.csv")

    with open(per_step_csv, "w", newline="", encoding="utf-8") as f:

        w = csv.DictWriter(f, fieldnames=list(rows_step[0].keys()))

        w.writeheader()

        w.writerows(rows_step)

        f.write(

            f"\n# summary,first4_nav_mean_cm,{first4_nav:.4f},last4_nav_mean_cm,{last4_nav:.4f},"

            f"last4_share_of_total,{last4_share:.4f}\n"

        )



    path_ade = path_head_ade_cm(path_cond, gt, meters)

    nav_ade_cm = d["ade_edino_m"] * 100

    path_last4 = path_dist_k[:, 4:].mean(axis=1) * 100



    corr_rows = []

    for label, x in (

        ("path_head_full8_vs_nav_ade", path_ade),

        ("path_head_last4_vs_nav_ade", path_last4),

    ):

        row = {"pair": label}

        row.update(corr_bootstrap(x, nav_ade_cm))

        corr_rows.append(row)



    traj_names = np.array([str(x) for x in d["traj_name"]])

    unique_traj = sorted(set(traj_names.tolist()))

    loo_rows = []

    for tname in unique_traj:

        mask = traj_names != tname

        if mask.sum() < 10:

            continue

        c = corr_bootstrap(path_ade[mask], nav_ade_cm[mask], n_boot=1000, seed=3)

        loo_rows.append({"left_out_traj": tname, **c})

    if loo_rows:

        pear_loo = [r["pearson_r"] for r in loo_rows if np.isfinite(r.get("pearson_r", np.nan))]

        corr_rows.append(

            {

                "pair": "loo_traj_path8_vs_nav (summary)",

                "pearson_r": float(np.mean(pear_loo)) if pear_loo else float("nan"),

                "pearson_ci95_lo": float(np.min(pear_loo)) if pear_loo else float("nan"),

                "pearson_ci95_hi": float(np.max(pear_loo)) if pear_loo else float("nan"),

                "spearman_r": float("nan"),

                "spearman_ci95_lo": float("nan"),

                "spearman_ci95_hi": float("nan"),

                "n": len(unique_traj),

            }

        )



    corr_csv = os.path.join(args.export_dir, "correlations.csv")

    with open(corr_csv, "w", newline="", encoding="utf-8") as f:

        w = csv.DictWriter(f, fieldnames=list(corr_rows[0].keys()))

        w.writeheader()

        w.writerows(corr_rows)



    strict = d["strict_turn"].astype(bool)

    loose = d["loose_turn"].astype(bool)

    buckets = {"strict_turn": strict, "strict_straight": ~loose, "middle": loose & ~strict}



    ade_sum = float(nav_ade_cm.sum())

    order = np.argsort(-nav_ade_cm)

    tail_frac = {}

    for pct in (1, 5, 10, 20):

        k = max(1, int(round(n * pct / 100)))

        tail_frac[pct] = float(nav_ade_cm[order[:k]].sum() / ade_sum)



    traj_contrib = {}

    for tname in unique_traj:

        m = traj_names == tname

        traj_contrib[tname] = float(nav_ade_cm[m].sum())

    top_traj = sorted(traj_contrib.items(), key=lambda x: -x[1])[:10]



    cum_gt = np.zeros((n, 8, 2), dtype=np.float64)

    for k in range(8):

        cum_gt[:, k] = gt[:, : k + 1].sum(axis=1)

    cum_pred = np.zeros_like(cum_gt)

    for k in range(8):

        cum_pred[:, k] = nav.mean(axis=1)[:, : k + 1].sum(axis=1)

    radial_gt = np.linalg.norm(cum_gt * meters, axis=-1)

    radial_err = np.linalg.norm((cum_pred - cum_gt) * meters, axis=-1)

    step_inc = np.diff(radial_err, axis=1, prepend=radial_err[:, :1])

    corr_radial, _ = stats.pearsonr(radial_gt[:, -1], radial_err[:, -1])



    old_mean = float("nan")

    if os.path.isfile(AUDIT_NPZ):

        audit = np.load(AUDIT_NPZ)

        old_mean = float(audit["ade_E-dino"].mean() * 100)



    new_mean = float(nav_ade_cm.mean())

    smoke20_mean = 20.05

    smoke20_path = 17.90

    smoke20_r = 0.918



    full_r = corr_rows[0].get("pearson_r", float("nan"))

    full_path_mean = float(path_ade.mean())



    md = []

    md.append("# pathact8 full1000 residual diagnosis\n")

    md.append(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}\n")

    md.append("## Verification (independent from checks.json)\n")

    md.append(f"- verify_ok: **{verify['ok']}**\n")

    for it in verify["items"]:

        md.append(f"- [{('PASS' if it['ok'] else 'FAIL')}] {it['name']}: {it['detail']}\n")



    md.append("\n## ADE: new export vs audit (code fact)\n")

    md.append(f"- Audit `per_frame.npz` E-dino mean: **{old_mean:.2f} cm** (seed/noise from original eval run).\n")

    md.append(f"- This export mean ADE: **{new_mean:.2f} cm** (seed={d.get('seed', meta.get('args', {}).get('seed') if os.path.isfile(meta_path) else '?')}).\n")

    if os.path.isfile(meta_path):

        with open(meta_path, encoding="utf-8") as f:

            meta = json.load(f)

        md.append(f"- Export meta seed/num_samples: {meta.get('seed')}, {meta.get('num_samples')}\n")

    md.append("- Difference does not imply model change; diffusion noise is resampled unless seed and pipeline match exactly.\n")



    md.append("\n## A. 20-frame phenomena supported at n=1000?\n")

    sup = []

    not_sup = []

    if np.isfinite(full_r) and full_r > 0.5:

        sup.append(f"Path-head full8 vs nav ADE correlation remains positive (Pearson r={full_r:.3f}).")

    else:

        not_sup.append("Strong path–nav correlation from smoke20 (r≈0.92) did not persist at full scale.")

    if abs(full_path_mean - new_mean) / new_mean < 0.15:

        sup.append(f"Path-head mean error ({full_path_mean:.2f} cm) same order as nav ADE ({new_mean:.2f} cm).")

    if tail_frac[10] > 0.25:

        sup.append(f"Tail concentration: worst 10% frames contribute {100*tail_frac[10]:.1f}% of summed frame ADE.")

    if smoke20_mean and abs(new_mean - 17.75) > 1.0:

        not_sup.append("Smoke20 nav ADE (20.05 cm) and subsample of 7 trajectories cannot be compared to full1000 or 17.75 cm headline.")



    md.append("**Supported (statistical):**\n")

    for s in sup:

        md.append(f"- {s}\n")

    md.append("\n**Not supported / not testable from smoke alone:**\n")

    for s in not_sup:

        md.append(f"- {s}\n")



    md.append("\n## B. Not supported\n")

    md.append("- Claim that resampled export must reproduce 17.75 cm exactly.\n")

    md.append("- Using nav last-4 vs nav ADE correlation as independent mechanism proof (last-4 is part of ADE).\n")



    md.append("\n## C. Best-supported bottleneck (inference)\n")

    if full_r > 0.6 and abs(full_path_mean - new_mean) < 3:

        md.append(

            "- **Path-conditioned nav error co-moves with path-head error** across frames; "

            "when path is wrong, deploy nav tends to worsen. This fits **path quality on hard frames** "

            "and/or **UNet following the given path**, but correlation alone is not causal.\n"

        )

    else:

        md.append(

            "- **Utilization / conditioning** may dominate if path–nav coupling weakens at n=1000; "

            "needs cross-check with 2×2 oracle bundle (not re-run here).\n"

        )



    md.append("\n## D. Still uncertain\n")

    md.append("- Fraction of gap from UNet under-using path vs faithfully tracking bad path (needs fidelity metrics, not in this script).\n")

    md.append("- Whether step-error growth is geometric accumulation vs radial amplification (radial GT vs err correlation at step 8: "

                f"Pearson {corr_radial:.3f} — descriptive only).\n")

    md.append("- Pure 2D far baselines without missing checkpoints.\n")



    md.append("\n## E. One change worth validating (no training this round)\n")

    md.append("- **GT path noise sweep** on frozen checkpoint (eval probe only): map path RMSE → nav ADE without oracle PG numbers.\n")



    md.append("\n## Scene strata (mean nav ADE cm)\n")

    for name, mask in buckets.items():

        if mask.sum() == 0:

            continue

        md.append(f"- {name}: n={int(mask.sum())}, mean={nav_ade_cm[mask].mean():.2f}, path_head={path_ade[mask].mean():.2f}\n")



    md.append("\n## Tail dominance (sum of frame ADE cm)\n")

    for pct, frac in tail_frac.items():

        md.append(f"- Worst {pct}%: {100*frac:.1f}% of total\n")

    md.append("\n## Top trajectories by summed frame ADE (not independent samples)\n")

    for tname, val in top_traj:

        cnt = int((traj_names == tname).sum())

        md.append(f"- {tname}: sum_ADE={val:.1f} cm over {cnt} frames\n")



    md.append("\n## Leave-one-trajectory-out correlation (path8 vs nav)\n")

    md.append(f"- Trajectories: {len(unique_traj)}; mean LOO Pearson r={np.mean(pear_loo) if pear_loo else float('nan'):.3f}\n")



    diag_path = os.path.join(args.export_dir, "diagnosis.md")

    with open(diag_path, "w", encoding="utf-8") as f:

        f.writelines(md)



    out_verify = os.path.join(args.export_dir, "verify_independent.json")

    with open(out_verify, "w", encoding="utf-8") as f:

        json.dump(verify, f, indent=2)



    print(f"Wrote {per_step_csv}, {corr_csv}, {diag_path}")

    print(f"verify_ok={verify['ok']} new_mean_ade_cm={new_mean:.2f} audit_mean_cm={old_mean:.2f}")





if __name__ == "__main__":

    main()


"""Hard-frame ablation: goal-only vs kappa blend vs oracle factorial (locked 1000)."""
import os
import numpy as np
from eval_position_noise import boot_mean
ORACLE = "logs/revalidation/oracle_factorial/per_frame.npz"
ATTR = "logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
OUT = "logs/revalidation/wp_hard_blend_ablation/summary.txt"
def main():
    o = np.load(ORACLE)
    a = np.load(ATTR)
    am = o["ade_mask"].astype(np.float64)
    wp_err = a["wp_bearing_err_deg"].astype(np.float64)
    wp_k = a["wp_kappa"].astype(np.float64)
    goal_err = a["goal_bearing_err_deg"].astype(np.float64)
    turn = a["turn_strict"].astype(bool)
    conds = {"goal_only": "ade_Db_dg_pred", "kappa_blend": "ade_Db_d_blend", "oracle_PG": "ade_Db_blend_dgp_dwGT", "oracle_GP": "ade_Db_blend_dgGT_dwp"}
    use_map = {k: 100.0 * (am - o[v].astype(np.float64)) for k, v in conds.items()}
    gain_kg = use_map["kappa_blend"] - use_map["goal_only"]
    masks = {"all": np.ones(len(am), bool), "hard_wp45": wp_err >= 45, "easy_wp15": wp_err < 15, "mid_wp30_45": (wp_err >= 30) & (wp_err < 45), "turn_strict": turn, "hard_and_turn": (wp_err >= 45) & turn, "goal_ok_wp_bad": (goal_err < 15) & (wp_err >= 45)}
    rng = np.random.default_rng(42)
    boot = 2000
    lines = ["=== Locked far: WP error vs fusion (oracle factorial, e60 WP cache) ===", ""]
    for mname, m in masks.items():
        idx = np.flatnonzero(m)
        if len(idx) < 5: continue
        lines.append(f"[{mname}] n={len(idx)} | median wp_err={np.median(wp_err[idx]):.1f} deg | median wp_kappa={np.median(wp_k[idx]):.1f}")
        for label in conds:
            b = boot_mean(use_map[label][idx], boot, rng)
            lines.append(f"  {label:<14} use {b[0]:+.2f} [{b[1]:+.2f}, {b[2]:+.2f}] cm")
        d = boot_mean(gain_kg[idx], boot, rng)
        lines.append(f"  kappa - goal_only     {d[0]:+.2f} [{d[1]:+.2f}, {d[2]:+.2f}] cm")
        pg_minus_k = boot_mean(use_map["oracle_PG"][idx] - use_map["kappa_blend"][idx], boot, rng)
        lines.append(f"  oracle_PG - kappa      {pg_minus_k[0]:+.2f} [{pg_minus_k[1]:+.2f}, {pg_minus_k[2]:+.2f}] cm (GT wp dir)")
        pp_pg = 100.0 * (o["ade_Db_d_blend"][idx] - o["ade_Db_blend_dgp_dwGT"][idx]).astype(np.float64)
        lines.append(f"  PP-PG use (PG wins if +) {boot_mean(pp_pg, boot, rng)[0]:+.2f} cm")
        lines.append("")
    hard = wp_err >= 45
    lines.append("--- Hard frame-level (wp_err>=45) ---")
    lines.append(f"kappa > goal_only: {(gain_kg[hard] > 0).mean()*100:.1f}% frames (mean delta {gain_kg[hard].mean():+.2f} cm)")
    lines.append(f"oracle_PG > kappa: {(use_map['oracle_PG'][hard] > use_map['kappa_blend'][hard]).mean()*100:.1f}% frames")
    pos = np.maximum(gain_kg, 0.0)
    lines.append(f"Share of positive (kappa-goal) gain on hard: {100*pos[hard].sum()/max(pos.sum(),1e-9):.1f}%")
    text = "\n".join(lines)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    print(text)
if __name__ == "__main__": main()

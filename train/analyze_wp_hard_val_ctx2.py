"""Lock Val-far large WP error frames (ctx2)."""
import csv, json, os, pickle
import numpy as np
import torch
from eval_by_distance import load_config
from eval_frame_sets import endpoint_lateral_m, turning_mask, yaw_change_deg, TURN_STRICT
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_testtime import angle_err
from eval_waypoint_head import head_predict
from train_e_dino import load_dino_head
from train_goal_dir import FAR_STEPS
from train_goal_dino import DFT_VAL_LIST, build_pairs, draw, load_cache
from analyze_wp_hard120 import path_kinematics

VAL_SEED, CTX = 1234, 2
CKPT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
OUT_DIR = "logs/revalidation/wp_hard_val_ctx2"

def pct(n, d):
    return 100.0 * n / d if d else float("nan")

def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config("config/nomad_b40.yaml")
    cache_dir = "logs/dino_cache/dinov2_vits14_reg"
    _, rows, _ = load_cache(cache_dir, "train")
    row_to_key = {int(v): k for k, v in rows.items()}
    with open(DFT_VAL_LIST) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    dataset = make_split_dataset(config, "train")
    spacing = int(config["datasets"]["go_stanford"].get("waypoint_spacing", 1))
    len_pred = int(config["len_traj_pred"])
    meters = meters_per_unit(dataset)
    val_pairs = build_pairs(config, "train", rows, lambda t: t in val_trajs, 0.3, max(2, CTX), "endpoint")
    chosen = draw(val_pairs, np.random.default_rng(VAL_SEED))
    chosen = chosen[val_pairs["steps"][chosen] >= FAR_STEPS]
    n = len(chosen)
    turn_gt = np.zeros(n, dtype=bool)
    items, meta = [], []
    for i, j in enumerate(chosen):
        traj, curr = row_to_key[int(val_pairs["curr"][j])]
        _, goal_t = row_to_key[int(val_pairs["goal"][j])]
        lat = endpoint_lateral_m(dataset, traj, int(curr), meters)
        yaw = yaw_change_deg(dataset, traj, int(curr))
        turn_gt[i] = turning_mask(np.array([lat]), np.array([yaw]), TURN_STRICT)[0]
        items.append((traj, int(curr), int(goal_t)))
        meta.append({"traj": traj, "t": int(curr), "goal_t": int(goal_t), "far_steps": int(val_pairs["steps"][j])})
    feats = np.load(os.path.join(cache_dir, "train", "features.npy"), mmap_mode="r")
    target = val_pairs["target"][chosen]
    head, _ = load_dino_head(CKPT, device)
    wp, _ = head_predict(head, items, rows, feats, device, batch_size=128)
    wp_err = angle_err(wp, target).astype(np.float64)
    cache = {}
    pw, mstep, prate = np.zeros(n), np.zeros(n), np.zeros(n)
    for i, (traj, t, g) in enumerate(items):
        if traj not in cache:
            with open(os.path.join(dataset.data_folder, traj, "traj_data.pkl"), "rb") as f:
                cache[traj] = pickle.load(f)
        kin = path_kinematics(cache[traj], t, g, spacing, len_pred)
        pw[i], mstep[i], prate[i] = kin["path_winding_8"], kin["max_step_yaw_deg"], kin["past_yaw_rate"]
    hard45, hard30 = wp_err >= 45.0, wp_err >= 30.0
    q66w, q66s, q66p = np.percentile(pw, 66.667), np.percentile(mstep, 66.667), np.percentile(prate, 66.667)
    acute_any = (pw >= q66w) | (mstep >= q66s) | (prate >= q66p)
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = {
        "n_far": n,
        "pct_turn_strict": pct(int(turn_gt.sum()), n),
        "n_hard45": int(hard45.sum()),
        "pct_hard45_of_far": pct(int(hard45.sum()), n),
        "pct_hard45_within_turn": pct(int((hard45 & turn_gt).sum()), int(turn_gt.sum())),
        "pct_hard45_within_nonturn": pct(int((hard45 & ~turn_gt).sum()), int((~turn_gt).sum())),
        "pct_turn_given_hard45": pct(int((hard45 & turn_gt).sum()), int(hard45.sum())),
        "n_hard30": int(hard30.sum()),
        "pct_hard30_of_far": pct(int(hard30.sum()), n),
        "pct_hard45_also_acute_any": pct(int((hard45 & acute_any).sum()), int(hard45.sum())),
        "pct_turn_strict_also_hard45": pct(int((hard45 & turn_gt).sum()), int(turn_gt.sum())),
    }
    tiers = []
    for lo, hi, name in [(0,15,"0_15"),(15,30,"15_30"),(30,45,"30_45"),(45,90,"45_90"),(90,999,"ge_90")]:
        m = (wp_err >= lo) & (wp_err < hi)
        tiers.append({"tier": name, "n": int(m.sum()), "pct_far": pct(int(m.sum()), n),
                      "pct_turn": pct(int((m & turn_gt).sum()), int(m.sum()) or 1),
                      "pct_acute_any": pct(int((m & acute_any).sum()), int(m.sum()) or 1)})
    with open(os.path.join(OUT_DIR, "hard45_frames.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["traj","t","goal_t","far_steps","wp_err_deg","turn_strict","path_winding_8","max_step_yaw_deg","past_yaw_rate","acute_any_p66"])
        w.writeheader()
        for i in np.flatnonzero(hard45):
            w.writerow({**meta[i], "wp_err_deg": float(wp_err[i]), "turn_strict": int(turn_gt[i]),
                "path_winding_8": float(pw[i]), "max_step_yaw_deg": float(mstep[i]), "past_yaw_rate": float(prate[i]), "acute_any_p66": int(acute_any[i])})
    np.savez(os.path.join(OUT_DIR, "val_far_ctx2_per_frame.npz"), wp_err_deg=wp_err, turn_strict=turn_gt,
             hard45=hard45, hard30=hard30, path_winding_8=pw, max_step_yaw_deg=mstep, past_yaw_rate=prate, acute_any_p66=acute_any, chosen_idx=chosen)
    lines = [
        "=== Val far: lock large WP error (ctx2) ===",
        f"n_far={n}  turn_strict={summary['pct_turn_strict']:.1f}% of far",
        "",
        "LOCK set: wp_err >= 45 deg",
        f"  n={summary['n_hard45']} = {summary['pct_hard45_of_far']:.2f}% of ALL far  (~P1b 12% on locked)",
        f"  among turn_strict only: {summary['pct_hard45_within_turn']:.2f}% frames are hard45",
        f"  among non_turn: {summary['pct_hard45_within_nonturn']:.2f}%",
        f"  of hard45: {summary['pct_turn_given_hard45']:.1f}% are turn_strict (rest straight-label)",
        "",
        "Compare to turn_strict (~54% of far): weighting ALL turns != weighting hard45",
        f"  Jaccard-like: both hard45 & turn: {int((hard45&turn_gt).sum())} frames",
        "",
        "Softer pool wp>=30: n=%d (%.2f%% far)" % (summary["n_hard30"], summary["pct_hard30_of_far"]),
        f"hard45 that are also acute_any(p66): {summary['pct_hard45_also_acute_any']:.1f}%",
        "",
        "Error tiers (pct_turn = within tier):",
    ]
    for t in tiers:
        lines.append(f"  {t['tier']}: n={t['n']} ({t['pct_far']:.1f}% far) turn={t['pct_turn']:.1f}% acute_any={t['pct_acute_any']:.1f}%")
    lines += ["", "Files: hard45_frames.csv, val_far_ctx2_per_frame.npz, summary.json"]
    with open(os.path.join(OUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({**summary, "tiers": tiers, "ckpt": CKPT}, f, indent=2)
    with open(os.path.join(OUT_DIR, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
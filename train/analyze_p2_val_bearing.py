"""P3a/P3b: Val WP bearing vs endpoint on far goals."""
import argparse, csv, os
import numpy as np
import torch
from eval_by_distance import load_config
from eval_frame_sets import TURN_STRICT, endpoint_lateral_m, turning_mask, yaw_change_deg
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_testtime import angle_err
from eval_waypoint_head import head_predict
from train_e_dino import load_dino_head
from train_goal_dir import FAR_STEPS
from train_goal_dino import DFT_VAL_LIST, build_pairs, draw, load_cache
RUNS = {"e60": ("logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth", 0), "ctx0": ("logs/nomad_d/nomad_dino_wp_hist_ctx0_ctrl_2026_10_24_22_11_12/dino_dir_best.pth", 0), "ctx2": ("logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth", 2)}
OUT_DIR = "logs/revalidation/p2_val_bearing"
VAL_SEED = 1234
def cluster_bootstrap(values, traj_ids, stat, n_boot=2000, seed=0):
    values = np.asarray(values, dtype=np.float64); traj_ids = np.asarray(traj_ids); uniq = np.unique(traj_ids)
    by_traj = {t: values[traj_ids == t] for t in uniq}; rng = np.random.default_rng(seed); boots = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, len(uniq), replace=True); sample = np.concatenate([by_traj[t] for t in pick]); boots.append(stat(sample))
    boots = np.sort(boots); lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]; return float(stat(values)), float(lo), float(hi)
def summarize(errors):
    errors = np.asarray(errors, dtype=np.float64)
    if len(errors) == 0: return {"n": 0, "median": float("nan"), "p90": float("nan"), "p95": float("nan"), "gt45_pct": float("nan"), "mean": float("nan")}
    return {"n": len(errors), "median": float(np.median(errors)), "p90": float(np.percentile(errors, 90)), "p95": float(np.percentile(errors, 95)), "gt45_pct": float(100 * (errors > 45).mean()), "mean": float(errors.mean())}
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--device", default="cuda:0"); parser.add_argument("--bootstrap", type=int, default=2000); parser.add_argument("--out-dir", default=OUT_DIR); args = parser.parse_args()
    device = torch.device(args.device); config = load_config("config/nomad_b40.yaml"); cache_dir = "logs/dino_cache/dinov2_vits14_reg"
    _, rows, _ = load_cache(cache_dir, "train"); row_to_key = {int(v): k for k, v in rows.items()}
    with open(DFT_VAL_LIST) as f: val_trajs = {line.strip() for line in f if line.strip()}
    dataset = make_split_dataset(config, "train"); meters = meters_per_unit(dataset)
    val_pairs = build_pairs(config, "train", rows, lambda t: t in val_trajs, 0.3, 2, "endpoint"); chosen = draw(val_pairs, np.random.default_rng(VAL_SEED)); chosen = chosen[val_pairs["steps"][chosen] >= FAR_STEPS]; n = len(chosen)
    traj_ids = np.empty(n, dtype=object); turn_strict = np.zeros(n, dtype=bool)
    for i, j in enumerate(chosen):
        traj, curr = row_to_key[int(val_pairs["curr"][j])]; traj_ids[i] = traj
        lat = endpoint_lateral_m(dataset, traj, int(curr), meters); yaw = yaw_change_deg(dataset, traj, int(curr)); turn_strict[i] = turning_mask(np.array([lat]), np.array([yaw]), TURN_STRICT)[0]
    target = val_pairs["target"][chosen]; subsets = {"all_far": np.ones(n, dtype=bool), "turn_strict": turn_strict, "non_turn": ~turn_strict}
    items = []
    for j in chosen:
        traj, curr = row_to_key[int(val_pairs["curr"][j])]; _, goal_t = row_to_key[int(val_pairs["goal"][j])]; items.append((traj, int(curr), int(goal_t)))
    feats = np.load(os.path.join(cache_dir, "train", "features.npy"), mmap_mode="r"); os.makedirs(args.out_dir, exist_ok=True)
    lines = ["=== P3a/P3b Val WP bearing (far) n=%d turn=%.1f%% ===" % (n, 100*turn_strict.mean()), ""]
    errors_by_model = {}; rows_out = []
    for name, (ckpt, _) in RUNS.items():
        head, _ = load_dino_head(ckpt, device); wp_dir, _ = head_predict(head, items, rows, feats, device, batch_size=128); err = angle_err(wp_dir, target); errors_by_model[name] = err; lines.append("--- %s ---" % name)
        for sub_name, mask in subsets.items():
            e = err[mask]; s = summarize(e)
            if s["n"]: _, lo, hi = cluster_bootstrap(e, traj_ids[mask], np.median, args.bootstrap, seed=hash((name, sub_name)) % (2**31)); lines.append("  [%s] n=%d med=%.2f (%.2f-%.2f) p90=%.2f p95=%.2f >45=%.1f%%" % (sub_name, s["n"], s["median"], lo, hi, s["p90"], s["p95"], s["gt45_pct"]))
            else: lines.append("  [%s] n=0" % sub_name)
            rows_out.append({"model": name, "subset": sub_name, **s})
        lines.append("")
    lines.append("--- paired mean err delta deg (neg favors first) ---")
    for a, b in [("ctx2", "e60"), ("ctx2", "ctx0"), ("ctx0", "e60")]:
        d = errors_by_model[a] - errors_by_model[b]
        for sub_name, mask in subsets.items():
            if mask.sum() == 0: continue
            md, lo, hi = cluster_bootstrap(d[mask], traj_ids[mask], np.mean, args.bootstrap, seed=hash((a,b,sub_name))%(2**31)); lines.append("  %s-%s [%s] %+.3f [%+.3f,%+.3f]" % (a,b,sub_name,md,lo,hi))
    report = "\n".join(lines); print(report)
    with open(os.path.join(args.out_dir, "summary.txt"), "w", encoding="utf-8") as f: f.write(report + "\n")
    with open(os.path.join(args.out_dir, "metrics.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows_out[0].keys()); w.writeheader(); w.writerows(rows_out)
    print("Saved", args.out_dir)
if __name__ == "__main__": main()
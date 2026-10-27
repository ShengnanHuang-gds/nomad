"""Morning Val-only table for P3 batch (no locked eval)."""
import csv, json, os, sys
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

VAL_SEED = 1234
SEED_A = {
    "ctx0": "logs/nomad_d/nomad_dino_wp_hist_ctx0_ctrl_2026_10_24_22_11_12/dino_dir_best.pth",
    "ctx2": "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth",
}
OUT = "logs/revalidation/p3_morning_table.txt"

def val_metrics(ckpt, context, device):
    config = load_config("config/nomad_b40.yaml")
    cache_dir = "logs/dino_cache/dinov2_vits14_reg"
    _, rows, _ = load_cache(cache_dir, "train")
    row_to_key = {int(v): k for k, v in rows.items()}
    with open(DFT_VAL_LIST) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    dataset = make_split_dataset(config, "train")
    meters = meters_per_unit(dataset)
    val_pairs = build_pairs(config, "train", rows, lambda t: t in val_trajs, 0.3, max(2, context), "endpoint")
    chosen = draw(val_pairs, np.random.default_rng(VAL_SEED))
    chosen = chosen[val_pairs["steps"][chosen] >= FAR_STEPS]
    turn = np.zeros(len(chosen), dtype=bool)
    items = []
    for i, j in enumerate(chosen):
        traj, curr = row_to_key[int(val_pairs["curr"][j])]
        lat = endpoint_lateral_m(dataset, traj, int(curr), meters)
        yaw = yaw_change_deg(dataset, traj, int(curr))
        turn[i] = turning_mask(np.array([lat]), np.array([yaw]), TURN_STRICT)[0]
        _, gt = row_to_key[int(val_pairs["goal"][j])]
        items.append((traj, int(curr), int(gt)))
    target = val_pairs["target"][chosen]
    feats = np.load(os.path.join(cache_dir, "train", "features.npy"), mmap_mode="r")
    head, _ = load_dino_head(ckpt, device)
    wp, _ = head_predict(head, items, rows, feats, device, batch_size=128)
    err = angle_err(wp, target)
    far_med = float(np.median(err))
    turn_med = float(np.median(err[turn])) if turn.any() else float("nan")
    nt_med = float(np.median(err[~turn])) if (~turn).any() else float("nan")
    turn_p90 = float(np.percentile(err[turn], 90)) if turn.any() else float("nan")
    turn_p95 = float(np.percentile(err[turn], 95)) if turn.any() else float("nan")
    gt45 = float(100 * (err > 45).mean())
    return {"val_far_median": far_med, "val_turn_median": turn_med, "val_turn_p90": turn_p90, "val_turn_p95": turn_p95, "val_gt45_pct": gt45, "val_nonturn_median": nt_med}

def load_manifest():
    rows = []
    for path in ("logs/queues/p3_turn_manifest.jsonl", "logs/queues/p3_batch_manifest.jsonl"):
        if not os.path.isfile(path):
            continue
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    runs = []
    for label, ck in SEED_A.items():
        runs.append(("SeedA", label, ck, 2 if label.startswith("ctx2") else 0))
    for row in load_manifest():
        rid = row["id"]
        ck = os.path.join(row["output_dir"], "dino_dir_best.pth")
        if rid.startswith("B_"):
            kind, seed = "B_turnstrict_x2", "0"
        elif rid.startswith("C_"):
            kind, seed = "C_turnstrict_x3", "0"
        elif rid.startswith("D_"):
            kind, seed = "D_curvature_tiers", "0"
        elif "turn" in rid:
            kind, seed = "ctx2_turn", rid.split("seed")[-1]
        elif "ctx2" in rid:
            kind, seed = "ctx2", rid.split("seed")[-1]
        else:
            kind, seed = "ctx0", rid.split("seed")[-1]
        ctx = 2 if kind != "ctx0" else 0
        runs.append((f"Seed{seed}", kind, ck, ctx))
    lines = ["P3 morning table (Val only, dino_dir_best.pth)", ""]
    metrics = []
    for seed, kind, ck, ctx in runs:
        if not os.path.isfile(ck):
            lines.append(f"SKIP {seed} {kind}: missing {ck}")
            continue
        m = val_metrics(ck, ctx, device)
        m.update({"seed": seed, "kind": kind})
        metrics.append(m)
        lines.append(f"{seed} {kind}: " + ", ".join(f"{k}={v:.2f}" for k, v in m.items() if k not in ("seed", "kind")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    if metrics:
        with open("logs/revalidation/p3_morning_metrics.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=metrics[0].keys())
            w.writeheader()
            w.writerows(metrics)
    print("\n".join(lines))
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
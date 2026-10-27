"""Mine hard turn/bearing training pairs from GoStanford (GT pose only, no LMDB)."""
from __future__ import annotations

import argparse
import csv
import json
import os
import pickle

import cv2  # noqa: F401 — before torch stack on Windows
import numpy as np
from tqdm import tqdm

from eval_by_distance import load_config

MIN_STEPS, MAX_STEPS, HORIZON = 4, 39, 8
TURN_LAT_M, TURN_YAW_DEG, BEARING_DEG, MIN_GOAL_M = 0.30, 45.0, 45.0, 0.3
DFT_VAL_LIST = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/val_trajectories.txt"


def yaw_rot(yaw):
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def to_local(xy, curr_xy, curr_yaw):
    return (xy - curr_xy) @ yaw_rot(curr_yaw)


def load_traj_names(split_folder):
    with open(os.path.join(split_folder, "traj_names.txt"), encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def load_val_set(path):
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip()}


def mine_traj(data_folder, name, min_goal_m):
    with open(os.path.join(data_folder, name, "traj_data.pkl"), "rb") as f:
        td = pickle.load(f)
    pos = np.asarray(td["position"], dtype=np.float64)
    yaw = np.asarray(td["yaw"], dtype=np.float64).reshape(-1)
    n = len(pos)
    rows, n_all = [], 0
    for t in range(0, n - HORIZON):
        max_g = min(n - 1, t + MAX_STEPS)
        if max_g < t + MIN_STEPS:
            continue
        end_local = to_local(pos[t + HORIZON], pos[t], float(yaw[t]))
        dyaw = float(yaw[t + HORIZON] - yaw[t])
        dyaw = (dyaw + np.pi) % (2.0 * np.pi) - np.pi
        hard_turn = (abs(end_local[1]) >= TURN_LAT_M) or (abs(np.degrees(dyaw)) >= TURN_YAW_DEG)
        for g in range(t + MIN_STEPS, max_g + 1):
            goal_local = to_local(pos[g], pos[t], float(yaw[t]))
            dist = float(np.linalg.norm(goal_local))
            if dist < min_goal_m:
                continue
            n_all += 1
            bearing = float(np.degrees(np.arctan2(goal_local[1], goal_local[0])))
            hard_bearing = abs(bearing) > BEARING_DEG
            if not (hard_turn or hard_bearing):
                continue
            steps = g - t
            rows.append(
                {
                    "traj_name": name,
                    "t": t,
                    "goal_time": g,
                    "steps": steps,
                    "far": int(steps >= 20),
                    "hard_turn": int(hard_turn),
                    "hard_bearing": int(hard_bearing),
                    "bearing_deg": round(bearing, 2),
                    "lat_m": round(float(end_local[1]), 4),
                    "dyaw_deg": round(float(np.degrees(dyaw)), 2),
                    "goal_dist_m": round(dist, 4),
                }
            )
    return rows, n_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--split", default="train", choices=("train", "test"))
    parser.add_argument("--min-goal-m", type=float, default=MIN_GOAL_M)
    parser.add_argument("--exclude-val", action="store_true", default=True)
    parser.add_argument("--no-exclude-val", action="store_false", dest="exclude_val")
    parser.add_argument("--out-dir", default="logs/revalidation/hard_pairs")
    args = parser.parse_args()

    config = load_config(args.config)
    dc = config["datasets"]["go_stanford"]
    names = load_traj_names(dc[args.split])
    val = load_val_set(DFT_VAL_LIST) if (args.split == "train" and args.exclude_val) else set()
    if val:
        before = len(names)
        names = [n for n in names if n not in val]
        print(f"exclude DINO val trajs: {before} -> {len(names)} (dropped {before - len(names)})")

    os.makedirs(args.out_dir, exist_ok=True)
    out_csv = os.path.join(args.out_dir, f"hard_pairs_{args.split}.csv")
    summary = {
        "split": args.split,
        "n_trajs": len(names),
        "n_pairs_all": 0,
        "n_hard": 0,
        "n_hard_turn": 0,
        "n_hard_bearing": 0,
        "n_hard_both": 0,
        "n_hard_far": 0,
        "n_hard_far_turn": 0,
        "n_hard_far_bearing": 0,
    }

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = None
        for name in tqdm(names, desc=f"mine {args.split}"):
            if not os.path.isfile(os.path.join(dc["data_folder"], name, "traj_data.pkl")):
                continue
            try:
                rows, n_all = mine_traj(dc["data_folder"], name, args.min_goal_m)
            except Exception as e:
                print(f"skip {name}: {e}")
                continue
            summary["n_pairs_all"] += n_all
            for row in rows:
                summary["n_hard"] += 1
                summary["n_hard_turn"] += row["hard_turn"]
                summary["n_hard_bearing"] += row["hard_bearing"]
                summary["n_hard_both"] += int(row["hard_turn"] and row["hard_bearing"])
                if row["far"]:
                    summary["n_hard_far"] += 1
                    summary["n_hard_far_turn"] += row["hard_turn"]
                    summary["n_hard_far_bearing"] += row["hard_bearing"]
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    n_all = max(summary["n_pairs_all"], 1)
    summary["frac_hard"] = summary["n_hard"] / n_all
    summary["csv"] = os.path.abspath(out_csv)
    summary_path = os.path.join(args.out_dir, f"hard_pairs_{args.split}_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {summary['n_hard']} hard rows -> {out_csv}")


if __name__ == "__main__":
    main()

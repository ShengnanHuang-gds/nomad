"""Re-run blend ablation with scaled wp kappa (subset of eval_blend_ablation)."""
import argparse
import csv
import os
import sys

import cv2  # noqa: F401
import numpy as np
import torch

from eval_blend_ablation import SET_NAMES, equal_blend
from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, rollout
from eval_waypoint_head import blend, endpoints, head_predict
from train_e_dino import load_dino_head
from train_goal_dino import load_cache
from revalidate import CACHE_ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--scales", default="0.7,0.85,1.0,1.15,1.3")
    ap.add_argument("--device", default="cuda:0")
    args = ap.parse_args()
    device = torch.device(args.device)
    config_b = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(PAIRED_FRAMES)
    sets, _, _ = frame_sets(dataset, moments, meters, SPREAD_NPZ)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda k: pred[k][fm][order]
    goal_dir = take("dino_dir").astype(np.float32)
    goal_kappa = take("dino_kappa").astype(np.float32)
    steps = (take("b_dist") / meters).astype(np.float32)
    cache_npz = os.path.join(args.run_dir, "eval_waypoint", "locked_per_frame.npz")
    cached = np.load(cache_npz)
    wp_dir = cached["wp_dir"].astype(np.float32)
    wp_kappa = cached["wp_kappa"].astype(np.float32)
    s = steps[:, None]
    model_eo, sched_eo = load_model(load_config("config/nomad_e_oracle.yaml"), E_CHECKPOINT, device)
    rows = []
    rng = np.random.default_rng(0)
    for sc in [float(x) for x in args.scales.split(",")]:
        kap = blend(goal_dir, goal_kappa, wp_dir, wp_kappa * sc)
        pos = {"kappa blend": (kap * s).astype(np.float32)}
        am, ade = rollout(model_eo, sched_eo, dataset, far, pos, device, 8, 8, 1, "kap-scale")
        idx = np.flatnonzero(sets["all"])
        boot = subset_index(len(idx), 1000, rng)
        u = boot_mean(am[idx] - ade["kappa blend"][idx], boot)
        rows.append({"scale": sc, "use_cm_all": 100 * u[0]})
        print("scale", sc, "all", 100 * u[0])
    out = os.path.join(args.run_dir, "eval_kappa_wp_scale")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "scales.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scale", "use_cm_all"])
        w.writeheader()
        w.writerows(rows)
    best = max(rows, key=lambda r: r["use_cm_all"])
    open(os.path.join(out, "best.txt"), "w").write(str(best) + "\n")


if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""Validation metrics for path-head readout A/B."""

from __future__ import annotations

import argparse
import csv
import json
import os

import cv2  # noqa: F401
import numpy as np
import torch

from eval_by_distance import load_config
from train_e_dino import load_dino_head
from train_goal_dino import (
    CACHE_DIR,
    DFT_VAL_LIST,
    _parse_batch,
    build_pairs,
    go_stanford_meters_per_unit,
    load_cache,
    loader,
    run_epoch,
)


def extra_path_metrics(head, batches, device, meters):
    ade_back, wrong, wrong_turn = [], [], []
    with torch.no_grad():
        for batch in batches:
            parsed = _parse_batch(batch, device)
            curr, goal, target, steps, ctx, winding_t = parsed[:6]
            target_path, odom_t = parsed[10], parsed[11]
            if target_path is None:
                continue
            out = head(curr, goal, ctx, odom=odom_t)
            path = out[-1].float()
            err = (path - target_path).norm(dim=-1) * meters * 100.0
            ade_back.append(err[:, 4:].mean(dim=-1).cpu().numpy())
            w = winding_t.cpu().numpy()
            pred_end = path[:, -1]
            gt_end = target_path[:, -1]
            u = lambda v: v / v.norm(dim=-1, keepdim=True).clamp(min=1e-6)
            dot = (u(pred_end) * u(gt_end)).sum(-1).cpu().numpy()
            wrong.append(dot < 0.0)
            wrong_turn.append(dot[w >= 45.0])
    if not ade_back:
        return {
            "path_ade_back4_cm": float("nan"),
            "wrong_way_frac": float("nan"),
            "wrong_way_turn45_frac": float("nan"),
            "n_val": 0,
        }
    ade_back = np.concatenate(ade_back)
    wrong = np.concatenate(wrong)
    wt = np.concatenate(wrong_turn) if wrong_turn else np.array([])
    return {
        "path_ade_back4_cm": float(np.mean(ade_back)),
        "wrong_way_frac": float(wrong.mean()),
        "wrong_way_turn45_frac": float(wt.mean()) if wt.size else float("nan"),
        "n_val": int(len(ade_back)),
    }


def eval_one(label, wp, val_batches, device, meters):
    head, _ = load_dino_head(wp, device)
    val_kw = dict(
        hard_bearing_deg=30.0,
        hard_weight=1.0,
        hard_far_only=True,
        sector_lambda=0.0,
        sector_mid_deg=15.0,
        sector_hard_boost=1.0,
        turn_winding_deg=0.0,
        turn_weight=1.0,
        turn_strict_weight=0.0,
        curvature_q=(None, None),
        curvature_weights=(1.0, 1.5, 3.0),
        multi_horizon_lambda=0.0,
        yaw_aux_lambda=0.0,
        yaw_aux_steps=0,
        yaw_integrate_lambda=0.0,
        path_lambda=0.0,
        path_dir_lambda=0.0,
        path_smooth_lambda=0.0,
        path_seg_lambda=0.0,
        path_seg_beta=0.1,
        freeze_dir=True,
        meters_per_unit=meters,
    )
    metrics = run_epoch(head, val_batches, device, desc=label, **val_kw)
    extra = extra_path_metrics(head, val_batches, device, meters)
    row = {
        "label": label,
        "checkpoint": wp.replace("\\", "/"),
        "path_ade_cm": metrics.get("path_ade_cm", float("nan")),
        "far_path_ade_cm": metrics.get("far_path_ade_cm", float("nan")),
        "path_turn_deg": metrics.get("path_turn_deg", float("nan")),
        "turn90_median_deg": metrics.get("turn90_median_deg", float("nan")),
    }
    row.update(extra)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wp-a", required=True)
    parser.add_argument("--wp-b", required=True)
    parser.add_argument("--label-a", default="A_cls")
    parser.add_argument("--label-b", default="B_step_query")
    parser.add_argument("--out", default="logs/revalidation/path_readout_ab/val_metrics.csv")
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config("config/nomad_b40.yaml")
    meters = float(go_stanford_meters_per_unit(config))
    cache_path, rows, _meta = load_cache(CACHE_DIR, "train")
    with open(DFT_VAL_LIST, encoding="utf-8") as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    val_pairs = build_pairs(
        config, "train", rows, lambda t: t in val_trajs, 0.3, 2, "endpoint", path_steps=8
    )
    val_chosen = np.arange(len(val_pairs["starts"]))
    val_batches = loader(cache_path, val_pairs, val_chosen, 512, False, 0, 2, 2)

    rows_out = [
        eval_one(args.label_a, args.wp_a, val_batches, device, meters),
        eval_one(args.label_b, args.wp_b, val_batches, device, meters),
    ]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    meta_path = os.path.join(os.path.dirname(args.out), "val_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"val_traj_count": len(val_trajs), "val_pairs": len(val_chosen)}, f, indent=2)
    print("wrote", args.out)
    for r in rows_out:
        print(r)


if __name__ == "__main__":
    main()
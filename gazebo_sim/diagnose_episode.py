#!/usr/bin/env python3
"""Offline root-cause hints for a hold-out episode JSON (+ optional .ticks.csv)."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pickle
from pathlib import Path

import numpy as np

from episode_coords import path_xy_world, uses_spawn_odom

ROOT = Path(__file__).resolve().parent


def gt_xy(run_id: str) -> np.ndarray:
    pkl = ROOT / run_id / "traj_data.pkl"
    with open(pkl, "rb") as f:
        return np.asarray(pickle.load(f)["position"], dtype=np.float64)[:, :2]


def dist_to_polyline(path: np.ndarray, poly: np.ndarray) -> float:
    if len(path) == 0:
        return float("nan")
    errs = [float(np.min(np.linalg.norm(poly - p, axis=1))) for p in path]
    return float(np.median(errs))


def load_csv_ticks(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def analyze(ep_path: Path) -> dict:
    with open(ep_path, encoding="utf-8") as f:
        ep = json.load(f)
    traj = ep.get("traj") or "house_run_06"
    gt = gt_xy(traj)
    teach0 = gt[0]
    path_raw = np.asarray(ep.get("path_xy") or [], dtype=np.float64)
    if ep.get("path_xy_world"):
        path_xy = np.asarray(ep["path_xy_world"], dtype=np.float64)
    else:
        path_xy = path_xy_world(ep, path_raw, teach0)
    spawn_odom = uses_spawn_odom(ep, path_raw, teach0)
    reset_m = ep.get("reset_align_m")
    if reset_m is None and len(path_raw):
        reset_m = (
            float(np.linalg.norm(path_raw[0]))
            if spawn_odom
            else float(np.linalg.norm(path_raw[0] - teach0))
        )
    off_corridor = dist_to_polyline(path_xy, gt) if len(path_xy) else float("nan")
    cn = int(ep.get("closest_node", 0))
    cn_max = int(ep.get("closest_node_max", cn))
    goal = int(ep.get("goal_node", len(gt) - 1))
    csv_path = Path(str(ep_path).replace(".json", ".ticks.csv"))
    ticks = load_csv_ticks(csv_path)
    plateau = False
    if ticks:
        nodes = [int(r["closest_node"]) for r in ticks if r.get("closest_node")]
        if len(nodes) >= 40:
            tail = nodes[len(nodes) // 2 :]
            plateau = max(tail) - min(tail) <= 1
    reasons: list[str] = []
    if reset_m is not None and reset_m > 0.5:
        if spawn_odom:
            raw0 = path_raw[0].tolist() if len(path_raw) else "?"
            reasons.append(
                f"RESET: spawn odom {reset_m:.2f}m from origin "
                f"(raw start {raw0}, teach anchor {teach0.tolist()})"
            )
        else:
            reasons.append(
                f"RESET: odom start {reset_m:.2f}m from teach "
                f"(teach {teach0.tolist()}, robot {path_raw[0].tolist() if len(path_raw) else '?'})"
            )
    if not math.isnan(off_corridor) and off_corridor > 0.8:
        reasons.append(
            f"GEOMETRY: median path-GT distance {off_corridor:.2f}m — off demo corridor"
        )
    if cn_max <= 8 and cn == cn_max and goal > cn + 5:
        reasons.append(
            f"GRAPH: closest_node plateau at {cn}/{goal} — dist_pred argmin stuck"
        )
    if plateau:
        reasons.append("GRAPH: closest_node flat in 2nd half (.ticks.csv)")
    if ticks:
        dists = [float(r["dist_min"]) for r in ticks if r.get("dist_min")]
        if dists and np.median(dists) >= 5:
            reasons.append(
                f"DISTPRED: median min dist {np.median(dists):.2f} >= threshold 5"
            )
    if not reasons:
        reasons.append(ep.get("primary_failure") or "re-run with --auto-log-csv")
    return {
        "reset_align_m": reset_m,
        "off_corridor_median_m": off_corridor,
        "closest_node": cn,
        "closest_node_max": cn_max,
        "goal_node": goal,
        "path_odom_m": ep.get("path_odom_m"),
        "likely_causes": reasons,
        "spawn_at_launch": spawn_odom,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_json", nargs="+")
    args = parser.parse_args()
    for p in args.episode_json:
        rep = analyze(Path(p))
        print("===", os.path.basename(p), "===")
        if rep["reset_align_m"] is not None:
            print(f"reset_align_m={rep['reset_align_m']:.3f}")
        else:
            print("reset_align_m=n/a")
        if rep.get("spawn_at_launch"):
            print("odom_frame: spawn_origin (+ teach anchor applied for GEOMETRY)")
        if not math.isnan(rep["off_corridor_median_m"]):
            print(f"off_corridor_median_m={rep['off_corridor_median_m']:.3f}")
        print(
            f"nodes {rep['closest_node']}/{rep['goal_node']} max={rep['closest_node_max']} "
            f"path_m={rep['path_odom_m']}"
        )
        for i, r in enumerate(rep["likely_causes"], 1):
            print(f"  {i}. {r}")
        print()


if __name__ == "__main__":
    main()
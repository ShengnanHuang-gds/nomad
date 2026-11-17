#!/usr/bin/env python3
"""Aggregate per-trajectory task metrics into training weights (JSON).

After Gazebo episodes (one JSON per run from nomad_navigate_ros2.py --episode-out), merge into
gazebo_sim/rollout_task_weights.json for train_gazebo_task.py.

Example (WSL, sim + PD running):
  for r in 00 01 02; do
    python3 gazebo_sim/reset_run_pose.py --run house_run_$r
    python3 gazebo_sim/nomad_navigate_ros2.py --topomap house_$r --episode-out gazebo_sim/episodes/house_$r.json &
    EP=$!; python3 gazebo_sim/pd_controller_ros2.py; wait $EP
  done
  python3 gazebo_sim/collect_task_metrics.py --episode-dir gazebo_sim/episodes
"""

from __future__ import annotations

import argparse
import json
import os
import pickle

from task_reward import episode_record

ROOT = os.path.dirname(os.path.abspath(__file__))


def teacher_path_m(run_dir: str) -> float | None:
    pkl = os.path.join(run_dir, "traj_data.pkl")
    if not os.path.isfile(pkl):
        return None
    with open(pkl, "rb") as f:
        pos = pickle.load(f)["position"]
    import numpy as np

    xy = np.asarray(pos, dtype=float)[:, :2]
    if len(xy) < 2:
        return None
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-dir", default=os.path.join(ROOT, "episodes"))
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "rollout_task_weights.json"),
    )
    parser.add_argument("--reward-config", default=os.path.join(ROOT, "task_reward.json"))
    args = parser.parse_args()

    if os.path.isfile(args.reward_config):
        with open(args.reward_config, encoding="utf-8") as f:
            reward_cfg = json.load(f)
    else:
        reward_cfg = {
            "success_bonus": 1.0,
            "fail_penalty": -1.0,
            "collision_penalty": 0.35,
            "path_penalty_per_m": 0.08,
            "path_only_if_success": True,
            "temperature": 1.0,
            "weight_floor": 0.05,
            "weight_ceil": 3.0,
        }

    rows = []
    for fn in sorted(os.listdir(args.episode_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(args.episode_dir, fn)
        with open(path, encoding="utf-8") as f:
            ep = json.load(f)
        traj = ep.get("traj") or fn.replace(".json", "").replace("house_", "house_run_")
        run_dir = os.path.join(ROOT, traj if traj.startswith("house_run_") else f"house_run_{traj.split('_')[-1]}")
        ref = teacher_path_m(run_dir)
        rec = episode_record(
            traj,
            ep["success"],
            ep["path_odom_m"],
            ep.get("collision_count", 0),
            ref,
            reward_cfg,
        )
        rows.append(rec)

    out = {
        "reward_config": reward_cfg,
        "trajectories": {r["traj"]: r for r in rows},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {args.out} ({len(rows)} trajectories)")
    for r in rows:
        print(
            f"  {r['traj']}: succ={r['success']} path={r['path_odom_m']:.2f}m "
            f"coll={r['collision_count']} w={r['weight']:.3f}"
        )


if __name__ == "__main__":
    main()
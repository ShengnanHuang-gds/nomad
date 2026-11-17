#!/usr/bin/env python3
"""Print first x y yaw from gazebo_sim/<run>/traj_data.pkl (for launch scripts)."""

from __future__ import annotations

import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Same start poses as record_house_multi.PLANS. Kept here so launch can run with system python3.
PLAN_POSE = {
    "house_run_03": (1.2, 1.5, -math.pi / 2),
    "house_run_04": (-0.5, -1.8, math.pi),
    "house_run_05": (2.0, -0.3, math.pi / 4),
    "house_run_06": (-2.2, 1.2, -math.pi / 4),
    "house_run_07": (0.0, 2.0, 3 * math.pi / 4),
}


def main() -> None:
    run = sys.argv[1] if len(sys.argv) > 1 else "house_run_06"
    pkl = ROOT / run / "traj_data.pkl"
    plan = PLAN_POSE.get(run)
    if pkl.is_file():
        with open(pkl, "rb") as f:
            d = pickle.load(f)
        yaw = float(d["yaw"][0])
        if "world_anchor" in d:
            x, y = float(d["world_anchor"][0]), float(d["world_anchor"][1])
        else:
            p = d["position"][0]
            # spawn-at-launch odom starts at (0,0); that is not the house world pose
            if plan is not None and math.hypot(float(p[0]), float(p[1])) < 1.5:
                x, y = float(plan[0]), float(plan[1])
            else:
                x, y = float(p[0]), float(p[1])
    elif plan is not None:
        x, y, yaw = plan
    else:
        raise SystemExit(f"no traj or plan for {run}")
    print(f"{x} {y} {yaw}")


if __name__ == "__main__":
    main()
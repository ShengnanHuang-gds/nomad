#!/usr/bin/env python3
"""Bootstrap rollout_task_weights.json before first sim pass (teacher path length only)."""

from __future__ import annotations

import json
import os

from collect_task_metrics import teacher_path_m
from task_reward import episode_record

ROOT = os.path.dirname(os.path.abspath(__file__))
REWARD_CFG = os.path.join(ROOT, "task_reward.json")


def main():
    with open(REWARD_CFG, encoding="utf-8") as f:
        reward_cfg = json.load(f)
    rows = {}
    for name in sorted(os.listdir(ROOT)):
        if not name.startswith("house_run_") or not os.path.isdir(os.path.join(ROOT, name)):
            continue
        ref = teacher_path_m(os.path.join(ROOT, name))
        rec = episode_record(name, True, ref or 5.0, 0, ref, reward_cfg)
        rows[name] = rec
    out = {"reward_config": reward_cfg, "trajectories": rows}
    path = os.path.join(ROOT, "rollout_task_weights.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote bootstrap {path} ({len(rows)} trajs)")


if __name__ == "__main__":
    main()
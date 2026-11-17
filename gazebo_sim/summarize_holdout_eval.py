#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "episodes_eval")
    rows = []
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(root, fn), encoding="utf-8") as f:
            d = json.load(f)
        rows.append((fn.replace(".json",""), d.get("success"), float(d.get("path_odom_m",0)), int(d.get("collision_count",0)), int(d.get("closest_node",-1)), int(d.get("goal_node",-1))))
    print(f"{'run':32} {'succ':>5} {'path_m':>8} {'coll':>5} {'node':>12}")
    for r in rows:
        print(f"{r[0]:32} {str(r[1]):>5} {r[2]:8.2f} {r[3]:5d} {r[4]}/{r[5]:>12}")

if __name__ == "__main__":
    main()
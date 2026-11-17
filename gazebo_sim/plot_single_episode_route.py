#!/usr/bin/env python3
"""One BEV figure: teacher vs robot for a single episode JSON."""
from __future__ import annotations
import argparse, json, os, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--out", default="")
    args = p.parse_args()
    with open(args.json, encoding="utf-8") as f:
        ep = json.load(f)
    traj = ep["traj"]
    with open(os.path.join(ROOT, traj, "traj_data.pkl"), "rb") as f:
        gt = np.asarray(pickle.load(f)["position"], float)[:, :2]
    fig, ax = plt.subplots(figsize=(8, 7), dpi=140)
    ax.plot(gt[:, 0], gt[:, 1], "-", color="#bbb", lw=3, label="teacher")
    ax.plot(gt[0, 0], gt[0, 1], "go", ms=12)
    ax.plot(gt[-1, 0], gt[-1, 1], "r*", ms=16)
    path = ep.get("path_xy") or []
    if path:
        rw = np.asarray(path, float)
        ax.plot(rw[:, 0], rw[:, 1], "-", color="#d62728", lw=2.5, label="robot odom")
        ax.plot(rw[-1, 0], rw[-1, 1], "x", color="#d62728", ms=12)
    cn, gn = int(ep["closest_node"]), int(ep["goal_node"])
    ax.plot(gt[min(cn, len(gt) - 1), 0], gt[min(cn, len(gt) - 1), 1], "D", color="#1f77b4", ms=12, label=f"node {cn}/{gn}")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(f"{os.path.basename(args.json)}  success={ep.get('success')}  path={ep.get('path_odom_m', 0):.2f}m")
    out = args.out or args.json.replace(".json", "_route.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(out)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""One-page overview of all house_* topomaps (node count + small path preview)."""

from __future__ import annotations

import argparse
import os
import pickle

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gazebo-sim", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    runs = sorted(
        d
        for d in os.listdir(args.gazebo_sim)
        if d.startswith("house_run_") and os.path.isdir(os.path.join(args.gazebo_sim, d))
    )
    fig, axes = plt.subplots(2, 4, figsize=(14, 7), dpi=120)
    axes = axes.ravel()

    for ax, run in zip(axes, runs):
        pkl = os.path.join(args.gazebo_sim, run, "traj_data.pkl")
        with open(pkl, "rb") as f:
            data = pickle.load(f)
        xy = np.asarray(data["position"], dtype=np.float64)[:, :2]
        n_jpg = len([x for x in os.listdir(os.path.join(args.gazebo_sim, run)) if x.endswith(".jpg")])
        ax.plot(xy[:, 0], xy[:, 1], "-", color="#555", lw=1.5)
        ax.scatter(xy[0, 0], xy[0, 1], c="g", s=40)
        ax.scatter(xy[-1, 0], xy[-1, 1], c="r", s=40)
        ax.set_aspect("equal", adjustable="datalim")
        tag = run.replace("house_run_", "house_")
        ax.set_title(f"{tag}\n{n_jpg} topo nodes", fontsize=9)
        ax.tick_params(labelsize=7)

    for j in range(len(runs), len(axes)):
        axes[j].axis("off")

    fig.suptitle("Gazebo house topomaps (exported to deployment/topomaps/images/)", fontsize=12)
    out = args.out or os.path.join(args.gazebo_sim, "topomap_all_overview.png")
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
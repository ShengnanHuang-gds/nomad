#!/usr/bin/env python3
"""Compare topomap house_XX node positions with original house_run_XX trajectory."""

from __future__ import annotations

import argparse
import os
import pickle

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

GAZEBO_SIM = os.path.dirname(os.path.abspath(__file__))
DEPLOY_IMG = os.path.normpath(
    os.path.join(
        GAZEBO_SIM,
        "..",
        "visualnav-transformer",
        "deployment",
        "topomaps",
        "images",
    )
)


def run_id(topomap_name: str) -> str:
    if topomap_name.startswith("house_"):
        return "house_run_" + topomap_name.split("_", 1)[1]
    return topomap_name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="house_00")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    run = run_id(args.name)
    pkl = os.path.join(GAZEBO_SIM, run, "traj_data.pkl")
    topo_dir = os.path.join(DEPLOY_IMG, args.name)
    with open(pkl, "rb") as f:
        data = pickle.load(f)
    pos = np.asarray(data["position"], dtype=np.float64)[:, :2]
    yaw = np.asarray(data["yaw"], dtype=np.float64).reshape(-1)

    n_topo = len(
        [
            x
            for x in os.listdir(topo_dir)
            if x.lower().endswith((".png", ".jpg")) and os.path.splitext(x)[0].isdigit()
        ]
    )
    n_jpg = len([x for x in os.listdir(os.path.join(GAZEBO_SIM, run)) if x.endswith(".jpg")])

    # Topomap is 1:1 export: node i == frame i
    n = min(n_topo, len(pos), n_jpg)
    node_xy = pos[:n]
    dense_xy = pos

    seg_dense = np.linalg.norm(np.diff(dense_xy, axis=0), axis=1)
    seg_nodes = np.linalg.norm(np.diff(node_xy, axis=0), axis=1) if n > 1 else np.array([])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), dpi=130)

    ax = axes[0]
    ax.plot(dense_xy[:, 0], dense_xy[:, 1], "-", color="#ccc", lw=2, label="dense traj (all odom)")
    ax.plot(
        node_xy[:, 0],
        node_xy[:, 1],
        "o-",
        color="#1f77b4",
        ms=5,
        lw=1.5,
        label=f"topomap nodes (n={n})",
    )
    for idx in [0, n // 4, n // 2, 3 * n // 4, n - 1]:
        ax.annotate(
            str(idx),
            (node_xy[idx, 0], node_xy[idx, 1]),
            fontsize=8,
            xytext=(5, 5),
            textcoords="offset points",
        )
    ax.scatter(node_xy[0, 0], node_xy[0, 1], c="#2ca02c", s=100, zorder=5, edgecolors="k", lw=0.5)
    ax.scatter(node_xy[-1, 0], node_xy[-1, 1], c="#d62728", s=100, zorder=5, edgecolors="k", lw=0.5)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Overlay: original path vs topomap chain")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.bar(
        [0, 1],
        [len(dense_xy), n],
        color=["#aaa", "#1f77b4"],
        width=0.5,
    )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["traj_data points", "topomap nodes"])
    ax.set_ylabel("count")
    ax.set_title(f"Samples (jpgs={n_jpg}, export 1:1 → {n_topo})")

    ax = axes[2]
    bins = np.arange(len(seg_nodes) + 1)
    ax.plot(bins[:-1], seg_nodes * 100, "o-", color="#1f77b4", ms=4, label="node spacing (cm)")
    if len(seg_dense):
        ax.axhline(seg_dense.mean() * 100, color="#888", ls="--", label=f"dense mean {seg_dense.mean()*100:.1f} cm")
    ax.set_xlabel("edge index (node i → i+1)")
    ax.set_ylabel("step length (cm)")
    ax.set_title(
        f"path length topo {seg_nodes.sum():.2f} m | full odom {seg_dense.sum():.2f} m"
    )
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    diff = np.zeros(0)
    if n == len(pos):
        diff = np.linalg.norm(node_xy - pos[:n], axis=1)

    fig.suptitle(
        f"{args.name} vs {run}: topomap is identical chain "
        f"(max xy error {diff.max() if len(diff) else 0:.2e} m)",
        fontsize=11,
        y=1.02,
    )
    out = args.out or os.path.join(GAZEBO_SIM, f"topomap_{args.name}_vs_traj.png")
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    print(
        f"nodes={n} jpgs={n_jpg} topo_files={n_topo} "
        f"length_m={seg_nodes.sum():.3f} full_m={seg_dense.sum():.3f} "
        f"node_step_cm mean={seg_nodes.mean()*100:.2f}" if len(seg_nodes) else ""
    )


if __name__ == "__main__":
    main()
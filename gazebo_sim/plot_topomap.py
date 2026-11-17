#!/usr/bin/env python3
"""Visualize a deployment topomap: BEV chain + thumbnail filmstrip."""

from __future__ import annotations

import argparse
import math
import os
import pickle

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def load_topomap_images(topomap_dir: str) -> list[np.ndarray]:
    paths = sorted(
        (
            os.path.join(topomap_dir, f)
            for f in os.listdir(topomap_dir)
            if f.lower().endswith((".png", ".jpg")) and os.path.splitext(f)[0].isdigit()
        ),
        key=lambda p: int(os.path.splitext(os.path.basename(p))[0]),
    )
    return [np.asarray(Image.open(p).convert("RGB")) for p in paths]


def load_traj_xy(run_dir: str) -> np.ndarray | None:
    pkl = os.path.join(run_dir, "traj_data.pkl")
    if not os.path.isfile(pkl):
        return None
    with open(pkl, "rb") as f:
        data = pickle.load(f)
    return np.asarray(data["position"], dtype=np.float64)[:, :2]


def filmstrip_row(images: list[np.ndarray], start: int, count: int, thumb_h: int) -> np.ndarray:
    thumbs = []
    gap = np.ones((thumb_h, 6, 3), dtype=np.uint8) * 240
    for idx in range(start, min(start + count, len(images))):
        im = Image.fromarray(images[idx])
        w = max(1, int(im.width * thumb_h / im.height))
        im = im.resize((w, thumb_h), Image.BILINEAR)
        thumbs.append(np.asarray(im))
        thumbs.append(gap)
    if not thumbs:
        return np.zeros((thumb_h, 10, 3), dtype=np.uint8)
    return np.concatenate(thumbs, axis=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="house_00")
    parser.add_argument(
        "--deploy-images",
        default=os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "visualnav-transformer",
                "deployment",
                "topomaps",
                "images",
            )
        ),
    )
    parser.add_argument("--gazebo-sim", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--out", default="")
    parser.add_argument("--thumb-h", type=int, default=72)
    parser.add_argument("--cols", type=int, default=12)
    args = parser.parse_args()

    topomap_dir = os.path.join(args.deploy_images, args.name)
    images = load_topomap_images(topomap_dir)
    if not images:
        raise SystemExit(f"no images in {topomap_dir}")

    run_name = "house_run_" + args.name.split("_", 1)[-1] if args.name.startswith("house_") else ""
    xy = load_traj_xy(os.path.join(args.gazebo_sim, run_name)) if run_name else None

    n = len(images)
    cols = args.cols
    n_rows = int(math.ceil(n / cols))

    fig_h = 4.5 + n_rows * 1.15
    fig = plt.figure(figsize=(16, fig_h), dpi=130)
    outer = fig.add_gridspec(2, 1, height_ratios=[2.2, 1.0], hspace=0.28)

    ax_bev = fig.add_subplot(outer[0])
    if xy is not None:
        ax_bev.plot(xy[:, 0], xy[:, 1], "-", color="#999", lw=1.8)
        step = max(1, len(xy) // max(n, 1))
        node_xy = xy[::step][:n]
        if len(node_xy) < n:
            node_xy = xy[np.linspace(0, len(xy) - 1, n).astype(int)]
        ax_bev.scatter(node_xy[:, 0], node_xy[:, 1], s=28, c="#1f77b4", zorder=3)
        for i in range(min(n, len(node_xy))):
            if i % max(1, n // 8) == 0 or i in (0, n - 1):
                ax_bev.annotate(
                    str(i),
                    (node_xy[i, 0], node_xy[i, 1]),
                    fontsize=7,
                    color="#0a3d6b",
                    xytext=(4, 4),
                    textcoords="offset points",
                )
        ax_bev.scatter(xy[0, 0], xy[0, 1], c="#2ca02c", s=90, zorder=5, label="start (node 0)")
        ax_bev.scatter(xy[-1, 0], xy[-1, 1], c="#d62728", s=90, zorder=5, label=f"goal (node {n-1})")
        ax_bev.set_xlabel("x (m)")
        ax_bev.set_ylabel("y (m)")
        ax_bev.legend(fontsize=8, loc="best")
    ax_bev.set_aspect("equal", adjustable="datalim")
    ax_bev.set_title(f"Topomap chain «{args.name}» — {n} nodes on recorded path", fontsize=11)

    inner = outer[1].subgridspec(n_rows, 1, hspace=0.12)
    for row in range(n_rows):
        ax = fig.add_subplot(inner[row])
        ax.imshow(filmstrip_row(images, row * cols, cols, args.thumb_h))
        ax.axis("off")
        i0, i1 = row * cols, min(n - 1, (row + 1) * cols - 1)
        ax.set_title(f"node images {i0} … {i1}", fontsize=8, loc="left", pad=2)

    out = args.out or os.path.join(args.gazebo_sim, f"topomap_{args.name}.png")
    fig.savefig(out, bbox_inches="tight", pad_inches=0.12)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
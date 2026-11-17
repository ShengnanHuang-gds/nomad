#!/usr/bin/env python3
"""BEV: teacher trajectory vs closed-loop odom path (if saved in episode JSON)."""
from __future__ import annotations
import argparse, json, os, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sys
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from episode_coords import path_xy_world

def load_gt_xy(run_id: str) -> np.ndarray:
    with open(os.path.join(ROOT, run_id, "traj_data.pkl"), "rb") as f:
        pos = pickle.load(f)["position"]
    return np.asarray(pos, dtype=np.float64)[:, :2]

def plot_one(ax, ep_path: str, title: str):
    with open(ep_path, encoding="utf-8") as f:
        ep = json.load(f)
    traj = ep.get("traj") or "house_run_06"
    gt = load_gt_xy(traj)
    ax.plot(gt[:, 0], gt[:, 1], "-", color="#bbb", lw=2.5, label="teacher GT")
    ax.plot(gt[0, 0], gt[0, 1], "go", ms=10, label="start")
    ax.plot(gt[-1, 0], gt[-1, 1], "r*", ms=14, label="goal")
    if ep.get("path_xy_world"):
        rw = np.asarray(ep["path_xy_world"], dtype=np.float64)
    elif ep.get("path_xy"):
        raw = np.asarray(ep["path_xy"], dtype=np.float64)
        rw = path_xy_world(ep, raw, gt[0])
    else:
        rw = None
    if rw is not None and len(rw):
        ax.plot(rw[:, 0], rw[:, 1], "-", color="#d62728", lw=2, label="robot odom")
        ax.plot(rw[0, 0], rw[0, 1], "s", color="#ff7f0e", ms=8)
        ax.plot(rw[-1, 0], rw[-1, 1], "x", color="#d62728", ms=10)
    else:
        cn = int(ep.get("closest_node", 0))
        gn = int(ep.get("goal_node", len(gt) - 1))
        ix = min(max(cn, 0), len(gt) - 1)
        ax.plot(gt[ix, 0], gt[ix, 1], "D", color="#1f77b4", ms=10, label=f"node {cn}/{gn}")
        ax.text(0.02, 0.98, "no path_xy", transform=ax.transAxes, va="top", fontsize=8, color="#555")
    succ = ep.get("success", False)
    pm = float(ep.get("path_odom_m", 0))
    ax.set_title(f"{title}\nsuccess={succ}  path={pm:.2f}m")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc="best")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-dir", default=os.path.join(ROOT, "episodes_eval_gpu"))
    parser.add_argument("--out", default=os.path.join(ROOT, "episodes_eval_gpu_routes.png"))
    args = parser.parse_args()
    eps = sorted(f for f in os.listdir(args.episode_dir) if f.endswith(".json") and f.startswith("house_"))
    if not eps:
        raise SystemExit(f"no episodes in {args.episode_dir}")
    n = len(eps)
    cols = 2
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 6 * rows), dpi=120)
    axes = np.atleast_1d(axes).reshape(rows, cols)
    for i, fn in enumerate(eps):
        r, c = divmod(i, cols)
        plot_one(axes[r, c], os.path.join(args.episode_dir, fn), fn.replace(".json", ""))
    for j in range(i + 1, rows * cols):
        r, c = divmod(j, cols)
        axes[r, c].axis("off")
    fig.suptitle("Hold-out: gray=teacher, red=robot odom", fontsize=12)
    fig.tight_layout()
    fig.savefig(args.out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.abspath(args.out))

if __name__ == "__main__":
    main()
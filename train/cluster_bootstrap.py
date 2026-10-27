"""Frame-level vs trajectory-level (cluster) bootstrap CIs on the locked far frames.

The 1000 locked frames come from 263 test trajectories, so frames of one trajectory are
correlated. The cluster bootstrap resamples trajectories with replacement and keeps all of
their frames, which gives honest intervals. Uses saved per-frame results only.

  goal use     masked ADE - ADE with a condition
  kept         use / use with the true goal position (ratio of means)
  paired diff  use(A) - use(B) on the same frames

Run from train/:
    python -u cluster_bootstrap.py
"""

import argparse
import json
import os

import numpy as np

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv

WAYPOINT_NPZ = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/eval_waypoint/locked_per_frame.npz"
SELECTION = "logs/revalidation/selection.json"


class Boot:
    def __init__(self, traj, n_boot, seed):
        self.n = len(traj)
        _u, self.cluster = np.unique(traj, return_inverse=True)
        self.k = self.cluster.max() + 1
        rng = np.random.default_rng(seed)
        self.frame_idx = rng.integers(0, self.n, size=(n_boot, self.n))
        self.traj_idx = rng.integers(0, self.k, size=(n_boot, self.k))

    def _cluster_sums(self, x, mask):
        s = np.bincount(self.cluster[mask], weights=x[mask], minlength=self.k)
        c = np.bincount(self.cluster[mask], minlength=self.k).astype(np.float64)
        return s, c

    def ratio(self, num, den, mask=None):
        """Point estimate and (frame CI, trajectory CI) of mean(num) / mean(den) on the masked frames."""
        mask = np.ones(self.n, bool) if mask is None else mask
        point = num[mask].mean() / den[mask].mean()
        # frame level: resample within the masked frames
        idx = np.flatnonzero(mask)
        fi = idx[self.frame_idx[:, : len(idx)] % len(idx)]
        f = num[fi].mean(1) / den[fi].mean(1)
        sn, cn = self._cluster_sums(num, mask)
        sd, _ = self._cluster_sums(den, mask)
        tn, td, tc = sn[self.traj_idx].sum(1), sd[self.traj_idx].sum(1), cn[self.traj_idx].sum(1)
        ok = tc > 0
        t = (tn[ok] / tc[ok]) / (td[ok] / tc[ok])
        return point, np.percentile(f, [2.5, 97.5]), np.percentile(t, [2.5, 97.5])

    def mean(self, x, mask=None):
        mask = np.ones(self.n, bool) if mask is None else mask
        idx = np.flatnonzero(mask)
        fi = idx[self.frame_idx[:, : len(idx)] % len(idx)]
        f = x[fi].mean(1)
        s, c = self._cluster_sums(x, mask)
        ts, tc = s[self.traj_idx].sum(1), c[self.traj_idx].sum(1)
        ok = tc > 0
        t = ts[ok] / tc[ok]
        return x[mask].mean(), np.percentile(f, [2.5, 97.5]), np.percentile(t, [2.5, 97.5]), int(len(np.unique(self.cluster[mask])))


def per_frame_uses(npz_path, names):
    d = np.load(npz_path)
    return {n: d[f"ade_mask_{n}"] - d[f"ade_{n}"] for n in names}


def main():
    parser = argparse.ArgumentParser(description="Trajectory-level bootstrap on saved locked per-frame results")
    parser.add_argument("--n-boot", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="logs/revalidation/cluster_bootstrap.csv")
    args = parser.parse_args()

    config_b = load_config("config/nomad_b40.yaml")
    dataset = make_split_dataset(config_b, "test")
    moments = load_paired_frames(PAIRED_FRAMES)
    sets, _l, _y = frame_sets(dataset, moments, meters_per_unit(dataset), SPREAD_NPZ)
    traj = np.array([n for n, _t, _g in moments])
    boot = Boot(traj, args.n_boot, args.seed)
    rows = []

    def report(label, x, mask_name="all", cm=True):
        m = sets[mask_name] if mask_name != "all" else None
        point, fci, tci, n_traj = boot.mean(x, m)
        s = 100.0 if cm else 1.0
        excl = "excludes 0" if (tci[0] > 0 or tci[1] < 0) else "crosses 0"
        print(f"  {label:<44} [{mask_name}] {s * point:+.2f}  frame [{s * fci[0]:+.2f}, {s * fci[1]:+.2f}]  "
              f"traj [{s * tci[0]:+.2f}, {s * tci[1]:+.2f}]  ({n_traj} traj, {excl})")
        rows.append({"comparison": label, "frames": mask_name, "estimate_cm": s * point, "frame_lo": s * fci[0],
                     "frame_hi": s * fci[1], "traj_lo": s * tci[0], "traj_hi": s * tci[1], "n_traj": n_traj,
                     "traj_ci_excludes_0": excl == "excludes 0"})

    # ---- waypoint / blend file ----
    d = np.load(WAYPOINT_NPZ)
    names = list(d["names"])
    use = {n: d["ade_mask"] - d[f"ade_{i}"] for i, n in enumerate(names)}
    if not np.array_equal(d["traj"], traj):
        raise RuntimeError("waypoint per-frame order does not match the locked frames")
    print("Paired differences, cm (95% CI: frame bootstrap vs trajectory bootstrap)")
    for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
        report("kappa blend - goal head (direct)", use["kappa blend"] - use["goal head (direct)"], set_name)
        report("waypoint head - goal head (direct)", use["waypoint head"] - use["goal head (direct)"], set_name)

    print("\nKept share of the true-goal use (ratio of means)")
    for n in ("goal head (direct)", "waypoint head", "kappa blend"):
        for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
            m = sets[set_name] if set_name != "all" else None
            point, fci, tci = boot.ratio(use[n], use["true goal"], m)
            print(f"  {n:<22} [{set_name}] {100 * point:5.1f}%  frame [{100 * fci[0]:.0f}, {100 * fci[1]:.0f}]  "
                  f"traj [{100 * tci[0]:.0f}, {100 * tci[1]:.0f}]")
            rows.append({"comparison": f"kept: {n}", "frames": set_name, "estimate_cm": 100 * point,
                         "frame_lo": 100 * fci[0], "frame_hi": 100 * fci[1], "traj_lo": 100 * tci[0], "traj_hi": 100 * tci[1]})

    # ---- re-selected checkpoints vs the direct test, from their own runs ----
    print("\nRe-selected checkpoints minus the direct test in the same run, cm")
    sel = json.load(open(SELECTION))
    for name, v in sel.items():
        if not isinstance(v, dict) or "kind" not in v:
            continue
        stem = os.path.splitext(v["checkpoint"])[0]
        path = os.path.join(v["run_dir"], f"eval_{stem}", "per_frame.npz")
        if not os.path.exists(path):
            print(f"  [skip] {name}: {path} missing")
            continue
        model = "Geo" if v["kind"] == "geo" else "E-dino"
        u = per_frame_uses(path, [model, "E-oracle+DINO"])
        report(f"{name} {v['checkpoint']} - direct", u[model] - u["E-oracle+DINO"])

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    write_csv(args.output, rows)
    print(f"\nSaved to {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()

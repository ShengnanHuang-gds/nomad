"""Fuse two direction predictors on the locked paired frames. No training.

Both heads output a von Mises (direction, kappa). Fusions:
  kappa-weighted   normalize(k1 d1 + k2 d2), kappa = |k1 d1 + k2 d2| (product of the two densities)
  max kappa        per row, the direction of the more confident head
Writes bearing_error.csv and predictions.npz (with fused_dir / fused_kappa and
maxk_dir / maxk_kappa) for eval_kappa_gate.py.

Run from train/:
    python -u eval_dir_fusion.py --predictions logs/nomad_d/<dino run>/eval_dino_dir_best/predictions.npz
"""

import argparse
import os

import numpy as np

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dino import bearing_rows, kappa_rows
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv


def fuse(d1, k1, d2, k2):
    resultant = k1[:, None] * d1 + k2[:, None] * d2
    norm = np.linalg.norm(resultant, axis=1, keepdims=True)
    return resultant / np.maximum(norm, 1e-6), norm[:, 0]


def main():
    parser = argparse.ArgumentParser(description="Fuse two direction heads by kappa")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--a", nargs=2, default=("dino_dir", "dino_kappa"), metavar=("DIR", "KAPPA"))
    parser.add_argument("--b", nargs=2, default=("dft_dir", "kappa"), metavar=("DIR", "KAPPA"))
    parser.add_argument("--names", nargs=2, default=("DINO", "D-ft"))
    parser.add_argument("--output-name", default="eval_fusion")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    args = parser.parse_args()

    config = load_config(args.config)
    dataset = make_split_dataset(config, "test")
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters_per_unit(dataset), args.spread)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(args.predictions)), args.output_name)
    os.makedirs(output_dir, exist_ok=True)

    pred = dict(np.load(args.predictions))
    d1, k1 = pred[args.a[0]], pred[args.a[1]]
    d2, k2 = pred[args.b[0]], pred[args.b[1]]
    pred["fused_dir"], pred["fused_kappa"] = fuse(d1, k1, d2, k2)
    pick = k1 >= k2
    pred["maxk_dir"] = np.where(pick[:, None], d1, d2)
    pred["maxk_kappa"] = np.maximum(k1, k2)

    name_a, name_b = args.names
    sources = {
        name_a: d1,
        name_b: d2,
        "kappa-weighted": pred["fused_dir"],
        "max kappa": pred["maxk_dir"],
        "straight ahead": None,
    }
    rows = bearing_rows(pred, sources, sets)
    print("Bearing error on the locked frames, degrees.")
    print(f"{'group':<7}{'frames':<28}{'source':<16}{'n':>6}{'median':>8}{'mean':>8}{'<=15deg':>9}")
    for row in rows:
        print(
            f"{row['group']:<7}{row['frames']:<28}{row['source']:<16}{row['n']:>6}"
            f"{row['median_deg']:8.1f}{row['mean_deg']:8.1f}{100 * row['within_15deg']:8.0f}%"
        )
    write_csv(os.path.join(output_dir, "bearing_error.csv"), rows)

    for group in ("4-8", "9-19", "20-40"):
        sel = pred["group"] == group
        print(f"{group}: {name_a} more confident on {100 * pick[sel].mean():.0f}% of rows")
    far = pred["group"] == "20-40"
    _bins, rho = kappa_rows(pred["fused_dir"][far], pred["fused_kappa"][far], pred["target"][far])
    print(f"kappa-weighted: far Spearman kappa vs error {rho:+.2f}")
    np.savez_compressed(os.path.join(output_dir, "predictions.npz"), **pred)
    print(f"Saved to {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

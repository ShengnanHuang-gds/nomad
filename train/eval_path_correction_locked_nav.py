"""Prepared locked-1000 nav eval for path correction (not run in setup phase).

Two modes (--mode):
  fixed_mu       — keep baseline mu_units; only replace 16-d path in e_dino_pos.
  deploy_blend   — full blend_path + wp_poly with corrected path (κ not recalibrated).

Implement before running; shares noise across baseline / dist / dir checkpoints.
"""
from __future__ import annotations

import argparse


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("fixed_mu", "deploy_blend"), required=True)
    ap.add_argument("--wp-base", required=True, help="Frozen pathact8 checkpoint")
    ap.add_argument("--wp-corr-a", default="", help="Distance correction best")
    ap.add_argument("--wp-corr-b", default="", help="Direction correction best")
    ap.add_argument("--e-run", default="logs/nomad/nomad_e_ft_pathact8")
    ap.add_argument("--frames", default="logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--num-samples", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--goal-pos-mode", default="blend_path")
    ap.add_argument("--path-source", default="wp_poly")
    args = ap.parse_args()
    raise SystemExit(
        "eval_path_correction_locked_nav.py is a prepared stub. "
        f"Requested mode={args.mode}. Wire WP correction forward + eval_e_dino sampling before running."
    )


if __name__ == "__main__":
    main()

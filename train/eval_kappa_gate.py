"""Kappa-gated D-ft direction into E-oracle, far group, no training.

Gate: on the top-k% kappa frames (threshold from all 1000 far frames), feed
E-oracle "D-ft dir + B dist"; on the rest, mask the goal (masked ADE, use 0).

Reported per frame set (all, strict turn, B masked spread):
  overall kept   gated use summed over every frame / clean use on every frame
  gated kept     on the gated frames only: D-ft use / clean use (the 50% gate)
Also kappa quintiles, and a reference gate that picks frames by the true
bearing error (perfect confidence), to show how far kappa is from ideal.

Run from train/:
    python -u eval_kappa_gate.py --run-dir logs/nomad_d/<dft run>
    python -u eval_kappa_gate.py --run-dir logs/nomad_d/<dino run> \
        --predictions eval_dino_dir_best/predictions.npz --dir-key dino_dir --kappa-key dino_kappa --label DINO
"""

import argparse
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT, run_e_oracle, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dir import angle_diff_deg, bearing_deg
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import load_model, subset_index

LEGACY_VARIANTS = ("clean", "D-ft dir + B dist", "true dir + B dist")
SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")
COVERAGES = (0.2, 0.4, 0.6, 1.0)


def boot_ratio(num, den, index):
    ratio = float(num.mean() / den.mean()) if den.mean() > 0 else float("nan")
    if index is None:
        return ratio, ratio, ratio
    boot = num[index].mean(axis=1) / np.maximum(den[index].mean(axis=1), 1e-9)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return ratio, float(lo), float(hi)


def far_predictions(path, dir_key, kappa_key):
    pred = np.load(path)
    far = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far], kind="stable")
    out = {key: pred[key][far][order] for key in ("target", "b_dist")}
    out["direction"] = pred[dir_key][far][order]
    out["kappa"] = pred[kappa_key][far][order]
    return out


def run_or_load(cache, args, config_e, dataset, moments, positions, device):
    variants = tuple(positions)
    if os.path.exists(cache):
        data = np.load(cache)
        stored = tuple(data["variants"]) if "variants" in data.files else LEGACY_VARIANTS
        if stored == variants:
            print(f"Per-frame ADE loaded from {cache}")
            return data["ade_mask"], {name: data[f"ade_{i}"] for i, name in enumerate(variants)}
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]
    model_e, scheduler_e = load_model(config_e, args.checkpoint_e, device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    ade, _fde, ade_mask, _fde_mask = run_e_oracle(
        model_e, scheduler_e, dataset, far, positions, device, args.num_samples, args.batch_size, variants
    )
    np.savez_compressed(
        cache,
        ade_mask=ade_mask,
        variants=np.array(variants),
        **{f"ade_{i}": ade[name] for i, name in enumerate(variants)},
    )
    return ade_mask, ade


def gate_rows(gate_name, scores, use_dir, use_clean, err, sets, coverages, rng, n_boot):
    rows = []
    for coverage in coverages:
        threshold = np.quantile(scores, 1.0 - coverage)
        gate = scores >= threshold
        for set_name in SET_NAMES:
            in_set = sets[set_name]
            idx = np.flatnonzero(in_set)
            gated = np.flatnonzero(in_set & gate)
            overall = np.where(gate, use_dir, 0.0)[idx]
            kept_all = boot_ratio(overall, use_clean[idx], subset_index(len(idx), n_boot, rng))
            kept_gated = boot_ratio(use_dir[gated], use_clean[gated], subset_index(len(gated), n_boot, rng))
            rows.append(
                {
                    "gate": gate_name,
                    "coverage": coverage,
                    "frames": set_name,
                    "n_set": int(len(idx)),
                    "n_gated": int(len(gated)),
                    "median_err_deg_gated": float(np.median(err[gated])),
                    "use_overall_cm": 100 * float(overall.mean()),
                    "clean_use_overall_cm": 100 * float(use_clean[idx].mean()),
                    "kept_overall": kept_all[0],
                    "kept_overall_lo": kept_all[1],
                    "kept_overall_hi": kept_all[2],
                    "use_gated_cm": 100 * float(use_dir[gated].mean()),
                    "clean_use_gated_cm": 100 * float(use_clean[gated].mean()),
                    "kept_gated": kept_gated[0],
                    "kept_gated_lo": kept_gated[1],
                    "kept_gated_hi": kept_gated[2],
                }
            )
    return rows


def kappa_bin_rows(kappa, use_dir, use_clean, err, sets, bins):
    edges = np.quantile(kappa, np.linspace(0.0, 1.0, bins + 1))
    which = np.clip(np.searchsorted(edges, kappa, side="right") - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        in_bin = which == b
        row = {"bin": b, "kappa_mean": float(kappa[in_bin].mean()), "median_err_deg": float(np.median(err[in_bin]))}
        for set_name in SET_NAMES:
            sel = in_bin & sets[set_name]
            clean = float(use_clean[sel].mean())
            row[f"{set_name} n"] = int(sel.sum())
            row[f"{set_name} dir_use_cm"] = 100 * float(use_dir[sel].mean())
            row[f"{set_name} clean_use_cm"] = 100 * clean
            row[f"{set_name} kept"] = float(use_dir[sel].mean() / clean) if clean > 0 else float("nan")
        rows.append(row)
    return rows


def pct(value):
    return f"{100 * value:5.0f}%"


def print_gates(rows, gate_name):
    print(f"\nGate by {gate_name}. use in cm, kept in % of clean E-oracle use [95% CI].")
    print(
        f"{'cover':>6}  {'frames':<18}{'n':>5}{'gated':>6}{'med err':>8}"
        f"{'overall use':>12}{'overall kept':>22}{'gated use':>10}{'gated clean':>12}{'gated kept':>22}"
    )
    for r in rows:
        if r["gate"] != gate_name:
            continue
        overall = f"{pct(r['kept_overall'])} [{100 * r['kept_overall_lo']:.0f}, {100 * r['kept_overall_hi']:.0f}]"
        gated = f"{pct(r['kept_gated'])} [{100 * r['kept_gated_lo']:.0f}, {100 * r['kept_gated_hi']:.0f}]"
        print(
            f"{100 * r['coverage']:5.0f}%  {r['frames']:<18}{r['n_set']:>5}{r['n_gated']:>6}"
            f"{r['median_err_deg_gated']:7.1f}d{r['use_overall_cm']:+12.2f}{overall:>22}"
            f"{r['use_gated_cm']:+10.2f}{r['clean_use_gated_cm']:+12.2f}{gated:>22}"
        )


def main():
    parser = argparse.ArgumentParser(description="Kappa-gated D-ft direction into E-oracle")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-e", default=E_CHECKPOINT)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--predictions", default="eval_goal_dir_best/predictions.npz", help="Inside --run-dir")
    parser.add_argument("--dir-key", default="dft_dir")
    parser.add_argument("--kappa-key", default="kappa")
    parser.add_argument("--label", default="D-ft")
    parser.add_argument("--output-name", default="eval_kappa_gate", help="Folder inside --run-dir")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--bins", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_b = load_config(args.config_b)
    config_e = load_config(args.config_e)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)
    output_dir = os.path.join(args.run_dir, args.output_name)
    os.makedirs(output_dir, exist_ok=True)

    pred = far_predictions(os.path.join(args.run_dir, args.predictions), args.dir_key, args.kappa_key)
    if len(pred["kappa"]) != len(moments):
        raise RuntimeError(f"{len(pred['kappa'])} far predictions for {len(moments)} frames")
    b_len = pred["b_dist"][:, None]
    gated_name = f"{args.label} dir + B dist"
    positions = {
        "clean": pred["target"],
        gated_name: pred["direction"] * b_len,
        "true dir + B dist": unit(pred["target"]) * b_len,
    }
    ade_mask, ade = run_or_load(
        os.path.join(output_dir, "per_frame_ade.npz"), args, config_e, dataset, moments, positions, device
    )

    use_clean = ade_mask - ade["clean"]
    use_dir = ade_mask - ade[gated_name]
    err = angle_diff_deg(bearing_deg(pred["direction"]), bearing_deg(pred["target"]))
    kappa = pred["kappa"]
    print(f"\nFar group, n={len(kappa)}. Clean E-oracle use {100 * use_clean.mean():+.2f} cm, ungated {args.label} "
          f"{100 * use_dir.mean():+.2f} cm, true dir + B dist {100 * (ade_mask - ade['true dir + B dist']).mean():+.2f} cm.")

    rng = np.random.default_rng(args.seed + 1)
    rows = gate_rows("kappa", kappa, use_dir, use_clean, err, sets, COVERAGES, rng, args.bootstrap)
    rows += gate_rows("true error (ideal)", -err, use_dir, use_clean, err, sets, COVERAGES[:-1], rng, args.bootstrap)
    print_gates(rows, "kappa")
    print_gates(rows, "true error (ideal)")
    write_csv(os.path.join(output_dir, "kappa_gate.csv"), rows)

    bins = kappa_bin_rows(kappa, use_dir, use_clean, err, sets, args.bins)
    print(f"\nKappa quintiles (0 = least confident). Per frame set: n, {args.label} use / clean use (cm), kept.")
    header = f"{'bin':>4}{'kappa':>8}{'med err':>8}"
    for set_name in SET_NAMES:
        header += f"  | {set_name[:16]:<16}{'':>18}"
    print(header)
    for row in bins:
        line = f"{row['bin']:>4}{row['kappa_mean']:8.2f}{row['median_err_deg']:7.1f}d"
        for set_name in SET_NAMES:
            line += (
                f"  | n={row[f'{set_name} n']:<4}{row[f'{set_name} dir_use_cm']:+6.2f}/"
                f"{row[f'{set_name} clean_use_cm']:+5.2f}{pct(row[f'{set_name} kept']):>7}"
            )
        print(line)
    write_csv(os.path.join(output_dir, "kappa_bins.csv"), bins)
    print(f"\nSaved to {os.path.abspath(output_dir)}")
    print(f"E-oracle saw only clean coordinates in training, so {args.label} rows are a lower bound for a trained E.")


if __name__ == "__main__":
    main()

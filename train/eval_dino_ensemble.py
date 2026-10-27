"""Ensemble several DINO bearing heads (kappa-weighted) and feed the result to E-oracle.

Inputs: predictions.npz files written by eval_goal_dino.py for each head (same
locked rows). Per row the ensemble direction is the normalized sum of kappa_i * d_i
and its kappa is |sum| / number of heads; the tta variant does the same with each
head's flip-averaged prediction. Reports bearing error by distance group and frame
set, then far goal use on the locked frames with one shared noise for: true position,
single head (plain, tta), ensemble (plain, tta) and, when best_config.json exists,
the val-tuned test-time transform applied to the ensemble. B is the no-position row.

Run from train/:
    python -u eval_dino_ensemble.py --predictions run1/eval_dino_dir_best/predictions.npz run2/... run3/...
"""

import argparse
import json
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import OUTPUT_DIR as TESTTIME_DIR
from eval_testtime import SET_NAMES, angle_err, rollout, transform


def ensemble(dirs, kappas):
    resultant = sum(k[:, None] * d for d, k in zip(dirs, kappas))
    norm = np.linalg.norm(resultant, axis=1, keepdims=True)
    return (resultant / np.maximum(norm, 1e-6)).astype(np.float32), (norm[:, 0] / len(dirs)).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Ensemble DINO bearing heads and test with E-oracle")
    parser.add_argument("--predictions", nargs="+", required=True)
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--checkpoint-e-oracle", default=E_CHECKPOINT)
    parser.add_argument("--best-config", default=os.path.join(TESTTIME_DIR, "best_config.json"))
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="logs/nomad_d/dino_ensemble")
    args = parser.parse_args()

    device = torch.device("cuda:0")
    os.makedirs(args.output_dir, exist_ok=True)
    preds = [dict(np.load(p)) for p in args.predictions]
    for p, path in zip(preds[1:], args.predictions[1:]):
        if not np.allclose(p["target"], preds[0]["target"]):
            raise RuntimeError(f"{path} rows do not match {args.predictions[0]}")
    base = preds[0]
    ens_dir, ens_kappa = ensemble([p["dino_dir"] for p in preds], [p["dino_kappa"] for p in preds])
    ens_tta_dir, ens_tta_kappa = ensemble([p["dino_tta_dir"] for p in preds], [p["dino_tta_kappa"] for p in preds])

    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lat, _yaw = frame_sets(dataset, moments, meters, args.spread)

    sources = {f"head {i}": p["dino_dir"] for i, p in enumerate(preds)}
    sources.update({"head 0 tta": base["dino_tta_dir"], "ensemble": ens_dir, "ensemble tta": ens_tta_dir})
    rows = []
    print("Bearing error, median deg (share within 15 deg; share above 45 deg)")
    for group in ("4-8", "9-19", "20-40"):
        in_group = base["group"] == group
        for set_name, mask in sets.items():
            if group != "20-40" and set_name != "all":
                continue
            sel = in_group & mask[base["frame_index"]]
            line = f"  {group:<6}{set_name:<28}"
            for name, d in sources.items():
                e = angle_err(d[sel], base["target"][sel])
                line += f" | {name} {np.median(e):5.1f} ({100 * (e <= 15).mean():3.0f}%; {100 * (e > 45).mean():3.0f}%)"
                rows.append({"group": group, "frames": set_name, "source": name, "median_deg": float(np.median(e)),
                             "within_15": float((e <= 15).mean()), "above_45": float((e > 45).mean())})
            print(line)
    write_csv(os.path.join(args.output_dir, "bearing_error.csv"), rows)

    far_m = base["group"] == "20-40"
    order = np.argsort(base["frame_index"][far_m], kind="stable")
    take = lambda arr: arr[far_m][order]
    steps = take(base["b_dist"]) / meters
    far = [(name, t, [g[4] for g in goals if g[0] == "20-40"][0]) for name, t, goals in moments]
    positions = {
        "true": (take(base["target"]) / meters).astype(np.float32),
        "head 0 (plain)": transform(take(base["dino_dir"]), take(base["dino_kappa"]), steps, 1.0, 0.0, 1.0),
        "head 0 (tta)": transform(take(base["dino_tta_dir"]), take(base["dino_tta_kappa"]), steps, 1.0, 0.0, 1.0),
        "ensemble (plain)": transform(take(ens_dir), take(ens_kappa), steps, 1.0, 0.0, 1.0),
        "ensemble (tta)": transform(take(ens_tta_dir), take(ens_tta_kappa), steps, 1.0, 0.0, 1.0),
    }
    if os.path.exists(args.best_config):
        with open(args.best_config) as f:
            best = json.load(f)
        d, k = (ens_tta_dir, ens_tta_kappa) if best["source"] == "tta" else (ens_dir, ens_kappa)
        positions[f"ensemble + {best['config']}"] = transform(take(d), take(k), steps, best["a"], best["c"], best["m"])
        print(f"Applying val-tuned transform to the ensemble: {best['config']}")

    config_eo = load_config(args.config_e_oracle)
    model_eo, sched_eo = load_model(config_eo, args.checkpoint_e_oracle, device)
    ade_mask, ade = rollout(model_eo, sched_eo, dataset, far, positions, device, args.num_samples, 8, args.seed + 1, "test")
    del model_eo
    torch.cuda.empty_cache()
    model_b, sched_b = load_model(config_b, args.checkpoint_b, device)
    ade_mask_b, ade_b = rollout(model_b, sched_b, dataset, far, {"B": None}, device, args.num_samples, 8, args.seed + 1, "test B")

    rng = np.random.default_rng(args.seed + 2)
    out = []
    print("\nLocked far frames. use = masked ADE - ADE (cm); kept vs E-oracle with the true position.")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        true_use = float((ade_mask[idx] - ade["true"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}")
        for name, am, a in [("B", ade_mask_b, ade_b["B"])] + [(k, ade_mask, ade[k]) for k in positions]:
            u = boot_mean(am[idx] - a[idx], boot)
            print(f"  {name:<40} use {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  kept {100 * u[0] / true_use:4.0f}%")
            out.append({"frames": set_name, "model": name, "use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2],
                        "kept": u[0] / true_use})
    boot_all = subset_index(len(far), args.bootstrap, rng)
    for k in list(positions)[2:]:
        u = boot_mean((ade_mask - ade[k]) - (ade_mask - ade["head 0 (plain)"]), boot_all)
        print(f"Paired: {k} - head 0 (plain) = {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}] cm")
    write_csv(os.path.join(args.output_dir, "test_results.csv"), out)
    print(f"Saved to {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()

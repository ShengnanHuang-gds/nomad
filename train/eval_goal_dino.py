"""Evaluate the DINOv2 direction head on the locked paired frames.

Uses the same (frame, group) rows and order as D-ft's predictions.npz, so the
target, B distance and D-ft direction come from there and the tables compare
like for like. Sources: DINO, DINO with flip test-time averaging, D-ft,
straight ahead. Writes bearing_error.csv, kappa_calibration_far.csv and a
predictions.npz with the D-ft keys plus dino_dir / dino_kappa and the TTA pair,
ready for eval_kappa_gate.py --dir-key dino_dir --kappa-key dino_kappa.

Run from train/:
    python -u eval_goal_dino.py --run-dir logs/nomad_d/<dino run>
"""

import argparse
import os
import pickle

import numpy as np
import torch

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dir import GROUP_ORDER, angle_diff_deg, bearing_deg
from eval_goal_head import make_split_dataset, meters_per_unit, spearman, write_csv
from train_goal_dino import CACHE_DIR, PairTokenHead, load_cache

DFT_PREDICTIONS = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/eval_goal_dir_best/predictions.npz"


@torch.no_grad()
def predict(head, features, curr_rows, goal_rows, ctx_rows, device, batch_size=512):
    dirs, kappas = [], []
    for start in range(0, len(curr_rows), batch_size):
        stop = start + batch_size
        curr = torch.from_numpy(features[curr_rows[start:stop]]).to(device).float()
        goal = torch.from_numpy(features[goal_rows[start:stop]]).to(device).float()
        ctx = None
        if ctx_rows.shape[1] > 0:
            chunk = ctx_rows[start:stop]
            ctx = torch.from_numpy(np.stack([features[chunk[:, j]] for j in range(chunk.shape[1])], axis=1))
            ctx = ctx.to(device).float()
        out = head(curr, goal, ctx)
        direction, kappa = out[0], out[1]
        dirs.append(direction.cpu().numpy())
        kappas.append(kappa.cpu().numpy())
    return np.concatenate(dirs), np.concatenate(kappas)


def combine_flip(direction, kappa, direction_flip, kappa_flip):
    mirrored = direction_flip * np.array([1.0, -1.0], dtype=np.float32)
    resultant = kappa[:, None] * direction + kappa_flip[:, None] * mirrored
    norm = np.linalg.norm(resultant, axis=1, keepdims=True)
    return resultant / np.maximum(norm, 1e-6), 0.5 * norm[:, 0]


def bearing_rows(pred, sources, sets):
    true_bearing = bearing_deg(pred["target"])
    rows = []
    for group in GROUP_ORDER:
        in_group = pred["group"] == group
        for set_name, frame_mask in sets.items():
            if group != "20-40" and set_name != "all":
                continue
            mask = in_group & frame_mask[pred["frame_index"]]
            for source, direction in sources.items():
                err = np.abs(true_bearing) if direction is None else angle_diff_deg(bearing_deg(direction), true_bearing)
                rows.append(
                    {
                        "group": group,
                        "frames": set_name,
                        "source": source,
                        "n": int(mask.sum()),
                        "median_deg": float(np.median(err[mask])),
                        "mean_deg": float(err[mask].mean()),
                        "within_15deg": float((err[mask] <= 15.0).mean()),
                    }
                )
    return rows


def kappa_rows(direction, kappa, target, bins=5):
    err = angle_diff_deg(bearing_deg(direction), bearing_deg(target))
    edges = np.quantile(kappa, np.linspace(0.0, 1.0, bins + 1))
    which = np.clip(np.searchsorted(edges, kappa, side="right") - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        sel = which == b
        rows.append(
            {
                "bin": b,
                "n": int(sel.sum()),
                "kappa_mean": float(kappa[sel].mean()),
                "implied_std_deg": float(np.degrees(1.0 / np.sqrt(kappa[sel].mean()))),
                "median_err_deg": float(np.median(err[sel])),
                "mean_err_deg": float(err[sel].mean()),
            }
        )
    return rows, spearman(kappa, err)


def main():
    parser = argparse.ArgumentParser(description="Evaluate the DINOv2 direction head on the locked frames")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="dino_dir_best.pth")
    parser.add_argument("--dft-predictions", default=DFT_PREDICTIONS)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    args = parser.parse_args()

    device = torch.device("cuda:0")
    config = load_config(args.config)
    dataset = make_split_dataset(config, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters, args.spread)
    output_dir = os.path.join(args.run_dir, f"eval_{os.path.splitext(args.checkpoint)[0]}")
    os.makedirs(output_dir, exist_ok=True)

    state = torch.load(os.path.join(args.run_dir, args.checkpoint), map_location=device, weights_only=False)
    meta, run_args = state["meta"], state["args"]
    context = run_args.get("context", 0)
    head = PairTokenHead(
        meta["dim"],
        meta["tokens"],
        run_args["width"],
        run_args["layers"],
        run_args["heads"],
        run_args["dropout"],
        context,
        n_sectors=run_args.get("n_sectors", 0),
    ).to(device)
    head.load_state_dict(state["head"])
    head.eval()
    print(f"DINO head epoch {state['epoch']}, val far median {state['far_median_deg']:.1f} deg")

    cache_path, rows, test_meta = load_cache(args.cache_dir, "test_paired")
    for key in ("model", "width", "height", "pool"):
        if test_meta[key] != meta[key]:
            raise RuntimeError(f"test cache {key}={test_meta[key]} but the head was trained on {meta[key]}")
    items = [(traj_name, t, g[4]) for traj_name, t, goals in moments for g in goals]
    curr_rows = np.array([rows[(traj_name, t)] for traj_name, t, _g in items])
    goal_rows = np.array([rows[(traj_name, g)] for traj_name, _t, g in items])
    ctx_rows = np.array(
        [[rows[(traj_name, t - j)] for j in range(1, context + 1)] for traj_name, t, _g in items], dtype=np.int64
    ).reshape(len(items), context)

    dft = dict(np.load(args.dft_predictions))
    if len(dft["target"]) != len(items):
        raise RuntimeError(f"{len(dft['target'])} D-ft rows for {len(items)} paired items")
    check = []
    for traj_name, t, g in items[:50]:
        with open(os.path.join(dataset.data_folder, traj_name, "traj_data.pkl"), "rb") as f:
            traj = pickle.load(f)
        pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)
        yaw = float(np.ravel(traj["yaw"][t])[0])
        d = pos[g] - pos[t]
        check.append([d[0] * np.cos(yaw) + d[1] * np.sin(yaw), -d[0] * np.sin(yaw) + d[1] * np.cos(yaw)])
    if not np.allclose(np.array(check), dft["target"][:50], atol=1e-3):
        raise RuntimeError("Paired item order does not match D-ft predictions")

    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    dino_dir, dino_kappa = predict(head, features, curr_rows, goal_rows, ctx_rows, device)
    pred = {**dft, "dino_dir": dino_dir, "dino_kappa": dino_kappa}
    if test_meta["flip"]:
        features_flip = np.load(os.path.join(cache_path, "features_flip.npy"), mmap_mode="r")
        flip_dir, flip_kappa = predict(head, features_flip, curr_rows, goal_rows, ctx_rows, device)
        pred["dino_tta_dir"], pred["dino_tta_kappa"] = combine_flip(dino_dir, dino_kappa, flip_dir, flip_kappa)

    sources = {"DINO": pred["dino_dir"]}
    if "dino_tta_dir" in pred:
        sources["DINO + flip TTA"] = pred["dino_tta_dir"]
    sources.update({"D-ft": pred["dft_dir"], "straight ahead": None})
    rows_out = bearing_rows(pred, sources, sets)
    print("\nBearing error on the locked frames, degrees.")
    print(f"{'group':<7}{'frames':<28}{'source':<17}{'n':>6}{'median':>8}{'mean':>8}{'<=15deg':>9}")
    for row in rows_out:
        print(
            f"{row['group']:<7}{row['frames']:<28}{row['source']:<17}{row['n']:>6}"
            f"{row['median_deg']:8.1f}{row['mean_deg']:8.1f}{100 * row['within_15deg']:8.0f}%"
        )
    write_csv(os.path.join(output_dir, "bearing_error.csv"), rows_out)

    far = pred["group"] == "20-40"
    calib = []
    for name, dkey, kkey in (("DINO", "dino_dir", "dino_kappa"), ("DINO + flip TTA", "dino_tta_dir", "dino_tta_kappa")):
        if dkey not in pred:
            continue
        bins, rho = kappa_rows(pred[dkey][far], pred[kkey][far], pred["target"][far])
        print(f"\n{name}: far kappa calibration, Spearman kappa vs error {rho:+.2f}")
        print(f"{'bin':>4}{'n':>6}{'kappa':>9}{'~std deg':>10}{'median err':>12}{'mean err':>10}")
        for row in bins:
            print(
                f"{row['bin']:>4}{row['n']:>6}{row['kappa_mean']:9.2f}{row['implied_std_deg']:10.1f}"
                f"{row['median_err_deg']:12.1f}{row['mean_err_deg']:10.1f}"
            )
            calib.append({"source": name, "spearman": rho, **row})
    write_csv(os.path.join(output_dir, "kappa_calibration_far.csv"), calib)
    np.savez_compressed(os.path.join(output_dir, "predictions.npz"), **pred)
    print(f"\nSaved to {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

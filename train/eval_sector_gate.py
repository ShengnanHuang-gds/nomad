"""Evaluate sector inference gating on locked frames (DINO token cache only, no image LMDB).

    python -u eval_sector_gate.py --run-dir logs/nomad_d/nomad_dino_dir_sector3_2026_10_24_10_10_28
"""

import argparse
import os
import pickle

import numpy as np
import torch

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, load_spread, turning_mask
from eval_goal_dino import DFT_PREDICTIONS, bearing_rows, combine_flip, kappa_rows, predict
from eval_goal_dir import angle_diff_deg, bearing_deg
from eval_goal_head import write_csv
from train_goal_dino import CACHE_DIR, PairTokenHead, load_cache
from vint_train.models.nomad.sector_gate import apply_sector_gate_numpy


def _scalar(value):
    return float(np.ravel(np.asarray(value, dtype=np.float64))[0])


def frame_motion_pkl(data_folder, moments, len_traj_pred, waypoint_spacing, meters):
    lateral, yaw = [], []
    step = len_traj_pred * waypoint_spacing
    for traj_name, t, _goals in moments:
        with open(os.path.join(data_folder, traj_name, "traj_data.pkl"), "rb") as f:
            traj = pickle.load(f)
        pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)
        yaws = traj["yaw"]
        dy = _scalar(yaws[min(t + step, len(yaws) - 1)]) - _scalar(yaws[t])
        dy = (dy + np.pi) % (2.0 * np.pi) - np.pi
        yaw.append(float(np.degrees(dy)))
        if t + step < len(pos):
            delta = pos[t + step] - pos[t]
        else:
            delta = pos[-1] - pos[t]
        cy, sy = np.cos(_scalar(yaws[t])), np.sin(_scalar(yaws[t]))
        lat = (-delta[0] * sy + delta[1] * cy) * meters
        lateral.append(float(lat))
    return np.array(lateral), np.array(yaw)


def frame_sets_pkl(config, moments, spread_path):
    dc = config["datasets"]["go_stanford"]
    meters = float(dc.get("metric_waypoint_spacing", 0.12)) * int(config.get("waypoint_spacing", 2))
    lateral, yaw = frame_motion_pkl(
        dc["data_folder"],
        moments,
        int(config["len_traj_pred"]),
        int(config.get("waypoint_spacing", 1)),
        meters,
    )
    sets = {
        "all": np.ones(len(moments), dtype=bool),
        "turn 0.15m/20deg": turning_mask(lateral, yaw, (0.15, 20.0)),
        "turn 0.30m/45deg": turning_mask(lateral, yaw, (0.30, 45.0)),
    }
    sets["straight (not 0.15m/20deg)"] = ~sets["turn 0.15m/20deg"]
    spread = load_spread(spread_path, len(moments))
    if spread is not None:
        sets["B masked spread"] = spread
    return sets


@torch.no_grad()
def predict_with_sectors(head, features, curr_rows, goal_rows, ctx_rows, device, batch_size=512):
    dirs, kappas, logits_list = [], [], []
    has_sector = getattr(head, "sector", None) is not None
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
        if has_sector and len(out) > 2:
            logits_list.append(out[2].cpu().numpy())
    dirs = np.concatenate(dirs)
    kappas = np.concatenate(kappas)
    logits = np.concatenate(logits_list) if logits_list else None
    return dirs, kappas, logits


def main():
    parser = argparse.ArgumentParser(description="Sector gate eval on locked frames (no LMDB)")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--checkpoint", default="dino_dir_best.pth")
    parser.add_argument("--dft-predictions", default=DFT_PREDICTIONS)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--mid-deg", type=float, default=15.0)
    parser.add_argument("--min-conf", type=float, default=0.55)
    parser.add_argument("--blend", type=float, default=0.65)
    parser.add_argument("--snap-deg", type=float, default=30.0)
    args = parser.parse_args()

    device = torch.device("cuda:0")
    config = load_config(args.config)
    moments = load_paired_frames(args.frames)
    sets = frame_sets_pkl(config, moments, args.spread)
    output_dir = os.path.join(args.run_dir, "eval_sector_gate")
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
    if head.sector is None:
        raise RuntimeError("Checkpoint has no sector head; use sector3 run-dir")

    cache_path, rows, test_meta = load_cache(args.cache_dir, "test_paired")
    items = [(traj_name, t, g[4]) for traj_name, t, goals in moments for g in goals]
    curr_rows = np.array([rows[(traj_name, t)] for traj_name, t, _g in items])
    goal_rows = np.array([rows[(traj_name, g)] for traj_name, _t, g in items])
    ctx_rows = np.array(
        [[rows[(traj_name, t - j)] for j in range(1, context + 1)] for traj_name, t, _g in items], dtype=np.int64
    ).reshape(len(items), context)

    dft = dict(np.load(args.dft_predictions))
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    raw_dir, kappa, logits = predict_with_sectors(head, features, curr_rows, goal_rows, ctx_rows, device)
    gate_kw = dict(mid_deg=args.mid_deg, snap_deg=args.snap_deg, min_conf=args.min_conf, blend_on_mismatch=args.blend)
    gated_dir = apply_sector_gate_numpy(raw_dir, logits, **gate_kw)

    pred = {**dft, "dino_dir": raw_dir, "dino_kappa": kappa, "dino_gated_dir": gated_dir}
    far = pred["group"] == "20-40"
    tb = bearing_deg(pred["target"])
    for name, key in (("raw", "dino_dir"), ("gated", "dino_gated_dir")):
        err = np.abs(angle_diff_deg(bearing_deg(pred[key]), tb))
        print(
            f"{name} far: median {np.median(err[far]):.1f} deg  "
            f">45% {100 * (err[far] > 45).mean():.1f}%  n={int(far.sum())}"
        )

    sources = {"DINO raw": pred["dino_dir"], "DINO sector gate": pred["dino_gated_dir"]}
    rows_out = bearing_rows(pred, sources, sets)
    write_csv(os.path.join(output_dir, "bearing_error.csv"), rows_out)
    np.savez_compressed(os.path.join(output_dir, "predictions.npz"), **pred)
    print(f"\nSaved to {os.path.abspath(output_dir)} (gate min_conf={args.min_conf} blend={args.blend})")


if __name__ == "__main__":
    main()

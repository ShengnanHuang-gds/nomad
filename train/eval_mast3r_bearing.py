"""Zero-shot goal bearing from MASt3R relative pose. No training.

For each locked (frame, group) row: view1 = current frame, view2 = goal frame,
both 160x120 upsampled to 512x384. MASt3R predicts view2's pixels as 3D points
in view1's camera frame. The focal is estimated from view1's own point map
(same robot camera for both views), then PnP + RANSAC on view2's confident
pixels gives the goal camera center C in view1's frame. Camera axes are x right,
y down, z forward, so the robot-frame bearing is atan2(-C_x, C_z) and the
horizontal distance |(C_z, C_x)| (MASt3R metric model, scale is approximate).

Rows follow D-ft's predictions.npz order, so target and B distance come from
there. Writes predictions.npz with mast3r_dir, mast3r_score (PnP inliers) and
mast3r_dist for eval_kappa_gate.py --dir-key mast3r_dir --kappa-key mast3r_score.

Run from train/:
    python -u eval_mast3r_bearing.py
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np
import torch
from PIL import Image
from safetensors.torch import load_file
from tqdm import tqdm

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_dino import bearing_rows
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv
from vint_train.data.data_utils import get_data_path

MAST3R_ROOT = "C:/Users/61078/Desktop/nomad/third_party/mast3r"
CHECKPOINT = os.path.join(MAST3R_ROOT, "checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric")
DFT_PREDICTIONS = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/eval_goal_dir_best/predictions.npz"
OUTPUT_DIR = "logs/nomad_d/mast3r_zero_shot"
WIDTH, HEIGHT = 512, 384


def load_image(data_folder, traj_name, t):
    img = Image.open(get_data_path(data_folder, traj_name, t)).convert("RGB").resize((WIDTH, HEIGHT), Image.BICUBIC)
    x = torch.from_numpy(np.asarray(img, dtype=np.float32) / 255.0).permute(2, 0, 1)
    return (x - 0.5) / 0.5


def relative_pose(pts1, pts2_in1, conf2, stride, conf_quantile, focal_fn):
    """Return (bearing direction [2], horizontal distance, inliers) for one pair.

    MASt3R's point confidence sits near its floor of 1 on these images, so the
    PnP correspondences are the top (1 - conf_quantile) share of view2 pixels.
    """
    focal = float(focal_fn(pts1))
    k = np.array([[focal, 0.0, WIDTH / 2.0], [0.0, focal, HEIGHT / 2.0], [0.0, 0.0, 1.0]])
    v, u = np.mgrid[0:HEIGHT:stride, 0:WIDTH:stride]
    xyz = pts2_in1[::stride, ::stride].reshape(-1, 3)
    c = conf2[::stride, ::stride].reshape(-1)
    uv = np.stack([u.reshape(-1), v.reshape(-1)], axis=1).astype(np.float64) + 0.5
    keep = (c >= np.quantile(c, conf_quantile)) & np.isfinite(xyz).all(axis=1) & (xyz[:, 2] > 0)
    if keep.sum() < 12:
        return np.array([1.0, 0.0]), 0.0, 0
    ok, rvec, tvec, inliers = cv2.solvePnPRansac(
        xyz[keep].astype(np.float64), uv[keep], k, None,
        iterationsCount=300, reprojectionError=4.0, confidence=0.999, flags=cv2.SOLVEPNP_SQPNP,
    )
    if not ok or inliers is None:
        return np.array([1.0, 0.0]), 0.0, 0
    rot, _ = cv2.Rodrigues(rvec)
    center = -rot.T @ tvec.reshape(3)
    planar = np.array([center[2], -center[0]])
    norm = np.linalg.norm(planar)
    if norm < 1e-6:
        return np.array([1.0, 0.0]), 0.0, int(len(inliers))
    return planar / norm, float(norm), int(len(inliers))


def main():
    parser = argparse.ArgumentParser(description="Zero-shot goal bearing from MASt3R")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint", default=CHECKPOINT)
    parser.add_argument("--dft-predictions", default=DFT_PREDICTIONS)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--groups", nargs="+", default=["4-8", "9-19", "20-40"])
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--stride", type=int, default=4, help="Pixel stride for PnP correspondences")
    parser.add_argument("--conf-quantile", type=float, default=0.5, help="Keep view2 pixels above this quantile")
    args = parser.parse_args()

    sys.path.insert(0, MAST3R_ROOT)
    from mast3r.model import AsymmetricMASt3R
    from dust3r.post_process import estimate_focal_knowing_depth

    device = torch.device("cuda:0")
    config = load_config(args.config)
    dataset = make_split_dataset(config, "test")
    moments = load_paired_frames(args.frames)
    sets, _lateral, _yaw = frame_sets(dataset, moments, meters_per_unit(dataset), args.spread)
    os.makedirs(args.output_dir, exist_ok=True)

    pred = dict(np.load(args.dft_predictions))
    items = [(traj_name, t, g[4], g[0]) for traj_name, t, goals in moments for g in goals]
    if len(items) != len(pred["target"]):
        raise RuntimeError("Paired item order does not match D-ft predictions")
    todo = [i for i, item in enumerate(items) if item[3] in args.groups]

    with open(os.path.join(args.checkpoint, "config.json")) as f:
        model = AsymmetricMASt3R(**json.load(f))
    missing, unexpected = model.load_state_dict(load_file(os.path.join(args.checkpoint, "model.safetensors")), strict=False)
    missing = [key for key in missing if ".scratch.layer_rn." not in key]
    if missing or unexpected:
        raise RuntimeError(f"MASt3R weights: missing {missing[:5]} unexpected {unexpected[:5]}")
    model = model.to(device).eval()
    pp = torch.tensor([[WIDTH / 2.0, HEIGHT / 2.0]], device=device)

    def focal_fn(pts1):
        pts = torch.from_numpy(pts1)[None].to(device)
        return estimate_focal_knowing_depth(pts, pp, focal_mode="weiszfeld")[0].item()

    n = len(items)
    direction = np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (n, 1))
    dist = np.zeros(n, dtype=np.float32)
    score = np.zeros(n, dtype=np.float32)
    shape = torch.tensor([[HEIGHT, WIDTH]], dtype=torch.int32)
    for start in tqdm(range(0, len(todo), args.batch_size), desc="MASt3R"):
        chunk = todo[start : start + args.batch_size]
        img1 = torch.stack([load_image(dataset.data_folder, items[i][0], items[i][1]) for i in chunk]).to(device)
        img2 = torch.stack([load_image(dataset.data_folder, items[i][0], items[i][2]) for i in chunk]).to(device)
        b = len(chunk)
        view1 = {"img": img1, "true_shape": shape.repeat(b, 1), "instance": [f"c{i}" for i in chunk]}
        view2 = {"img": img2, "true_shape": shape.repeat(b, 1), "instance": [f"g{i}" for i in chunk]}
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
            res1, res2 = model(view1, view2)
        pts1 = res1["pts3d"].float().cpu().numpy()
        pts2 = res2["pts3d_in_other_view"].float().cpu().numpy()
        conf2 = res2["conf"].float().cpu().numpy()
        for j, i in enumerate(chunk):
            d, r, inl = relative_pose(pts1[j], pts2[j], conf2[j], args.stride, args.conf_quantile, focal_fn)
            direction[i], dist[i], score[i] = d, r, inl

    pred["mast3r_dir"], pred["mast3r_dist"], pred["mast3r_score"] = direction, dist, score
    sources = {"MASt3R": direction, "D-ft": pred["dft_dir"], "straight ahead": None}
    rows = bearing_rows(pred, sources, sets)
    rows = [row for row in rows if row["group"] in args.groups]
    print("\nBearing error on the locked frames, degrees.")
    print(f"{'group':<7}{'frames':<28}{'source':<16}{'n':>6}{'median':>8}{'mean':>8}{'<=15deg':>9}")
    for row in rows:
        print(
            f"{row['group']:<7}{row['frames']:<28}{row['source']:<16}{row['n']:>6}"
            f"{row['median_deg']:8.1f}{row['mean_deg']:8.1f}{100 * row['within_15deg']:8.0f}%"
        )
    write_csv(os.path.join(args.output_dir, "bearing_error.csv"), rows)
    for group in args.groups:
        sel = pred["group"] == group
        true_len = np.linalg.norm(pred["target"][sel], axis=1)
        ratio = np.median(dist[sel] / np.maximum(true_len, 1e-6))
        print(f"{group}: median MASt3R distance / true {ratio:.2f}, median inliers {np.median(score[sel]):.0f}, "
              f"failed {100 * (score[sel] == 0).mean():.1f}%")
    np.savez_compressed(os.path.join(args.output_dir, "predictions.npz"), **pred)
    print(f"Saved to {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()

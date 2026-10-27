"""Evaluate the goal-position head D on the locked paired frames.

Reports position error in meters by goal distance, on fixed turning and
spread frames, sigma calibration, and the far-bin E-oracle gain expected
from the position-noise curve.

Run from train/:

    python -u eval_goal_head.py --head logs/nomad_d/<run>/goal_head_latest.pth
"""

import argparse
import csv
import os

import numpy as np
import torch
from torchvision import transforms
from tqdm import tqdm

from eval_by_distance import (
    DISTANCE_GROUPS,
    build_nomad,
    load_config,
    load_observation,
    load_paired_frames,
)
from eval_frame_sets import NOISE_CURVE, PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from vint_train.data.vint_dataset import ViNT_Dataset
from vint_train.models.nomad.nomad import GoalPosHead

B_CHECKPOINT = "logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth"
IMAGE_NORMALIZE = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])


def make_split_dataset(config, split):
    data_config = config["datasets"]["go_stanford"]
    return ViNT_Dataset(
        data_folder=data_config["data_folder"],
        data_split_folder=data_config[split],
        dataset_name="go_stanford",
        image_size=config["image_size"],
        waypoint_spacing=data_config.get("waypoint_spacing", 1),
        min_dist_cat=config["distance"]["min_dist_cat"],
        max_dist_cat=config["distance"]["max_dist_cat"],
        min_action_distance=config["action"]["min_dist_cat"],
        max_action_distance=config["action"]["max_dist_cat"],
        negative_mining=data_config.get("negative_mining", True),
        len_traj_pred=config["len_traj_pred"],
        learn_angle=config["learn_angle"],
        context_size=config["context_size"],
        context_type=config.get("context_type", "temporal"),
        end_slack=data_config.get("end_slack", 0),
        goals_per_obs=data_config.get("goals_per_obs", 1),
        normalize=config["normalize"],
        goal_type=config.get("goal_type", "image"),
    )


def meters_per_unit(dataset):
    return float(dataset.data_config["metric_waypoint_spacing"]) * dataset.waypoint_spacing


def load_frozen_nomad(config, checkpoint_path, device):
    if config.get("goal_pos_oracle"):
        raise RuntimeError("D reads baseline B features. Use a config without goal_pos_oracle.")
    model, _scheduler = build_nomad(config)
    map_loc = device
    if isinstance(map_loc, str):
        map_loc = torch.device(map_loc)
    if map_loc.type == "cuda" and not torch.cuda.is_available():
        map_loc = torch.device("cpu")
        device = map_loc
    state_dict = torch.load(checkpoint_path, map_location=map_loc, weights_only=False)
    if isinstance(state_dict, dict) and "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]
    incompatible = model.load_state_dict(state_dict, strict=False)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(
            f"{checkpoint_path} does not match the B config: missing {len(incompatible.missing_keys)} "
            f"unexpected {len(incompatible.unexpected_keys)}"
        )
    model = model.to(device)
    model.eval()
    model.requires_grad_(False)
    print(f"Frozen B loaded, all keys matched: {checkpoint_path}")
    return model


def load_head(path, embedding_dim, device):
    head = GoalPosHead(embedding_dim)
    head.load_state_dict(torch.load(path, map_location=device, weights_only=False))
    return head.to(device).eval()


def normalize_images(obs_image, goal_image, device):
    """obs_image [B, 3*(context+1), H, W], goal_image [B, 3, H, W]. Matches train_nomad."""
    obs_parts = torch.split(obs_image, 3, dim=1)
    batch_obs = torch.cat([IMAGE_NORMALIZE(part) for part in obs_parts], dim=1).to(device)
    batch_goal = IMAGE_NORMALIZE(goal_image).to(device)
    return batch_obs, batch_goal


def encode(model, batch_obs, batch_goal):
    no_mask = torch.zeros((batch_obs.shape[0],), dtype=torch.long, device=batch_obs.device)
    return model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)


@torch.no_grad()
def predict_paired(model, head, dataset, moments, device, batch_size):
    """One prediction per (frame, distance group). Positions in meters."""
    meters = meters_per_unit(dataset)
    items = []
    for frame_index, (traj_name, t, goals) in enumerate(moments):
        for name, _lo, _hi, k, goal_time in goals:
            items.append((frame_index, traj_name, t, name, k, goal_time))

    mu_all, sigma_all, target_all = [], [], []
    for start in tqdm(range(0, len(items), batch_size), desc="D paired frames", leave=False):
        chunk = items[start : start + batch_size]
        obs_list, goal_list, pos_list = [], [], []
        for _frame, traj_name, t, _name, _k, goal_time in chunk:
            obs, goal, _actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
            pos_list.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        mu, sigma = head(encode(model, batch_obs, batch_goal))
        mu_all.append(mu.cpu().numpy())
        sigma_all.append(sigma.cpu().numpy())
        target_all.append(np.stack(pos_list) * meters)

    return {
        "frame_index": np.array([item[0] for item in items]),
        "group": np.array([item[3] for item in items]),
        "k": np.array([item[4] for item in items]),
        "mu": np.concatenate(mu_all),
        "sigma": np.concatenate(sigma_all),
        "target": np.concatenate(target_all),
    }


def spearman(a, b):
    if len(a) < 3:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    return float(np.corrcoef(ra, rb)[0, 1])


def load_noise_curve(path):
    try:
        with open(path, newline="") as f:
            rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(f)]
    except FileNotFoundError:
        return None
    rows.sort(key=lambda row: row["mean_position_error_m"])
    x = np.array([row["mean_position_error_m"] for row in rows])
    y = np.array([row["ade_use"] for row in rows])
    return x, y


def error_stats(pred, rows_mask):
    err = np.linalg.norm(pred["mu"][rows_mask] - pred["target"][rows_mask], axis=1)
    sigma = pred["sigma"][rows_mask]
    sigma_norm = np.linalg.norm(sigma, axis=1)
    z = np.abs(pred["mu"][rows_mask] - pred["target"][rows_mask]) / sigma
    goal_dist = np.linalg.norm(pred["target"][rows_mask], axis=1)
    if len(err) == 0:
        nan = float("nan")
        return {"n": 0, "err_mean": nan, "err_median": nan, "err_p90": nan, "goal_dist_mean": nan,
                "sigma_norm_mean": nan, "spearman_sigma_err": nan, "coverage_1sigma": nan}
    return {
        "n": int(len(err)),
        "err_mean": float(err.mean()),
        "err_median": float(np.median(err)),
        "err_p90": float(np.percentile(err, 90)),
        "goal_dist_mean": float(goal_dist.mean()),
        "sigma_norm_mean": float(sigma_norm.mean()),
        "spearman_sigma_err": spearman(sigma_norm, err),
        "coverage_1sigma": float((z < 1.0).mean()),
    }


def summarize(pred, sets, noise_curve):
    rows = []
    frame_index = pred["frame_index"]
    for _lo, _hi, group in DISTANCE_GROUPS:
        in_group = pred["group"] == group
        for set_name, frame_mask in sets.items():
            if group != "20-40" and set_name != "all":
                continue
            row_mask = in_group & frame_mask[frame_index]
            row = {"group": group, "frames": set_name, **error_stats(pred, row_mask)}
            if noise_curve is not None and group == "20-40":
                x, y = noise_curve
                kept = float(np.interp(row["err_mean"], x, y))
                row["oracle_use_at_this_error"] = kept
                row["oracle_use_clean"] = float(y[0])
                row["oracle_use_kept_fraction"] = kept / float(y[0])
            rows.append(row)
    return rows


def calibration_bins(pred, group="20-40", bins=5):
    mask = pred["group"] == group
    err = np.linalg.norm(pred["mu"][mask] - pred["target"][mask], axis=1)
    sigma_norm = np.linalg.norm(pred["sigma"][mask], axis=1)
    edges = np.quantile(sigma_norm, np.linspace(0.0, 1.0, bins + 1))
    which = np.clip(np.searchsorted(edges, sigma_norm, side="right") - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        sel = which == b
        rows.append(
            {
                "group": group,
                "bin": b,
                "n": int(sel.sum()),
                "sigma_norm_mean": float(sigma_norm[sel].mean()) if sel.any() else float("nan"),
                "err_mean": float(err[sel].mean()) if sel.any() else float("nan"),
            }
        )
    return rows


def print_summary(rows, calib):
    print("\nPosition error of D, meters (||mu - true goal_pos||).")
    print("coverage_1sigma: share of axes with |error| < sigma. A calibrated Gaussian gives 0.683.")
    print(
        f"{'group':<7}{'frames':<28}{'n':>6}{'goal m':>8}{'mean':>8}{'median':>8}{'p90':>8}"
        f"{'sigma':>8}{'rho':>7}{'cov':>7}{'oracle kept':>14}"
    )
    for row in rows:
        kept = row.get("oracle_use_at_this_error")
        kept_text = "" if kept is None else f"{100 * kept:.1f}cm {100 * row['oracle_use_kept_fraction']:.0f}%"
        print(
            f"{row['group']:<7}{row['frames']:<28}{row['n']:>6}{row['goal_dist_mean']:8.2f}"
            f"{row['err_mean']:8.3f}{row['err_median']:8.3f}{row['err_p90']:8.3f}"
            f"{row['sigma_norm_mean']:8.3f}{row['spearman_sigma_err']:7.2f}{row['coverage_1sigma']:7.2f}"
            f"{kept_text:>14}"
        )
    print("oracle kept: far E-oracle ADE use read off the noise curve at D's mean error (pessimistic, isotropic noise).")
    print("\nFar calibration by predicted sigma quintile (sigma = ||(sigma_x, sigma_y)||).")
    print(f"{'bin':>4}{'n':>6}{'sigma':>9}{'error':>9}")
    for row in calib:
        print(f"{row['bin']:>4}{row['n']:>6}{row['sigma_norm_mean']:9.3f}{row['err_mean']:9.3f}")


def write_csv(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


class PairedEvaluator:
    """Loads the locked frames and fixed frame sets once, then scores any head."""

    def __init__(self, dataset, frames_path=PAIRED_FRAMES, spread_path=SPREAD_NPZ, noise_curve_path=NOISE_CURVE):
        self.dataset = dataset
        self.moments = load_paired_frames(frames_path)
        self.sets, _lateral, _yaw = frame_sets(dataset, self.moments, meters_per_unit(dataset), spread_path)
        self.noise_curve = load_noise_curve(noise_curve_path)
        counts = ", ".join(f"{name} {int(mask.sum())}" for name, mask in self.sets.items())
        print(f"Paired frames {len(self.moments)}: {counts}")

    def run(self, model, head, device, batch_size, output_dir=None, verbose=True):
        was_training = head.training
        head.eval()
        pred = predict_paired(model, head, self.dataset, self.moments, device, batch_size)
        if was_training:
            head.train()
        rows = summarize(pred, self.sets, self.noise_curve)
        calib = calibration_bins(pred)
        if verbose:
            print_summary(rows, calib)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            write_csv(os.path.join(output_dir, "position_error.csv"), rows)
            write_csv(os.path.join(output_dir, "calibration_far.csv"), calib)
            np.savez_compressed(os.path.join(output_dir, "predictions.npz"), **pred)
            print(f"Saved D evaluation to {os.path.abspath(output_dir)}")
        return rows, calib, pred


def main():
    parser = argparse.ArgumentParser(description="Evaluate goal-position head D on the paired frames")
    parser.add_argument("--config", "-c", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--head", required=True)
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--noise-curve", default=NOISE_CURVE)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config(args.config)
    dataset = make_split_dataset(config, "test")
    model = load_frozen_nomad(config, args.checkpoint_b, device)
    head = load_head(args.head, config["encoding_size"], device)
    output_dir = args.output_dir or os.path.join(os.path.dirname(args.head), "eval_paired")
    evaluator = PairedEvaluator(dataset, args.frames, args.spread, args.noise_curve)
    evaluator.run(model, head, device, args.batch_size, output_dir)


if __name__ == "__main__":
    main()

"""Position-noise oracle and far-goal subset checks. No training.

Uses the locked paired frames, far bin only (20-40). One shared diffusion
noise draw covers baseline B, the clean E-oracle, and every noisy E-oracle
condition. Position noise is isotropic Gaussian on x and y in meters, one
unit vector per frame scaled by each sigma, so the curve is paired.

E-oracle was trained on clean goal_pos. Noisy coordinates at test time are a
distribution shift, so the curve is a pessimistic estimate of a localization
head with the same Euclidean error.

Run from train/:

    python -u eval_position_noise.py
"""

import argparse
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from torchvision import transforms
from tqdm import tqdm

from eval_by_distance import (
    ade_fde,
    build_nomad,
    load_config,
    load_observation,
    load_paired_frames,
    make_test_dataset,
    prepare_batch,
)
from vint_train.training.train_utils import append_goal_pos, get_action

SIGMAS_M = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0)
TURN_LATERAL_M = 0.15
TURN_YAW_DEG = 20.0
SPREAD_LATERAL_M = 0.10
ANGLE_DEG = 30.0
DIRECTION_LATERAL_M = 0.15


def load_model(config, checkpoint_path, device):
    model, scheduler = build_nomad(config)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    state_dict = checkpoint["state_dict"] if isinstance(checkpoint, dict) and "state_dict" in checkpoint else checkpoint
    incompatible = model.load_state_dict(state_dict, strict=False)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(
            f"Checkpoint does not match the config: missing {len(incompatible.missing_keys)} "
            f"unexpected {len(incompatible.unexpected_keys)} ({checkpoint_path})"
        )
    print(f"load_state_dict: all keys matched ({checkpoint_path})")
    model = model.to(device)
    model.eval()
    return model, scheduler


def far_moments(moments):
    selected = []
    for traj_name, t, goals in moments:
        far = [goal for goal in goals if goal[0] == "20-40"]
        if len(far) != 1:
            raise RuntimeError(f"{traj_name} t={t} has {len(far)} far goals")
        selected.append((traj_name, t, far[0]))
    return selected


def yaw_change_deg(dataset, traj_name, t):
    yaw = np.asarray(dataset._get_trajectory(traj_name)["yaw"], dtype=object).reshape(-1)
    step = dataset.len_traj_pred * dataset.waypoint_spacing
    dy = float(np.ravel(yaw[t + step])[0]) - float(np.ravel(yaw[t])[0])
    dy = (dy + np.pi) % (2.0 * np.pi) - np.pi
    return float(np.degrees(dy))


def angle_between(a, b):
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-4 or nb < 1e-4:
        return np.nan
    cosine = float(np.dot(a, b) / (na * nb))
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def encode_cond(model, batch_obs, batch_goal, mask_value, device):
    goal_mask = torch.full((batch_obs.shape[0],), mask_value, dtype=torch.long, device=device)
    cond = model(
        "vision_encoder",
        obs_img=batch_obs,
        goal_img=batch_goal,
        input_goal_mask=goal_mask,
    )
    return cond, goal_mask


def diffuse(model, scheduler, cond, noise, num_samples, device):
    cond = cond.repeat_interleave(num_samples, dim=0)
    sample = noise.clone()
    for k in scheduler.timesteps:
        noise_pred = model(
            "noise_pred_net",
            sample=sample,
            timestep=k.unsqueeze(-1).repeat(sample.shape[0]).to(device),
            global_cond=cond,
        )
        sample = scheduler.step(model_output=noise_pred, timestep=k, sample=sample).prev_sample
    actions = get_action(sample)
    return actions.reshape(noise.shape[0] // num_samples, num_samples, -1, noise.shape[-1])


def to_numpy(pred):
    if torch.is_tensor(pred):
        pred = pred.detach().cpu().numpy()
    return pred


def mean_ade_fde(pred, gt, meters):
    ade, fde = ade_fde(to_numpy(pred), gt, meters)
    return float(ade.mean()), float(fde.mean())


def endpoint_y(pred, meters):
    return to_numpy(pred)[:, -1, 1] * meters


def boot_mean(values, index):
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean()) if len(values) else float("nan")
    if index is None or len(values) < 2:
        return mean, mean, mean
    boot = values[index].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return mean, float(lo), float(hi)


def subset_index(count, n_boot, rng):
    if n_boot <= 0 or count < 2:
        return None
    return rng.integers(0, count, size=(n_boot, count))


def run_eval(dataset, moments, models, transform, device, meters, num_samples, batch_size, unit_noise, sigmas):
    n = len(moments)
    n_sigma = len(sigmas)
    ade_goal_b = np.zeros(n)
    ade_mask_b = np.zeros(n)
    fde_goal_b = np.zeros(n)
    fde_mask_b = np.zeros(n)
    ade_mask_e = np.zeros(n)
    fde_mask_e = np.zeros(n)
    ade_goal_e = np.zeros((n, n_sigma))
    fde_goal_e = np.zeros((n, n_sigma))
    end_y_b_mask = np.zeros((n, num_samples))
    end_y_b_goal = np.zeros((n, num_samples))
    end_y_e_mask = np.zeros((n, num_samples))
    end_y_e_goal = np.zeros((n, num_samples))
    gt_lat = np.zeros(n)
    gt_yaw = np.zeros(n)
    goal_angle = np.full(n, np.nan)
    goal_dist = np.zeros(n)
    pred_horizon = dataset.len_traj_pred
    model_b, scheduler_b = models["b"]
    model_e, scheduler_e = models["e"]

    for start in tqdm(range(0, n, batch_size), desc="far frames", leave=False):
        chunk = moments[start : start + batch_size]
        obs_list = []
        goal_list = []
        gt_list = []
        pos_list = []
        for traj_name, t, goal in chunk:
            _name, _lo, _hi, _k, goal_time = goal
            obs, goal_image, actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal_image)
            gt_list.append(actions[:, :2])
            pos_list.append(goal_pos)
        batch_obs, batch_goal = prepare_batch(obs_list, goal_list, transform, device)
        clean_pos = torch.tensor(np.stack(pos_list), dtype=torch.float32, device=device)
        noise = torch.randn((len(chunk) * num_samples, pred_horizon, 2), device=device)
        z = torch.tensor(unit_noise[start : start + len(chunk)], dtype=torch.float32, device=device)

        with torch.no_grad():
            cond_b_goal, mask_b_goal = encode_cond(model_b, batch_obs, batch_goal, 0, device)
            cond_b_mask, _mask_b_mask = encode_cond(model_b, batch_obs, batch_goal, 1, device)
            pred_b_goal = diffuse(model_b, scheduler_b, cond_b_goal, noise, num_samples, device)
            pred_b_mask = diffuse(model_b, scheduler_b, cond_b_mask, noise, num_samples, device)

            cond_e_goal, mask_e_goal = encode_cond(model_e, batch_obs, batch_goal, 0, device)
            cond_e_mask, mask_e_mask = encode_cond(model_e, batch_obs, batch_goal, 1, device)
            pred_e_mask = diffuse(
                model_e,
                scheduler_e,
                append_goal_pos(cond_e_mask, clean_pos, mask_e_mask),
                noise,
                num_samples,
                device,
            )
            pred_e_goal = []
            for sigma in sigmas:
                noisy_pos = clean_pos + z * (float(sigma) / meters)
                pred_e_goal.append(
                    diffuse(
                        model_e,
                        scheduler_e,
                        append_goal_pos(cond_e_goal, noisy_pos, mask_e_goal),
                        noise,
                        num_samples,
                        device,
                    )
                )

        for i, ((traj_name, t, _goal), gt, goal_pos) in enumerate(zip(chunk, gt_list, pos_list)):
            index = start + i
            ade_goal_b[index], fde_goal_b[index] = mean_ade_fde(pred_b_goal[i], gt, meters)
            ade_mask_b[index], fde_mask_b[index] = mean_ade_fde(pred_b_mask[i], gt, meters)
            ade_mask_e[index], fde_mask_e[index] = mean_ade_fde(pred_e_mask[i], gt, meters)
            end_y_b_goal[index] = endpoint_y(pred_b_goal[i], meters)
            end_y_b_mask[index] = endpoint_y(pred_b_mask[i], meters)
            end_y_e_mask[index] = endpoint_y(pred_e_mask[i], meters)
            clean_index = sigmas.index(0.0)
            end_y_e_goal[index] = endpoint_y(pred_e_goal[clean_index][i], meters)
            for s, pred in enumerate(pred_e_goal):
                ade_goal_e[index, s], fde_goal_e[index, s] = mean_ade_fde(pred[i], gt, meters)
            gt_lat[index] = float(gt[-1, 1] * meters)
            gt_yaw[index] = yaw_change_deg(dataset, traj_name, t)
            goal_angle[index] = angle_between(goal_pos, gt[-1])
            goal_dist[index] = float(np.linalg.norm(goal_pos) * meters)

    return {
        "ade_goal_b": ade_goal_b,
        "ade_mask_b": ade_mask_b,
        "fde_goal_b": fde_goal_b,
        "fde_mask_b": fde_mask_b,
        "ade_mask_e": ade_mask_e,
        "fde_mask_e": fde_mask_e,
        "ade_goal_e": ade_goal_e,
        "fde_goal_e": fde_goal_e,
        "end_y_b_mask": end_y_b_mask,
        "end_y_b_goal": end_y_b_goal,
        "end_y_e_mask": end_y_e_mask,
        "end_y_e_goal": end_y_e_goal,
        "gt_lat": gt_lat,
        "gt_yaw": gt_yaw,
        "goal_angle": goal_angle,
        "goal_dist": goal_dist,
    }


def save_curve(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_plot(path, rows, b_use):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    x = np.array([row["mean_position_error_m"] for row in rows])
    y = np.array([row["ade_use"] for row in rows])
    lo = np.array([row["ade_use_lo"] for row in rows])
    hi = np.array([row["ade_use_hi"] for row in rows])
    y_fde = np.array([row["fde_use"] for row in rows])
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.axhline(0.0, color="0.4", linewidth=1)
    b_label = 0.0 if abs(b_use) < 5e-4 else b_use
    ax.axhline(b_use, color="C1", linestyle="--", linewidth=1, label=f"B 的 ADE 利用度 {b_label:.3f} m")
    ax.fill_between(x, lo, hi, color="C0", alpha=0.18)
    ax.plot(x, y, marker="o", color="C0", label="E-oracle ADE 利用度")
    ax.plot(x, y_fde, marker="s", color="C2", label="E-oracle FDE 利用度")
    labeled_x = []
    for row in rows:
        if labeled_x and row["mean_position_error_m"] - labeled_x[-1] < 0.45:
            continue
        labeled_x.append(row["mean_position_error_m"])
        ax.annotate(
            f"σ={row['sigma_m']:.2g}",
            (row["mean_position_error_m"], row["ade_use"]),
            textcoords="offset points",
            xytext=(0, 10 if row["ade_use"] < 0.012 else -14),
            ha="center",
            fontsize=8,
        )
    ax.set_xlim(-0.08, max(float(x.max()) * 1.06, 0.2))
    ax.set_xlabel("远处 goal_pos 的平均位置误差 (m)")
    ax.set_ylabel("利用度 (m)")
    ax.set_title("Epoch 29 远处组：位置误差与目标利用度")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.text(
        0.01,
        0.01,
        "训练只见过干净坐标。测试加噪是分布偏移，曲线偏悲观。",
        fontsize=8,
        color="0.35",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fmt_ci(mean, lo, hi):
    return f"{mean:.3f} [{lo:.3f}, {hi:.3f}]"


def main():
    parser = argparse.ArgumentParser(description="Noisy goal_pos curve and far-goal subset analysis")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-b", default="logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth")
    parser.add_argument("--checkpoint-e", default="logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth")
    parser.add_argument(
        "--frames",
        default="logs/nomad/nomad_b40_2026_09_29_16_35_23/eval_epoch20_paired/paired_frames.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/eval_epoch29_position_noise",
    )
    parser.add_argument("--sigmas", default=",".join(str(s) for s in SIGMAS_M))
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turn-lateral", type=float, default=TURN_LATERAL_M)
    parser.add_argument("--turn-yaw", type=float, default=TURN_YAW_DEG)
    parser.add_argument("--spread-lateral", type=float, default=SPREAD_LATERAL_M)
    parser.add_argument("--angle", type=float, default=ANGLE_DEG)
    args = parser.parse_args()

    sigmas = tuple(float(part) for part in args.sigmas.split(",") if part.strip())
    os.makedirs(args.output_dir, exist_ok=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")
    print(
        "Rules fixed before the run: "
        f"turn = |endpoint lateral| >= {args.turn_lateral:.2f} m or |yaw change| >= {args.turn_yaw:.0f} deg; "
        f"spread = B masked samples have endpoint y both < -{args.spread_lateral:.2f} m and > {args.spread_lateral:.2f} m; "
        f"large angle = goal direction vs 8-step endpoint > {args.angle:.0f} deg."
    )
    print("Position noise: independent N(0, sigma^2) meters on x and y. sigma=0 is the clean oracle.")

    config_b = load_config(args.config_b)
    config_e = load_config(args.config_e)
    if config_b.get("goal_pos_oracle"):
        raise RuntimeError("Baseline config must leave goal_pos_oracle off")
    if not config_e.get("goal_pos_oracle"):
        raise RuntimeError("E-oracle config must set goal_pos_oracle: true")
    if 0.0 not in sigmas:
        raise RuntimeError("sigmas must include 0 so the clean oracle stays on the curve")

    transform = transforms.Compose(
        [transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]
    )
    print("Loading test split and image cache...")
    dataset = make_test_dataset(config_e)
    meters = float(dataset.data_config["metric_waypoint_spacing"]) * dataset.waypoint_spacing
    print(f"meters per waypoint unit: {meters}")
    moments = far_moments(load_paired_frames(args.frames))
    print(f"far frames: {len(moments)}")

    model_b, scheduler_b = load_model(config_b, args.checkpoint_b, device)
    model_e, scheduler_e = load_model(config_e, args.checkpoint_e, device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    unit_noise = np.random.default_rng(args.seed + 11).normal(size=(len(moments), 2)).astype(np.float32)

    result = run_eval(
        dataset,
        moments,
        {"b": (model_b, scheduler_b), "e": (model_e, scheduler_e)},
        transform,
        device,
        meters,
        args.num_samples,
        args.batch_size,
        unit_noise,
        sigmas,
    )

    n = len(moments)
    boot_rng = np.random.default_rng(args.seed + 1)
    all_index = subset_index(n, args.bootstrap, boot_rng)
    use_b = result["ade_mask_b"] - result["ade_goal_b"]
    fde_use_b = result["fde_mask_b"] - result["fde_goal_b"]
    b_ade_use, b_ade_lo, b_ade_hi = boot_mean(use_b, all_index)
    b_fde_use, b_fde_lo, b_fde_hi = boot_mean(fde_use_b, all_index)

    curve_rows = []
    realized_norm = np.linalg.norm(unit_noise, axis=1)
    for s, sigma in enumerate(sigmas):
        position_error = realized_norm * float(sigma)
        use = result["ade_mask_e"] - result["ade_goal_e"][:, s]
        fde_use = result["fde_mask_e"] - result["fde_goal_e"][:, s]
        ade_use, ade_lo, ade_hi = boot_mean(use, all_index)
        fde_mean, fde_lo, fde_hi = boot_mean(fde_use, all_index)
        goal_mean, goal_lo, goal_hi = boot_mean(result["ade_goal_e"][:, s], all_index)
        curve_rows.append(
            {
                "sigma_m": float(sigma),
                "mean_position_error_m": float(position_error.mean()),
                "ade_goal": goal_mean,
                "ade_goal_lo": goal_lo,
                "ade_goal_hi": goal_hi,
                "ade_mask": float(result["ade_mask_e"].mean()),
                "ade_use": ade_use,
                "ade_use_lo": ade_lo,
                "ade_use_hi": ade_hi,
                "fde_use": fde_mean,
                "fde_use_lo": fde_lo,
                "fde_use_hi": fde_hi,
            }
        )

    turning = (np.abs(result["gt_lat"]) >= args.turn_lateral) | (np.abs(result["gt_yaw"]) >= args.turn_yaw)
    spread = (result["end_y_b_mask"].min(axis=1) < -args.spread_lateral) & (
        result["end_y_b_mask"].max(axis=1) > args.spread_lateral
    )
    angle = result["goal_angle"]
    large_angle = np.isfinite(angle) & (angle > args.angle)
    defined_angle = np.isfinite(angle)
    subsets = (
        ("all far", np.ones(n, dtype=bool)),
        ("turning", turning),
        ("not turning", ~turning),
        ("masked spread", spread),
        ("masked not spread", ~spread),
        (f"angle > {args.angle:.0f}", large_angle),
        (f"angle <= {args.angle:.0f}", defined_angle & ~large_angle),
    )

    def direction_flags(end_y, mask):
        eligible = mask & (np.abs(result["gt_lat"]) >= DIRECTION_LATERAL_M)
        pred_side = np.sign(end_y.mean(axis=1))
        gt_side = np.sign(result["gt_lat"])
        return eligible, (pred_side == gt_side) & eligible

    subset_rows = []
    print("\nFar group, mean of N samples, meters. Use = mask ADE - goal ADE.")
    print(f"B ADE use {fmt_ci(b_ade_use, b_ade_lo, b_ade_hi)}  FDE use {fmt_ci(b_fde_use, b_fde_lo, b_fde_hi)}")
    print("\nsigma is the std on each axis. mean position error is the average Euclidean ||noise||.")
    print(f"{'sigma':>8}{'err m':>8}{'ADE goal':>10}{'ADE use':>28}{'FDE use':>28}")
    for row in curve_rows:
        print(
            f"{row['sigma_m']:8.2f}{row['mean_position_error_m']:8.3f}{row['ade_goal']:10.3f}"
            f"{fmt_ci(row['ade_use'], row['ade_use_lo'], row['ade_use_hi']):>28}"
            f"{fmt_ci(row['fde_use'], row['fde_use_lo'], row['fde_use_hi']):>28}"
        )

    print("\nSubsets. Gain = E-oracle clean ADE use - B ADE use, paired over the subset.")
    print(f"{'subset':<22}{'n':>6}{'E ADE':>8}{'B ADE':>8}{'E use':>24}{'B use':>24}{'gain':>24}")
    for name, mask in subsets:
        idx = np.flatnonzero(mask)
        sub_boot = subset_index(len(idx), args.bootstrap, boot_rng)
        e_use = result["ade_mask_e"][idx] - result["ade_goal_e"][idx, 0]
        b_use = use_b[idx]
        e_mean, e_lo, e_hi = boot_mean(e_use, sub_boot)
        b_mean, b_lo, b_hi = boot_mean(b_use, sub_boot)
        gain, gain_lo, gain_hi = boot_mean(e_use - b_use, sub_boot)
        e_goal = float(result["ade_goal_e"][idx, 0].mean()) if len(idx) else float("nan")
        b_goal = float(result["ade_goal_b"][idx].mean()) if len(idx) else float("nan")
        eligible, e_dir_flags = direction_flags(result["end_y_e_goal"], mask)
        _eligible_b, b_dir_flags = direction_flags(result["end_y_b_goal"], mask)
        _eligible_em, e_mask_flags = direction_flags(result["end_y_e_mask"], mask)
        _eligible_bm, b_mask_flags = direction_flags(result["end_y_b_mask"], mask)
        dir_idx = np.flatnonzero(eligible)
        dir_boot = subset_index(len(dir_idx), args.bootstrap, boot_rng)
        e_dir, e_dir_lo, e_dir_hi = boot_mean(e_dir_flags[dir_idx].astype(np.float64), dir_boot)
        b_dir, b_dir_lo, b_dir_hi = boot_mean(b_dir_flags[dir_idx].astype(np.float64), dir_boot)
        e_mask_dir, _, _ = boot_mean(e_mask_flags[dir_idx].astype(np.float64), dir_boot)
        b_mask_dir, _, _ = boot_mean(b_mask_flags[dir_idx].astype(np.float64), dir_boot)
        row = {
            "subset": name,
            "n": int(len(idx)),
            "e_ade_goal": e_goal,
            "b_ade_goal": b_goal,
            "e_ade_use": e_mean,
            "e_ade_use_lo": e_lo,
            "e_ade_use_hi": e_hi,
            "b_ade_use": b_mean,
            "b_ade_use_lo": b_lo,
            "b_ade_use_hi": b_hi,
            "use_gain": gain,
            "use_gain_lo": gain_lo,
            "use_gain_hi": gain_hi,
            "n_direction": int(len(dir_idx)),
            "e_direction": e_dir,
            "e_direction_lo": e_dir_lo,
            "e_direction_hi": e_dir_hi,
            "b_direction": b_dir,
            "b_direction_lo": b_dir_lo,
            "b_direction_hi": b_dir_hi,
            "e_mask_direction": e_mask_dir,
            "b_mask_direction": b_mask_dir,
        }
        subset_rows.append(row)
        print(
            f"{name:<22}{len(idx):6d}{e_goal:8.3f}{b_goal:8.3f}"
            f"{fmt_ci(e_mean, e_lo, e_hi):>24}{fmt_ci(b_mean, b_lo, b_hi):>24}{fmt_ci(gain, gain_lo, gain_hi):>24}"
        )

    spread_range = result["end_y_b_mask"].max(axis=1) - result["end_y_b_mask"].min(axis=1)
    print(
        "\nB masked endpoint range (max y - min y), meters: "
        f"median {np.median(spread_range):.3f}  "
        f"p90 {np.percentile(spread_range, 90):.3f}"
    )
    print(
        f"Turning {int(turning.sum())}  spread {int(spread.sum())}  "
        f"angle>{args.angle:.0f} {int(large_angle.sum())}  "
        f"angle undefined {int((~defined_angle).sum())}"
    )
    if large_angle.any():
        print(
            f"Large-angle frames: median goal distance {np.median(result['goal_dist'][large_angle]):.2f} m, "
            f"median angle {np.median(angle[large_angle]):.1f} deg"
        )
    print("\nDirection = sign of the mean predicted endpoint y matches the 8-step label.")
    print(f"Scored only where |label lateral| >= {DIRECTION_LATERAL_M:.2f} m.")
    print(f"{'subset':<22}{'n':>6}{'E goal':>22}{'B goal':>22}{'E mask':>8}{'B mask':>8}")
    for row in subset_rows:
        print(
            f"{row['subset']:<22}{row['n_direction']:6d}"
            f"{fmt_ci(row['e_direction'], row['e_direction_lo'], row['e_direction_hi']):>22}"
            f"{fmt_ci(row['b_direction'], row['b_direction_lo'], row['b_direction_hi']):>22}"
            f"{row['e_mask_direction']:8.3f}{row['b_mask_direction']:8.3f}"
        )

    curve_path = os.path.join(args.output_dir, "position_noise_curve.csv")
    plot_path = os.path.join(args.output_dir, "position_noise_curve.png")
    subset_path = os.path.join(args.output_dir, "subset_summary.csv")
    frame_path = os.path.join(args.output_dir, "per_frame.npz")
    save_curve(curve_path, curve_rows)
    save_curve(subset_path, subset_rows)
    save_plot(plot_path, curve_rows, b_ade_use)
    np.savez_compressed(
        frame_path,
        sigmas_m=np.asarray(sigmas),
        unit_noise=unit_noise,
        **result,
        turning=turning,
        spread=spread,
        large_angle=large_angle,
    )
    print(f"\nCSV: {os.path.abspath(curve_path)}")
    print(f"subsets: {os.path.abspath(subset_path)}")
    print(f"plot: {os.path.abspath(plot_path)}")
    print("Clean coordinates were the only positions seen in training. The noisy curve is pessimistic.")


if __name__ == "__main__":
    main()

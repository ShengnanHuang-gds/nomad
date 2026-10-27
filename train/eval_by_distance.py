"""Evaluate baseline NoMaD by goal distance on the GoStanford test split.

Each kept test frame is used at three goal distances (one k drawn inside
4-8, 9-19, and 20-40). The observation time is the same across groups, and
the three goals share one diffusion noise sample. The diffusion head is then
run twice: with the goal image (input_goal_mask=0) and with it masked
(input_goal_mask=1). ADE and FDE are in meters. Goal-use confidence intervals
are percentile bootstrap over these paired frames.

Run from the train/ directory, after at least one epoch has written ema_latest.pth:

    python eval_by_distance.py -c config/nomad_b40.yaml
    python eval_by_distance.py -c config/nomad_b40.yaml --checkpoint logs/nomad/<run>/ema_latest.pth
"""

import argparse
import csv
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from torchvision import transforms
from tqdm import tqdm

from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from diffusion_policy.model.diffusion.conditional_unet1d import ConditionalUnet1D
from vint_train.data.vint_dataset import ViNT_Dataset
from vint_train.models.nomad.nomad import DenseNetwork, NoMaD
from vint_train.models.nomad.nomad_vint import NoMaD_ViNT, replace_bn_with_gn
from vint_train.training.train_utils import append_goal_pos, get_action

# Frame-distance bins requested for the thesis table.
DISTANCE_GROUPS = (
    (4, 8, "4-8"),
    (9, 19, "9-19"),
    (20, 40, "20-40"),
)
def load_config(config_path):
    with open("config/defaults.yaml", "r") as f:
        config = yaml.safe_load(f)
    with open(config_path, "r") as f:
        config.update(yaml.safe_load(f))
    return config


def build_nomad(config):
    vision_encoder = NoMaD_ViNT(
        obs_encoding_size=config["encoding_size"],
        context_size=config["context_size"],
        mha_num_attention_heads=config["mha_num_attention_heads"],
        mha_num_attention_layers=config["mha_num_attention_layers"],
        mha_ff_dim_factor=config["mha_ff_dim_factor"],
    )
    vision_encoder = replace_bn_with_gn(vision_encoder)
    if "goal_pos_dim" in config:
        goal_pos_dim = int(config["goal_pos_dim"])
    else:
        goal_pos_dim = 2 if config.get("goal_pos_oracle") else 0
    noise_pred_net = ConditionalUnet1D(
        input_dim=2,
        global_cond_dim=config["encoding_size"] + goal_pos_dim,
        down_dims=config["down_dims"],
        cond_predict_scale=config["cond_predict_scale"],
    )
    model = NoMaD(
        vision_encoder=vision_encoder,
        noise_pred_net=noise_pred_net,
        dist_pred_net=DenseNetwork(embedding_dim=config["encoding_size"]),
    )
    scheduler = DDPMScheduler(
        num_train_timesteps=config["num_diffusion_iters"],
        beta_schedule="squaredcos_cap_v2",
        clip_sample=True,
        prediction_type="epsilon",
    )
    scheduler.set_timesteps(config["num_diffusion_iters"])
    return model, scheduler


def resolve_checkpoint(explicit_path):
    if explicit_path:
        if not os.path.isfile(explicit_path):
            raise FileNotFoundError(f"Checkpoint not found: {explicit_path}")
        return explicit_path
    matches = sorted(glob.glob(os.path.join("logs", "nomad", "nomad_b40_*", "ema_latest.pth")))
    if not matches:
        raise FileNotFoundError(
            "No logs/nomad/nomad_b40_*/ema_latest.pth yet. "
            "Train at least one epoch, or pass --checkpoint."
        )
    return matches[-1]


def make_test_dataset(config):
    data_config = config["datasets"]["go_stanford"]
    waypoint_spacing = data_config.get("waypoint_spacing", 1)
    return ViNT_Dataset(
        data_folder=data_config["data_folder"],
        data_split_folder=data_config["test"],
        dataset_name="go_stanford",
        image_size=config["image_size"],
        waypoint_spacing=waypoint_spacing,
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


def list_paired_moments(dataset, samples_per_group, seed):
    """One observation time, one goal k inside each distance group.

    A moment is kept only when every group has at least one reachable k, so the
    three groups contain the same frames. Returns
    (traj_name, t, [(group, k_min, k_max, k, goal_time), ...]).
    """
    waypoint_spacing = dataset.waypoint_spacing
    candidates = []
    for traj_name in dataset.traj_names:
        traj_len = len(dataset._get_trajectory(traj_name)["position"])
        begin_time = dataset.context_size * waypoint_spacing
        end_time = traj_len - dataset.end_slack - dataset.len_traj_pred * waypoint_spacing
        for t in range(begin_time, end_time):
            feasible = []
            for lo, hi, name in DISTANCE_GROUPS:
                ks = [k for k in range(lo, hi + 1) if t + k * waypoint_spacing < traj_len]
                if not ks:
                    feasible = None
                    break
                feasible.append((name, lo, hi, ks))
            if feasible is not None:
                candidates.append((traj_name, t, feasible))

    rng = np.random.default_rng(seed)
    if samples_per_group > 0 and len(candidates) > samples_per_group:
        picked = np.sort(rng.choice(len(candidates), size=samples_per_group, replace=False))
        candidates = [candidates[i] for i in picked]

    moments = []
    for traj_name, t, feasible in candidates:
        goals = []
        for name, lo, hi, ks in feasible:
            k = int(rng.choice(ks))
            goals.append((name, lo, hi, k, t + k * waypoint_spacing))
        moments.append((traj_name, t, goals))
    return moments


def save_paired_frames(path, moments):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["traj_name", "t", "group", "k_min", "k_max", "k", "goal_time"])
        for traj_name, t, goals in moments:
            for name, lo, hi, k, goal_time in goals:
                writer.writerow([traj_name, t, name, lo, hi, k, goal_time])


def load_paired_frames(path):
    grouped = {}
    order = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["traj_name"], int(row["t"]))
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(
                (row["group"], int(row["k_min"]), int(row["k_max"]), int(row["k"]), int(row["goal_time"]))
            )
    return [(traj_name, t, grouped[(traj_name, t)]) for traj_name, t in order]


def prepare_batch(obs_list, goal_list, transform, device):
    """Match train_nomad: Normalize each 3-channel slice, then concatenate context."""
    obs_batch = torch.stack(obs_list, dim=0)
    goal_batch = torch.stack(goal_list, dim=0)
    obs_images = torch.split(obs_batch, 3, dim=1)
    batch_obs = torch.cat([transform(obs) for obs in obs_images], dim=1).to(device)
    batch_goal = transform(goal_batch).to(device)
    return batch_obs, batch_goal


def sample_actions(model, scheduler, batch_obs, batch_goal, goal_mask_value, num_samples, pred_horizon, device, noise, goal_pos=None):
    """Sample num_samples trajectories per observation. goal_mask_value is 0 or 1.

    noise is the shared initial diffusion noise, shape [batch * num_samples, pred_horizon, 2].
    Goal and masked runs must receive the same tensor so their difference is not sampling noise.
    """
    batch_size = batch_obs.shape[0]
    goal_mask = torch.full((batch_size,), goal_mask_value, dtype=torch.long, device=device)
    cond = model(
        "vision_encoder",
        obs_img=batch_obs,
        goal_img=batch_goal,
        input_goal_mask=goal_mask,
    )
    if goal_pos is not None:
        cond = append_goal_pos(cond, goal_pos, goal_mask)
    cond = cond.repeat_interleave(num_samples, dim=0)
    diffusion_output = noise.clone()
    for k in scheduler.timesteps:
        noise_pred = model(
            "noise_pred_net",
            sample=diffusion_output,
            timestep=k.unsqueeze(-1).repeat(diffusion_output.shape[0]).to(device),
            global_cond=cond,
        )
        diffusion_output = scheduler.step(
            model_output=noise_pred,
            timestep=k,
            sample=diffusion_output,
        ).prev_sample
    actions = get_action(diffusion_output)
    return actions.reshape(batch_size, num_samples, pred_horizon, noise.shape[-1])


def ade_fde(pred, gt, meters_per_unit):
    """pred [N, T, 2], gt [T, 2], both in dataset waypoint units. Returns meters, shape [N]."""
    dist = np.linalg.norm((pred - gt[None]) * meters_per_unit, axis=-1)
    return dist.mean(axis=-1), dist[:, -1]


def load_observation(dataset, traj_name, t, goal_time):
    waypoint_spacing = dataset.waypoint_spacing
    context_times = list(
        range(
            t - dataset.context_size * waypoint_spacing,
            t + 1,
            waypoint_spacing,
        )
    )
    obs_image = torch.cat([dataset._load_image(traj_name, time) for time in context_times])
    goal_image = dataset._load_image(traj_name, goal_time)
    actions, goal_pos = dataset._compute_actions(dataset._get_trajectory(traj_name), t, goal_time)
    return (
        obs_image.float(),
        goal_image.float(),
        np.asarray(actions, dtype=np.float32),
        np.asarray(goal_pos, dtype=np.float32),
    )


METRIC_KEYS = (
    "ade_goal_mean",
    "ade_goal_min",
    "fde_goal_mean",
    "fde_goal_min",
    "ade_mask_mean",
    "ade_mask_min",
    "fde_mask_mean",
    "fde_mask_min",
)


def evaluate_paired(model, scheduler, dataset, moments, transform, device, num_samples, batch_size, meters_per_unit, pred_horizon, goal_pos_oracle=False, score_steps=None):
    """Evaluate every distance group on the same frames with one shared noise draw.

    score_steps scores only the first k predicted waypoints (all of them when None).
    """
    k = pred_horizon if score_steps is None else int(score_steps)
    group_names = [name for _lo, _hi, name in DISTANCE_GROUPS]
    per_group = {name: {key: [] for key in METRIC_KEYS} for name in group_names}
    for start in tqdm(range(0, len(moments), batch_size), desc="paired frames", leave=False):
        chunk = moments[start : start + batch_size]
        obs_list = []
        goal_lists = {name: [] for name in group_names}
        gt_lists = {name: [] for name in group_names}
        pos_lists = {name: [] for name in group_names}
        for traj_name, t, goals in chunk:
            obs, _goal, _actions, _goal_pos = load_observation(dataset, traj_name, t, goals[0][4])
            obs_list.append(obs)
            for name, _lo, _hi, _k, goal_time in goals:
                _obs, goal, actions, goal_pos = load_observation(dataset, traj_name, t, goal_time)
                goal_lists[name].append(goal)
                gt_lists[name].append(actions[:, :2])
                pos_lists[name].append(goal_pos)
        noise = torch.randn(
            (len(chunk) * num_samples, pred_horizon, 2),
            device=device,
        )
        with torch.no_grad():
            for name in group_names:
                batch_obs, batch_goal = prepare_batch(obs_list, goal_lists[name], transform, device)
                batch_pos = None
                if goal_pos_oracle:
                    batch_pos = torch.tensor(np.stack(pos_lists[name]), dtype=torch.float32, device=device)
                pred_goal = sample_actions(
                    model, scheduler, batch_obs, batch_goal, 0, num_samples, pred_horizon, device, noise, goal_pos=batch_pos
                )
                pred_mask = sample_actions(
                    model, scheduler, batch_obs, batch_goal, 1, num_samples, pred_horizon, device, noise, goal_pos=batch_pos
                )
                pred_goal = pred_goal.detach().cpu().numpy()
                pred_mask = pred_mask.detach().cpu().numpy()
                for i, gt in enumerate(gt_lists[name]):
                    ade_g, fde_g = ade_fde(pred_goal[i][:, :k], gt[:k], meters_per_unit)
                    ade_m, fde_m = ade_fde(pred_mask[i][:, :k], gt[:k], meters_per_unit)
                    per_group[name]["ade_goal_mean"].append(float(ade_g.mean()))
                    per_group[name]["ade_goal_min"].append(float(ade_g.min()))
                    per_group[name]["fde_goal_mean"].append(float(fde_g.mean()))
                    per_group[name]["fde_goal_min"].append(float(fde_g.min()))
                    per_group[name]["ade_mask_mean"].append(float(ade_m.mean()))
                    per_group[name]["ade_mask_min"].append(float(ade_m.min()))
                    per_group[name]["fde_mask_mean"].append(float(fde_m.mean()))
                    per_group[name]["fde_mask_min"].append(float(fde_m.min()))
    return per_group


def bootstrap_ci(values, sample_index, n_boot):
    """Percentile interval of the sample mean. sample_index is shared across groups."""
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    if n_boot <= 0 or len(values) < 2:
        return mean, mean, mean
    boot_means = values[sample_index].mean(axis=1)
    lo, hi = np.quantile(boot_means, [0.025, 0.975])
    return mean, float(lo), float(hi)


def summarize_groups(per_group, moments, n_boot, seed):
    n = len(moments)
    rng = np.random.default_rng(seed)
    sample_index = rng.integers(0, n, size=(n_boot, n)) if n_boot > 0 and n >= 2 else None
    rows = []
    for lo, hi, name in DISTANCE_GROUPS:
        metrics = {key: np.asarray(per_group[name][key], dtype=np.float64) for key in METRIC_KEYS}
        if len(metrics["ade_goal_mean"]) == 0:
            continue
        use = {
            "goal_use_ade_mean": metrics["ade_mask_mean"] - metrics["ade_goal_mean"],
            "goal_use_ade_min": metrics["ade_mask_min"] - metrics["ade_goal_min"],
            "goal_use_fde_mean": metrics["fde_mask_mean"] - metrics["fde_goal_mean"],
            "goal_use_fde_min": metrics["fde_mask_min"] - metrics["fde_goal_min"],
        }
        row = {"group": name, "k_min": lo, "k_max": hi, "n": int(len(metrics["ade_goal_mean"]))}
        for key, values in {**metrics, **use}.items():
            mean, ci_lo, ci_hi = bootstrap_ci(values, sample_index, n_boot)
            row[key] = mean
            row[f"{key}_lo"] = ci_lo
            row[f"{key}_hi"] = ci_hi
        rows.append(row)
    return rows


def print_table(rows):
    header = (
        f"{'group':<8}{'n':>6}{'ADE goal':>10}{'ADE mask':>10}{'ADE use':>10}"
        f"{'FDE goal':>10}{'FDE mask':>10}{'FDE use':>10}"
    )
    print("\nmean of N samples (meters)")
    print(header)
    for row in rows:
        print(
            f"{row['group']:<8}{row['n']:>6}"
            f"{row['ade_goal_mean']:>10.3f}{row['ade_mask_mean']:>10.3f}{row['goal_use_ade_mean']:>10.3f}"
            f"{row['fde_goal_mean']:>10.3f}{row['fde_mask_mean']:>10.3f}{row['goal_use_fde_mean']:>10.3f}"
        )
    print("\n95% bootstrap CI of the paired-frame mean")
    print(f"{'group':<8}{'ADE use':>22}{'FDE use':>22}")
    for row in rows:
        ade = f"{row['goal_use_ade_mean']:.3f} [{row['goal_use_ade_mean_lo']:.3f}, {row['goal_use_ade_mean_hi']:.3f}]"
        fde = f"{row['goal_use_fde_mean']:.3f} [{row['goal_use_fde_mean_lo']:.3f}, {row['goal_use_fde_mean_hi']:.3f}]"
        print(f"{row['group']:<8}{ade:>22}{fde:>22}")
    print("\nmin of N samples, then averaged over the group (meters)")
    print(header)
    for row in rows:
        print(
            f"{row['group']:<8}{row['n']:>6}"
            f"{row['ade_goal_min']:>10.3f}{row['ade_mask_min']:>10.3f}{row['goal_use_ade_min']:>10.3f}"
            f"{row['fde_goal_min']:>10.3f}{row['fde_mask_min']:>10.3f}{row['goal_use_fde_min']:>10.3f}"
        )
    print("goal use = masked error - goal error. Positive means the goal image helps.")
    print("CI excludes 0 when the goal effect is distinguishable from sampling noise at 95%.")


def save_csv(path, rows):
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def save_plot(path, rows):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    for key, label in (("ade_goal_mean", "给 goal"), ("ade_mask_mean", "遮住 goal")):
        y = np.array([row[key] for row in rows])
        lo = np.array([row[f"{key}_lo"] for row in rows])
        hi = np.array([row[f"{key}_hi"] for row in rows])
        ax.errorbar(x, y, yerr=[y - lo, hi - y], marker="o", capsize=4, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([row["group"] for row in rows])
    ax.set_xlabel("goal 距离分组（帧）")
    ax.set_ylabel("ADE (m)")
    ax.set_title("基线 B：按 goal 距离的 ADE")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Evaluate NoMaD ADE/FDE by goal distance")
    parser.add_argument("--config", "-c", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint", default="", help="EMA state dict. Default: latest nomad_b40 ema_latest.pth")
    parser.add_argument("--num-samples", type=int, default=8, help="Diffusion samples per observation (N)")
    parser.add_argument("--samples-per-group", type=int, default=1000, help="Paired frames. 0 keeps every frame that reaches all bins")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples for the 95% CI. 0 skips it")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="", help="Default: <checkpoint dir>/eval_by_distance")
    parser.add_argument("--frames", default="", help="CSV of paired frames. Empty draws a new set from --seed")
    parser.add_argument("--score-steps", type=int, default=0, help="Score only the first k waypoints. 0 scores all")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.score_steps > config["len_traj_pred"]:
        raise ValueError(f"--score-steps {args.score_steps} exceeds len_traj_pred {config['len_traj_pred']}")
    checkpoint_path = resolve_checkpoint(args.checkpoint)
    output_dir = args.output_dir or os.path.join(os.path.dirname(checkpoint_path), "eval_by_distance")
    os.makedirs(output_dir, exist_ok=True)

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    else:
        device = torch.device("cpu")
    print(f"device: {device}")
    print(f"checkpoint: {checkpoint_path}")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    transform = transforms.Compose(
        [transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]
    )
    print("Loading test split and image cache...")
    dataset = make_test_dataset(config)
    meters_per_unit = float(dataset.data_config["metric_waypoint_spacing"]) * dataset.waypoint_spacing
    print(f"meters per waypoint unit: {meters_per_unit}")

    if args.frames:
        print(f"Loading paired frames from {args.frames}")
        moments = load_paired_frames(args.frames)
    else:
        print("Selecting paired frames (same time, one goal in each distance group)...")
        moments = list_paired_moments(dataset, args.samples_per_group, args.seed)
        frames_path = os.path.join(output_dir, "paired_frames.csv")
        save_paired_frames(frames_path, moments)
        print(f"  saved frames: {os.path.abspath(frames_path)}")
    print(f"  paired frames: {len(moments)}")
    if not moments:
        print("No observation time reaches every distance group.", file=sys.stderr)
        sys.exit(1)

    model, scheduler = build_nomad(config)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint
    incompatible = model.load_state_dict(state_dict, strict=False)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        print(f"load_state_dict missing: {len(incompatible.missing_keys)} unexpected: {len(incompatible.unexpected_keys)}")
        if incompatible.missing_keys:
            print("  missing:", ", ".join(incompatible.missing_keys[:8]))
        if incompatible.unexpected_keys:
            print("  unexpected:", ", ".join(incompatible.unexpected_keys[:8]))
    else:
        print("load_state_dict: all keys matched")
    model = model.to(device)
    model.eval()

    # Reseed after model init so the diffusion noise does not depend on dropout masks or parameter init.
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    print(f"Evaluating {len(moments)} paired frames, N={args.num_samples}, bootstrap={args.bootstrap}")
    per_group = evaluate_paired(
        model,
        scheduler,
        dataset,
        moments,
        transform,
        device,
        args.num_samples,
        args.batch_size,
        meters_per_unit,
        config["len_traj_pred"],
        goal_pos_oracle=bool(config.get("goal_pos_oracle", False)),
        score_steps=args.score_steps or None,
    )
    rows = summarize_groups(per_group, moments, args.bootstrap, args.seed + 1)

    if not rows:
        print("No evaluation samples.", file=sys.stderr)
        sys.exit(1)

    print_table(rows)
    csv_path = os.path.join(output_dir, "ade_fde_by_distance.csv")
    plot_path = os.path.join(output_dir, "ade_by_distance.png")
    save_csv(csv_path, rows)
    save_plot(plot_path, rows)
    print(f"\nCSV: {os.path.abspath(csv_path)}")
    print(f"plot: {os.path.abspath(plot_path)}")
    print("Read ADE use / FDE use: positive means masking the goal increases error, so the model used the goal image.")


if __name__ == "__main__":
    main()

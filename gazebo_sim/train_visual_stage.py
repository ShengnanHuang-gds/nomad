#!/usr/bin/env python3
"""Fresh, cache-free NoMaD visual adaptation on local CUDA.

00-04 train, 05 validate, 06-07 never read. This does not run navigation.
Old optimizer/scheduler/index/LMDB states are deliberately not resumed.
"""

import argparse
import copy
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image

from csv_log import CsvLog
from visual_stage_data import TRAIN_ROUTES, VisualStageData, extract_verified_handoff, audit_legacy_train_index

ROOT = Path(__file__).resolve().parents[1]


def make_batch(data, tensors, items, torch, device, rng=None):
    """No cache lookup; goals come from the same split as the observations."""
    obs, goals, actions, distances, valid = [], [], [], [], []
    for route, node in items:
        goal_route = route
        if rng is None:
            offset = data.horizon
        else:
            offset = int(rng.integers(0, min(20, len(tensors[route])-node-1) + 1))
            if rng.random() < 0.1:
                goal_route = str(rng.choice([r for r in TRAIN_ROUTES if r != route]))
        goal = node + offset if goal_route == route else int(rng.integers(len(tensors[goal_route])))
        obs.append(torch.cat(tensors[route][node-data.context:node+1], dim=0))
        goals.append(tensors[goal_route][goal])
        actions.append(data.actions(route, node) / data.spacing_m)
        distances.append(offset if goal_route == route else 20)
        valid.append(float(goal_route == route and 3 < offset < 20))
    return (torch.stack(obs).to(device), torch.stack(goals).to(device),
            torch.as_tensor(np.asarray(actions), dtype=torch.float32, device=device),
            torch.tensor(distances, dtype=torch.float32, device=device),
            torch.tensor(valid, dtype=torch.float32, device=device))


def train_step(model, ema, optimizer, batch, scheduler, stats, torch, ema_decay=0.99):
    obs, goals, target, distance, action_mask = batch
    cond = model("vision_encoder", obs_img=obs, goal_img=goals,
                 input_goal_mask=torch.zeros(len(obs), dtype=torch.long, device=obs.device))
    predicted_distance = model("dist_pred_net", obsgoal_cond=cond).flatten()
    distance_loss = ((predicted_distance - distance) / 20).square().mean()
    delta = torch.diff(target, dim=1, prepend=torch.zeros_like(target[:, :1]))
    low = torch.as_tensor(stats["min"], dtype=target.dtype, device=target.device)
    high = torch.as_tensor(stats["max"], dtype=target.dtype, device=target.device)
    normalized = (delta-low) / (high-low) * 2 - 1
    noise = torch.randn_like(normalized)
    steps = torch.randint(scheduler.config.num_train_timesteps, (len(obs),), device=obs.device)
    noisy = scheduler.add_noise(normalized, noise, steps)
    predicted = model("noise_pred_net", sample=noisy, timestep=steps, global_cond=cond)
    per_item = (predicted-noise).square().mean(dim=(1, 2))
    noise_loss = (per_item*action_mask).sum() / action_mask.sum().clamp_min(1)
    loss = noise_loss + distance_loss
    if not torch.isfinite(loss):
        raise FloatingPointError("Nonfinite training loss; stopped before optimizer update")
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    with torch.no_grad():
        for dst, src in zip(ema.parameters(), model.parameters()):
            dst.lerp_(src, 1-ema_decay)
        for dst, src in zip(ema.buffers(), model.buffers()):
            dst.copy_(src)
    return {"loss": float(loss.detach()), "noise_loss": float(noise_loss.detach()),
            "distance_loss_normalized": float(distance_loss.detach()),
            "action_examples": int(action_mask.sum())}


def finish_epoch(scheduler):
    """One scheduler transition after one completed training epoch."""
    scheduler.step()
    return scheduler.state_dict()


def evaluate(model, data, tensors, runtime, scheduler, torch, device):
    all_error, turn_error, correct, distance_errors = [], [], [], []
    model.eval()
    devices = [device.index if device.index is not None else torch.cuda.current_device()] if device.type == "cuda" else []
    with torch.random.fork_rng(devices=devices), torch.inference_mode():
        torch.manual_seed(12345)
        for start in range(0, len(data.valid), 4):
            items = data.valid[start:start+4]
            obs, goals, target, distance, _ = make_batch(data, tensors, items, torch, device)
            cond = model("vision_encoder", obs_img=obs, goal_img=goals,
                         input_goal_mask=torch.zeros(len(obs), dtype=torch.long, device=device))
            cond = cond.repeat_interleave(8, dim=0)
            noise = torch.randn((len(obs)*8, data.horizon, 2), device=device)
            scheduler.set_timesteps(scheduler.config.num_train_timesteps)
            for step in scheduler.timesteps:
                predicted = model("noise_pred_net", sample=noise, timestep=step, global_cond=cond)
                noise = scheduler.step(model_output=predicted, timestep=step, sample=noise).prev_sample
            sample = runtime.to_numpy(runtime.get_action(noise)).reshape(len(obs), 8, data.horizon, 2)
            sample *= data.spacing_m  # same units as physical validation labels
            gt = runtime.to_numpy(target) * data.spacing_m
            errors = np.linalg.norm(sample-gt[:, None], axis=-1).mean(axis=-1)
            all_error.extend(errors.ravel().tolist())
            for k, item in enumerate(items):
                if data.turn_class(*item) != "straight":
                    turn_error.extend(errors[k].tolist())
                    correct.extend((np.sign(sample[k, :, 2, 1]) == np.sign(gt[k, 2, 1])).tolist())
            # Calibrate self, adjacent, and future distances on validation only.
            goal_list = [tensors[r][n+offset] for r, n in items for offset in (0, 1, 4, 8)]
            val_cond = model("vision_encoder", obs_img=obs.repeat_interleave(4, dim=0),
                             goal_img=torch.stack(goal_list).to(device),
                             input_goal_mask=torch.zeros(len(goal_list), dtype=torch.long, device=device))
            dp = runtime.to_numpy(model("dist_pred_net", obsgoal_cond=val_cond).flatten())
            distance_errors.extend((dp-np.tile([0, 1, 4, 8], len(items)))**2)
    if not turn_error:
        raise ValueError("Validation has no turning observations")
    result = {"validation_ade_m": float(np.mean(all_error)),
              "validation_turn_ade_m": float(np.mean(turn_error)),
              "validation_turn_sign_accuracy": float(np.mean(correct)),
              "validation_distance_rmse": float(np.sqrt(np.mean(distance_errors)))}
    result["selection_score"] = result["validation_ade_m"] + result["validation_turn_ade_m"] + 0.01*result["validation_distance_rmse"]
    if not all(math.isfinite(value) for value in result.values()):
        raise FloatingPointError("Nonfinite validation metric")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, help="new output directory; existing files are not overwritten")
    p.add_argument("--handoff", default=str(ROOT / "gazebo_sim/training_handoff"))
    p.add_argument("--prepare-only", action="store_true", help="verify data and export split report without Torch/GPU")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--steps-per-epoch", type=int, default=32)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if min(args.epochs, args.steps_per_epoch, args.batch_size) < 1 or not math.isfinite(args.lr) or args.lr <= 0:
        p.error("positive finite learning rate and positive training counts are required")
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        p.error("output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    manifest = extract_verified_handoff(args.handoff, out / "handoff")
    data = VisualStageData(out / "handoff/dataset")
    report = data.report()
    report["legacy_train_index_audit"] = audit_legacy_train_index(out / "handoff")
    (out / "data_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.prepare_only:
        print(f"Verified archive: {manifest['archive']['sha256']}")
        print(f"Train: {len(data.train)} observations (00-04); validation: {len(data.valid)} (05); no old caches used.")
        return

    import torch
    import yaml
    import nomad_navigate_ros2 as runtime
    from vint_train.training.train_utils import ACTION_STATS
    if not torch.cuda.is_available():
        p.error("CUDA is required for training; use the local GPU NOMAD_PY")
    device = torch.device("cuda")
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    models = yaml.safe_load((runtime.DEPLOY / "config/models.yaml").read_text(encoding="utf-8"))
    entry = models["nomad_b40"]
    config = runtime.resolve_path(runtime.DEPLOY / "config", entry["config_path"])
    checkpoint = runtime.resolve_path(runtime.DEPLOY, entry["ckpt_path"])
    initial_hash = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    known_hash = json.loads((ROOT / "gazebo_sim/visual_audit_b40_gpu/manifest.json").read_text())["checkpoint_sha256"]
    if initial_hash != known_hash:
        p.error("nomad_b40 no longer points to the verified base checkpoint; refusing an ambiguous warm start")
    mp = runtime.load_train_config(config)
    if mp["context_size"] != data.context or mp["len_traj_pred"] != data.horizon or not mp.get("normalize", True):
        p.error("stage expects the verified normalized context=3, horizon=8 b40 architecture")
    model = runtime.load_model(str(checkpoint), mp, device)
    try:
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    except TypeError:
        state = torch.load(checkpoint, map_location="cpu")
    model.load_state_dict(state, strict=True)
    del state
    ema = copy.deepcopy(model).eval().requires_grad_(False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scheduler = runtime.DDPMScheduler(num_train_timesteps=mp["num_diffusion_iters"],
                                      beta_schedule="squaredcos_cap_v2", clip_sample=True, prediction_type="epsilon")
    tensors = {}
    for route, info in data.routes.items():
        tensors[route] = []
        for path in info["paths"]:
            with Image.open(path) as image:
                tensors[route].append(runtime.transform_images(image.convert("RGB"), mp["image_size"], center_crop=False).squeeze(0))
    provenance = {**vars(args), "initial_checkpoint": str(checkpoint), "initial_checkpoint_sha256": initial_hash,
                  "optimizer_reset": True, "scheduler_reset": True, "scheduler_steps_per_epoch": 1,
                  "goal_mask_probability": 0.0, "negative_probability": 0.1,
                  "ema_decay": 0.99,
                  "action_stats": {k: np.asarray(v).tolist() for k, v in ACTION_STATS.items()},
                  "turn_balanced_observation_sampling": True,
                  "distance_loss": "MSE(predicted_distance/20, label/20)",
                  "selection": "min ADE + turn ADE + 0.01*distance RMSE; turn ADE/direction/distance cannot regress from baseline",
                  "torch": torch.__version__, "handoff_sha256": manifest["archive"]["sha256"]}
    (out / "stage_config.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    architecture = ("model_type", "vision_encoder", "context_size", "encoding_size",
                    "obs_encoder", "attn_unet", "cond_predict_scale", "mha_num_attention_heads",
                    "mha_num_attention_layers", "mha_ff_dim_factor", "down_dims", "num_diffusion_iters",
                    "normalize", "len_traj_pred", "learn_angle", "image_size")
    export_config = {key: copy.deepcopy(mp[key]) for key in architecture if key in mp}
    export_config["run_name"] = "nomad_visual_clean_stage"
    export_config["goal_mask_prob"] = 0.0
    export_config["distance"] = {"min_dist_cat": 0, "max_dist_cat": 20}
    export_config["action"] = {"min_dist_cat": 3, "max_dist_cat": 20}
    export_config["inference_only_config"] = True
    export_config["training_recipe"] = str(out / "stage_config.json")
    export_config["datasets"] = {"go_stanford": {
        "data_folder": str(out / "handoff/dataset"),
        "train_routes": list(TRAIN_ROUTES), "validation_routes": ["house_run_05"],
        "note": "cache-free train_visual_stage.py; dataset name retains the 0.12m action-unit convention"}}
    (out / "model.yaml").write_text(yaml.safe_dump(export_config), encoding="utf-8")
    metrics_log, step_log = CsvLog(out / "metrics.csv"), CsvLog(out / "steps.csv")
    best, update, baseline = float("inf"), 0, None
    started = time.monotonic()

    def assess(epoch, train_loss=None):
        nonlocal best, baseline
        metrics = evaluate(ema, data, tensors, runtime, scheduler, torch, device)
        if baseline is None:
            baseline = dict(metrics)
        eligible = (metrics["validation_turn_ade_m"] <= baseline["validation_turn_ade_m"]
                    and metrics["validation_turn_sign_accuracy"] >= baseline["validation_turn_sign_accuracy"]
                    and metrics["validation_distance_rmse"] <= baseline["validation_distance_rmse"])
        metrics_log.write({"epoch": epoch, "updates": update, "train_loss": train_loss,
                           "next_lr": optimizer.param_groups[0]["lr"], "eligible": eligible, **metrics})
        if eligible and metrics["selection_score"] < best:
            best = metrics["selection_score"]
            torch.save(ema.state_dict(), out / "best.tmp")
            (out / "best.tmp").replace(out / "best.pth")
            (out / "best.json").write_text(json.dumps({"epoch": epoch, "updates": update, **metrics}, indent=2), encoding="utf-8")
        print(f"epoch={epoch} updates={update} validation={metrics} elapsed={time.monotonic()-started:.1f}s", flush=True)

    weights = data.sampling_weights()
    weights /= weights.sum()
    try:
        assess(-1)  # baseline can remain best if adaptation does not improve validation
        for epoch in range(args.epochs):
            model.train()
            losses = []
            for _ in range(args.steps_per_epoch):
                indices = rng.choice(len(data.train), size=args.batch_size, replace=True, p=weights)
                items = [data.train[int(i)] for i in indices]
                batch = make_batch(data, tensors, items, torch, device, rng)
                loss = train_step(model, ema, optimizer, batch, scheduler, ACTION_STATS, torch)
                update += 1
                losses.append(loss["loss"])
                step_log.write({"epoch": epoch, "update": update, "lr": optimizer.param_groups[0]["lr"], **loss})
            state = finish_epoch(lr_scheduler)
            (out / "scheduler_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
            assess(epoch, float(np.mean(losses)))
    finally:
        metrics_log.close()
        step_log.close()
    print(f"Finished. Best EMA weights: {out / 'best.pth'}; check best.json (epoch=-1 means baseline won).")


if __name__ == "__main__":
    main()

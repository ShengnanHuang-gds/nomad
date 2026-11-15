"""Joint path output layer + diffusion A/B (arms A freeze path, B trains last Linear only)."""
from __future__ import annotations
import argparse
import copy
import csv
import json
import os
import subprocess
import sys
import time
import numpy as np
import torch
import torch.nn.functional as F
from diffusers.training_utils import EMAModel
from torch.utils.data import DataLoader
from tqdm import tqdm
from warmup_scheduler import GradualWarmupScheduler
from e_path_joint_common import (
    build_cond_blend_path,
    clone_path_output_layer,
    gt_path_from_actions,
    mu_from_frozen_wp,
    path_loss_smooth_l1,
    save_joint_bundle,
    sha256_file,
)
from eval_by_distance import load_config
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, meters_per_unit, normalize_images
from train_e_dino import (
    ViNTWithDinoRows,
    append_goal_pos,
    build_e_model,
    estimated_goal_pos,
    get_delta,
    load_dino_head,
    train_one_epoch,
)
from train_goal_dino import CACHE_DIR, load_cache
from vint_train.training.train_utils import ACTION_STATS, normalize_data
from vint_train.visualizing.visualize_utils import from_numpy
DEFAULT_E = "logs/nomad/nomad_e_ft_pathact8/ema_latest.pth"
DEFAULT_WP = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
DEFAULT_DINO = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
class PathLinearEMA:
    """Shadow weights updated in lockstep with diffusers EMAModel on the UNet."""
    def __init__(self, module: torch.nn.Linear):
        self.module = module
        self.averaged = copy.deepcopy(module.state_dict())
        self.optimization_step = 0
        self.power = 0.75
    def get_decay(self):
        self.optimization_step += 1
        return min(self.power, (1 + self.optimization_step) / (10 + self.optimization_step))
    def step(self):
        decay = self.get_decay()
        for k, v in self.module.state_dict().items():
            self.averaged[k] = self.averaged[k] * decay + v * (1.0 - decay)
    def state_dict(self):
        return copy.deepcopy(self.averaged)
def trainable_params_manifest(model, path_head_train=None):
    out = []
    for n, p in model.noise_pred_net.named_parameters():
        if p.requires_grad:
            out.append({"name": f"noise_pred_net.{n}", "shape": list(p.shape), "n": p.numel()})
    if path_head_train is not None:
        for n, p in path_head_train.named_parameters():
            if p.requires_grad:
                out.append({"name": f"path_head_train.{n}", "shape": list(p.shape), "n": p.numel()})
    return out
def train_one_epoch_b(
    model,
    loc_model,
    ema,
    path_ema,
    dino_head,
    wp_head_frozen,
    path_head_train,
    features,
    loader,
    optimizer,
    scheduler_noise,
    device,
    args,
    epoch,
    lr_scheduler=None,
):
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    model.noise_pred_net.train()
    dino_head.eval()
    wp_head_frozen.eval()
    path_head_train.train()
    loss_diff_sum = loss_path_sum = 0.0
    count = 0
    goal_mask_prob = args.goal_mask_prob
    num_batches = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    lr_start = float(optimizer.param_groups[0]["lr"])
    with tqdm(loader, total=num_batches, desc=f"B epoch {epoch}", leave=False) as bar:
        for i, batch in enumerate(bar):
            if i >= num_batches:
                break
            (
                obs_image,
                goal_image,
                actions,
                _distance,
                _goal_pos,
                _idx,
                action_mask,
                curr_rows,
                goal_rows,
                past_rows,
            ) = batch
            batch_obs, batch_goal = normalize_images(obs_image, goal_image, device)
            action_mask = action_mask.to(device)
            b = actions.shape[0]
            goal_mask = (torch.rand(b, device=device) < goal_mask_prob).long()
            with torch.no_grad():
                obsgoal_cond = model(
                    "vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=goal_mask
                )
            mu = mu_from_frozen_wp(
                loc_model,
                dino_head,
                features,
                batch_obs,
                batch_goal,
                curr_rows,
                goal_rows,
                device,
                wp_head_frozen,
                wp_scale=args.wp_scale,
                past_rows=past_rows,
            )
            path_in = None
            est_pos = build_cond_blend_path(
                mu,
                wp_head_frozen,
                path_head_train,
                features,
                curr_rows,
                goal_rows,
                past_rows,
                device,
                args.pos_dim,
                args.path_units,
                args.meters_per_unit,
                frozen_path_for_cond=False,
            )
            if goal_mask.any():
                est_pos = est_pos.clone()
                est_pos[goal_mask.bool(), :] = 0.0
            diffusion_cond = append_goal_pos(obsgoal_cond, est_pos, goal_mask)
            deltas = get_delta(actions)
            naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
            noise = torch.randn_like(naction)
            timesteps = torch.randint(0, scheduler_noise.config.num_train_timesteps, (b,), device=device).long()
            noisy = scheduler_noise.add_noise(naction, noise, timesteps)
            pred = model("noise_pred_net", sample=noisy, timestep=timesteps, global_cond=diffusion_cond)
            per = F.mse_loss(pred, noise, reduction="none").mean(dim=list(range(1, pred.ndim)))
            loss_diff = (per * action_mask).mean() / (action_mask.mean() + 1e-2)
            tgt_path = gt_path_from_actions(actions.to(device))
            if path_in is None:
                from e_path_joint_common import wp_path_input_features
                path_in = wp_path_input_features(
                    wp_head_frozen, features, curr_rows, goal_rows, past_rows, device
                )
            pred_path = path_head_train(path_in).view(-1, 8, 2)
            if args.path_units == "meters":
                pred_path = pred_path / max(float(args.meters_per_unit), 1e-6)
            loss_path = path_loss_smooth_l1(pred_path, tgt_path, beta=1.0)
            loss = loss_diff + float(args.path_loss_weight) * loss_path
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.grad_clip:
                params = list(model.noise_pred_net.parameters()) + list(path_head_train.parameters())
                torch.nn.utils.clip_grad_norm_(params, float(args.max_grad_norm))
            optimizer.step()
            if lr_scheduler is not None and args.lr_schedule == "per_step":
                lr_scheduler.step()
            ema.step(model)
            path_ema.step()
            n = int(action_mask.sum().item())
            loss_diff_sum += loss_diff.item() * max(n, 1)
            loss_path_sum += loss_path.item() * max(n, 1)
            count += max(n, 1)
            bar.set_postfix(Ld=f"{loss_diff.item():.4f}", Lp=f"{loss_path.item():.4f}")
    lr_end = float(optimizer.param_groups[0]["lr"])
    return (
        loss_diff_sum / max(count, 1),
        loss_path_sum / max(count, 1),
        lr_start,
        lr_end,
    )
def run_val_subprocess(train_root, output_dir, epoch, args, path_head_ema_file: str = ""):
    val_json = os.path.join(output_dir, f"val_nav_epoch{epoch}.json")
    if args.arm == "b" and path_head_ema_file:
        val_script = "eval_e_joint_ab_val.py"
        extra = ["--path-head-train", path_head_ema_file, "--wp-head", args.wp_head]
    else:
        val_script = "eval_e_path_adapt_val.py"
        extra = []
        if args.wp_head:
            extra.extend(["--wp-head", args.wp_head])
    val_cmd = [
        sys.executable,
        "-u",
        os.path.join(train_root, val_script),
        "--checkpoint",
        os.path.join(output_dir, f"ema_{epoch}.pth"),
        "--manifest-csv",
        args.val_manifest_csv,
        "--dino-head",
        args.dino_head,
        "--config-e-dino",
        args.config,
        "--config-b",
        args.config_b,
        "--path-units",
        args.path_units,
        "--path-source",
        args.path_source,
        "--path-gate",
        args.path_gate,
        "--goal-pos-mode",
        args.goal_pos_mode,
        "--wp-scale",
        str(args.wp_scale),
        "--pos-dim",
        str(args.pos_dim),
        "--epoch",
        str(epoch),
        "--out-dir",
        output_dir,
        "--out-json",
        val_json,
    ]
    val_cmd.extend(extra)
    env = os.environ.copy()
    dp = os.path.join(os.path.dirname(train_root), "diffusion_policy")
    env["PYTHONPATH"] = dp if not env.get("PYTHONPATH") else dp + os.pathsep + env["PYTHONPATH"]
    subprocess.run(val_cmd, cwd=train_root, check=True, env=env)
    with open(val_json, encoding="utf-8") as vf:
        return json.load(vf)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("a", "b"), required=True)
    parser.add_argument("--config", default="config/nomad_e_dino_path.yaml")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--init-ckpt", default=DEFAULT_E)
    parser.add_argument("--dino-head", default=DEFAULT_DINO)
    parser.add_argument("--wp-head", default=DEFAULT_WP)
    parser.add_argument("--goal-pos-mode", default="blend_path")
    parser.add_argument("--path-source", default="wp_poly")
    parser.add_argument("--path-units", default="dataset")
    parser.add_argument("--path-gate", default="none")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument("--pos-dim", type=int, default=18)
    parser.add_argument("--true-pos-prob", type=float, default=0.0)
    parser.add_argument("--goal-mask-prob", type=float, default=0.0)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr-unet", type=float, default=3e-6)
    parser.add_argument("--lr-path", type=float, default=1e-5)
    parser.add_argument("--path-loss-weight", type=float, default=1.0)
    parser.add_argument("--warmup-epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--val-manifest-csv", required=True)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--start-epoch", type=int, default=0)
    parser.add_argument("--resume-bundle", default="", help="bundle_epochN.pth for strict resume")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--max-batches", type=int, default=0)
    parser.add_argument("--lr-schedule", default="per_step", choices=("per_step", "epoch"))
    parser.add_argument("--reset-train-rng-after-init", action="store_true")
    args = parser.parse_args()
    for p in (args.init_ckpt, args.dino_head, args.wp_head, args.checkpoint_b):
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing checkpoint/config file: {p}")
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config(args.config)
    config["epochs"] = args.epochs
    config["batch_size"] = args.batch_size
    config["lr"] = args.lr_unet
    config["warmup_epochs"] = args.warmup_epochs
    config["clipping"] = True
    config["max_norm"] = 1.0
    args.grad_clip = True
    args.max_grad_norm = 1.0
    args.goal_mask_prob = args.goal_mask_prob
    args.true_pos_prob = args.true_pos_prob
    args.print_every = 0
    run_name = args.run_dir or os.path.join(
        "logs",
        "revalidation",
        f"e_path_joint_{args.arm}_{time.strftime('%Y_%m_%d_%H_%M_%S')}",
    )
    output_dir = run_name if os.path.isabs(run_name) else os.path.join(os.path.dirname(__file__), run_name)
    os.makedirs(output_dir, exist_ok=True)
    init_meta = {
        "init_ckpt": os.path.abspath(args.init_ckpt),
        "init_sha256": sha256_file(args.init_ckpt),
        "wp_head": os.path.abspath(args.wp_head),
        "wp_sha256": sha256_file(args.wp_head),
        "arm": args.arm,
        "seed": args.seed,
    }
    with open(os.path.join(output_dir, "init_meta.json"), "w", encoding="utf-8") as f:
        json.dump(init_meta, f, indent=2)
    cache_path, rows, meta = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    dino_head, dino_meta = load_dino_head(args.dino_head, device)
    wp_head, wp_meta = load_dino_head(args.wp_head, device)
    for key in ("model", "width", "height", "pool"):
        if dino_meta[key] != meta[key] or wp_meta[key] != meta[key]:
            raise RuntimeError("DINO/WP cache mismatch vs head")
    data_config = config["datasets"]["go_stanford"]
    dataset = ViNTWithDinoRows(
        data_folder=data_config["data_folder"],
        data_split_folder=data_config["train"],
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
        dino_rows=rows,
    )
    dl_gen = torch.Generator()
    dl_gen.manual_seed(int(args.seed))
    loader = DataLoader(
        dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=args.num_workers,
        persistent_workers=args.num_workers > 0,
        drop_last=True,
        generator=dl_gen,
    )
    args.meters_per_unit = float(meters_per_unit(dataset))
    steps_per_epoch = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    total_steps = steps_per_epoch * int(config["epochs"])
    print(
        f"arm={args.arm} samples={len(dataset)} batch={config['batch_size']} "
        f"batches/epoch={steps_per_epoch} updates={total_steps} meters/unit={args.meters_per_unit:.4f}"
    )
    model, noise_scheduler = build_e_model(config, args.pos_dim)
    state = torch.load(args.init_ckpt, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "ema" in state:
        state = state["ema"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state, strict=True)
    model.to(device)
    loc_model = load_frozen_nomad(load_config(args.config_b), args.checkpoint_b, device)
    if args.reset_train_rng_after_init:
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(args.seed)
        dl_gen.manual_seed(int(args.seed))
    model.vision_encoder.requires_grad_(False)
    model.dist_pred_net.requires_grad_(False)
    dino_head.requires_grad_(False)
    for p in wp_head.parameters():
        p.requires_grad_(False)
    path_head_train = None
    path_ema = None
    if args.arm == "b":
        path_head_train = clone_path_output_layer(wp_head).to(device)
        path_ema = PathLinearEMA(path_head_train)
    opt_params = [{"params": model.noise_pred_net.parameters(), "lr": args.lr_unet}]
    if path_head_train is not None:
        opt_params.append({"params": path_head_train.parameters(), "lr": args.lr_path})
    optimizer = torch.optim.AdamW(opt_params, weight_decay=1e-4)
    warmup_epochs = int(config.get("warmup_epochs", 1))
    if args.lr_schedule == "per_step":
        from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
        warmup_steps = max(steps_per_epoch * max(warmup_epochs, 1), 1)
        sched_warm = LinearLR(optimizer, start_factor=1e-2, end_factor=1.0, total_iters=warmup_steps)
        sched_cos = CosineAnnealingLR(optimizer, T_max=max(total_steps - warmup_steps, 1))
        lr_scheduler = SequentialLR(optimizer, schedulers=[sched_warm, sched_cos], milestones=[warmup_steps])
        print(f"LR per_step warmup_steps={warmup_steps} first_lr={sched_warm.get_last_lr()[0]:.2e}")
    else:
        cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(int(config["epochs"]), 1))
        lr_scheduler = (
            GradualWarmupScheduler(optimizer, multiplier=1, total_epoch=warmup_epochs, after_scheduler=cosine)
            if warmup_epochs > 0
            else cosine
        )
    ema = EMAModel(model=model, power=0.75)
    ema.averaged_model.load_state_dict(model.state_dict(), strict=True)
    manifest = trainable_params_manifest(model, path_head_train)
    with open(os.path.join(output_dir, "trainable_params.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"trainable tensors: {len(manifest)}")
    train_root = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(output_dir, "train_log.csv")
    log_rows = []
    best_ade = float("inf")
    best_epoch = -1
    global_step = 0
    if args.start_epoch > 0 and os.path.isfile(log_path):
        with open(log_path, newline="", encoding="utf-8") as lf:
            log_rows = list(csv.DictReader(lf))
        for r in log_rows:
            if r.get("val_nav_ade_cm"):
                ade = float(r["val_nav_ade_cm"])
                ep = int(float(r["epoch"]))
                if ade < best_ade:
                    best_ade, best_epoch = ade, ep
        print(f"Resumed log: {len(log_rows)} rows, best_epoch={best_epoch}, best_ade={best_ade:.4f} cm")
    if args.resume_bundle:
        from e_path_joint_common import load_joint_bundle
        bk = load_joint_bundle(args.resume_bundle, device)
        model.load_state_dict(bk["model"], strict=True)
        ema.averaged_model.load_state_dict(bk["ema"], strict=True)
        if bk.get("optimizer") is not None:
            optimizer.load_state_dict(bk["optimizer"])
        if bk.get("scheduler") is not None:
            lr_scheduler.load_state_dict(bk["scheduler"])
        global_step = int(bk.get("global_step", 0))
        if hasattr(ema, "optimization_step"):
            ema.optimization_step = int(bk.get("ema_step", getattr(ema, "optimization_step", 0)))
        if path_ema is not None and bk.get("path_head_train") is not None:
            path_ema.averaged = copy.deepcopy(bk["path_head_train"])
            path_head_train.load_state_dict(bk["path_head_train"])
        print(f"Loaded resume bundle: {args.resume_bundle} global_step={global_step}")
    for epoch in range(args.start_epoch, int(config["epochs"])):
        t0 = time.time()
        if args.arm == "a":
            loss, lr0, lr1 = train_one_epoch(
                model,
                loc_model,
                ema,
                dino_head,
                wp_head,
                None,
                features,
                loader,
                optimizer,
                noise_scheduler,
                device,
                args,
                epoch,
                lr_scheduler=lr_scheduler if args.lr_schedule == "per_step" else None,
            )
            row = {"epoch": epoch, "train_loss": loss, "lr_start": lr0, "lr_end": lr1}
        else:
            ld, lp, lr0, lr1 = train_one_epoch_b(
                model,
                loc_model,
                ema,
                path_ema,
                dino_head,
                wp_head,
                path_head_train,
                features,
                loader,
                optimizer,
                noise_scheduler,
                device,
                args,
                epoch,
                lr_scheduler=lr_scheduler if args.lr_schedule == "per_step" else None,
            )
            row = {
                "epoch": epoch,
                "train_loss_diff": ld,
                "train_loss_path": lp,
                "lr_start": lr0,
                "lr_end": lr1,
            }
        global_step += steps_per_epoch
        if args.lr_schedule == "epoch":
            lr_scheduler.step()
        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, f"ema_{epoch}.pth"))
        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, "ema_latest.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, f"unet_{epoch}.pth"))
        path_head_file = ""
        if path_ema is not None:
            path_head_file = os.path.join(output_dir, f"path_head_ema_{epoch}.pth")
            torch.save(path_ema.state_dict(), path_head_file)
            torch.save(path_ema.state_dict(), os.path.join(output_dir, "path_head_ema_latest.pth"))
        save_joint_bundle(
            os.path.join(output_dir, f"bundle_epoch{epoch}.pth"),
            model_state=model.state_dict(),
            ema_state=ema.averaged_model.state_dict(),
            path_head_state=path_ema.state_dict() if path_ema else None,
            optimizer_state=optimizer.state_dict(),
            scheduler_state=lr_scheduler.state_dict(),
            ema_step=ema.optimization_step,
            epoch=epoch,
            global_step=global_step,
            meta=init_meta,
        )
        if args.val_manifest_csv:
            ph = path_head_file if args.arm == "b" else ""
            val_out = run_val_subprocess(train_root, output_dir, epoch, args, ph)
            row["val_nav_ade_cm"] = val_out["nav_ade_cm"]
            row["val_nav_per_frame_csv"] = val_out.get("per_frame_csv", "")
            if val_out["nav_ade_cm"] < best_ade:
                best_ade = val_out["nav_ade_cm"]
                best_epoch = epoch
                row["is_best_nav_ade"] = True
        row["minutes"] = (time.time() - t0) / 60
        log_rows.append(row)
        with open(os.path.join(output_dir, "train_log.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=sorted({k for r in log_rows for k in r}))
            w.writeheader()
            w.writerows(log_rows)
    summary = {"best_epoch": best_epoch, "best_val_nav_ade_cm": best_ade, "arm": args.arm}
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary))
if __name__ == "__main__":
    main()

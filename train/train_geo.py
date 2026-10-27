"""Joint training of NoMaD-Geo: NoMaD + DINO bearing head, the estimate fed to the UNet.

Init: NoMaD parts from E-oracle Epoch 29 (UNet condition widened from 258 to 259,
the new std column zero-initialized); bearing head from the 60-epoch DINO head.
DINOv2 stays frozen and is read from the token cache. The NoMaD vision encoder is
frozen unless --train-encoder; the UNet, distance head and bearing head train.

UNet condition: [obsgoal_cond(256), x, y, std]. Per sample, the position is
  true      goal_pos, std 0                                   (prob --p-true)
  shuffled  a random bearing times the predicted distance, std MAX_ANGLE_STD (--p-shuffle)
  estimate  head bearing times the predicted distance, std = 1/sqrt(kappa)  (the rest)
Rows whose goal is masked get zeros, as in E-oracle. The distance never carries
diffusion gradients into the distance head. --head-grad stop also detaches the
bearing and std, so the head learns only from its own loss.

Loss: alpha * distance + (1 - alpha) * diffusion + lambda * von Mises bearing NLL
(bearing loss on action-range goals >= 0.3 m, weighted by distance / 20).

Validation: held-out trajectories (the D-ft list, excluded from training here),
fixed far goals (20-39 steps). Reports head bearing error and far goal use with the
model's own estimate and with the true position; ema_best.pth maximizes the former.

Run from train/:
    python -u train_geo.py --run-name geo_g1
"""

import argparse
import csv
import json
import math
import os
import time

import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.nn.functional as F
from diffusers.training_utils import EMAModel
from torch.utils.data import DataLoader
from tqdm import tqdm

from eval_by_distance import load_config, load_observation
from eval_goal_head import meters_per_unit, normalize_images
from eval_position_noise import diffuse, mean_ade_fde
from train_e_dino import DINO_BEST, E_ORACLE_CHECKPOINT, ViNTWithDinoRows, build_e_model, read_tokens
from train_goal_dino import CACHE_DIR, DFT_VAL_LIST, load_cache
from train_goal_dir import log_i0
from vint_train.models.nomad.nomad_geo import GEO_DIM, MAX_ANGLE_STD, NoMaDGeo
from vint_train.models.nomad.pair_token_head import PairTokenHead
from vint_train.training.train_utils import ACTION_STATS, get_delta, normalize_data
from vint_train.visualizing.visualize_utils import from_numpy

FAR_MIN, FAR_MAX = 20, 39


def head_from_state(state):
    meta, run_args = state["meta"], state["args"]
    return PairTokenHead(
        meta["dim"],
        meta["tokens"],
        run_args["width"],
        run_args["layers"],
        run_args["heads"],
        run_args["dropout"],
        run_args.get("context", 0),
        n_sectors=run_args.get("n_sectors", 0),
    )


def build_geo(config, head_state):
    nomad, scheduler = build_e_model(config, GEO_DIM)
    scheduler.set_timesteps(config["num_diffusion_iters"])
    return NoMaDGeo(nomad, head_from_state(head_state)), scheduler


def init_from_e_oracle(geo, e_oracle_path, head_state):
    state = torch.load(e_oracle_path, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    target = geo.nomad.state_dict()
    loaded, widened = {}, 0
    for key, value in state.items():
        if key not in target:
            raise RuntimeError(f"E-oracle key missing in NoMaD-Geo: {key}")
        if value.shape == target[key].shape:
            loaded[key] = value
        elif value.ndim == 2 and value.shape[0] == target[key].shape[0] and value.shape[1] + 1 == target[key].shape[1]:
            wide = torch.zeros_like(target[key])
            wide[:, : value.shape[1]] = value
            loaded[key] = wide
            widened += 1
        else:
            raise RuntimeError(f"Shape mismatch {key}: {tuple(value.shape)} vs {tuple(target[key].shape)}")
    missing = set(target) - set(loaded)
    if missing:
        raise RuntimeError(f"NoMaD-Geo keys not filled from E-oracle: {sorted(missing)[:5]}")
    geo.nomad.load_state_dict(loaded, strict=True)
    geo.dir_head.load_state_dict(head_state["head"], strict=True)
    print(f"Init: E-oracle ({widened} cond matrices widened, std column = 0) + DINO head epoch {head_state['epoch']}")


def make_dataset(config, rows, split="train"):
    data_config = config["datasets"]["go_stanford"]
    return ViNTWithDinoRows(
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
        dino_rows=rows,
    )


def val_items(index_to_data, val_trajs, n, seed):
    rng = np.random.default_rng(seed)
    entries = [e for e in index_to_data if e[0] in val_trajs and e[2] >= FAR_MIN]
    pick = rng.choice(len(entries), size=min(n, len(entries)), replace=False)
    items = []
    for i in sorted(pick):
        traj_name, t, max_goal = entries[i]
        k = int(rng.integers(FAR_MIN, min(FAR_MAX, max_goal) + 1))
        items.append((traj_name, t, t + k))
    return items


@torch.no_grad()
def validate(model, scheduler, dataset, items, rows, features, device, meters, num_samples, batch_size, seed):
    model.eval()
    gen = torch.Generator(device=device).manual_seed(seed)
    ade = {"mask": [], "estimate": [], "true": []}
    bearing_err, dist_ratio = [], []
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        obs_l, goal_l, gt_l, pos_l = [], [], [], []
        for traj_name, t, g in chunk:
            obs, goal, actions, goal_pos = load_observation(dataset, traj_name, t, g)
            obs_l.append(obs)
            goal_l.append(goal)
            gt_l.append(actions[:, :2])
            pos_l.append(goal_pos)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
        b = len(chunk)
        zeros = torch.zeros(b, dtype=torch.long, device=device)
        ones = torch.ones(b, dtype=torch.long, device=device)
        cond_goal = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=zeros)
        cond_mask = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=ones)
        curr = read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float()
        goal = read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float()
        pos, std, direction, _kappa, steps = model.estimate_goal(cond_goal, curr, goal)
        true_pos = torch.tensor(np.stack(pos_l), dtype=torch.float32, device=device)
        noise = torch.randn((b * num_samples, dataset.len_traj_pred, 2), device=device, generator=gen)
        conds = {
            "mask": model.geo_condition(cond_mask, torch.zeros_like(pos), torch.zeros_like(std), ones),
            "estimate": model.geo_condition(cond_goal, pos, std, zeros),
            "true": model.geo_condition(cond_goal, true_pos, torch.zeros_like(std), zeros),
        }
        for name, cond in conds.items():
            pred = diffuse(model, scheduler, cond, noise, num_samples, device)
            for i, gt in enumerate(gt_l):
                ade[name].append(mean_ade_fde(pred[i], gt, meters)[0])
        tdir = F.normalize(true_pos, dim=-1)
        bearing_err.append(torch.rad2deg(torch.acos((direction * tdir).sum(-1).clamp(-1, 1))).cpu().numpy())
        dist_ratio.append((steps / true_pos.norm(dim=-1).clamp(min=1e-6)).cpu().numpy())
    ade = {k: np.asarray(v) for k, v in ade.items()}
    use_est = float((ade["mask"] - ade["estimate"]).mean())
    use_true = float((ade["mask"] - ade["true"]).mean())
    return {
        "val_use_estimate_cm": 100 * use_est,
        "val_use_true_cm": 100 * use_true,
        "val_kept": use_est / use_true if use_true > 0 else float("nan"),
        "val_ade_estimate_cm": 100 * float(ade["estimate"].mean()),
        "val_far_bearing_median_deg": float(np.median(np.concatenate(bearing_err))),
        "val_far_dist_ratio_median": float(np.median(np.concatenate(dist_ratio))),
    }


def train_one_epoch(model, ema, loader, features, optimizer, lr_sched, noise_scheduler, device, meters, args, epoch):
    model.train()
    if not args.train_encoder:
        model.nomad.vision_encoder.eval()
    sums = {"loss": 0.0, "diffusion": 0.0, "distance": 0.0, "bearing": 0.0}
    n_batches = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    with tqdm(loader, total=n_batches, desc=f"geo epoch {epoch}", leave=False) as bar:
        for i, batch in enumerate(bar):
            if i >= n_batches:
                break
            obs_image, goal_image, actions, distance, goal_pos, _idx, action_mask, curr_rows, goal_rows = batch
            batch_obs, batch_goal = normalize_images(obs_image, goal_image, device)
            action_mask = action_mask.to(device)
            distance = distance.float().to(device)
            goal_pos = goal_pos.float().to(device)
            b = actions.shape[0]
            goal_mask = (torch.rand(b, device=device) < args.goal_mask_prob).long()

            with torch.set_grad_enabled(args.train_encoder):
                cond = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=goal_mask)
            dist_pred = model("dist_pred_net", obsgoal_cond=cond).squeeze(-1)
            steps = dist_pred.detach().clamp(min=0.0)
            curr = read_tokens(features, curr_rows).to(device).float()
            goal = read_tokens(features, goal_rows).to(device).float()
            direction, kappa = model("dir_head", curr_tokens=curr, goal_tokens=goal)
            std = NoMaDGeo.angle_std(kappa)
            dir_c, std_c = (direction.detach(), std.detach()) if args.head_grad == "stop" else (direction, std)

            r = torch.rand(b, device=device)
            use_true = r < args.p_true
            use_shuf = (r >= args.p_true) & (r < args.p_true + args.p_shuffle)
            theta = torch.rand(b, device=device) * 2.0 * math.pi
            shuf = torch.stack([theta.cos(), theta.sin()], dim=-1) * steps.unsqueeze(-1)
            pos = dir_c * steps.unsqueeze(-1)
            pos = torch.where(use_true.unsqueeze(-1), goal_pos, torch.where(use_shuf.unsqueeze(-1), shuf, pos))
            std_in = torch.where(use_true, torch.zeros_like(std_c), torch.where(use_shuf, torch.full_like(std_c, MAX_ANGLE_STD), std_c))
            diffusion_cond = model.geo_condition(cond, pos, std_in, goal_mask)

            naction = from_numpy(normalize_data(get_delta(actions), ACTION_STATS)).to(device)
            noise = torch.randn_like(naction)
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (b,), device=device).long()
            noisy = noise_scheduler.add_noise(naction, noise, timesteps)
            noise_pred = model("noise_pred_net", sample=noisy, timestep=timesteps, global_cond=diffusion_cond)
            per = F.mse_loss(noise_pred, noise, reduction="none").mean(dim=(1, 2))
            diffusion_loss = (per * action_mask).mean() / (action_mask.mean() + 1e-2)

            unmasked = 1.0 - goal_mask.float()
            dist_loss = (F.mse_loss(dist_pred, distance, reduction="none") * unmasked).mean() / (unmasked.mean() + 1e-2)

            target_m = goal_pos * meters
            valid = (action_mask > 0) & (target_m.norm(dim=-1) >= args.min_goal_m)
            weight = distance / 20.0 * valid.float()
            cos_err = (direction * F.normalize(target_m, dim=-1, eps=1e-6)).sum(-1).clamp(-1.0, 1.0)
            nll = -kappa * cos_err + log_i0(kappa)
            bearing_loss = (nll * weight).sum() / weight.sum().clamp(min=1e-6)

            loss = args.alpha * dist_loss + (1.0 - args.alpha) * diffusion_loss + args.lambda_dir * bearing_loss
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            lr_sched.step()
            ema.step(model)

            for key, value in (("loss", loss), ("diffusion", diffusion_loss), ("distance", dist_loss), ("bearing", bearing_loss)):
                sums[key] += value.item()
            bar.set_postfix(diff=f"{diffusion_loss.item():.4f}", brg=f"{bearing_loss.item():.2f}")
            if args.print_every > 0 and i % args.print_every == 0:
                print(
                    f"(epoch {epoch}) (batch {i}/{n_batches - 1}) diffusion {diffusion_loss.item():.4f} "
                    f"distance {dist_loss.item():.2f} bearing {bearing_loss.item():.3f}"
                )
    return {f"train_{k}": v / max(n_batches, 1) for k, v in sums.items()}


def main():
    parser = argparse.ArgumentParser(description="Joint training of NoMaD-Geo")
    parser.add_argument("--config", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--checkpoint-e-oracle", default=E_ORACLE_CHECKPOINT)
    parser.add_argument("--dino-head", default=DINO_BEST)
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--val-list", default=DFT_VAL_LIST)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--warmup-epochs", type=float, default=1.0)
    parser.add_argument("--train-encoder", action="store_true",
                        help="Also train the NoMaD vision encoder (about 3x slower per batch on the laptop GPU)")
    parser.add_argument("--lr-encoder", type=float, default=1e-5, help="Encoder and distance head")
    parser.add_argument("--lr-unet", type=float, default=3e-5)
    parser.add_argument("--lr-head", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--alpha", type=float, default=1e-4, help="Distance loss weight, as in NoMaD")
    parser.add_argument("--lambda-dir", type=float, default=0.05, help="Bearing NLL weight")
    parser.add_argument("--p-true", type=float, default=0.5)
    parser.add_argument("--p-shuffle", type=float, default=0.0)
    parser.add_argument("--head-grad", choices=("stop", "through"), default="stop")
    parser.add_argument("--goal-mask-prob", type=float, default=0.5)
    parser.add_argument("--min-goal-m", type=float, default=0.3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=1)
    parser.add_argument("--val-frames", type=int, default=256)
    parser.add_argument("--val-samples", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--print-every", type=int, default=200)
    parser.add_argument("--max-batches", type=int, default=0, help="Per-epoch cap for smoke tests")
    parser.add_argument("--run-name", default="geo")
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    cudnn.benchmark = True
    device = torch.device("cuda:0")
    output_dir = os.path.join("logs", "nomad_geo", f"{args.run_name}_{time.strftime('%Y_%m_%d_%H_%M_%S')}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"output: {os.path.abspath(output_dir)}\n{vars(args)}")

    config = load_config(args.config)
    cache_path, rows, cache_meta = load_cache(args.cache_dir, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    head_state = torch.load(args.dino_head, map_location="cpu", weights_only=False)
    for key in ("model", "width", "height", "pool"):
        if head_state["meta"][key] != cache_meta[key]:
            raise RuntimeError(f"cache {key}={cache_meta[key]} vs head {head_state['meta'][key]}")
    with open(os.path.join(output_dir, "geo_meta.json"), "w") as f:
        json.dump({"head_meta": head_state["meta"], "head_args": head_state["args"], "train_args": vars(args)}, f, indent=2)

    with open(args.val_list) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    train_set = make_dataset(config, rows)
    val_set = make_dataset(config, rows)
    items = val_items(val_set.index_to_data, val_trajs, args.val_frames, seed=1234)
    train_set.index_to_data = [e for e in train_set.index_to_data if e[0] not in val_trajs]
    meters = meters_per_unit(train_set)
    loader = DataLoader(
        train_set, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers,
        persistent_workers=args.num_workers > 0, drop_last=True,
    )
    print(f"train samples {len(train_set)} (val trajectories excluded: {len(val_trajs)}), val far frames {len(items)}")

    model, noise_scheduler = build_geo(config, head_state)
    init_from_e_oracle(model, args.checkpoint_e_oracle, head_state)
    model.to(device)

    groups = [
        {"params": list(model.nomad.dist_pred_net.parameters()), "lr": args.lr_encoder},
        {"params": list(model.nomad.noise_pred_net.parameters()), "lr": args.lr_unet},
        {"params": list(model.dir_head.parameters()), "lr": args.lr_head},
    ]
    if args.train_encoder:
        groups.insert(0, {"params": list(model.nomad.vision_encoder.parameters()), "lr": args.lr_encoder})
    else:
        model.nomad.vision_encoder.requires_grad_(False)
    trainable = sum(p.numel() for g in groups for p in g["params"] if p.requires_grad)
    print(f"train encoder: {args.train_encoder} | trainable parameters {trainable / 1e6:.2f}M")
    optimizer = torch.optim.AdamW(groups, weight_decay=args.weight_decay)
    steps_per_epoch = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    total = steps_per_epoch * args.epochs
    warm = max(1, int(steps_per_epoch * args.warmup_epochs))
    lr_sched = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm)))
    )
    ema = EMAModel(model=model, power=0.75)

    val0 = validate(model, noise_scheduler, val_set, items, rows, features, device, meters, args.val_samples, 32, args.seed)
    print("[init] " + " | ".join(f"{k} {v:.3f}" for k, v in val0.items()))
    log_rows = [{"epoch": -1, **val0}]
    best = -math.inf
    for epoch in range(args.epochs):
        start = time.time()
        train_stats = train_one_epoch(
            model, ema, loader, features, optimizer, lr_sched, noise_scheduler, device, meters, args, epoch
        )
        val = validate(
            ema.averaged_model, noise_scheduler, val_set, items, rows, features, device, meters, args.val_samples, 32, args.seed
        )
        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, f"ema_{epoch}.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, "latest.pth"))
        selected = val["val_use_estimate_cm"] > best
        if selected:
            best = val["val_use_estimate_cm"]
            torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, "ema_best.pth"))
        row = {"epoch": epoch, **train_stats, **val, "best": selected, "minutes": (time.time() - start) / 60}
        log_rows.append(row)
        with open(os.path.join(output_dir, "train_log.csv"), "w", newline="") as f:
            keys = list(dict.fromkeys(k for r in log_rows for k in r))
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(log_rows)
        print(
            f"[epoch {epoch}] diffusion {train_stats['train_diffusion']:.4f} bearing {train_stats['train_bearing']:.3f} | "
            f"val use est {val['val_use_estimate_cm']:+.2f} / true {val['val_use_true_cm']:+.2f} cm "
            f"(kept {100 * val['val_kept']:.0f}%) | bearing {val['val_far_bearing_median_deg']:.1f} deg | "
            f"dist ratio {val['val_far_dist_ratio_median']:.2f}{' | best' if selected else ''} | {row['minutes']:.1f} min"
        )
    print(f"Done. Best val use (estimate) {best:+.2f} cm -> {os.path.join(output_dir, 'ema_best.pth')}")


if __name__ == "__main__":
    main()

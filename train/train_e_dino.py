"""Train E with an estimated goal position: DINO direction x B distance (+ sigma).

Frozen: the policy's vision_encoder and dist_pred_net, the DINO PairTokenHead,
and B (Epoch 29), which always supplies the distance, as in the direct test.
Trainable: noise_pred_net only.

--init-from b         start from B; the new cond_encoder columns are zeroed
--init-from e_oracle  start from E-oracle (pos_dim 2), which already uses [x, y]
--true-pos-prob p     per sample, feed the true goal_pos with probability p

Appended condition (dataset units, same as goal_pos):
  [mu_x, mu_y] or [mu_x, mu_y, sigma], mu = dino_dir * b_dist_steps,
  sigma = b_dist_steps / sqrt(kappa), clipped. True-position rows get sigma 0.
When the goal is masked, the appended values are zeroed (same as E-oracle).

Run from train/:

    python -u train_e_dino.py
    python -u train_e_dino.py --config config/nomad_e_dino_mu.yaml --init-from e_oracle \
        --epochs 10 --lr 3e-5 --warmup-epochs 1
    python -u train_e_dino.py --config config/nomad_e_dino_mu.yaml --init-from e_oracle \
        --goal-pos-mode blend --epochs 10 --lr 3e-5 --warmup-epochs 1
"""

import argparse
import csv
import math
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from diffusers.training_utils import EMAModel
from diffusion_policy.model.diffusion.conditional_unet1d import ConditionalUnet1D
from torch.utils.data import DataLoader
from tqdm import tqdm
from warmup_scheduler import GradualWarmupScheduler

from eval_by_distance import load_config
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, meters_per_unit, normalize_images
from train_goal_dino import CACHE_DIR, PairTokenHead, load_cache


def blend_torch(g_dir, g_k, w_dir, w_k, wp_scale=1.0):
    r = g_k.unsqueeze(-1) * g_dir + (wp_scale * w_k).unsqueeze(-1) * w_dir
    return r / r.norm(dim=-1, keepdim=True).clamp(min=1e-6)
from vint_train.data.vint_dataset import ViNT_Dataset
from vint_train.models.nomad.nomad import DenseNetwork, NoMaD
from vint_train.models.nomad.nomad_vint import NoMaD_ViNT, replace_bn_with_gn
from vint_train.training.train_utils import (
    ACTION_STATS,
    append_goal_pos,
    get_delta,
    normalize_data,
)
from vint_train.visualizing.visualize_utils import from_numpy

DINO_BEST = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
WP_BEST = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth"
E_ORACLE_CHECKPOINT = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth"


class ViNTWithDinoRows(ViNT_Dataset):
    """Same samples as ViNT_Dataset, plus row indices into the DINO feature cache."""

    def __init__(self, *args, dino_rows=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.dino_rows = dino_rows

    def __getitem__(self, i):
        f_curr, curr_time, max_goal_dist = self.index_to_data[i]
        f_goal, goal_time, goal_is_negative = self._sample_goal(f_curr, curr_time, max_goal_dist)
        context_times = list(
            range(
                curr_time + -self.context_size * self.waypoint_spacing,
                curr_time + 1,
                self.waypoint_spacing,
            )
        )
        obs_image = torch.cat([self._load_image(f_curr, t) for t in context_times])
        goal_image = self._load_image(f_goal, goal_time)
        curr_traj_data = self._get_trajectory(f_curr)
        actions, goal_pos = self._compute_actions(curr_traj_data, curr_time, goal_time)
        if goal_is_negative:
            distance = self.max_dist_cat
        else:
            distance = (goal_time - curr_time) // self.waypoint_spacing
        action_mask = (
            (distance < self.max_action_distance)
            and (distance > self.min_action_distance)
            and (not goal_is_negative)
        )
        return (
            torch.as_tensor(obs_image, dtype=torch.float32),
            torch.as_tensor(goal_image, dtype=torch.float32),
            torch.as_tensor(actions, dtype=torch.float32),
            torch.as_tensor(distance, dtype=torch.int64),
            torch.as_tensor(goal_pos, dtype=torch.float32),
            torch.as_tensor(self.dataset_index, dtype=torch.int64),
            torch.as_tensor(action_mask, dtype=torch.float32),
            int(self.dino_rows[(f_curr, curr_time)]),
            int(self.dino_rows[(f_goal, goal_time)]),
        )


def build_e_model(config, pos_dim):
    vision_encoder = replace_bn_with_gn(
        NoMaD_ViNT(
            obs_encoding_size=config["encoding_size"],
            context_size=config["context_size"],
            mha_num_attention_heads=config["mha_num_attention_heads"],
            mha_num_attention_layers=config["mha_num_attention_layers"],
            mha_ff_dim_factor=config["mha_ff_dim_factor"],
        )
    )
    noise_pred_net = ConditionalUnet1D(
        input_dim=2,
        global_cond_dim=config["encoding_size"] + pos_dim,
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
    return model, scheduler


def load_b_into_e(model_e, checkpoint_b, pos_dim, device):
    """Copy B weights; zero-init the new cond_encoder columns for the appended dims."""
    state_b = torch.load(checkpoint_b, map_location="cpu", weights_only=False)
    if isinstance(state_b, dict) and "state_dict" in state_b:
        state_b = state_b["state_dict"]
    state_e = model_e.state_dict()
    loaded = {}
    zeroed = 0
    for key, value in state_b.items():
        if key not in state_e:
            raise RuntimeError(f"B key missing in E: {key}")
        target = state_e[key]
        if value.shape == target.shape:
            loaded[key] = value
        elif (
            value.ndim == 2
            and target.shape[0] == value.shape[0]
            and target.shape[1] == value.shape[1] + pos_dim
        ):
            wide = torch.zeros_like(target)
            wide[:, : value.shape[1]] = value
            loaded[key] = wide
            zeroed += 1
        else:
            raise RuntimeError(f"Shape mismatch for {key}: B {tuple(value.shape)} vs E {tuple(target.shape)}")
    missing = set(state_e) - set(loaded)
    if missing:
        raise RuntimeError(f"E keys not filled from B: {sorted(missing)[:5]}")
    model_e.load_state_dict(loaded, strict=True)
    model_e.to(device)
    print(f"Loaded B into E; zero-initialized {zeroed} cond_encoder weight matrices (+{pos_dim} cols)")
    return model_e


def load_dino_head(path, device):
    state = torch.load(path, map_location=device, weights_only=False)
    meta, run_args = state["meta"], state["args"]
    context = run_args.get("context", 0)
    multi = (run_args.get("multi_horizon") or "").strip()
    aux_horizons = tuple(int(x) for x in multi.split(",") if x.strip()) if multi else ()
    head = PairTokenHead(
        meta["dim"],
        meta["tokens"],
        run_args["width"],
        run_args["layers"],
        run_args["heads"],
        run_args["dropout"],
        context,
        n_sectors=run_args.get("n_sectors", 0),
        aux_horizons=aux_horizons,
    ).to(device)
    head.load_state_dict(state["head"])
    head.eval()
    head.requires_grad_(False)
    print(f"DINO head epoch {state['epoch']}, val far median {state['far_median_deg']:.1f} deg ({path})")
    return head, meta


def read_tokens(features, rows):
    rows = np.asarray(rows, dtype=np.int64)
    order = np.argsort(rows)
    out = np.empty((len(rows),) + features.shape[1:], dtype=np.float16)
    out[order] = features[rows[order]]
    return torch.from_numpy(out)


@torch.no_grad()
def estimated_goal_pos(
    loc_model,
    dino_head,
    features,
    batch_obs,
    batch_goal,
    curr_rows,
    goal_rows,
    pos_dim,
    device,
    wp_head=None,
    wp_scale=1.0,
    goal_pos_mode="goal",
):
    """[mu_x, mu_y] or [mu_x, mu_y, sigma] in dataset units. Masked rows are zeroed by append_goal_pos.

    Distance always comes from the frozen B distance head (loc_model), matching the direct test.
    goal_pos_mode: goal = far DINO head only; blend = kappa-weighted goal + waypoint heads.
    """
    no_mask = torch.zeros(len(batch_obs), dtype=torch.long, device=device)
    cond = loc_model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
    steps = loc_model("dist_pred_net", obsgoal_cond=cond).squeeze(-1).clamp(min=0.0)
    curr = read_tokens(features, curr_rows).to(device).float()
    goal = read_tokens(features, goal_rows).to(device).float()
    dino_out = dino_head(curr, goal)
    direction, kappa = dino_out[0], dino_out[1]
    if goal_pos_mode == "blend":
        if wp_head is None:
            raise ValueError("goal_pos_mode=blend requires wp_head")
        w_out = wp_head(curr, goal)
        direction = blend_torch(direction, kappa, w_out[0], w_out[1], wp_scale=wp_scale)
    elif goal_pos_mode != "goal":
        raise ValueError(f"unknown goal_pos_mode: {goal_pos_mode}")
    mu = direction * steps.unsqueeze(-1)
    if pos_dim == 2:
        return mu
    sigma = (steps / kappa.clamp(min=1e-3).sqrt()).clamp(max=40.0)
    return torch.cat([mu, sigma.unsqueeze(-1)], dim=-1)


def train_one_epoch(
    model, loc_model, ema, dino_head, wp_head, features, loader, optimizer, scheduler_noise, device, args, epoch
):
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    model.noise_pred_net.train()
    loss_sum, count = 0.0, 0
    goal_mask_prob = args.goal_mask_prob
    num_batches = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    with tqdm(loader, total=num_batches, desc=f"E epoch {epoch}", leave=False) as bar:
        for i, batch in enumerate(bar):
            if i >= num_batches:
                break
            obs_image, goal_image, actions, _distance, goal_pos, _idx, action_mask, curr_rows, goal_rows = batch
            batch_obs, batch_goal = normalize_images(obs_image, goal_image, device)
            action_mask = action_mask.to(device)
            b = actions.shape[0]
            goal_mask = (torch.rand(b, device=device) < goal_mask_prob).long()
            with torch.no_grad():
                obsgoal_cond = model(
                    "vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=goal_mask
                )
                est_pos = estimated_goal_pos(
                    loc_model,
                    dino_head,
                    features,
                    batch_obs,
                    batch_goal,
                    curr_rows,
                    goal_rows,
                    args.pos_dim,
                    device,
                    wp_head=wp_head,
                    wp_scale=args.wp_scale,
                    goal_pos_mode=args.goal_pos_mode,
                )
                if args.true_pos_prob > 0:
                    use_true = torch.rand(b, device=device) < args.true_pos_prob
                    est_pos[use_true, :2] = goal_pos.to(device)[use_true]
                    if args.pos_dim == 3:
                        est_pos[use_true, 2] = 0.0
            diffusion_cond = append_goal_pos(obsgoal_cond, est_pos, goal_mask)

            deltas = get_delta(actions)
            naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
            noise = torch.randn_like(naction)
            timesteps = torch.randint(0, scheduler_noise.config.num_train_timesteps, (b,), device=device).long()
            noisy = scheduler_noise.add_noise(naction, noise, timesteps)
            pred = model("noise_pred_net", sample=noisy, timestep=timesteps, global_cond=diffusion_cond)
            per = F.mse_loss(pred, noise, reduction="none").mean(dim=list(range(1, pred.ndim)))
            loss = (per * action_mask).mean() / (action_mask.mean() + 1e-2)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            ema.step(model)

            n = int(action_mask.sum().item())
            loss_sum += loss.item() * max(n, 1)
            count += max(n, 1)
            bar.set_postfix(loss=f"{loss.item():.4f}")
            if args.print_every > 0 and i % args.print_every == 0:
                print(f"(epoch {epoch}) (batch {i}/{num_batches - 1}) action loss {loss.item():.4f}")
    return loss_sum / max(count, 1)


def main():
    parser = argparse.ArgumentParser(description="Train E-μσ with DINO direction + B distance")
    parser.add_argument("--config", default="config/nomad_e_dino.yaml")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--init-from", choices=("b", "e_oracle"), default="b",
                        help="b: B weights, new cond columns zeroed. e_oracle: start from E-oracle (pos_dim 2)")
    parser.add_argument("--checkpoint-e-oracle", default=E_ORACLE_CHECKPOINT)
    parser.add_argument("--true-pos-prob", type=float, default=0.0,
                        help="Per-sample probability of feeding the true goal_pos instead of the DINO estimate")
    parser.add_argument("--warmup-epochs", type=int, default=-1, help="-1 = use config")
    parser.add_argument("--dino-head", default=DINO_BEST)
    parser.add_argument("--wp-head", default=WP_BEST, help="Waypoint DINO head (for --goal-pos-mode blend)")
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument(
        "--goal-pos-mode",
        choices=("goal", "blend"),
        default="goal",
        help="goal: dino_dir * B steps; blend: kappa mix goal + wp dirs, then * B steps",
    )
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--pos-dim", type=int, choices=(0, 2, 3), default=0, help="2=E-μ, 3=E-μσ, 0=config goal_pos_dim")
    parser.add_argument("--epochs", type=int, default=0, help="0 = use config")
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--lr", type=float, default=0.0)
    parser.add_argument("--goal-mask-prob", type=float, default=-1.0)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--print-every", type=int, default=100)
    parser.add_argument("--max-batches", type=int, default=0)
    parser.add_argument("--run-name", default="")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.epochs > 0:
        config["epochs"] = args.epochs
    if args.batch_size > 0:
        config["batch_size"] = args.batch_size
    if args.lr > 0:
        config["lr"] = args.lr
    if args.warmup_epochs >= 0:
        config["warmup_epochs"] = args.warmup_epochs
    args.goal_mask_prob = config["goal_mask_prob"] if args.goal_mask_prob < 0 else args.goal_mask_prob
    args.pos_dim = args.pos_dim or int(config.get("goal_pos_dim", 3))
    if args.pos_dim != int(config.get("goal_pos_dim", args.pos_dim)):
        raise ValueError(f"--pos-dim {args.pos_dim} disagrees with {args.config} goal_pos_dim; eval reads the config")
    if args.init_from == "e_oracle" and args.pos_dim != 2:
        raise ValueError("E-oracle conditions on [x, y]; --init-from e_oracle needs pos_dim 2")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    blend_tag = "_blend" if args.goal_pos_mode == "blend" else ""
    tag = f"d{args.pos_dim}_{args.init_from}_true{int(round(100 * args.true_pos_prob))}{blend_tag}"
    run_name = args.run_name or f"nomad_e_dino_{tag}_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    output_dir = os.path.join("logs", "nomad", run_name)
    os.makedirs(output_dir, exist_ok=True)
    print(
        f"device: {device}\noutput: {os.path.abspath(output_dir)}\npos_dim: {args.pos_dim} | init {args.init_from} | "
        f"true_pos_prob {args.true_pos_prob} | goal_pos_mode {args.goal_pos_mode} | wp_scale {args.wp_scale} | "
        f"lr {config['lr']} | epochs {config['epochs']} | warmup {config.get('warmup_epochs', 4)}"
    )

    cache_path, rows, meta = load_cache(args.cache_dir, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    dino_head, dino_meta = load_dino_head(args.dino_head, device)
    wp_head = None
    if args.goal_pos_mode == "blend":
        wp_head, wp_meta = load_dino_head(args.wp_head, device)
        for key in ("model", "width", "height", "pool"):
            if wp_meta[key] != meta[key]:
                raise RuntimeError(f"WP cache {key}={meta[key]} vs head {wp_meta[key]}")
    for key in ("model", "width", "height", "pool"):
        if dino_meta[key] != meta[key]:
            raise RuntimeError(f"DINO cache {key}={meta[key]} vs head {dino_meta[key]}")

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
    loader = DataLoader(
        dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=args.num_workers,
        persistent_workers=args.num_workers > 0,
        drop_last=True,
    )
    print(f"train samples: {len(dataset)}, meters/unit: {meters_per_unit(dataset):.3f}")

    model, noise_scheduler = build_e_model(config, args.pos_dim)
    if args.init_from == "b":
        load_b_into_e(model, args.checkpoint_b, args.pos_dim, device)
        loc_model = model
    else:
        state = torch.load(args.checkpoint_e_oracle, map_location="cpu", weights_only=False)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state, strict=True)
        model.to(device)
        print(f"Loaded E-oracle into E (strict): {args.checkpoint_e_oracle}")
        loc_model = load_frozen_nomad(load_config(args.config_b), args.checkpoint_b, device)
    model.vision_encoder.requires_grad_(False)
    model.dist_pred_net.requires_grad_(False)
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    trainable = list(model.noise_pred_net.parameters())
    print(f"Trainable UNet params: {sum(p.numel() for p in trainable) / 1e6:.2f}M")

    optimizer = torch.optim.AdamW(trainable, lr=float(config["lr"]), weight_decay=1e-4)
    total_epochs = int(config["epochs"])
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_epochs)
    lr_scheduler = GradualWarmupScheduler(
        optimizer, multiplier=1, total_epoch=int(config.get("warmup_epochs", 4)), after_scheduler=cosine
    )
    ema = EMAModel(model=model, power=0.75)

    log_rows = []
    for epoch in range(total_epochs):
        start = time.time()
        train_loss = train_one_epoch(
            model, loc_model, ema, dino_head, wp_head, features, loader, optimizer, noise_scheduler, device, args, epoch
        )
        lr_scheduler.step()

        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, f"ema_{epoch}.pth"))
        torch.save(ema.averaged_model.state_dict(), os.path.join(output_dir, "ema_latest.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, f"{epoch}.pth"))
        torch.save(model.state_dict(), os.path.join(output_dir, "latest.pth"))
        row = {
            "epoch": epoch,
            "train_action_loss": train_loss,
            "lr": optimizer.param_groups[0]["lr"],
            "minutes": (time.time() - start) / 60,
        }
        log_rows.append(row)
        with open(os.path.join(output_dir, "train_log.csv"), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerows(log_rows)
        print(f"[epoch {epoch}] action loss {train_loss:.4f} | lr {row['lr']:.2e} | {row['minutes']:.1f} min")

    with open(os.path.join(output_dir, "args.txt"), "w") as f:
        f.write(f"checkpoint_b={args.checkpoint_b}\ndino_head={args.dino_head}\npos_dim={args.pos_dim}\n")
        f.write(f"goal_pos_mode={args.goal_pos_mode}\nwp_head={args.wp_head}\nwp_scale={args.wp_scale}\n")
        f.write(f"cache={args.cache_dir}\ngoal_mask_prob={args.goal_mask_prob}\n")
        f.write(f"init_from={args.init_from}\ncheckpoint_e_oracle={args.checkpoint_e_oracle}\n")
        f.write(f"true_pos_prob={args.true_pos_prob}\nlr={config['lr']}\nepochs={config['epochs']}\n")
    print(f"Done. Checkpoints in {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

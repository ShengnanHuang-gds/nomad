"""Train D-ft: a goal-direction head on its own copy of B's vision encoder.

B itself stays untouched. D gets a copy of B's Epoch 29 EMA vision encoder.
By default goal_encoder, compress_goal_enc and sa_encoder are trainable and
the per-frame obs_encoder stays frozen (--unfreeze all trains everything).

The head predicts only the bearing of the goal in the robot frame as a von
Mises distribution (direction, kappa). Distance comes from B's distance head
at evaluation time. The first --warmup-epochs use 1 - cos(error); the rest use
the von Mises NLL  -kappa*cos(error) + log I0(kappa).

Samples: action_mask == 1 (no negatives, distance inside the action range)
and |goal_pos| >= --min-goal-m. Loss weight is proportional to the goal
distance in steps (--weight distance) or uniform (--weight none). No weighting
by turning frames.

Validation: a fixed share of training trajectories (split by trajectory,
seeded, list saved). The epoch with the lowest far (>= 20 steps) median
validation bearing error is saved as goal_dir_best.pth. The locked 1000 test
frames are not used here.

Run from train/:

    python -u train_goal_dir.py
"""

import argparse
import csv
import math
import os
import time

import numpy as np
import torch
import torch.backends.cudnn as cudnn
from torch.utils.data import DataLoader
from tqdm import tqdm

from eval_by_distance import load_config
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images
from vint_train.models.nomad.nomad import GoalDirectionHead

TRAINABLE_DEFAULT = ("goal_encoder", "compress_goal_enc", "sa_encoder")
FAR_STEPS = 20


def build_d_encoder(config, checkpoint_b, device, unfreeze):
    """Return a private copy of B's vision encoder with the requested parts trainable."""
    nomad = load_frozen_nomad(config, checkpoint_b, device)
    encoder = nomad.vision_encoder
    del nomad
    if unfreeze == "all":
        encoder.requires_grad_(True)
    else:
        for name in TRAINABLE_DEFAULT:
            getattr(encoder, name).requires_grad_(True)
    return encoder


def set_train_mode(encoder, unfreeze):
    encoder.train()
    if unfreeze != "all":
        encoder.obs_encoder.eval()


def encode_d(encoder, batch_obs, batch_goal):
    no_mask = torch.zeros((batch_obs.shape[0],), dtype=torch.long, device=batch_obs.device)
    return encoder(batch_obs, batch_goal, input_goal_mask=no_mask)


def log_i0(kappa):
    return torch.log(torch.special.i0e(kappa)) + kappa


def cos_error(direction, target_xy):
    target_dir = torch.nn.functional.normalize(target_xy, dim=-1, eps=1e-6)
    return (direction * target_dir).sum(dim=-1).clamp(-1.0, 1.0)


def direction_loss(direction, kappa, target_xy, weight, use_nll):
    cos_err = cos_error(direction, target_xy)
    if use_nll:
        per_sample = -kappa * cos_err + log_i0(kappa)
    else:
        per_sample = 1.0 - cos_err
    return (per_sample * weight).sum() / weight.sum(), cos_err


def valid_batch(goal_pos, distance, action_mask, meters, min_goal_m, weight_mode):
    target = goal_pos.float() * meters
    keep = action_mask.bool() & (torch.linalg.norm(target, dim=-1) >= min_goal_m)
    if weight_mode == "distance":
        weight = distance.float() / FAR_STEPS
    else:
        weight = torch.ones_like(distance, dtype=torch.float32)
    return keep, target, weight


def split_trajectories(traj_names, val_fraction, seed):
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(traj_names))
    n_val = max(1, int(round(val_fraction * len(traj_names))))
    val = sorted(traj_names[i] for i in order[:n_val])
    return set(val)


def restrict(dataset, traj_set, keep_inside):
    dataset.index_to_data = [entry for entry in dataset.index_to_data if (entry[0] in traj_set) == keep_inside]
    return dataset


def seed_val_worker(worker_id):
    np.random.seed(1234 + worker_id)


@torch.no_grad()
def validate(encoder, head, loader, device, meters, min_goal_m, weight_mode):
    encoder.eval()
    head.eval()
    errors, far_flags, nll_sum, cos_sum, count = [], [], 0.0, 0.0, 0
    for obs_image, goal_image, _actions, distance, goal_pos, _idx, action_mask in tqdm(loader, desc="val", leave=False):
        keep, target, weight = valid_batch(goal_pos, distance, action_mask, meters, min_goal_m, weight_mode)
        if not keep.any():
            continue
        batch_obs, batch_goal = normalize_images(obs_image[keep], goal_image[keep], device)
        direction, kappa = head(encode_d(encoder, batch_obs, batch_goal))
        target = target[keep].to(device)
        cos_err = cos_error(direction, target)
        nll = -kappa * cos_err + log_i0(kappa)
        errors.append(torch.rad2deg(torch.acos(cos_err)).cpu().numpy())
        far_flags.append((distance[keep] >= FAR_STEPS).numpy())
        nll_sum += nll.sum().item()
        cos_sum += (1.0 - cos_err).sum().item()
        count += int(keep.sum())
    errors = np.concatenate(errors)
    far = np.concatenate(far_flags)
    return {
        "val_samples": count,
        "val_median_deg": float(np.median(errors)),
        "val_far_median_deg": float(np.median(errors[far])),
        "val_far_mean_deg": float(errors[far].mean()),
        "val_vm_nll": nll_sum / count,
        "val_one_minus_cos": cos_sum / count,
    }


def train_one_epoch(encoder, head, optimizer, loader, device, meters, args, epoch):
    use_nll = epoch >= args.warmup_epochs
    set_train_mode(encoder, args.unfreeze)
    head.train()
    errors, far_flags, loss_sum, count = [], [], 0.0, 0
    num_batches = len(loader) if args.max_batches <= 0 else min(len(loader), args.max_batches)
    stage = "vm-nll" if use_nll else "1-cos"
    window_err, window_n = 0.0, 0
    with tqdm(loader, total=num_batches, desc=f"D-ft epoch {epoch} ({stage})", leave=False) as bar:
        for i, (obs_image, goal_image, _actions, distance, goal_pos, _idx, action_mask) in enumerate(bar):
            if i >= num_batches:
                break
            keep, target, weight = valid_batch(goal_pos, distance, action_mask, meters, args.min_goal_m, args.weight)
            if not keep.any():
                continue
            batch_obs, batch_goal = normalize_images(obs_image[keep], goal_image[keep], device)
            direction, kappa = head(encode_d(encoder, batch_obs, batch_goal))
            loss, cos_err = direction_loss(
                direction, kappa, target[keep].to(device), weight[keep].to(device), use_nll
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            deg = torch.rad2deg(torch.acos(cos_err.detach())).cpu().numpy()
            errors.append(deg)
            far_flags.append((distance[keep] >= FAR_STEPS).numpy())
            n = int(keep.sum())
            loss_sum += loss.item() * n
            count += n
            window_err += float(deg.sum())
            window_n += n
            bar.set_postfix(loss=f"{loss.item():.3f}", deg=f"{deg.mean():.1f}")
            if args.print_every > 0 and i % args.print_every == 0:
                print(
                    f"(epoch {epoch}) (batch {i}/{num_batches - 1}) {stage} loss {loss.item():.4f}  "
                    f"mean bearing error {window_err / window_n:.1f} deg"
                )
                window_err, window_n = 0.0, 0
    errors = np.concatenate(errors)
    far = np.concatenate(far_flags)
    return {
        "stage": stage,
        "train_loss": loss_sum / max(count, 1),
        "train_median_deg": float(np.median(errors)),
        "train_far_median_deg": float(np.median(errors[far])),
        "train_samples": count,
    }


def main():
    parser = argparse.ArgumentParser(description="Train D-ft (goal direction on a private encoder copy)")
    parser.add_argument("--config", "-c", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--unfreeze", choices=("goal", "all"), default="goal")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--warmup-epochs", type=int, default=2)
    parser.add_argument("--lr-encoder", type=float, default=2e-5)
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--weight", choices=("distance", "none"), default="distance")
    parser.add_argument("--min-goal-m", type=float, default=0.3)
    parser.add_argument("--val-fraction", type=float, default=0.08)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--print-every", type=int, default=200)
    parser.add_argument("--max-batches", type=int, default=0, help="Per-epoch cap for smoke tests")
    parser.add_argument("--max-val-batches", type=int, default=0, help="Validation cap for smoke tests")
    parser.add_argument("--run-name", default="nomad_dft")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    if args.warmup_epochs > args.epochs:
        raise ValueError("--warmup-epochs cannot exceed --epochs")
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    cudnn.benchmark = True
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    output_dir = args.output_dir or os.path.join(
        "logs", "nomad_d", f"{args.run_name}_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    )
    os.makedirs(output_dir, exist_ok=True)
    print(f"device: {device}\noutput: {os.path.abspath(output_dir)}")

    config = load_config(args.config)
    train_dataset = make_split_dataset(config, "train")
    val_dataset = make_split_dataset(config, "train")
    val_trajs = split_trajectories(train_dataset.traj_names, args.val_fraction, args.seed)
    with open(os.path.join(output_dir, "val_trajectories.txt"), "w") as f:
        f.write("\n".join(sorted(val_trajs)) + "\n")
    restrict(train_dataset, val_trajs, keep_inside=False)
    restrict(val_dataset, val_trajs, keep_inside=True)
    meters = meters_per_unit(train_dataset)
    print(
        f"trajectories: {len(train_dataset.traj_names) - len(val_trajs)} train, {len(val_trajs)} val | "
        f"samples: {len(train_dataset)} train, {len(val_dataset)} val"
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        persistent_workers=args.num_workers > 0,
    )
    val_workers = min(2, args.num_workers)
    if args.max_val_batches > 0:
        val_dataset.index_to_data = val_dataset.index_to_data[: args.max_val_batches * args.batch_size]
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=val_workers,
        worker_init_fn=seed_val_worker,
        persistent_workers=False,
    )

    encoder = build_d_encoder(config, args.checkpoint_b, device, args.unfreeze)
    head = GoalDirectionHead(config["encoding_size"]).to(device)
    encoder_params = [p for p in encoder.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        [
            {"params": encoder_params, "lr": args.lr_encoder},
            {"params": head.parameters(), "lr": args.lr_head},
        ],
        weight_decay=args.weight_decay,
    )
    print(
        f"Trainable: encoder {sum(p.numel() for p in encoder_params) / 1e6:.2f}M ({args.unfreeze}), "
        f"head {sum(p.numel() for p in head.parameters())}"
    )
    print(
        f"Schedule: {args.warmup_epochs} epochs of 1-cos, then von Mises NLL to epoch {args.epochs - 1}. "
        f"lr encoder {args.lr_encoder}, head {args.lr_head}. weight {args.weight}, min goal {args.min_goal_m} m"
    )

    log_rows = []
    best = math.inf
    log_path = os.path.join(output_dir, "train_log.csv")
    for epoch in range(args.epochs):
        start = time.time()
        train_stats = train_one_epoch(encoder, head, optimizer, train_loader, device, meters, args, epoch)
        val_stats = validate(encoder, head, val_loader, device, meters, args.min_goal_m, args.weight)
        state = {
            "epoch": epoch,
            "vision_encoder": encoder.state_dict(),
            "head": head.state_dict(),
            "args": vars(args),
            **val_stats,
        }
        torch.save(state, os.path.join(output_dir, f"goal_dir_{epoch}.pth"))
        selected = val_stats["val_far_median_deg"] < best
        if selected:
            best = val_stats["val_far_median_deg"]
            torch.save(state, os.path.join(output_dir, "goal_dir_best.pth"))
        row = {"epoch": epoch, **train_stats, **val_stats, "best": selected, "minutes": (time.time() - start) / 60}
        log_rows.append(row)
        with open(log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerows(log_rows)
        print(
            f"[epoch {epoch} {train_stats['stage']}] bearing median train {train_stats['train_median_deg']:.1f} "
            f"/ val {val_stats['val_median_deg']:.1f} deg | far train {train_stats['train_far_median_deg']:.1f} "
            f"/ val {val_stats['val_far_median_deg']:.1f} deg | val NLL {val_stats['val_vm_nll']:.3f}"
            f"{' | best' if selected else ''} | {row['minutes']:.1f} min"
        )
    print(f"Best epoch by val far median bearing: {best:.1f} deg -> goal_dir_best.pth")
    print(f"Training log: {os.path.abspath(log_path)}")


if __name__ == "__main__":
    main()

"""Train the goal-position head D on frozen baseline B (Epoch 29 EMA).

B stays fixed: vision encoder, diffusion UNet and distance head are loaded
from ema_29.pth with requires_grad False. Only GoalPosHead is trained.

Loss uses valid samples only: action_mask == 1, which already drops negative
goals and distances outside the action range. The goal is never masked here,
because a frozen encoder gives a masked sample no goal information to learn
from. Targets are goal_pos in meters (dataset units times 0.12 m).

The first --mse-epochs use squared error on mu only. The rest use a Gaussian
NLL on mu and sigma.

Run from train/:

    python -u train_goal_head.py
"""

import argparse
import csv
import os
import time

import numpy as np
import torch
import torch.backends.cudnn as cudnn
from torch.utils.data import DataLoader
from tqdm import tqdm

from eval_by_distance import load_config
from eval_goal_head import (
    B_CHECKPOINT,
    PairedEvaluator,
    encode,
    load_frozen_nomad,
    make_split_dataset,
    meters_per_unit,
    normalize_images,
)
from eval_frame_sets import NOISE_CURVE, PAIRED_FRAMES, SPREAD_NPZ
from vint_train.models.nomad.nomad import GoalPosHead


def position_loss(mu, sigma, target, use_nll):
    if not use_nll:
        return ((mu - target) ** 2).sum(dim=-1).mean()
    return (0.5 * ((target - mu) / sigma) ** 2 + torch.log(sigma)).sum(dim=-1).mean()


def train_one_epoch(model, head, optimizer, loader, device, meters, use_nll, epoch, print_every, max_batches):
    head.train()
    totals = {"loss": 0.0, "err": 0.0, "sigma": 0.0, "n": 0}
    window = {"loss": 0.0, "err": 0.0, "n": 0}
    num_batches = len(loader) if max_batches <= 0 else min(len(loader), max_batches)
    stage = "nll" if use_nll else "mse"
    with tqdm(loader, total=num_batches, desc=f"D epoch {epoch} ({stage})", leave=False) as bar:
        for i, (obs_image, goal_image, _actions, _distance, goal_pos, _dataset_idx, action_mask) in enumerate(bar):
            if i >= num_batches:
                break
            keep = action_mask.bool()
            if not keep.any():
                continue
            batch_obs, batch_goal = normalize_images(obs_image[keep], goal_image[keep], device)
            target = goal_pos[keep].float().to(device) * meters
            with torch.no_grad():
                cond = encode(model, batch_obs, batch_goal)
            mu, sigma = head(cond)
            loss = position_loss(mu, sigma, target, use_nll)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            n = int(keep.sum())
            err = torch.linalg.norm(mu.detach() - target, dim=-1).sum().item()
            totals["loss"] += loss.item() * n
            totals["err"] += err
            totals["sigma"] += torch.linalg.norm(sigma.detach(), dim=-1).sum().item()
            totals["n"] += n
            window["loss"] += loss.item() * n
            window["err"] += err
            window["n"] += n
            bar.set_postfix(loss=f"{loss.item():.3f}", err_m=f"{err / n:.3f}")
            if print_every > 0 and i % print_every == 0:
                print(
                    f"(epoch {epoch}) (batch {i}/{num_batches - 1}) {stage} "
                    f"loss {window['loss'] / window['n']:.4f}  mean error {window['err'] / window['n']:.3f} m"
                )
                window = {"loss": 0.0, "err": 0.0, "n": 0}
    n = max(totals["n"], 1)
    return {
        "train_loss": totals["loss"] / n,
        "train_err_m": totals["err"] / n,
        "train_sigma_norm_m": totals["sigma"] / n,
        "train_samples": totals["n"],
    }


def main():
    parser = argparse.ArgumentParser(description="Train goal-position head D on frozen B")
    parser.add_argument("--config", "-c", default="config/nomad_b40.yaml")
    parser.add_argument("--checkpoint-b", default=B_CHECKPOINT)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--mse-epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--print-every", type=int, default=200)
    parser.add_argument("--max-batches", type=int, default=0, help="Per-epoch cap for smoke tests. 0 runs the full epoch")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--noise-curve", default=NOISE_CURVE)
    parser.add_argument("--run-name", default="nomad_d")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    if args.mse_epochs > args.epochs:
        raise ValueError("--mse-epochs cannot exceed --epochs")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    cudnn.benchmark = True
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    output_dir = args.output_dir or os.path.join(
        "logs", "nomad_d", f"{args.run_name}_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    )
    os.makedirs(output_dir, exist_ok=True)
    print(f"device: {device}")
    print(f"output: {os.path.abspath(output_dir)}")

    config = load_config(args.config)
    train_dataset = make_split_dataset(config, "train")
    test_dataset = make_split_dataset(config, "test")
    meters = meters_per_unit(train_dataset)
    print(f"train samples {len(train_dataset)}  meters per unit {meters}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
        persistent_workers=args.num_workers > 0,
    )

    model = load_frozen_nomad(config, args.checkpoint_b, device)
    head = GoalPosHead(config["encoding_size"]).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    print(f"Trainable parameters: {sum(p.numel() for p in head.parameters())} (head only)")
    print(
        f"Schedule: {args.mse_epochs} MSE epochs, then {args.epochs - args.mse_epochs} Gaussian NLL epochs. "
        f"lr {args.lr}"
    )

    evaluator = PairedEvaluator(test_dataset, args.frames, args.spread, args.noise_curve)
    log_path = os.path.join(output_dir, "train_log.csv")
    log_rows = []

    for epoch in range(args.epochs):
        use_nll = epoch >= args.mse_epochs
        start = time.time()
        stats = train_one_epoch(
            model, head, optimizer, train_loader, device, meters, use_nll, epoch, args.print_every, args.max_batches
        )
        torch.save(head.state_dict(), os.path.join(output_dir, f"goal_head_{epoch}.pth"))
        torch.save(head.state_dict(), os.path.join(output_dir, "goal_head_latest.pth"))
        rows, _calib, _pred = evaluator.run(
            model, head, device, args.eval_batch_size,
            output_dir=os.path.join(output_dir, f"eval_epoch{epoch}"),
            verbose=False,
        )
        by_key = {(row["group"], row["frames"]): row for row in rows}
        far = by_key[("20-40", "all")]
        log_row = {
            "epoch": epoch,
            "stage": "nll" if use_nll else "mse",
            **stats,
            "near_err_m": by_key[("4-8", "all")]["err_mean"],
            "mid_err_m": by_key[("9-19", "all")]["err_mean"],
            "far_err_m": far["err_mean"],
            "far_sigma_norm_m": far["sigma_norm_mean"],
            "far_spearman": far["spearman_sigma_err"],
            "far_coverage_1sigma": far["coverage_1sigma"],
            "far_oracle_use_kept_m": far.get("oracle_use_at_this_error", float("nan")),
            "minutes": (time.time() - start) / 60.0,
        }
        log_rows.append(log_row)
        with open(log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(log_row.keys()))
            writer.writeheader()
            writer.writerows(log_rows)
        print(
            f"[epoch {epoch} {log_row['stage']}] train error {stats['train_err_m']:.3f} m | paired error "
            f"near {log_row['near_err_m']:.3f}  mid {log_row['mid_err_m']:.3f}  far {log_row['far_err_m']:.3f} m | "
            f"far sigma {log_row['far_sigma_norm_m']:.3f}  rho {log_row['far_spearman']:.2f}  "
            f"cov {log_row['far_coverage_1sigma']:.2f} | {log_row['minutes']:.1f} min"
        )

    print(f"\nFinal head (epoch {args.epochs - 1}), fixed in advance:")
    evaluator.run(model, head, device, args.eval_batch_size, output_dir=os.path.join(output_dir, "eval_final"))
    print(f"Training log: {os.path.abspath(log_path)}")


if __name__ == "__main__":
    main()

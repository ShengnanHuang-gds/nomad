"""Train only distance- or direction-correction MLP on frozen pathact8 (SmoothL1 path loss).

Does not modify train_goal_dino.py. Select checkpoint by val far path ADE (mean cm).
"""
from __future__ import annotations

import cv2  # noqa: F401
import argparse
import hashlib
import json
import math
import os
import time

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config
from train_goal_dino import go_stanford_meters_per_unit
from path_correction_ab import FrozenPathAct8WithCorrection, count_trainable
from train_goal_dino import (
    DFT_VAL_LIST,
    CACHE_DIR,
    _parse_batch,
    build_pairs,
    draw,
    load_cache,
    load_head_checkpoint,
    loader,
)
from train_goal_dir import FAR_STEPS
from vint_train.models.nomad.pair_token_head import PairTokenHead

DEFAULT_INIT = (
    "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_model(init_path: str, mode: str, device: torch.device) -> FrozenPathAct8WithCorrection:
    ckpt = torch.load(init_path, map_location="cpu", weights_only=False)
    args = ckpt.get("args", {})
    _, _, cache_meta = load_cache(CACHE_DIR, "train")
    base = PairTokenHead(
        cache_meta["dim"],
        cache_meta["tokens"],
        int(args.get("width", 256)),
        int(args.get("layers", 4)),
        int(args.get("heads", 8)),
        float(args.get("dropout", 0.1)),
        int(args.get("context", 2)),
        n_sectors=0,
        path_steps=int(args.get("path_steps", 8)),
        path_mlp=int(args.get("path_mlp", 0)),
        path_residual=int(args.get("path_residual", 0)),
        path_spatial=str(args.get("path_spatial", "") or ""),
        odom_dim=int(args.get("odom_dim", 0)),
        path_rot=bool(args.get("path_rot", False)),
    )
    load_head_checkpoint(base, ckpt["head"])
    return FrozenPathAct8WithCorrection(base, mode).to(device)


def path_metrics(pred: torch.Tensor, tgt: torch.Tensor, meters: float, turn_strict, loose_turn):
    """pred/tgt [B,K,2] dataset units."""
    err_m = pred.sub(tgt).norm(dim=-1) * meters
    ade = err_m.mean(dim=-1)
    back4 = err_m[:, -4:].mean(dim=-1) if err_m.shape[1] >= 4 else ade
    rp = pred.norm(dim=-1) * meters
    rt = tgt.norm(dim=-1) * meters
    dist_err = (rp - rt).abs().mean(dim=-1)
    ok = (rp > 1e-6) & (rt > 1e-6)
    cos = (pred * tgt).sum(-1) / (pred.norm(dim=-1) * tgt.norm(dim=-1)).clamp(min=1e-12)
    ang = torch.rad2deg(torch.acos(cos.clamp(-1, 1)))
    ang_err = torch.where(ok, ang, torch.zeros_like(ang))
    ang_err = ang_err.sum(dim=-1) / ok.sum(dim=-1).clamp(min=1).float()

    def bucket(name, mask):
        if mask is None or not mask.any():
            return {}
        m = mask.bool()
        return {f"{name}_ade_cm": float(ade[m].mean() * 100.0)}

    st = turn_strict > 0.5 if turn_strict is not None else torch.zeros(len(ade), dtype=torch.bool, device=ade.device)
    lo = loose_turn > 0.5 if loose_turn is not None else torch.ones(len(ade), dtype=torch.bool, device=ade.device)
    mid = lo & ~st
    straight = ~lo
    out = {
        "path_ade_cm": float(ade.mean() * 100.0),
        "path_back4_cm": float(back4.mean() * 100.0),
        "path_dist_err_m": float(dist_err.mean()),
        "path_ang_err_deg": float(ang_err.mean()),
    }
    out.update(bucket("strict_turn", st))
    out.update(bucket("strict_straight", straight))
    out.update(bucket("middle", mid))
    return ade, out


def run_epoch(model, batches, device, meters, optimizer=None, scheduler=None, desc=""):
    training = optimizer is not None
    model.train(training)
    loss_sum, count = 0.0, 0
    ades, f_ades = [], []
    with torch.set_grad_enabled(training):
        for batch in tqdm(batches, desc=desc, leave=False):
            (
                curr,
                goal,
                _target,
                steps,
                ctx,
                _w,
                turn_strict_t,
                _ta,
                _av,
                _ty,
                target_path,
                odom_t,
            ) = _parse_batch(batch, device)
            if target_path is None:
                continue
            weight = steps.float() / FAR_STEPS
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p_corr, p_base, _raw = model(curr, goal, ctx, odom_t)
            p_corr = p_corr.float()
            tgt = target_path.float()
            path_l1 = torch.nn.functional.smooth_l1_loss(p_corr, tgt, beta=1.0, reduction="none").mean(
                dim=(1, 2)
            )
            loss = (path_l1 * weight).mean()
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.correction.parameters(), 1.0)
                optimizer.step()
                if scheduler is not None:
                    scheduler.step()
            loss_sum += float(loss.item()) * len(path_l1)
            count += len(path_l1)
            ade, _m = path_metrics(p_corr, tgt, meters, turn_strict_t, None)
            ades.append(ade.detach().cpu().numpy())
            f_ades.append((steps >= FAR_STEPS).cpu().numpy())
    ades = np.concatenate(ades) if ades else np.array([])
    far = np.concatenate(f_ades).astype(bool) if f_ades else np.array([], dtype=bool)
    metrics = {
        "loss": loss_sum / max(count, 1),
        "path_ade_cm": float(ades.mean() * 100.0) if ades.size else float("nan"),
        "far_path_ade_cm": float(ades[far].mean() * 100.0) if far.any() else float(ades.mean() * 100.0),
    }
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--correction-mode", choices=("dist", "dir"), required=True)
    ap.add_argument("--init", default=DEFAULT_INIT)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--config", default="config/nomad_b40.yaml")
    ap.add_argument("--cache-dir", default=CACHE_DIR)
    ap.add_argument("--val-list", default=DFT_VAL_LIST)
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--path-steps", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-batches", type=int, default=0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=0.05)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--no-flip", action="store_true")
    ap.add_argument("--min-goal-m", type=float, default=0.3)
    ap.add_argument("--output-dir", default="")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    output_dir = args.output_dir or os.path.join(
        "logs", "nomad_d", f"{args.run_name}_{time.strftime('%Y_%m_%d_%H_%M_%S')}"
    )
    os.makedirs(output_dir, exist_ok=True)

    config = load_config(args.config)
    meters = go_stanford_meters_per_unit(config)
    cache_path, rows, meta = load_cache(args.cache_dir, "train")
    flip = meta["flip"] and not args.no_flip
    with open(args.val_list) as f:
        val_trajs = {line.strip() for line in f if line.strip()}

    train_pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t not in val_trajs,
        args.min_goal_m,
        args.context,
        "endpoint",
        (),
        False,
        None,
        0,
        args.path_steps,
        0,
    )
    val_pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t in val_trajs,
        args.min_goal_m,
        args.context,
        "endpoint",
        (),
        False,
        None,
        0,
        args.path_steps,
        0,
    )
    train_chosen = draw(train_pairs, np.random.default_rng(args.seed))
    val_chosen = draw(val_pairs, np.random.default_rng(1234))
    steps_per_epoch = math.ceil(len(train_pairs["starts"]) / args.batch_size)
    if args.max_batches > 0:
        steps_per_epoch = min(steps_per_epoch, args.max_batches)

    model = build_model(args.init, args.correction_mode, device)
    n_trainable = count_trainable(model)
    total_updates = steps_per_epoch * args.epochs

    print(
        f"correction={args.correction_mode} | train frames={len(train_pairs['starts'])} "
        f"| batches/ep={steps_per_epoch} | updates={total_updates} | trainable={n_trainable}"
    )

    optimizer = torch.optim.AdamW(model.correction.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    sched_epochs = args.epochs
    total = steps_per_epoch * sched_epochs
    warm = steps_per_epoch
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda s: (s + 1) / warm if s < warm else 0.5 * (1.0 + math.cos(math.pi * (s - warm) / max(1, total - warm))),
    )

    meta_out = {
        "correction_mode": args.correction_mode,
        "init": args.init,
        "init_sha256": sha256_file(args.init) if os.path.isfile(args.init) else None,
        "train_frames": len(train_pairs["starts"]),
        "batches_per_epoch": steps_per_epoch,
        "total_updates": total_updates,
        "trainable_params": n_trainable,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "seed": args.seed,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "loss": "smooth_l1 path 8pts beta=1.0 dataset units, weight=steps/FAR_STEPS",
        "select_metric": "far_path_ade_cm",
        "frozen": "PairTokenHead entire base (encoder, out, path_head); DINO cache read-only",
    }
    with open(os.path.join(output_dir, "train_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_out, f, indent=2)

    best_score = float("inf")
    best_path = os.path.join(output_dir, "dino_dir_best.pth")
    for ep in range(args.epochs):
        tr_batches = loader(
            cache_path, train_pairs, train_chosen, args.batch_size, flip, args.seed + ep, args.workers, args.context
        )
        if args.max_batches > 0:
            tr_batches = list(tr_batches)[: args.max_batches]
        tr = run_epoch(model, tr_batches, device, meters, optimizer, scheduler, desc=f"train ep{ep}")
        va_batches = loader(cache_path, val_pairs, val_chosen, 512, False, 0, args.workers, args.context)
        va = run_epoch(model, va_batches, device, meters, None, None, desc=f"val ep{ep}")
        score = va["far_path_ade_cm"]
        print(
            f"ep {ep} train loss {tr['loss']:.4f} | val path {va['path_ade_cm']:.2f} "
            f"far {score:.2f} cm"
        )
        with open(os.path.join(output_dir, "val_metrics.jsonl"), "a", encoding="utf-8") as vlf:
            vlf.write(json.dumps({"epoch": ep, "train": tr, "val": va}) + "\n")
        st = {
            "epoch": ep,
            "correction": model.correction.state_dict(),
            "correction_mode": args.correction_mode,
            "base_init": args.init,
            "val": va,
            "train": tr,
        }
        torch.save(st, os.path.join(output_dir, f"correction_ep{ep}.pth"))
        if score < best_score:
            best_score = score
            torch.save(st, best_path)

    print(f"best far path ADE {best_score:.2f} cm -> {best_path}")


if __name__ == "__main__":
    main()

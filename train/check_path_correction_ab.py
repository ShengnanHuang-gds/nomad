"""Math/freeze checks for path distance vs direction correction (no training)."""
from __future__ import annotations

import cv2  # noqa: F401
import argparse
import json
import os
import sys

import numpy as np
import torch

from eval_by_distance import load_config
from train_goal_dino import go_stanford_meters_per_unit
from path_correction_ab import (
    NEAR_ZERO_M,
    FrozenPathAct8WithCorrection,
    apply_direction_correction,
    apply_distance_correction,
    count_trainable,
    radius_ratio_error,
)
from train_goal_dino import _parse_batch, build_pairs, draw, load_cache, load_head_checkpoint, loader
from vint_train.models.nomad.pair_token_head import PairTokenHead

DEFAULT_INIT = (
    "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
)
DEFAULT_VAL_LIST = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/val_trajectories.txt"
CACHE_DIR = "logs/dino_cache/dinov2_vits14_reg"


def load_wrapper(init_path: str, mode: str, device: torch.device) -> FrozenPathAct8WithCorrection:
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
        path_steps=8,
        path_mlp=int(args.get("path_mlp", 0)),
        path_residual=int(args.get("path_residual", 0)),
        path_spatial=str(args.get("path_spatial", "") or ""),
        odom_dim=int(args.get("odom_dim", 0)),
        path_rot=bool(args.get("path_rot", False)),
    )
    load_head_checkpoint(base, ckpt["head"])
    model = FrozenPathAct8WithCorrection(base, mode).to(device)
    return model


def one_batch(device: torch.device, batch_size: int = 32, seed: int = 0):
    config = load_config("config/nomad_b40.yaml")
    cache_path, rows, meta = load_cache(CACHE_DIR, "train")
    with open(DEFAULT_VAL_LIST) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t not in val_trajs,
        0.0,
        2,
        "endpoint",
        (),
        False,
        None,
        0,
        8,
        0,
    )
    chosen = draw(pairs, np.random.default_rng(seed))
    batches = loader(cache_path, pairs, chosen, batch_size, meta["flip"], seed, 0, 2)
    batch = next(iter(batches))
    curr, goal, _target, _steps, ctx, *_rest = _parse_batch(batch, device)
    return curr, goal, ctx


def run_checks(init_path: str, device: torch.device, batch_size: int = 32) -> dict:
    report = {"ok": True, "checks": []}

    def add(name: str, ok: bool, detail: str):
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["ok"] = False

    meters = go_stanford_meters_per_unit(load_config("config/nomad_b40.yaml"))
    eps_u = NEAR_ZERO_M / meters

    for mode in ("dist", "dir"):
        model = load_wrapper(init_path, mode, device)
        n_corr = count_trainable(model)
        n_base_trainable = sum(p.numel() for p in model.base.parameters() if p.requires_grad)
        add(f"{mode}_trainable_only_correction", n_base_trainable == 0 and n_corr > 0, f"corr_params={n_corr}")

        model.train(True)
        add(f"{mode}_base_stays_eval", not model.base.training, f"base.training={model.base.training}")

        curr, goal, ctx = one_batch(device, batch_size=batch_size)
        p_corr, p_base, raw = model(curr, goal, ctx)
        max_zero = (p_corr - p_base).abs().max().item()
        add(f"{mode}_zero_init_matches_base", max_zero < 1e-6, f"max|Δ|={max_zero:.3e}")

        if mode == "dist":
            # direction preserved: cross product ~ 0
            cross = (p_base[..., 0] * p_corr[..., 1] - p_base[..., 1] * p_corr[..., 0]).abs()
            norm = (p_base.norm(dim=-1) * p_corr.norm(dim=-1)).clamp(min=1e-12)
            sin_err = (cross / norm).max().item()
            add(f"{mode}_direction_preserved", sin_err < 1e-5, f"max|sin|={sin_err:.3e}")
            r_err = radius_ratio_error(p_corr, p_base, NEAR_ZERO_M, meters)
            add(f"{mode}_radius_may_change", True, f"median radius err m={float(torch.nanmedian(r_err)):.4f}")
        else:
            dr = (p_corr.norm(dim=-1) - p_base.norm(dim=-1)).abs().max().item()
            add(f"{mode}_radius_preserved", dr < 1e-5, f"max|r_diff| units={dr:.3e}")
            raw2 = torch.randn_like(raw) * 0.1
            p2 = apply_direction_correction(p_base, raw2)
            ang_chg = (p_base * p2).sum(-1) / (p_base.norm(dim=-1) * p2.norm(dim=-1)).clamp(min=1e-12)
            add(f"{mode}_nonzero_rot_changes_heading", float(ang_chg.min()) < 0.999, "sanity rot")

        near = (p_base.norm(dim=-1) * meters) < NEAR_ZERO_M
        add(f"{mode}_near_origin_points", True, f"count={int(near.sum())}/{near.numel()} (report only)")

        tgt = torch.randn_like(p_base)
        loss = torch.nn.functional.smooth_l1_loss(p_corr, tgt, beta=1.0)
        model.zero_grad(set_to_none=True)
        loss.backward()
        base_grad = sum(float(p.grad.abs().sum()) for p in model.base.parameters() if p.grad is not None)
        corr_grad = sum(float(p.grad.abs().sum()) for p in model.correction.parameters() if p.grad is not None)
        add(f"{mode}_grad_only_correction", base_grad == 0.0 and corr_grad > 0, f"base_grad={base_grad} corr_grad={corr_grad:.3e}")

        # exp finite on random logits
        if mode == "dist":
            big = torch.full((4, 8), 20.0, device=device)
            ex = torch.exp(big)
            finite = torch.isfinite(ex).all().item()
            add(f"{mode}_exp_finite_at_s20", finite, f"exp(20)={ex.max().item():.3e}")

    dist_m = load_wrapper(init_path, "dist", device)
    dir_m = load_wrapper(init_path, "dir", device)
    add("same_corr_arch_params", count_trainable(dist_m) == count_trainable(dir_m), f"n={count_trainable(dist_m)}")

    feat_dim = dist_m.correction.net[0].in_features
    add(
        "feature_path_head_input_dim",
        feat_dim == 256,
        f"path_head input D={feat_dim} (pathact8: CLS feat 256-d, see PairTokenHead._path_feat)",
    )

    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", default=DEFAULT_INIT)
    ap.add_argument("--out", default="")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if not os.path.isfile(args.init):
        print(f"MISSING init {args.init}", file=sys.stderr)
        sys.exit(1)
    report = run_checks(args.init, device, args.batch_size)
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()

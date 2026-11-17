#!/usr/bin/env python3
"""Train an additional image-only heading output on local CUDA, without navigation."""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image

from csv_log import CsvLog
from visual_stage_data import TRAIN_ROUTES, VALID_ROUTES, VisualStageData, extract_verified_handoff
from visual_yaw_data import yaw_pairs, pair_weights, yaw_metrics

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--steps-per-epoch", type=int, default=32)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=5e-5)
    args = p.parse_args()
    if min(args.epochs, args.steps_per_epoch, args.batch_size) < 1 or not math.isfinite(args.lr) or args.lr <= 0:
        p.error("positive training counts and finite positive lr required")
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        p.error("output directory must be new or empty")

    import torch
    import nomad_navigate_ros2 as runtime
    from visual_yaw import VisualYaw
    if not torch.cuda.is_available():
        p.error("CUDA is required; CPU training is disabled")
    device = torch.device("cuda")
    base_checkpoint = ROOT / "gazebo_sim/visual_stage_clean/best.pth"
    base_config = ROOT / "gazebo_sim/visual_stage_clean/model.yaml"
    expected = json.loads((ROOT / "gazebo_sim/visual_audit_clean_gpu/manifest.json").read_text())["checkpoint_sha256"]
    base_hash = hashlib.sha256(base_checkpoint.read_bytes()).hexdigest()
    if base_hash != expected:
        p.error("base XY checkpoint is not the fixed epoch-6 model")
    out.mkdir(parents=True, exist_ok=True)
    archive = extract_verified_handoff(ROOT / "gazebo_sim/training_handoff", out / "handoff")
    data = VisualStageData(out / "handoff/dataset")
    train_pairs = yaw_pairs(data, TRAIN_ROUTES)
    valid_pairs = yaw_pairs(data, VALID_ROUTES)
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    mp = runtime.load_train_config(base_config)
    base = runtime.load_model(str(base_checkpoint), mp, device)
    state = torch.load(base_checkpoint, map_location="cpu", weights_only=True)
    base.load_state_dict(state, strict=True)
    del state
    model = VisualYaw.from_nomad(base).to(device)
    del base  # Only the copied image-pair encoder and new head are trained.
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    images = {}
    for route, values in data.routes.items():
        images[route] = []
        for path in values["paths"]:
            with Image.open(path) as pil:
                images[route].append(runtime.transform_images(pil.convert("RGB"), mp["image_size"], center_crop=False).squeeze(0))

    def batch(pairs):
        a = torch.stack([images[r][i] for r, i, _, _ in pairs]).to(device)
        b = torch.stack([images[r][j] for r, _, j, _ in pairs]).to(device)
        angles = torch.tensor([angle for _, _, _, angle in pairs], dtype=torch.float32, device=device)
        return a, b, angles

    def evaluate():
        model.eval()
        predictions, targets = [], []
        with torch.inference_mode():
            for start in range(0, len(valid_pairs), 32):
                a, b, target = batch(valid_pairs[start:start+32])
                output = model(a, b)
                predictions.extend(torch.atan2(output[:, 1], output[:, 0]).cpu().tolist())
                targets.extend(target.cpu().tolist())
        return yaw_metrics(predictions, targets)

    config = {**vars(args), "kind": "image_pair_yaw_v1", "base_config": str(base_config),
              "base_checkpoint": str(base_checkpoint), "base_checkpoint_sha256": base_hash,
              "train_routes": list(TRAIN_ROUTES), "validation_routes": list(VALID_ROUTES),
              "train_pairs": len(train_pairs), "validation_pairs": len(valid_pairs),
              "max_pair_frame_gap": 20, "seed": 42, "input": "current RGB and goal RGB only",
              "output": "cos/sin of relative heading", "angle_supervision": "wrapped goal yaw minus current yaw",
              "loss": "MSE(raw_vector, target_cos_sin) + 0.25 * circular_cosine_loss",
              "xy_checkpoint_modified": False, "scheduler_steps_per_epoch": 1,
              "validation_gate": "MAE<=10deg; p90<=20deg; large-turn sign accuracy>=0.95",
              "gate_note": "engineering screening on route05, not a closed-loop safety or success guarantee",
              "handoff_sha256": archive["archive"]["sha256"], "torch": torch.__version__}
    (out / "head_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    log, steps = CsvLog(out / "metrics.csv"), CsvLog(out / "steps.csv")
    best, best_gate, updates = float("inf"), False, 0
    started = time.monotonic()

    def assess(epoch, loss=None):
        nonlocal best, best_gate
        metrics = evaluate()
        if not all(math.isfinite(metrics[k]) for k in ("mae_deg", "p90_deg", "selection_score")):
            raise FloatingPointError("nonfinite heading validation result")
        log.write({"epoch": epoch, "updates": updates, "train_loss": loss,
                   "next_lr": optimizer.param_groups[0]["lr"], **metrics})
        passed = metrics["validation_gate_passed"]
        if (passed and not best_gate) or (passed == best_gate and metrics["selection_score"] < best):
            best = metrics["selection_score"]
            best_gate = passed
            torch.save(model.state_dict(), out / "best.tmp")
            (out / "best.tmp").replace(out / "best_yaw.pth")
            (out / "best.json").write_text(json.dumps({"epoch": epoch, "updates": updates,
                "checkpoint_sha256": hashlib.sha256((out / "best_yaw.pth").read_bytes()).hexdigest(),
                "checkpoint_bytes": (out / "best_yaw.pth").stat().st_size,
                "selected_on": "house_run_05", **metrics}, indent=2), encoding="utf-8")
        print(f"epoch={epoch} updates={updates} validation={metrics} elapsed={time.monotonic()-started:.1f}s", flush=True)

    probabilities = pair_weights(train_pairs)
    try:
        assess(-1)
        for epoch in range(args.epochs):
            model.train()
            losses = []
            for _ in range(args.steps_per_epoch):
                choices = rng.choice(len(train_pairs), size=args.batch_size, p=probabilities)
                a, b, angle = batch([train_pairs[int(i)] for i in choices])
                unit, raw = model(a, b, return_raw=True)
                target = torch.stack([torch.cos(angle), torch.sin(angle)], dim=1)
                loss = (raw-target).square().mean()+0.25*(1-(unit*target).sum(dim=1)).mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite heading loss")
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                updates += 1
                losses.append(float(loss.detach()))
                steps.write({"epoch": epoch, "update": updates,
                             "lr": optimizer.param_groups[0]["lr"], "loss": losses[-1]})
            scheduler.step()
            (out / "scheduler_state.json").write_text(json.dumps(scheduler.state_dict(), indent=2), encoding="utf-8")
            assess(epoch, float(np.mean(losses)))
    finally:
        log.close()
        steps.close()
    if hashlib.sha256(base_checkpoint.read_bytes()).hexdigest() != base_hash:
        raise RuntimeError("base XY checkpoint changed during heading training")
    print(f"Heading training complete: {out}; inspect best.json before any held-out test or navigation.")


if __name__ == "__main__":
    main()

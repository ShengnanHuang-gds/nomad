#!/usr/bin/env python3
"""Fixed visual-yaw module test on house_06 images, without ROS nodes or motion."""

import argparse
import csv
import hashlib
import json
import math
import pickle
from pathlib import Path

from PIL import Image

from audit_visual_model import CASES
from visual_yaw_data import yaw_metrics

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--head-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    folder, out = Path(args.head_dir).resolve(), Path(args.out).resolve()
    config = json.loads((folder / "head_config.json").read_text())
    best = json.loads((folder / "best.json").read_text())
    if not best["validation_gate_passed"] or best["epoch"] < 0:
        p.error("heading module has not passed the predeclared route05 validation gate; stop before held-out testing")
    if config.get("kind") != "image_pair_yaw_v1":
        p.error("unsupported heading model kind")
    if out.exists() and any(out.iterdir()):
        p.error("output directory must be new or empty")
    import torch
    import nomad_navigate_ros2 as runtime
    from visual_yaw import VisualYaw
    if not torch.cuda.is_available():
        p.error("CUDA required; no automatic CPU fallback")
    device = torch.device("cuda")
    checkpoint = Path(config["base_checkpoint"])
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != config["base_checkpoint_sha256"]:
        p.error("base checkpoint identity mismatch")
    mp = runtime.load_train_config(Path(config["base_config"]))
    base = runtime.load_model(str(checkpoint), mp, device)
    model = VisualYaw.from_nomad(base).to(device)
    head_path = folder / "best_yaw.pth"
    if hashlib.sha256(head_path.read_bytes()).hexdigest() != best["checkpoint_sha256"]:
        p.error("heading checkpoint does not match its selected validation record")
    model.load_state_dict(torch.load(head_path, map_location="cpu", weights_only=True), strict=True)
    model.eval()
    del base
    data_dir = ROOT / "gazebo_sim/house_run_06"
    with (data_dir / "traj_data.pkl").open("rb") as f:
        poses = pickle.load(f)
    images = []
    for i in range(len(poses["yaw"])):
        with Image.open(data_dir / f"{i}.jpg") as pil:
            images.append(runtime.transform_images(pil.convert("RGB"), mp["image_size"], center_crop=False).squeeze(0))
    out.mkdir(parents=True, exist_ok=True)
    rows, prediction, truth = [], [], []
    with torch.inference_mode():
        for obs in sorted({i for i, _ in CASES}):
            current = torch.stack([images[obs]]*len(images)).to(device)
            goal = torch.stack(images).to(device)
            # Batch to avoid unnecessarily large GPU allocations.
            outputs = torch.cat([model(current[i:i+16], goal[i:i+16]) for i in range(0, len(images), 16)])
            if not torch.isfinite(outputs).all():
                raise FloatingPointError("Nonfinite heading prediction in held-out test")
            angles = torch.atan2(outputs[:, 1], outputs[:, 0]).cpu().tolist()
            for g, pred in enumerate(angles):
                target = (float(poses["yaw"][g]-poses["yaw"][obs])+math.pi) % (2*math.pi)-math.pi
                error = (pred-target+math.pi) % (2*math.pi)-math.pi
                rows.append({"obs_node": obs, "goal_node": g,
                             "target_relative_yaw_deg": math.degrees(target),
                             "predicted_relative_yaw_deg": math.degrees(pred),
                             "circular_error_deg": abs(math.degrees(error)),
                             "key_case": (obs, g) in CASES})
                prediction.append(pred)
                truth.append(target)
    with (out / "heading_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = yaw_metrics(prediction, truth)
    # The route05 gate is already fixed; do not interpret a test gate as model selection.
    summary.pop("validation_gate_passed")
    summary["key_cases"] = [r for r in rows if r["key_case"]]
    summary["note"] = "house06 test only; no model selection or closed-loop claim"
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"head_sha256": hashlib.sha256(head_path.read_bytes()).hexdigest(),
        "head_bytes": head_path.stat().st_size, "head_dir": str(folder), "base_checkpoint_sha256": config["base_checkpoint_sha256"],
        "selected_epoch": best["epoch"], "selected_on": "house_run_05", "device": "cuda", "torch": torch.__version__,
        "input": "current and goal RGB images only"}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

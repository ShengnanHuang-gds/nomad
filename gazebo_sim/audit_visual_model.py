#!/usr/bin/env python3
"""Offline GPU audit of the deployed visual model; never starts a ROS node.

Uses the deployment loader, preprocessing, DDPM scheduler and action decoder.
Teacher poses are used only to label CSV results, never as model input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
import time
from pathlib import Path


CASES = [(0, 4), (8, 12), (8, 13), (8, 16), (12, 13), (12, 16), (12, 22),
         (22, 30), (22, 31), (30, 31), (30, 35), (38, 42), (38, 43),
         (42, 43), (42, 47), (51, 56), (51, 57), (56, 57), (56, 62)]
# The second turn ends in frame 35. This capture has no exit-straight image.
REFERENCE_TURN_ENDS = {8: 14, 10: 14, 12: 14, 24: 35, 26: 35, 28: 35, 30: 35, 32: 35}


def context_indices(node, size, mode):
    if mode == "repeat":
        return [node] * (size + 1)
    return [max(0, node - size + k) for k in range(size + 1)]


def summarize_waypoints(points):
    import numpy as np
    points = np.asarray(points)
    angles = np.degrees(np.arctan2(points[:, 1], points[:, 0]))
    return {"dx_median": float(np.median(points[:, 0])),
            "dy_median": float(np.median(points[:, 1])),
            "bearing_deg_median": float(np.median(angles)),
            "bearing_deg_p10": float(np.percentile(angles, 10)),
            "bearing_deg_p90": float(np.percentile(angles, 90)),
            "left_fraction": float(np.mean(points[:, 1] > 0)),
            "forward_fraction": float(np.mean(points[:, 0] > 0))}


def write_csv(path, rows):
    if rows:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def read_reference_capture(folder):
    """Read independently timestamped images and poses for offline scoring."""
    from route_frame_sync import MAX_BRACKET_NS

    report = json.loads((folder / "gazebo_reference_pose.json").read_text(encoding="utf-8"))
    frames = report["frames"]
    if report["run"] != "house_run_06" or len(frames) <= max(REFERENCE_TURN_ENDS.values()):
        raise ValueError("reference capture must contain both recorded house_06 turns")
    positions, yaw = [], []
    previous_stamp = 0
    for index, row in enumerate(frames):
        stamp, pose = row["image_stamp_ns"], row["gazebo_pose"]
        if (stamp <= previous_stamp or not pose or not row["tilt_ok"]
                or not 0 <= stamp - pose["before_stamp_ns"] <= MAX_BRACKET_NS
                or not 0 <= pose["after_stamp_ns"] - stamp <= MAX_BRACKET_NS):
            raise ValueError(f"reference image {index} has no valid Gazebo pose bracket")
        positions.append(pose["position_xyz_m"][:2])
        yaw.append(math.radians(pose["roll_pitch_yaw_deg"][2]))
        previous_stamp = stamp
    paths = [folder / f"{index}.jpg" for index in range(len(frames))]
    return paths, {"position": positions, "yaw": yaw}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="nomad_b40")
    p.add_argument("--config", default="", help="explicit model YAML, paired with --checkpoint")
    p.add_argument("--checkpoint", default="", help="explicit EMA state_dict, paired with --config")
    p.add_argument("--topomap", default="house_06")
    p.add_argument("--run", default="house_run_06")
    p.add_argument("--reference-dir", type=Path,
                   help="audit middle vs end goal images from the partial synchronized house_06 capture")
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--cpu", action="store_true", help="explicit opt-in; default requires CUDA")
    p.add_argument("--out", default="gazebo_sim/visual_audit_b40")
    args = p.parse_args()
    if args.samples < 1:
        p.error("--samples must be positive")
    if bool(args.config) != bool(args.checkpoint):
        p.error("provide both --config and --checkpoint")

    import numpy as np
    import torch
    import yaml
    from PIL import Image
    # Import the real runtime functions without instantiating its Node or calling init/spin.
    import nomad_navigate_ros2 as runtime
    from pd_controller_ros2 import pd_controller

    if not args.cpu and not torch.cuda.is_available():
        p.error("CUDA is unavailable in this Python. Use the WSL NOMAD_PY with GPU support, or explicitly --cpu.")
    device = torch.device("cpu" if args.cpu else "cuda")
    if args.config:
        cfg, checkpoint = Path(args.config).resolve(), Path(args.checkpoint).resolve()
    else:
        models = yaml.safe_load((runtime.DEPLOY / "config/models.yaml").read_text(encoding="utf-8"))
        entry = models[args.model]
        cfg = runtime.resolve_path(runtime.DEPLOY / "config", entry["config_path"])
        checkpoint = runtime.resolve_path(runtime.DEPLOY, entry["ckpt_path"])
    mp = runtime.load_train_config(cfg)
    model = runtime.load_model(str(checkpoint), mp, device).eval()
    try:
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    except TypeError:  # older local torch versions
        state = torch.load(checkpoint, map_location="cpu")
    model.load_state_dict(state, strict=True)
    del state

    if args.reference_dir:
        folder = args.reference_dir.resolve()
        paths, poses = read_reference_capture(folder)
        goals = teach = [Image.open(path).convert("RGB") for path in paths]
        cases = [(node, target) for node, end in REFERENCE_TURN_ENDS.items()
                 for target in (node + 1, end)]
        context_modes = {"temporal": "previous reference images"}
    else:
        folder = runtime.DEPLOY / "topomaps/images" / args.topomap
        paths = sorted((f for f in folder.iterdir() if f.suffix.lower() in (".jpg", ".png")),
                       key=lambda f: int(f.stem))
        if [int(f.stem) for f in paths] != list(range(len(paths))) or len(paths) != 63:
            p.error("this house_06 audit requires contiguous topomap image indices 0..62")
        goals = [Image.open(f).convert("RGB") for f in paths]
        teach_dir = Path(__file__).parent / args.run
        teach = [Image.open(teach_dir / f"{i}.jpg").convert("RGB") for i in range(len(goals))]
        with (teach_dir / "traj_data.pkl").open("rb") as f:
            poses = pickle.load(f)
        cases = CASES
        context_modes = {"temporal": "previous teaching images", "repeat": "same image repeated"}
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists():
        p.error(f"{output} already contains an audit; choose a new --out to preserve it")
    (output / "manifest.json").write_text(json.dumps({
        "checkpoint": str(checkpoint), "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "config": str(cfg), "model_params": mp, "strict_checkpoint_load": True,
        "device": str(device), "torch": torch.__version__, "seed": args.seed,
        "samples": args.samples, "topomap": str(folder),
        "context_modes": context_modes,
        "cases": cases, "synchronized_reference": bool(args.reference_dir),
        "caveat": "offline images only; no ROS, motion or closed-loop performance"
    }, indent=2), encoding="utf-8")
    if args.reference_dir is None:
        write_csv(output / "image_match.csv", [
            {"node": i, "decoded_pixel_mse": float(np.mean((np.asarray(a, dtype=float)-np.asarray(b, dtype=float))**2))}
            if a.size == b.size else {"node": i, "decoded_pixel_mse": "different image sizes"}
            for i, (a, b) in enumerate(zip(teach, goals))])
    scheduler = runtime.DDPMScheduler(num_train_timesteps=mp["num_diffusion_iters"],
                                      beta_schedule="squaredcos_cap_v2", clip_sample=True,
                                      prediction_type="epsilon")
    distances, actions, arrays = [], [], {}
    started = time.monotonic()
    nodes = sorted({a for a, _ in cases})
    pos = np.asarray(poses["position"])
    with torch.inference_mode():
        for mode in context_modes:
            for node in nodes:
                indices = context_indices(node, mp["context_size"], mode)
                obs = runtime.transform_images([teach[k] for k in indices], mp["image_size"], center_crop=False).to(device)
                conditions = []
                for start in range(0, len(goals), 16):
                    chunk = goals[start:start + 16]
                    batch = torch.cat([runtime.transform_images(g, mp["image_size"], center_crop=False)
                                       for g in chunk]).to(device)
                    cond = model("vision_encoder", obs_img=obs.repeat(len(chunk), 1, 1, 1),
                                 goal_img=batch, input_goal_mask=torch.zeros(len(chunk), dtype=torch.long, device=device))
                    conditions.append(cond)
                conditions = torch.cat(conditions)
                d = runtime.to_numpy(model("dist_pred_net", obsgoal_cond=conditions).flatten())
                for goal, value in enumerate(d):
                    distances.append({"context_mode": mode, "obs_node": node, "goal_node": goal,
                                      "dist_pred": float(value), "global_best_goal": int(d.argmin())})
                for _, goal in (case for case in cases if case[0] == node):
                    for mask in (0, 1):
                        cond = conditions[goal:goal + 1]
                        if mask:
                            goal_tensor = runtime.transform_images(goals[goal], mp["image_size"], center_crop=False).to(device)
                            cond = model("vision_encoder", obs_img=obs, goal_img=goal_tensor,
                                         input_goal_mask=torch.ones(1, dtype=torch.long, device=device))
                        cond = cond.repeat(args.samples, *([1] * (cond.ndim - 1)))
                        # Same random sequence in each case isolates changes due to conditioning.
                        torch.manual_seed(args.seed)
                        noise = torch.randn((args.samples, mp["len_traj_pred"], 2), device=device)
                        scheduler.set_timesteps(mp["num_diffusion_iters"])
                        for step in scheduler.timesteps:
                            pred = model("noise_pred_net", sample=noise, timestep=step, global_cond=cond)
                            noise = scheduler.step(model_output=pred, timestep=step, sample=noise).prev_sample
                        sample = runtime.to_numpy(runtime.get_action(noise))
                        if mp.get("normalize", True):
                            sample *= runtime.MAX_V / runtime.DEFAULT_RATE
                        key = f"{mode}_obs{node}_goal{goal}_mask{mask}"
                        arrays[key] = sample
                        dx, dy = pos[goal, :2] - pos[node, :2]
                        yaw = float(poses["yaw"][node])
                        gx, gy = math.cos(yaw)*dx+math.sin(yaw)*dy, -math.sin(yaw)*dx+math.cos(yaw)*dy
                        goal_yaw = math.degrees(math.remainder(float(poses["yaw"][goal]) - yaw, 2 * math.pi))
                        for index in (2, 7):
                            first_waypoint = sample[0, index]
                            linear, angular = pd_controller(first_waypoint)
                            actions.append({"context_mode": mode, "obs_node": node, "goal_node": goal,
                                            "goal_mask": mask, "waypoint_index": index,
                                            "dist_pred": float(d[goal]), "goal_body_dx": gx, "goal_body_dy": gy,
                                            "goal_relative_yaw_deg": goal_yaw,
                                            "sample0_dx": float(first_waypoint[0]),
                                            "sample0_dy": float(first_waypoint[1]),
                                            "sample0_cmd_v": linear, "sample0_cmd_w": angular,
                                            **summarize_waypoints(sample[:, index])})
                # Keep useful results even if the audit is interrupted.
                write_csv(output / "distance_matrix.csv", distances)
                write_csv(output / "action_summary.csv", actions)
                np.savez_compressed(output / "sampled_actions.npz", **arrays)
                print(f"{mode} obs={node}: best_goal={int(d.argmin())} self_dist={float(d[node]):.3f} elapsed={time.monotonic()-started:.1f}s", flush=True)
    print(f"Wrote offline visual audit to {output.resolve()}")


if __name__ == "__main__":
    main()

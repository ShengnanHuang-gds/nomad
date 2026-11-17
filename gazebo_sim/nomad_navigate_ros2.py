#!/usr/bin/env python3
"""Official NoMaD topomap navigation for ROS2 Gazebo (TurtleBot3 house).

Mirrors deployment/src/navigate.py (NoMaD branch): dist_pred localization,
subgoal selection, DDPM waypoint, publishes /nomad/waypoint.

Run in WSL after Gazebo + burger_cam (same as record_house_multi):
  export PYTHONPATH=/path/to/visualnav-transformer/diffusion_policy:$PYTHONPATH
  python3 gazebo_sim/nomad_navigate_ros2.py --topomap house_00 --model nomad_gazebo
  python3 gazebo_sim/pd_controller_ros2.py

Optional metrics: --log-csv rollout.csv (odom path length, scan-based collision proxy).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import time
from pathlib import Path

import cv2  # noqa: F401 — before torch when PYTHONPATH includes diffusion_policy
import numpy as np
import rclpy
import torch
import yaml
from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from PIL import Image as PILImage
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import Bool, Float32MultiArray

REPO = Path(__file__).resolve().parents[1]
VT = REPO / "visualnav-transformer"
DEPLOY = VT / "deployment"
TRAIN = VT / "train"
DP = VT / "diffusion_policy"

sys.path.insert(0, str(TRAIN))
sys.path.insert(0, str(DEPLOY / "src"))
if str(DP) not in os.environ.get("PYTHONPATH", ""):
    os.environ["PYTHONPATH"] = (
        str(DP)
        + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
    )

from utils import load_model, to_numpy, transform_images  # noqa: E402
from vint_train.training.train_utils import get_action  # noqa: E402

IMAGE_TOPIC = "/camera/image_raw"
MAX_V = 0.2
MAX_W = 0.4
DEFAULT_RATE = 4.0


def spawn_at_launch_enabled(arg_flag: bool) -> bool:
    if arg_flag:
        return True
    env = os.environ.get("NOMAD_SPAWN_AT_LAUNCH", "").strip().lower()
    return env in ("1", "true", "yes", "on")


def msg_to_pil_rgb(msg: Image) -> PILImage.Image:
    enc = msg.encoding.lower()
    if enc in ("rgb8", "bgr8"):
        channels = 3
    elif enc in ("rgba8", "bgra8"):
        channels = 4
    else:
        raise ValueError(f"unsupported image encoding: {msg.encoding}")
    img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, channels)
    if enc.startswith("bgr"):
        img = img[:, :, :3][:, :, ::-1]
    elif channels == 4:
        img = img[:, :, :3]
    return PILImage.fromarray(img, "RGB")


def resolve_path(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if not p.is_file():
        raise FileNotFoundError(p)
    return p


def load_train_config(config_path: Path) -> dict:
    with open(TRAIN / "config" / "defaults.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(config_path, encoding="utf-8") as f:
        cfg.update(yaml.safe_load(f))
    return cfg


class NoMaDNavigate(Node):
    def __init__(self, args: argparse.Namespace):
        super().__init__("nomad_navigate")
        self.args = args
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() and not args.cpu else "cpu"
        )
        self.get_logger().info(f"device {self.device}")

        if args.config and args.checkpoint:
            model_params = load_train_config(Path(args.config))
            ckpt = Path(args.checkpoint)
        else:
            models_yaml = DEPLOY / "config" / "models.yaml"
            with open(models_yaml, encoding="utf-8") as f:
                models = yaml.safe_load(f)
            if args.model not in models:
                raise KeyError(f"{args.model} not in {models_yaml}")
            rel_cfg = models[args.model]["config_path"]
            rel_ckpt = models[args.model]["ckpt_path"]
            model_params = load_train_config(
                resolve_path(DEPLOY / "config", rel_cfg)
            )
            ckpt = resolve_path(DEPLOY, rel_ckpt)

        self.model_params = model_params
        self.context_size = int(model_params["context_size"])
        self.model = load_model(str(ckpt), model_params, self.device)
        self.model.eval()

        self.noise_scheduler = DDPMScheduler(
            num_train_timesteps=model_params["num_diffusion_iters"],
            beta_schedule="squaredcos_cap_v2",
            clip_sample=True,
            prediction_type="epsilon",
        )

        topomap_dir = DEPLOY / "topomaps" / "images" / args.topomap
        if not topomap_dir.is_dir():
            raise FileNotFoundError(topomap_dir)
        names = sorted(
            (p for p in topomap_dir.iterdir() if p.suffix.lower() in (".png", ".jpg")),
            key=lambda p: int(p.stem),
        )
        self.topomap = [PILImage.open(p).convert("RGB") for p in names]
        self.get_logger().info(f"topomap {args.topomap}: {len(self.topomap)} nodes")

        assert -1 <= args.goal_node < len(self.topomap)
        self.goal_node = (
            len(self.topomap) - 1 if args.goal_node < 0 else args.goal_node
        )
        self.closest_node = 0

        self.context_queue: list[PILImage.Image] = []
        self._scan_min: float | None = None
        self._odom_xy: tuple[float, float] | None = None
        self._path_m = 0.0
        self._last_xy: tuple[float, float] | None = None
        self._path_xy: list[list[float]] = []
        self._collision_events = 0
        self._collision = False
        self._log_rows: list[dict] = []
        self._tick_count = 0
        self._finished = False
        self._closest_node_max = 0
        self._nav_active_ticks = 0
        self._reset_align_m: float | None = None
        self._last_dist_window: list[float] = []
        self._last_dist_min = float("nan")
        self._last_sg_idx = -1
        self._expected_start: tuple[float, float] | None = None
        self._odom_yaw: float | None = None
        self._teach_yaw = None
        self._teach_pos = None
        self._spawn_at_launch = spawn_at_launch_enabled(args.spawn_at_launch)
        if args.traj_name:
            pkl = Path(__file__).resolve().parent / args.traj_name / "traj_data.pkl"
            if pkl.is_file():
                import pickle

                with open(pkl, "rb") as f:
                    blob = pickle.load(f)
                gt = blob["position"][0]
                if "yaw" in blob:
                    self._teach_yaw = [float(a) for a in blob["yaw"]]
                    self._teach_pos = [(float(p[0]), float(p[1])) for p in blob["position"]]
                self._teach_anchor = (float(gt[0]), float(gt[1]))
                self._expected_start = (
                    (0.0, 0.0) if self._spawn_at_launch else self._teach_anchor
                )
                if self._spawn_at_launch:
                    self.get_logger().info(
                        "spawn-at-launch: reset odom near (0,0); "
                        f"teach anchor ({self._teach_anchor[0]:.3f}, {self._teach_anchor[1]:.3f})"
                    )
                else:
                    self.get_logger().info(
                        f"expect reset odom near ({self._expected_start[0]:.3f}, {self._expected_start[1]:.3f})"
                    )

        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.create_subscription(Image, args.image_topic, self._on_image, qos)
        self.create_subscription(Odometry, "/odom", self._on_odom, 10)
        if args.scan_topic:
            self.create_subscription(LaserScan, args.scan_topic, self._on_scan, 10)

        self._wp_pub = self.create_publisher(Float32MultiArray, "/nomad/waypoint", 10)
        self._goal_pub = self.create_publisher(Bool, "/nomad/reached_goal", 10)
        self._act_pub = self.create_publisher(
            Float32MultiArray, "/nomad/sampled_actions", 10
        )

        period = 1.0 / args.rate
        self.create_timer(period, self._navigate_step)
        self.get_logger().info(
            f"goal_node={self.goal_node} radius={args.radius} close_threshold={args.close_threshold} subgoal_lead={args.subgoal_lead} waypoint={args.waypoint}"
        )

    def _on_image(self, msg: Image):
        try:
            pil = msg_to_pil_rgb(msg)
        except ValueError as e:
            self.get_logger().warn(str(e))
            return
        if len(self.context_queue) < self.context_size + 1:
            self.context_queue.append(pil)
        else:
            self.context_queue.pop(0)
            self.context_queue.append(pil)

    def _on_odom(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self._odom_yaw = math.atan2(siny, cosy)
        xy = (float(p.x), float(p.y))
        self._odom_xy = xy
        if self._last_xy is not None:
            self._path_m += math.hypot(xy[0] - self._last_xy[0], xy[1] - self._last_xy[1])
        self._last_xy = xy
        if not self._path_xy or self._path_xy[-1] != [xy[0], xy[1]]:
            self._path_xy.append([xy[0], xy[1]])

    def _on_scan(self, msg: LaserScan):
        valid = [
            r
            for r in msg.ranges
            if msg.range_min < r < msg.range_max and not math.isinf(r) and not math.isnan(r)
        ]
        self._scan_min = min(valid) if valid else None

    def _teach_spin_waypoint(self, node: int):
        if not self.args.teach_yaw_spin or self._teach_yaw is None or self._odom_yaw is None:
            return None
        if self._teach_pos is None or node < 0 or node >= len(self._teach_yaw):
            return None
        target = node
        i = node
        while i + 1 < len(self._teach_yaw):
            x0, y0 = self._teach_pos[i]
            x1, y1 = self._teach_pos[i + 1]
            step = math.hypot(x1 - x0, y1 - y0)
            dyaw = (self._teach_yaw[i + 1] - self._teach_yaw[i] + math.pi) % (2 * math.pi) - math.pi
            if step > 0.05 or abs(dyaw) < math.radians(4):
                break
            target = i + 1
            i += 1
        err = (self._teach_yaw[target] - self._odom_yaw + math.pi) % (2 * math.pi) - math.pi
        if abs(err) < math.radians(self.args.teach_yaw_deg):
            return None
        return np.array([0.0, 0.0, math.cos(err), math.sin(err)], dtype=np.float64)

    def _collision_proxy(self) -> bool:
        if self._scan_min is None:
            return False
        return self._scan_min < self.args.collision_m

    def _primary_failure(self) -> str:
        if self._reset_align_m is not None and self._reset_align_m > self.args.max_reset_err_m:
            return "reset_pose_mismatch"
        if self._collision and self.args.stop_on_collision:
            return "collision"
        if self.closest_node >= self.goal_node:
            return "none"
        if (
            not self._spawn_at_launch
            and self._closest_node_max < 3
            and (self._reset_align_m or 0) > 1.0
        ):
            return "off_corridor_from_start"
        if self._last_dist_window and self._last_dist_min >= self.args.close_threshold:
            return "dist_pred_not_close_to_subgoal"
        if self._closest_node_max <= self.closest_node + 1 and self._nav_active_ticks > 100:
            return "closest_node_plateau"
        return "policy_or_sim_drift"

    def _finish_episode(self, reached: bool):
        if self._finished or not self.args.episode_out:
            return
        self._finished = True
        failure = self._primary_failure()
        spawn = self._spawn_at_launch
        path_world: list[list[float]] = list(self._path_xy)
        if spawn and self._teach_anchor:
            ax, ay = self._teach_anchor
            path_world = [[float(p[0]) + ax, float(p[1]) + ay] for p in self._path_xy]
        summary = {
            "traj": self.args.traj_name
            or self.args.topomap.replace("house_", "house_run_", 1),
            "topomap": self.args.topomap,
            "success": bool(reached),
            "path_odom_m": float(self._path_m),
            "collision_count": int(self._collision_events),
            "ticks": int(self._tick_count),
            "nav_ticks": int(self._nav_active_ticks),
            "closest_node": int(self.closest_node),
            "closest_node_max": int(self._closest_node_max),
            "goal_node": int(self.goal_node),
            "reset_align_m": self._reset_align_m,
            "dist_pred_min_last": self._last_dist_min,
            "dist_pred_window_last": self._last_dist_window,
            "subgoal_idx_last": int(self._last_sg_idx),
            "subgoal_lead": int(self.args.subgoal_lead),
            "primary_failure": failure,
            "path_xy": self._path_xy,
            "path_xy_world": path_world,
            "spawn_at_launch": spawn,
            "odom_frame": "spawn_origin" if spawn else "teach_odom",
            "teach_anchor_xy": list(self._teach_anchor) if spawn and self._teach_anchor else None,
        }
        os.makedirs(os.path.dirname(os.path.abspath(self.args.episode_out)) or ".", exist_ok=True)
        import json

        with open(self.args.episode_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        self.get_logger().info(f"episode summary -> {self.args.episode_out}")
        if rclpy.ok():
            rclpy.shutdown()

    @torch.no_grad()
    def _navigate_step(self):
        if self._finished:
            return
        self._tick_count += 1
        if len(self.context_queue) <= self.context_size:
            return
        if self._reset_align_m is None and self._expected_start and self._odom_xy:
            self._reset_align_m = math.hypot(
                self._odom_xy[0] - self._expected_start[0],
                self._odom_xy[1] - self._expected_start[1],
            )
            self.get_logger().info(f"reset_align_m={self._reset_align_m:.3f}")
            if self._reset_align_m > self.args.max_reset_err_m:
                hint = (
                    "fix gz set_pose / --verify on reset"
                    if not self._spawn_at_launch
                    else "odom not at origin — restart launch_tb3_house_at_run.sh"
                )
                self.get_logger().error(
                    f"reset misaligned {self._reset_align_m:.2f}m > {self.args.max_reset_err_m} — "
                    f"episode metrics invalid; {hint}"
                )
        self._nav_active_ticks += 1
        if self._collision_proxy():
            self._collision_events += 1
            if self.args.stop_on_collision:
                self._collision = True

        args = self.args
        chosen_waypoint = np.zeros(4, dtype=np.float64)
        reached = self.closest_node == self.goal_node

        if not reached and not self._collision:
            mp = self.model_params
            obs_images = transform_images(
                self.context_queue, mp["image_size"], center_crop=False
            )
            obs_images = torch.cat(torch.split(obs_images, 3, dim=1), dim=1).to(
                self.device
            )
            mask = torch.zeros(1, dtype=torch.long, device=self.device)

            start = max(self.closest_node - args.radius, 0)
            end = min(self.closest_node + args.radius + 1, self.goal_node)
            goal_batch = torch.concat(
                [
                    transform_images(g, mp["image_size"], center_crop=False).to(
                        self.device
                    )
                    for g in self.topomap[start : end + 1]
                ],
                dim=0,
            )
            n_goals = goal_batch.shape[0]
            obsgoal_cond = self.model(
                "vision_encoder",
                obs_img=obs_images.repeat(n_goals, 1, 1, 1),
                goal_img=goal_batch,
                input_goal_mask=mask.repeat(n_goals),
            )
            dists = to_numpy(
                self.model("dist_pred_net", obsgoal_cond=obsgoal_cond).flatten()
            )
            min_idx = int(np.argmin(dists))
            self.closest_node = min_idx + start
            self._closest_node_max = max(self._closest_node_max, self.closest_node)
            self._last_dist_window = [float(x) for x in dists.tolist()]
            self._last_dist_min = float(dists[min_idx])
            lead = args.subgoal_lead if dists[min_idx] < args.close_threshold else 0
            sg_idx = min(min_idx + lead, len(obsgoal_cond) - 1)
            self._last_sg_idx = int(sg_idx)
            obs_cond = obsgoal_cond[sg_idx].unsqueeze(0)
            if obs_cond.ndim == 2:
                obs_cond = obs_cond.repeat(args.num_samples, 1)
            else:
                obs_cond = obs_cond.repeat(args.num_samples, 1, 1)

            naction = torch.randn(
                (args.num_samples, mp["len_traj_pred"], 2), device=self.device
            )
            self.noise_scheduler.set_timesteps(mp["num_diffusion_iters"])
            for k in self.noise_scheduler.timesteps:
                noise_pred = self.model(
                    "noise_pred_net",
                    sample=naction,
                    timestep=k,
                    global_cond=obs_cond,
                )
                naction = self.noise_scheduler.step(
                    model_output=noise_pred, timestep=k, sample=naction
                ).prev_sample

            naction = to_numpy(get_action(naction))
            samp = Float32MultiArray()
            samp.data = [0.0, *naction.flatten().tolist()]
            self._act_pub.publish(samp)
            chosen_waypoint = naction[0, args.waypoint]
            if mp.get("normalize", True):
                chosen_waypoint = chosen_waypoint * (MAX_V / args.rate)
            spin = self._teach_spin_waypoint(self.closest_node)
            if spin is not None:
                chosen_waypoint = spin

        wp = Float32MultiArray()
        wp.data = chosen_waypoint.tolist()
        self._wp_pub.publish(wp)
        reached = self.closest_node == self.goal_node
        self._goal_pub.publish(Bool(data=reached))

        if args.log_csv:
            self._log_rows.append(
                {
                    "t": time.time(),
                    "closest_node": self.closest_node,
                    "dist_min": self._last_dist_min,
                    "sg_idx": self._last_sg_idx,
                    "reached": int(reached),
                    "path_m": self._path_m,
                    "odom_x": self._odom_xy[0] if self._odom_xy else "",
                    "odom_y": self._odom_xy[1] if self._odom_xy else "",
                    "scan_min": self._scan_min if self._scan_min is not None else "",
                    "collision_events": self._collision_events,
                }
            )

        if reached:
            self.get_logger().info(
                f"reached goal node {self.goal_node} path_m={self._path_m:.2f}"
            )
            if args.episode_out:
                self._finish_episode(True)
        elif self._collision and args.stop_on_collision:
            self.get_logger().warn(
                f"collision proxy stop scan_min={self._scan_min} path_m={self._path_m:.2f}"
            )
            if args.episode_out:
                self._finish_episode(False)
        elif args.max_ticks and self._tick_count >= args.max_ticks:
            self.get_logger().warn(f"max_ticks={args.max_ticks} path_m={self._path_m:.2f}")
            if args.episode_out:
                self._finish_episode(reached)

    def write_log(self, path: str):
        if not self._log_rows:
            return
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        fields = list(self._log_rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(self._log_rows)


def parse_args():
    p = argparse.ArgumentParser(description="NoMaD topomap navigation (ROS2)")
    p.add_argument("--model", default="nomad_gazebo", help="key in deployment/config/models.yaml")
    p.add_argument("--config", default="", help="override train config yaml")
    p.add_argument("--checkpoint", default="", help="override .pth")
    p.add_argument("--topomap", "-d", default="house_00", help="deployment/topomaps/images/<name>")
    p.add_argument("--goal-node", "-g", type=int, default=-1)
    p.add_argument("--waypoint", "-w", type=int, default=2)
    p.add_argument("--teach-yaw-spin", action="store_true")
    p.add_argument("--teach-yaw-deg", type=float, default=8.0)
    p.add_argument("--close-threshold", "-t", type=int, default=5)
    p.add_argument(
        "--subgoal-lead",
        type=int,
        default=1,
        help="nodes ahead of the closest node when dist_pred is under close_threshold",
    )
    p.add_argument("--radius", "-r", type=int, default=4)
    p.add_argument("--num-samples", "-n", type=int, default=8)
    p.add_argument("--rate", type=float, default=DEFAULT_RATE, help="Hz (match pd DT)")
    p.add_argument("--image-topic", default=IMAGE_TOPIC)
    p.add_argument("--scan-topic", default="/scan", help="empty to disable collision proxy")
    p.add_argument("--collision-m", type=float, default=0.15)
    p.add_argument("--stop-on-collision", action="store_true")
    p.add_argument("--log-csv", default="", help="write per-tick metrics on shutdown")
    p.add_argument("--episode-out", default="", help="write success/path/collision JSON and exit")
    p.add_argument("--traj-name", default="", help="label in episode JSON")
    p.add_argument("--max-ticks", type=int, default=0, help="episode timeout in navigate ticks")
    p.add_argument(
        "--max-reset-err-m",
        type=float,
        default=0.5,
        help="log/warn when first-nav odom is farther from traj start (see primary_failure)",
    )
    p.add_argument(
        "--spawn-at-launch",
        action="store_true",
        help="Gazebo spawned at teach xy (launch_tb3_house_at_run); /odom starts at origin",
    )
    p.add_argument(
        "--auto-log-csv",
        action="store_true",
        help="with --episode-out, also write <episode>.ticks.csv",
    )
    p.add_argument("--cpu", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    if not args.scan_topic:
        args.scan_topic = ""
    if args.auto_log_csv and args.episode_out:
        stem, ext = os.path.splitext(args.episode_out)
        if ext.lower() != ".csv":
            args.log_csv = stem + ".ticks.csv"
    rclpy.init()
    node = NoMaDNavigate(args)
    try:
        if not node._finished:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    if args.episode_out and not node._finished:
        node._finish_episode(node.closest_node == node.goal_node)
    if args.log_csv:
        node.write_log(args.log_csv)
        node.get_logger().info(f"wrote {args.log_csv}")
    try:
        node.destroy_node()
    except Exception:
        pass
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
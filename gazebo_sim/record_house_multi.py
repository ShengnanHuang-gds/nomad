#!/usr/bin/env python3
"""Record scripted trajectories in turtlebot3_house (go_stanford layout)."""

from __future__ import annotations

import math
import os
import pickle
import sys
import time

import numpy as np
from PIL import Image as PILImage
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image

from route_frame_sync import RouteFrameSync, stamp_ns, wrapped_delta

ROOT = os.path.dirname(os.path.abspath(__file__))
SPACING = 0.12
YAW_SPACING = math.radians(8)
MAX_YAW_GAP = math.radians(12)

PLANS = {
    "house_run_03": {
        "pose": (1.2, 1.5, -math.pi / 2),
        "segs": [
            ("dist", 0.14, 0.0, 1.1),
            ("yaw", -0.35, -math.pi / 2),
            ("dist", 0.14, 0.0, 1.0),
            ("yaw", 0.35, math.pi / 3),
            ("dist", 0.14, 0.0, 0.9),
            ("yaw", -0.35, -math.pi / 4),
            ("dist", 0.14, 0.0, 1.2),
        ],
    },
    "house_run_04": {
        "pose": (-0.5, -1.8, math.pi),
        "segs": [
            ("dist", 0.14, 0.0, 0.85),
            ("yaw", 0.35, math.pi / 2),
            ("dist", 0.14, 0.0, 1.05),
            ("yaw", 0.35, math.pi / 2),
            ("dist", 0.14, 0.0, 0.75),
            ("yaw", -0.35, -math.pi / 3),
            ("dist", 0.14, 0.0, 1.0),
            ("yaw", -0.35, -math.pi / 4),
            ("dist", 0.14, 0.0, 0.7),
        ],
    },
    "house_run_05": {
        "pose": (2.0, -0.3, math.pi / 4),
        "segs": [
            ("dist", 0.14, 0.0, 1.0),
            ("yaw", -0.35, -math.pi / 2),
            ("dist", 0.14, 0.0, 0.95),
            ("yaw", 0.35, math.pi / 2),
            ("dist", 0.14, 0.0, 1.1),
            ("yaw", 0.35, math.pi / 4),
            ("dist", 0.14, 0.0, 0.8),
        ],
    },
    "house_run_06": {
        "pose": (-2.2, 1.2, -math.pi / 4),
        "segs": [
            ("dist", 0.14, 0.0, 0.9),
            ("yaw", 0.35, math.pi / 4),
            ("dist", 0.14, 0.0, 1.15),
            ("yaw", -0.35, -math.pi / 2),
            ("dist", 0.14, 0.0, 0.85),
            ("yaw", -0.35, -math.pi / 4),
            ("dist", 0.14, 0.0, 1.0),
            ("yaw", 0.35, math.pi / 3),
            ("dist", 0.14, 0.0, 0.65),
        ],
    },
    "house_run_07": {
        "pose": (0.0, 2.0, 3 * math.pi / 4),
        "segs": [
            ("dist", 0.14, 0.0, 1.2),
            ("yaw", -0.35, -math.pi / 2),
            ("dist", 0.14, 0.0, 0.8),
            ("yaw", 0.35, math.pi / 2),
            ("dist", 0.14, 0.0, 1.05),
            ("yaw", -0.35, -math.pi / 3),
            ("dist", 0.14, 0.0, 0.75),
            ("yaw", 0.35, math.pi / 4),
            ("dist", 0.14, 0.0, 0.9),
        ],
    },
}


def yaw_of(q):
    return math.atan2(
        2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
    )


def set_pose(x, y, yaw):
    from gz_pose_utils import set_robot_pose

    ent = set_robot_pose(x, y, yaw)
    print(f"set_pose ok entity={ent} x={x:.3f} y={y:.3f} yaw={yaw:.3f}", flush=True)


class Recorder(Node):
    def __init__(self, out):
        super().__init__("house_rec")
        self.out = out
        os.makedirs(out, exist_ok=True)
        self.pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.st = None
        self.odom_received_at = None
        self.sync = RouteFrameSync()
        qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.create_subscription(Odometry, "/odom", self.odom_cb, 10)
        self.create_subscription(Image, "/camera/image_raw", self.img_cb, qos)
        self.frames = []

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        state = (p.x, p.y, yaw_of(msg.pose.pose.orientation))
        if not all(math.isfinite(value) for value in state):
            raise RuntimeError("nonfinite odometry pose")
        if self.sync.add_odom(stamp_ns(msg.header.stamp), state):
            self.st = state
            self.odom_received_at = time.monotonic()

    def img_cb(self, msg):
        self.sync.add_image(stamp_ns(msg.header.stamp), msg)

    def publish_twist(self, v, w):
        msg = TwistStamped()
        msg.header.frame_id = "base_link"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = v
        msg.twist.angular.z = w
        self.pub.publish(msg)

    def stop(self, *, drain_callbacks=True):
        for _ in range(8):
            self.publish_twist(0.0, 0.0)
            if drain_callbacks:
                rclpy.spin_once(self, timeout_sec=0.05)
            else:
                time.sleep(0.05)

    def save_frame(self, frame, *, force=False):
        x, y, yaw = frame.pose
        if self.frames:
            prev_x, prev_y, prev_yaw = self.frames[-1][1]
            distance = math.hypot(x - prev_x, y - prev_y)
            dyaw = abs(wrapped_delta(prev_yaw, yaw))
            if dyaw > MAX_YAW_GAP:
                raise RuntimeError(f"missing intermediate turn images: gap {math.degrees(dyaw):.1f}°")
            if not force and distance < SPACING and dyaw < YAW_SPACING:
                return
        img = frame.image
        if (img.encoding not in ("rgb8", "bgr8") or img.step < img.width * 3
                or len(img.data) != img.height * img.step):
            raise RuntimeError(f"unsupported camera buffer: {img.encoding} {img.width}x{img.height}")
        image = PILImage.frombytes("RGB", (img.width, img.height), bytes(img.data),
                                   "raw", "BGR" if img.encoding == "bgr8" else "RGB", img.step, 1)
        index = len(self.frames)
        image.save(os.path.join(self.out, f"{index}.jpg"), quality=92)
        self.frames.append((frame.stamp, frame.pose, frame.odom_before, frame.odom_after))
        print(f"frame {index} stamp_ns={frame.stamp}", flush=True)

    def save_ready(self):
        for frame in self.sync.paired():
            self.save_frame(frame)

    def save_endpoint(self, minimum_stamp=0):
        deadline = time.monotonic() + 8
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            batch = list(self.sync.paired())
            for frame in batch:
                self.save_frame(frame, force=frame is batch[-1] and frame.stamp >= minimum_stamp)
            if batch and batch[-1].stamp >= minimum_stamp:
                return
        raise RuntimeError("timed out waiting for a new camera frame with a close odometry bracket")

    def motion_tick(self, v, w):
        rclpy.spin_once(self, timeout_sec=0.05)
        if time.monotonic() - self.odom_received_at > 2:
            raise RuntimeError("odometry stopped during recording")
        self.save_ready()
        self.publish_twist(v, w)

    def finish_segment(self):
        self.stop()
        self.save_endpoint(self.sync.last_odom_stamp)

    def drive_dist(self, v, w, dist, wall=180):
        x0, y0, _ = self.st
        deadline = time.monotonic() + wall
        while rclpy.ok() and time.monotonic() < deadline:
            self.motion_tick(v, w)
            if math.hypot(self.st[0] - x0, self.st[1] - y0) >= dist:
                self.finish_segment()
                return
        raise RuntimeError("translation did not reach its requested distance")

    def drive_yaw(self, w, dyaw, wall=120):
        yaw0 = self.st[2]
        deadline = time.monotonic() + wall
        direction = math.copysign(1.0, dyaw)
        while rclpy.ok() and time.monotonic() < deadline:
            self.motion_tick(0.0, w)
            if direction * wrapped_delta(yaw0, self.st[2]) >= abs(dyaw) - 0.03:
                self.finish_segment()
                return
        raise RuntimeError("turn did not reach its requested yaw")


def run_one(name, *, spawn_at_launch: bool = False, out_root=ROOT):
    plan = PLANS[name]
    out = os.path.join(out_root, name)
    if os.path.exists(out) and os.listdir(out):
        raise RuntimeError(f"recording directory already contains data: {out}; use --out-root")
    x, y, yaw = plan["pose"]
    if spawn_at_launch:
        print(
            f"spawn-at-launch record {name}: skip set_pose "
            f"(expect launch_tb3_house_at_run + verify first)",
            flush=True,
        )
    else:
        set_pose(x, y, yaw)
    rclpy.init()
    node = Recorder(out)
    try:
        node.save_endpoint()
        for seg in plan["segs"]:
            if seg[0] == "dist":
                _, v, w, dist = seg
                node.drive_dist(v, w, dist)
            else:
                _, w, dyaw = seg
                node.drive_yaw(w, dyaw)
    finally:
        try:
            if rclpy.ok():
                node.stop(drain_callbacks=False)
        finally:
            node.destroy_node()
            rclpy.try_shutdown()
    poses = np.asarray([frame[1] for frame in node.frames], dtype=np.float64)
    pos, yaw_a = poses[:, :2], poses[:, 2]
    payload = {
        "position": pos, "yaw": yaw_a, "pose_source": "wheel_odometry_at_image_stamp",
        "image_stamp_ns": np.asarray([frame[0] for frame in node.frames], dtype=np.int64),
        "odom_before_stamp_ns": np.asarray([frame[2] for frame in node.frames], dtype=np.int64),
        "odom_after_stamp_ns": np.asarray([frame[3] for frame in node.frames], dtype=np.int64),
    }
    if spawn_at_launch:
        payload["world_anchor"] = [float(x), float(y)]
    partial = os.path.join(out, "traj_data.pkl.tmp")
    with open(partial, "wb") as f:
        pickle.dump(payload, f)
    os.replace(partial, os.path.join(out, "traj_data.pkl"))
    tot = float(
        sum(np.linalg.norm(pos[i] - pos[i - 1]) for i in range(1, len(pos)))
    )
    dy = float(np.degrees(np.unwrap(yaw_a)[-1] - np.unwrap(yaw_a)[0]))
    print(f"DONE {name} frames={len(node.frames)} path_m={tot:.2f} yaw={dy:.1f}")
    time.sleep(2)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spawn-at-launch",
        action="store_true",
        help="do not gz teleport; odom starts at launch spawn (matches holdout)",
    )
    parser.add_argument("runs", nargs="*", help="e.g. house_run_06")
    parser.add_argument("--out-root", default=ROOT, help="parent directory for new recordings")
    args = parser.parse_args()
    names = args.runs or list(PLANS.keys())
    for n in names:
        if n not in PLANS:
            print(f"unknown run {n}", file=sys.stderr)
            continue
        run_one(n, spawn_at_launch=args.spawn_at_launch, out_root=args.out_root)


def topomap_name(run: str) -> str:
    return "house_" + run.replace("house_run_", "")


def rerecord_until_ok(
    runs: list[str],
    *,
    py: str,
    model: str = "nomad_b40",
    max_tries: int = 8,
    max_mse: float = 2500.0,
    max_dist: float = 5.0,
) -> None:
    import shutil
    import subprocess
    from datetime import datetime

    root = ROOT
    stamp = lambda: datetime.now().strftime("%Y%m%d_%H%M%S")

    for run in runs:
        if run not in PLANS:
            raise SystemExit(f"unknown run {run}")
        top = topomap_name(run)
        for attempt in range(1, max_tries + 1):
            print(f"\n======== {run} try {attempt}/{max_tries} ========", flush=True)
            print(
                f"T1: bash gazebo_sim/launch_tb3_house_at_run.sh {run}",
                flush=True,
            )
            input("T1 running, Enter...")
            out_dir = os.path.join(root, run)
            if os.path.isdir(out_dir):
                bak = os.path.join(root, f"{run}_bak_{stamp()}")
                shutil.move(out_dir, bak)
                print(f"backup {out_dir} -> {bak}", flush=True)
            os.makedirs(out_dir, exist_ok=True)

            subprocess.check_call(
                [
                    py,
                    os.path.join(root, "reset_run_pose.py"),
                    "--run",
                    run,
                    "--skip-teleport",
                    "--verify",
                    "--max-err-m",
                    "0.8",
                    "--settle-s",
                    "8",
                ]
            )
            subprocess.check_call(
                [
                    py,
                    __file__,
                    "--spawn-at-launch",
                    run,
                ]
            )
            subprocess.check_call(
                [
                    py,
                    os.path.join(root, "export_topomap.py"),
                    "--run",
                    run,
                    "--name",
                    top,
                ]
            )
            print(
                f"record done — T1: Ctrl+C → relaunch launch_tb3_house_at_run.sh {run}",
                flush=True,
            )
            input("relaunched T1, Enter to verify+gate...")
            subprocess.check_call(
                [
                    py,
                    os.path.join(root, "reset_run_pose.py"),
                    "--run",
                    run,
                    "--skip-teleport",
                    "--verify",
                    "--max-err-m",
                    "0.8",
                    "--settle-s",
                    "8",
                ]
            )
            rc = subprocess.run(
                [
                    py,
                    os.path.join(root, "debug_dist_pred.py"),
                    "--model",
                    model,
                    "--topomap",
                    top,
                    "--run",
                    run,
                    "--gate",
                    "--max-mse",
                    str(max_mse),
                    "--max-dist",
                    str(max_dist),
                    "--wait-s",
                    "6",
                ]
            ).returncode
            if rc == 0:
                print(f"PASS {run} / {top}\n", flush=True)
                break
            raise SystemExit(
                f"FAIL {run}: live camera != teach0. Not recording again the same way."
            )
        else:
            raise SystemExit(f"gave up on {run} after {max_tries} tries")


if __name__ == "__main__":
    import argparse
    import os as _os
    import sys as _sys

    if len(_sys.argv) >= 2 and _sys.argv[1] == "--rerecord-until-ok":
        _parser = argparse.ArgumentParser()
        _parser.add_argument("--rerecord-until-ok", action="store_true")
        _parser.add_argument(
            "--runs",
            default="house_run_03,house_run_04,house_run_05,house_run_06,house_run_07",
        )
        _parser.add_argument("--model", default="nomad_b40")
        _parser.add_argument("--max-tries", type=int, default=8)
        _parser.add_argument("--max-mse", type=float, default=2500.0)
        _parser.add_argument("--max-dist", type=float, default=5.0)
        _args, _ = _parser.parse_known_args()
        _py = _os.environ.get("NOMAD_PY") or _sys.executable
        _runs = [x.strip() for x in _args.runs.split(",") if x.strip()]
        rerecord_until_ok(
            _runs,
            py=_py,
            model=_args.model,
            max_tries=_args.max_tries,
            max_mse=_args.max_mse,
            max_dist=_args.max_dist,
        )
    else:
        main()

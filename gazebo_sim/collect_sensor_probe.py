#!/usr/bin/env python3
"""Collect the live camera, odometry, and Gazebo pose. One optional in-place turn."""

import hashlib
import json
import math
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import CameraInfo, Image, LaserScan
from tf2_ros import Buffer, TransformListener
import tf2_ros
from PIL import Image as PilImage

ROOT = Path("/mnt/c/Users/61078/Desktop/nomad")
OUT = ROOT / "gazebo_sim/visual_sensor_probe"
SHARE = Path("/opt/ros/jazzy/share/turtlebot3_gazebo")
SOURCES = [
    SHARE / "launch/turtlebot3_house.launch.py",
    SHARE / "launch/spawn_turtlebot3.launch.py",
    SHARE / "launch/robot_state_publisher.launch.py",
    SHARE / "models/turtlebot3_burger_cam/model.sdf",
    SHARE / "models/turtlebot3_burger_cam/model.config",
    SHARE / "urdf/turtlebot3_burger_cam.urdf",
    SHARE / "params/turtlebot3_burger_cam_bridge.yaml",
    SHARE / "worlds/turtlebot3_house.world",
    ROOT / "gazebo_sim/launch_tb3_house_at_run.sh",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stamp_dict(stamp):
    return {"sec": int(stamp.sec), "nanosec": int(stamp.nanosec)}


def yaw_pitch_roll(x, y, z, w):
    """Intrinsic ZYX yaw/pitch/roll. This is a calculation convention, not a claim that the source uses it."""
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    return {"yaw_rad": yaw, "pitch_rad": pitch, "roll_rad": roll}


class PoseWatch(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.latest = {}
        self.error = ""
        self.stop = threading.Event()
        self.proc = None

    def run(self):
        env = os.environ.copy()
        env.update({"GZ_IP": "127.0.0.1", "GZ_RELAY": "127.0.0.1", "GZ_PARTITION": ""})
        self.proc = subprocess.Popen(
            ["gz", "topic", "-e", "-t", "/world/default/dynamic_pose/info"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        stamp = {}
        current = None
        section = None
        try:
            for line in self.proc.stdout:
                if self.stop.is_set():
                    break
                text = line.strip().strip(",")
                if text.startswith("sec:"):
                    stamp["sec"] = int(text.split(":", 1)[1])
                elif text.startswith("nsec:"):
                    stamp["nsec"] = int(text.split(":", 1)[1])
                elif text.startswith("name:"):
                    current = {"name": text.split(":", 1)[1].strip().strip('"'), "stamp": dict(stamp), "recv_unix": time.time()}
                    section = None
                elif current is not None and text.startswith("position"):
                    section = "position"
                    current.setdefault("position", {})
                elif current is not None and text.startswith("orientation"):
                    section = "orientation"
                    current.setdefault("orientation", {})
                elif current is not None and section and text[:1] in "xyzw" and ":" in text:
                    key, value = text.split(":", 1)
                    current[section][key.strip()] = float(value)
                elif text == "}" and current is not None and "orientation" in current and "position" in current:
                    name = current["name"]
                    if name in ("burger_cam", "camera_link", "base_link"):
                        self.latest[name] = current
                    current = None
                    section = None
        except Exception as exc:
            self.error = repr(exc)
        finally:
            if self.proc.poll() is None:
                self.proc.terminate()

    def close(self):
        self.stop.set()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class Probe(Node):
    def __init__(self):
        super().__init__("visual_sensor_probe")
        self.image = None
        self.info = None
        self.odom = None
        self.scan = None
        self.rows = []
        self.images = []
        self.image_dir = OUT / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.create_subscription(Image, "/camera/image_raw", self.on_image, qos_profile_sensor_data)
        self.create_subscription(CameraInfo, "/camera/camera_info", self.on_info, qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos_profile_sensor_data)
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        self.cmd = None
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def on_image(self, msg):
        self.image = msg
        if len(self.images) >= 40:
            return
        raw = bytes(msg.data)
        expected = msg.height * msg.step
        if len(raw) < expected or msg.height == 0 or msg.width == 0:
            return
        mode = {"rgb8": "RGB", "bgr8": "RGB"}.get(msg.encoding)
        if mode is None:
            return
        image = PilImage.frombytes("RGB", (msg.width, msg.height), raw[:expected])
        if msg.encoding == "bgr8":
            image = PilImage.merge("RGB", image.split()[::-1])
        name = f"{len(self.images):02d}.png"
        image.save(self.image_dir / name)
        self.images.append({
            "file": f"images/{name}", "stamp": stamp_dict(msg.header.stamp),
            "recv_unix": time.time(), "frame_id": msg.header.frame_id,
            "encoding": msg.encoding, "width": msg.width, "height": msg.height, "step": msg.step,
        })

    def on_info(self, msg):
        self.info = msg

    def on_odom(self, msg):
        self.odom = msg

    def on_scan(self, msg):
        self.scan = msg

    def snapshot(self, pose, phase):
        now = time.time()
        row = {"phase": phase, "recv_unix": now}
        if self.odom is not None:
            q = self.odom.pose.pose.orientation
            p = self.odom.pose.pose.position
            row["odom"] = {
                "stamp": stamp_dict(self.odom.header.stamp), "frame_id": self.odom.header.frame_id,
                "child_frame_id": self.odom.child_frame_id,
                "position": {"x": p.x, "y": p.y, "z": p.z},
                "orientation": {"x": q.x, "y": q.y, "z": q.z, "w": q.w},
                "zyx": yaw_pitch_roll(q.x, q.y, q.z, q.w),
                "twist": {"linear_x": self.odom.twist.twist.linear.x, "angular_z": self.odom.twist.twist.angular.z},
            }
        if pose:
            row["gazebo_dynamic_pose"] = pose
            q = pose.get("orientation", {})
            if all(k in q for k in "xyzw"):
                row["gazebo_model_zyx"] = yaw_pitch_roll(q["x"], q["y"], q["z"], q["w"])
        if self.scan is not None:
            vals = [v for v in self.scan.ranges if math.isfinite(v) and v > self.scan.range_min]
            row["scan"] = {
                "stamp": stamp_dict(self.scan.header.stamp), "frame_id": self.scan.header.frame_id,
                "min_m": min(vals) if vals else None, "valid": len(vals),
            }
        if self.image is not None:
            row["image_stamp"] = stamp_dict(self.image.header.stamp)
            row["image_frame_id"] = self.image.header.frame_id
        self.rows.append(row)
        return row

    def publish(self, angular_z):
        if self.cmd is None:
            self.cmd = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.angular.z = float(angular_z)
        self.cmd.publish(msg)

    def zeros(self, repeats=20):
        for _ in range(repeats):
            self.publish(0.0)
            time.sleep(0.05)


def copy_sources():
    dest = OUT / "config_snapshot"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in SOURCES:
        target = dest / src.name
        shutil.copy2(src, target)
        copied.append({"source": str(src), "copy": f"config_snapshot/{src.name}",
                       "bytes": src.stat().st_size, "sha256": sha256(src)})
    return copied


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    copied = copy_sources()
    (OUT / "config_sources.json").write_text(json.dumps({
        "copied": copied,
        "chain": [
            "gazebo_sim/launch_tb3_house_at_run.sh sets TURTLEBOT3_MODEL=burger_cam and calls turtlebot3_house.launch.py",
            "turtlebot3_house.launch.py includes gz_sim with worlds/turtlebot3_house.world and spawn_turtlebot3.launch.py",
            "spawn uses models/turtlebot3_<TURTLEBOT3_MODEL>/model.sdf and params/turtlebot3_<TURTLEBOT3_MODEL>_bridge.yaml",
            "robot_state_publisher reads urdf/turtlebot3_<TURTLEBOT3_MODEL>.urdf",
            "This launch log printed urdf_file_name turtlebot3_burger_cam.urdf and created entity successfully",
        ],
        "gz_sim_resource_path_on_server": "/opt/ros/jazzy/share/turtlebot3_gazebo/models",
        "world_name_in_world_file": "default",
        "spawn_entity_name": "burger_cam",
    }, indent=2), encoding="utf-8")
    pose_watch = PoseWatch()
    pose_watch.start()
    rclpy.init()
    node = Probe()
    started = time.time()
    while time.time() - started < 12 and (node.image is None or node.odom is None or "burger_cam" not in pose_watch.latest):
        rclpy.spin_once(node, timeout_sec=0.1)
    stationary_until = time.time() + 3
    while time.time() < stationary_until and len(node.images) < 30:
        rclpy.spin_once(node, timeout_sec=0.05)
        if int((time.time() - started) * 5) % 2 == 0:
            node.snapshot(pose_watch.latest.get("burger_cam"), "stationary")
    info = {}
    if node.info is not None:
        msg = node.info
        info = {
            "stamp": stamp_dict(msg.header.stamp), "frame_id": msg.header.frame_id,
            "width": msg.width, "height": msg.height, "distortion_model": msg.distortion_model,
            "d": list(msg.d), "k": list(msg.k), "r": list(msg.r), "p": list(msg.p),
            "binning_x": msg.binning_x, "binning_y": msg.binning_y,
        }
    (OUT / "camera_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    frames = {}
    for target in ("base_link", "camera_link", "camera_rgb_frame", "camera_rgb_optical_frame", "base_scan"):
        try:
            tf = node.tf_buffer.lookup_transform("base_footprint", target, rclpy.time.Time())
            t, q = tf.transform.translation, tf.transform.rotation
            frames[target] = {
                "parent": "base_footprint", "stamp": stamp_dict(tf.header.stamp),
                "translation": {"x": t.x, "y": t.y, "z": t.z},
                "rotation": {"x": q.x, "y": q.y, "z": q.z, "w": q.w},
                "zyx": yaw_pitch_roll(q.x, q.y, q.z, q.w),
            }
        except tf2_ros.TransformException as exc:
            frames[target] = {"error": str(exc)}
    try:
        frames["all_frames_yaml"] = node.tf_buffer.all_frames_as_yaml()
    except Exception as exc:
        frames["all_frames_yaml_error"] = repr(exc)
    (OUT / "tf_static.json").write_text(json.dumps(frames, indent=2), encoding="utf-8")
    before = node.snapshot(pose_watch.latest.get("burger_cam"), "before_probe")
    scan_min = (before.get("scan") or {}).get("min_m")
    pose_ok = "burger_cam" in pose_watch.latest and pose_watch.latest["burger_cam"].get("stamp", {}).get("sec", 0) > 0
    reason = ""
    probe = {"executed": False}
    publishers = subprocess.run(["ros2", "topic", "info", "/cmd_vel"], capture_output=True, text=True).stdout
    if "Publisher count: 0" not in publishers:
        reason = "cmd_vel already has a publisher; probe skipped"
    elif not pose_ok:
        reason = "no timed Gazebo burger_cam pose; probe skipped"
    elif node.image is None or node.scan is None or node.odom is None:
        reason = "image, scan, or odom missing; probe skipped"
    elif scan_min is None or scan_min <= 0.3:
        reason = f"scan clearance {scan_min} is not greater than 0.3 m; probe skipped"
    else:
        probe["executed"] = True
        start_pose = pose_watch.latest["burger_cam"]
        start_zyx = yaw_pitch_roll(*(start_pose["orientation"][k] for k in "xyzw"))
        start_clock = node.get_clock().now().nanoseconds
        wall0 = time.time()
        try:
            while True:
                node.publish(0.15)
                rclpy.spin_once(node, timeout_sec=0.02)
                current = pose_watch.latest.get("burger_cam", start_pose)
                current_zyx = yaw_pitch_roll(*(current["orientation"][k] for k in "xyzw"))
                delta = (current_zyx["yaw_rad"] - start_zyx["yaw_rad"] + math.pi) % (2 * math.pi) - math.pi
                sim_s = (node.get_clock().now().nanoseconds - start_clock) / 1e9
                node.snapshot(current, "probe")
                if abs(delta) >= math.radians(12) or sim_s >= 1.5 or time.time() - wall0 >= 30:
                    probe.update({"stop_delta_yaw_rad": delta, "stop_sim_s": sim_s, "stop_wall_s": time.time() - wall0})
                    break
                vals = []
                if node.scan is not None:
                    vals = [v for v in node.scan.ranges if math.isfinite(v) and v > node.scan.range_min]
                if vals and min(vals) < 0.15:
                    probe["stop"] = "scan_near"
                    break
                if time.time() - current.get("recv_unix", 0) > 2:
                    probe["stop"] = "pose_stale"
                    break
        finally:
            node.zeros()
        time.sleep(0.3)
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.05)
        after = node.snapshot(pose_watch.latest.get("burger_cam"), "after_probe")
        end_zyx = after.get("gazebo_model_zyx", {})
        odom_zyx = (after.get("odom") or {}).get("zyx", {})
        before_odom = (before.get("odom") or {}).get("zyx", {})
        probe["comparison"] = {
            "convention": "delta uses atan2 ZYX yaw; positive is the right-handed rotation about that source z axis",
            "gazebo_model_yaw_start": start_zyx, "gazebo_model_yaw_end": end_zyx,
            "gazebo_yaw_delta_rad": (end_zyx.get("yaw_rad", 0) - start_zyx["yaw_rad"] + math.pi) % (2 * math.pi) - math.pi,
            "odom_yaw_start": before_odom, "odom_yaw_end": odom_zyx,
            "odom_yaw_delta_rad": (odom_zyx.get("yaw_rad", 0) - before_odom.get("yaw_rad", 0) + math.pi) % (2 * math.pi) - math.pi,
            "camera_tf_is_static_from_urdf": True,
        }
    probe["skip_reason"] = reason
    probe["pose_watch_error"] = pose_watch.error
    probe["camera_link_pose_same_message_family"] = pose_watch.latest.get("camera_link")
    (OUT / "probe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
    (OUT / "sync.jsonl").write_text("".join(json.dumps(row) + "\n" for row in node.rows), encoding="utf-8")
    (OUT / "images_index.json").write_text(json.dumps(node.images, indent=2), encoding="utf-8")
    node.zeros()
    pose_watch.close()
    node.destroy_node()
    rclpy.shutdown()
    print(json.dumps({"images": len(node.images), "probe": probe["executed"], "reason": reason}, indent=2))


if __name__ == "__main__":
    main()
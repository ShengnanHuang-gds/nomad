#!/usr/bin/env python3
"""One in-place turn after the stationary capture. Checks other publishers first."""

import json
import math
import subprocess
import time
from pathlib import Path

import rclpy

from collect_sensor_probe import OUT, PoseWatch, Probe, yaw_pitch_roll

def main():
    info = subprocess.run(["ros2", "topic", "info", "/cmd_vel"], capture_output=True, text=True).stdout
    (OUT / "cmd_vel_info_before_probe.txt").write_text(info, encoding="utf-8")
    if "Publisher count: 0" not in info:
        (OUT / "probe.json").write_text(json.dumps({
            "executed": False,
            "skip_reason": "another cmd_vel publisher exists; this process had not published yet",
            "topic_info": info,
        }, indent=2), encoding="utf-8")
        print("skipped other publisher")
        return
    pose_watch = PoseWatch()
    pose_watch.start()
    rclpy.init()
    node = Probe()
    deadline = time.time() + 8
    while time.time() < deadline and (node.scan is None or "burger_cam" not in pose_watch.latest):
        rclpy.spin_once(node, timeout_sec=0.1)
    before = node.snapshot(pose_watch.latest.get("burger_cam"), "before_probe")
    scan_min = (before.get("scan") or {}).get("min_m")
    pose = pose_watch.latest.get("burger_cam")
    probe = {"executed": False, "publisher_check": "Publisher count: 0 before this process published"}
    if pose is None or pose.get("stamp", {}).get("sec", 0) <= 0:
        probe["skip_reason"] = "no timed Gazebo burger_cam pose"
    elif scan_min is None or scan_min <= 0.3:
        probe["skip_reason"] = f"scan clearance {scan_min} is not greater than 0.3 m"
    else:
        probe["executed"] = True
        start_zyx = yaw_pitch_roll(*(pose["orientation"][k] for k in "xyzw"))
        start_clock = node.get_clock().now().nanoseconds
        wall0 = time.time()
        try:
            while True:
                node.publish(0.15)
                rclpy.spin_once(node, timeout_sec=0.02)
                current = pose_watch.latest.get("burger_cam", pose)
                current_zyx = yaw_pitch_roll(*(current["orientation"][k] for k in "xyzw"))
                delta = (current_zyx["yaw_rad"] - start_zyx["yaw_rad"] + math.pi) % (2 * math.pi) - math.pi
                sim_s = (node.get_clock().now().nanoseconds - start_clock) / 1e9
                node.snapshot(current, "probe")
                if abs(delta) >= math.radians(12) or sim_s >= 1.5 or time.time() - wall0 >= 30:
                    probe.update({"stop_delta_yaw_rad": delta, "stop_sim_s": sim_s, "stop_wall_s": time.time() - wall0})
                    break
                if time.time() - current.get("recv_unix", 0) > 2:
                    probe["stop"] = "pose_stale"
                    break
        finally:
            node.zeros()
        for _ in range(15):
            rclpy.spin_once(node, timeout_sec=0.05)
        after = node.snapshot(pose_watch.latest.get("burger_cam"), "after_probe")
        end_zyx = after.get("gazebo_model_zyx", {})
        odom_end = (after.get("odom") or {}).get("zyx", {})
        odom_start = (before.get("odom") or {}).get("zyx", {})
        probe["comparison"] = {
            "convention": "ZYX yaw from quaternion; positive is right-handed about that source z axis. Absolute zeros are not compared.",
            "gazebo_model_start": {**start_zyx, "position": pose.get("position"), "stamp": pose.get("stamp")},
            "gazebo_model_end": {**end_zyx, "position": (after.get("gazebo_dynamic_pose") or {}).get("position"),
                                 "stamp": (after.get("gazebo_dynamic_pose") or {}).get("stamp")},
            "gazebo_yaw_delta_rad": (end_zyx.get("yaw_rad", 0) - start_zyx["yaw_rad"] + math.pi) % (2 * math.pi) - math.pi,
            "odom_start": odom_start, "odom_end": odom_end,
            "odom_yaw_delta_rad": (odom_end.get("yaw_rad", 0) - odom_start.get("yaw_rad", 0) + math.pi) % (2 * math.pi) - math.pi,
            "scan_min_before_m": scan_min,
        }
        probe["camera_link_raw"] = pose_watch.latest.get("camera_link")
    if "skip_reason" in probe:
        pass
    (OUT / "probe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
    with (OUT / "sync.jsonl").open("a", encoding="utf-8") as handle:
        for row in node.rows:
            handle.write(json.dumps(row) + "\n")
    index_path = OUT / "images_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index.extend(node.images)
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    node.zeros()
    pose_watch.close()
    node.destroy_node()
    rclpy.shutdown()
    print(json.dumps({"executed": probe["executed"], "reason": probe.get("skip_reason", ""), "keys": list(probe)}, indent=2))

if __name__ == "__main__":
    main()
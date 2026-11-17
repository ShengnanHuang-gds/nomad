#!/usr/bin/env python3
"""Quick checks before hold-out eval (run via run_holdout*.sh or source nomad_wsl_env)."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

from gz_pose_utils import list_gazebo_models

REQUIRED_TOPICS = ("/odom", "/camera/image_raw")


def ros_topics_cli(timeout: float = 8.0) -> set[str]:
    """ros2 topic list — needs ROS in PATH (source nomad_wsl_env or setup.bash)."""
    ros_setup = os.environ.get(
        "ROS_SETUP",
        "/opt/ros/jazzy/setup.bash",
    )
    cmd = f'source "{ros_setup}" 2>/dev/null; ros2 topic list'
    try:
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return set()
    return {ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()}


def ros_topics_rclpy(wait_s: float = 12.0) -> set[str]:
    """Discovery via rclpy (same path as verify_06 / nomad_navigate)."""
    import rclpy
    from rclpy.node import Node

    class _Probe(Node):
        def __init__(self) -> None:
            super().__init__("sim_prereq_probe")

    rclpy.init()
    node = _Probe()
    seen: set[str] = set()
    t0 = time.time()
    try:
        while time.time() - t0 < wait_s:
            for name, _ in node.get_topic_names_and_types():
                seen.add(name)
            if all(t in seen for t in REQUIRED_TOPICS):
                break
            rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return seen


def wait_sim_topics(wait_s: float = 12.0) -> tuple[set[str], str]:
    topics = ros_topics_rclpy(wait_s=wait_s)
    if all(t in topics for t in REQUIRED_TOPICS):
        return topics, "rclpy"
    extra = ros_topics_cli()
    topics |= extra
    if all(t in topics for t in REQUIRED_TOPICS):
        return topics, "ros2"
    return topics, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--need-gpu", action="store_true")
    args = parser.parse_args()
    ok = True
    if not shutil.which("ros2") and not shutil.which("bash"):
        print("FAIL: ros2 not in PATH — run: source gazebo_sim/nomad_wsl_env.sh")
        return 1
    topics, via = wait_sim_topics()
    if all(t in topics for t in REQUIRED_TOPICS):
        print(
            f"OK sim: /odom + /camera/image_raw ({via or 'topics'}) "
            "(Terminal 1: launch_tb3_house_at_run.sh)"
        )
    else:
        missing = [t for t in REQUIRED_TOPICS if t not in topics]
        print(
            f"FAIL: Gazebo not ready — missing {missing} (seen {len(topics)} topics). "
            "Terminal 1 keep running: bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06. "
            "Then: source gazebo_sim/nomad_wsl_env.sh && bash gazebo_sim/run_holdout_06_b40.sh"
        )
        ok = False
    if not shutil.which("gz"):
        print("WARN: gz CLI not in PATH (teleport optional; spawn-at-launch is OK)")
    else:
        models = list_gazebo_models()
        if models:
            rob = [m for m in models if "turtle" in m.lower() or "burger" in m.lower()]
            print(f"OK gz models: {rob or models[:3]}")
        elif ok:
            print("WARN: gz model -l empty (OK if ROS topics above are fine)")
    if args.need_gpu:
        try:
            import torch

            if not torch.cuda.is_available():
                print("WARN: torch.cuda.is_available() is False")
        except ImportError:
            print("FAIL: torch not installed in this python")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
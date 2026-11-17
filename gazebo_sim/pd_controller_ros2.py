#!/usr/bin/env python3
"""ROS2 PD controller: /nomad/waypoint -> /cmd_vel (TurtleBot3 Gazebo)."""

from __future__ import annotations

import argparse
import math
import time

import numpy as np
import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool, Float32MultiArray
from csv_log import CsvLog

MAX_V = 0.2
MAX_W = 1.5
DT = 0.25  # 1 / frame_rate (4 Hz); must match navigate node
RATE_HZ = 9
EPS = 1e-8
WAYPOINT_TIMEOUT = 1.0


def clip_angle(theta: float) -> float:
    return (theta + math.pi) % (2 * math.pi) - math.pi


def pd_controller(waypoint: np.ndarray) -> tuple[float, float]:
    assert len(waypoint) in (2, 4)
    if len(waypoint) == 2:
        dx, dy = float(waypoint[0]), float(waypoint[1])
    else:
        dx, dy, hx, hy = [float(x) for x in waypoint[:4]]
        if abs(dx) < EPS and abs(dy) < EPS:
            w = clip_angle(math.atan2(hy, hx)) / DT
            return 0.0, float(np.clip(w, -MAX_W, MAX_W))
    if abs(dx) < EPS and abs(dy) < EPS:
        return 0.0, 0.0
    if abs(dx) < EPS:
        w = np.sign(dy) * math.pi / (2 * DT)
        return 0.0, float(np.clip(w, -MAX_W, MAX_W))
    v = dx / DT
    w = math.atan(dy / dx) / DT
    v = float(np.clip(v, 0.0, MAX_V))
    w = float(np.clip(w, -MAX_W, MAX_W))
    return v, w


class PdController(Node):
    def __init__(self, log_csv=""):
        super().__init__("nomad_pd_controller")
        self._waypoint: np.ndarray | None = None
        self._waypoint_time = 0.0
        self._waypoint_mono = None
        self._waypoint_seq = 0
        self._command_log = CsvLog(log_csv)
        self._reached = False
        self.create_subscription(
            Float32MultiArray, "/nomad/waypoint", self._on_waypoint, 10
        )
        self.create_subscription(
            Bool, "/nomad/reached_goal", self._on_reached, 10
        )
        self._pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.create_timer(1.0 / RATE_HZ, self._tick)
        self.get_logger().info("nomad PD: waiting for /nomad/waypoint")

    def _on_waypoint(self, msg: Float32MultiArray):
        if not msg.data:
            return
        self._waypoint = np.asarray(msg.data, dtype=np.float64)
        self._waypoint_time = time.time()
        self._waypoint_mono = time.monotonic()
        self._waypoint_seq += 1
        self.get_logger().info(
            f"waypoint len={len(self._waypoint)} dx={msg.data[0]:.4f} dy={msg.data[1]:.4f}"
        )

    def _on_reached(self, msg: Bool):
        if msg.data:
            self._reached = True

    def _publish_command(self, msg, reason):
        self._pub.publish(msg)
        wp = self._waypoint
        self._command_log.write({
            "t": time.time(),
            "cmd_stamp_ros_s": msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            "cmd_v": float(msg.twist.linear.x),
            "cmd_w": float(msg.twist.angular.z),
            "reason": reason,
            "waypoint_seq": self._waypoint_seq,
            "wp_received_t": self._waypoint_time if wp is not None else "",
            "wp_age_s": time.monotonic() - self._waypoint_mono
            if self._waypoint_mono is not None else "",
            "wp_dx": float(wp[0]) if wp is not None else "",
            "wp_dy": float(wp[1]) if wp is not None else "",
            "wp_hx": float(wp[2]) if wp is not None and len(wp) == 4 else "",
            "wp_hy": float(wp[3]) if wp is not None and len(wp) == 4 else "",
        })

    def _tick(self):
        stamp = self.get_clock().now().to_msg()
        stop = TwistStamped()
        stop.header.stamp = stamp
        stop.header.frame_id = "base_link"
        if self._reached:
            self._publish_command(stop, "reached_goal")
            self.get_logger().info("reached goal — zero cmd_vel")
            return
        if self._waypoint is None:
            self._publish_command(stop, "waiting_waypoint")
            return
        if time.monotonic() - self._waypoint_mono > WAYPOINT_TIMEOUT:
            self._publish_command(stop, "waypoint_timeout")
            return
        v, w = pd_controller(self._waypoint)
        cmd = TwistStamped()
        cmd.header.stamp = stamp
        cmd.header.frame_id = "base_link"
        cmd.twist.linear.x = v
        cmd.twist.angular.z = w
        self._publish_command(cmd, "tracking")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-csv", default="", help="stream every published cmd_vel and its input waypoint")
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = PdController(log_csv=args.log_csv)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    try:
        stop = TwistStamped()
        stop.header.frame_id = "base_link"
        stop.header.stamp = node.get_clock().now().to_msg()
        node._publish_command(stop, "shutdown")
    except Exception:
        pass
    node._command_log.close()
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ROS2 PD controller: /nomad/waypoint -> /cmd_vel (TurtleBot3 Gazebo)."""

from __future__ import annotations

import math
import time

import numpy as np
import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool, Float32MultiArray

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
    if abs(dx) < EPS:
        w = np.sign(dy) * math.pi / (2 * DT)
        return 0.0, float(np.clip(w, -MAX_W, MAX_W))
    v = dx / DT
    w = math.atan(dy / dx) / DT
    v = float(np.clip(v, 0.0, MAX_V))
    w = float(np.clip(w, -MAX_W, MAX_W))
    return v, w


class PdController(Node):
    def __init__(self):
        super().__init__("nomad_pd_controller")
        self._waypoint: np.ndarray | None = None
        self._waypoint_time = 0.0
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
        self.get_logger().info(
            f"waypoint len={len(self._waypoint)} dx={msg.data[0]:.4f} dy={msg.data[1]:.4f}"
        )

    def _on_reached(self, msg: Bool):
        if msg.data:
            self._reached = True

    def _tick(self):
        stamp = self.get_clock().now().to_msg()
        stop = TwistStamped()
        stop.header.stamp = stamp
        stop.header.frame_id = "base_link"
        if self._reached:
            self._pub.publish(stop)
            self.get_logger().info("reached goal — zero cmd_vel")
            return
        if self._waypoint is None:
            self._pub.publish(stop)
            return
        if time.time() - self._waypoint_time > WAYPOINT_TIMEOUT:
            self._pub.publish(stop)
            return
        v, w = pd_controller(self._waypoint)
        cmd = TwistStamped()
        cmd.header.stamp = stamp
        cmd.header.frame_id = "base_link"
        cmd.twist.linear.x = v
        cmd.twist.angular.z = w
        self._pub.publish(cmd)


def main():
    rclpy.init()
    node = PdController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    try:
        stop = TwistStamped()
        stop.header.frame_id = "base_link"
        stop.header.stamp = node.get_clock().now().to_msg()
        node._pub.publish(stop)
    except Exception:
        pass
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
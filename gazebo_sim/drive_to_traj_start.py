#!/usr/bin/env python3
"""Drive burger_cam to target (x,y,yaw) using /odom and TwistStamped /cmd_vel."""

from __future__ import annotations

import argparse
import math
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node

MAX_V = 0.14
MAX_W = 0.35
GOAL_XY = 0.45
GOAL_YAW = 0.12


def yaw_from_quat(q) -> float:
    return math.atan2(
        2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
    )


class DriveToPose(Node):
    def __init__(self, tx: float, ty: float, tyaw: float, wall_s: float):
        super().__init__("drive_to_traj_start")
        self.tx, self.ty, self.tyaw = tx, ty, tyaw
        self.deadline = time.time() + wall_s
        self.xy: tuple[float, float] | None = None
        self.yaw = 0.0
        self._phase = "go_xy"
        self._pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.create_subscription(Odometry, "/odom", self._odom, 10)
        self.create_timer(0.1, self._tick)

    def _odom(self, msg: Odometry):
        p = msg.pose.pose.position
        self.xy = (float(p.x), float(p.y))
        self.yaw = yaw_from_quat(msg.pose.pose.orientation)

    def _stop(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        self._pub.publish(msg)

    def _tick(self):
        if self.xy is None:
            return
        if time.time() > self.deadline:
            self.get_logger().error("drive_to_pose timeout")
            self._stop()
            rclpy.shutdown()
            raise SystemExit(1)
        x, y = self.xy
        dx, dy = self.tx - x, self.ty - y
        dist = math.hypot(dx, dy)
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"
        if self._phase == "go_xy":
            if dist <= GOAL_XY:
                self._phase = "align_yaw"
                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = 0.0
            else:
                heading = math.atan2(dy, dx)
                err = (heading - self.yaw + math.pi) % (2 * math.pi) - math.pi
                cmd.twist.linear.x = MAX_V * max(0.2, 1.0 - abs(err))
                cmd.twist.angular.z = max(-MAX_W, min(MAX_W, 2.2 * err))
        else:
            err = (self.tyaw - self.yaw + math.pi) % (2 * math.pi) - math.pi
            if abs(err) <= GOAL_YAW:
                self._stop()
                self.get_logger().info(
                    f"drive done at ({x:.3f},{y:.3f}) yaw={self.yaw:.3f}"
                )
                rclpy.shutdown()
                return
            cmd.twist.linear.x = 0.0
            cmd.twist.angular.z = max(-MAX_W, min(MAX_W, 2.0 * err))
        self._pub.publish(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--yaw", type=float, required=True)
    parser.add_argument("--wall-s", type=float, default=180.0)
    args = parser.parse_args()
    rclpy.init()
    node = DriveToPose(args.x, args.y, args.yaw, args.wall_s)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node._stop()
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""One short in-place sim turn timed by /clock. Publishes zero on every exit."""

import math
import subprocess
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GzNode

ENTITY_ID = 271
MODEL = "burger_cam"


def yaw_of(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


class Spin(Node):
    def __init__(self, angular):
        super().__init__("nomad_align_spin", parameter_overrides=[
            Parameter("use_sim_time", Parameter.Type.BOOL, True)])
        self.angular = angular
        self.scan_min = None
        self.clock_ns = None
        self.pose = None
        self.pose_wall = None
        self.cmd = None
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        from rosgraph_msgs.msg import Clock
        self.create_subscription(Clock, "/clock", self.on_clock, qos_profile_sensor_data)
        self.gz = GzNode()
        if not self.gz.subscribe(Pose_V, "/world/default/dynamic_pose/info", self.on_pose):
            raise RuntimeError("could not subscribe to Gazebo model pose")

    def on_scan(self, msg):
        vals = [v for v in msg.ranges if math.isfinite(v) and v > msg.range_min]
        if vals:
            self.scan_min = min(vals)

    def on_clock(self, msg):
        self.clock_ns = int(msg.clock.sec) * 1_000_000_000 + int(msg.clock.nanosec)

    def on_pose(self, msg):
        for pose in msg.pose:
            if pose.id == ENTITY_ID and pose.name == MODEL:
                self.pose = pose
                self.pose_wall = time.monotonic()

    def publish(self, angular):
        if self.cmd is None:
            self.cmd = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        msg = TwistStamped()
        if self.clock_ns is not None:
            msg.header.stamp.sec = self.clock_ns // 1_000_000_000
            msg.header.stamp.nanosec = self.clock_ns % 1_000_000_000
        msg.twist.angular.z = float(angular)
        self.cmd.publish(msg)

    def zeros(self):
        for _ in range(20):
            self.publish(0.0)
            rclpy.spin_once(self, timeout_sec=0.02)

    def wait_until(self, start_ns, sim_s, wall_deadline):
        while rclpy.ok() and time.monotonic() < wall_deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            if self.clock_ns is None or self.pose is None:
                continue
            if self.pose_wall is not None and time.monotonic() - self.pose_wall > 2:
                return "pose_stale"
            if self.clock_ns - start_ns >= int(sim_s * 1_000_000_000):
                return "ok"
        return "wall_timeout"


def main():
    angular = float(sys.argv[1])
    if not 0 < abs(angular) <= 0.12:
        raise SystemExit("angular speed must be within 0.12 rad/s")
    info = subprocess.run(["ros2", "topic", "info", "/cmd_vel"], capture_output=True, text=True).stdout
    if "Publisher count: 0" not in info:
        raise SystemExit("another cmd_vel publisher is present")
    rclpy.init()
    node = Spin(angular)
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and (node.scan_min is None or node.clock_ns is None or node.pose is None):
            rclpy.spin_once(node, timeout_sec=0.1)
        print(f"scan_min_m={node.scan_min} clock_ns={node.clock_ns}", flush=True)
        if node.scan_min is None or node.scan_min <= 0.3 or node.clock_ns is None or node.pose is None:
            raise SystemExit("preconditions failed")
        wall_deadline = time.monotonic() + 30
        start_ns = node.clock_ns
        start_yaw = yaw_of(node.pose.orientation)
        node.publish(0.0)
        status = node.wait_until(start_ns, 0.5, wall_deadline)
        if status != "ok":
            print(f"pre_still={status}", flush=True)
            raise SystemExit(status)
        motion_ns = node.clock_ns
        reached = False
        while rclpy.ok() and time.monotonic() < wall_deadline:
            node.publish(angular)
            rclpy.spin_once(node, timeout_sec=0.02)
            if node.pose_wall is None or time.monotonic() - node.pose_wall > 2:
                print("pose_stale", flush=True)
                break
            delta = (yaw_of(node.pose.orientation) - start_yaw + math.pi) % (2 * math.pi) - math.pi
            sim_motion = (node.clock_ns - motion_ns) / 1e9
            if abs(delta) >= math.radians(10) or sim_motion >= 2.0:
                reached = abs(delta) >= math.radians(8)
                print(f"motion_delta_deg={math.degrees(delta):.3f} motion_sim_s={sim_motion:.3f}", flush=True)
                break
        else:
            print("motion_wall_timeout", flush=True)
        post_ns = node.clock_ns
        node.publish(0.0)
        node.wait_until(post_ns, 0.5, wall_deadline)
        delta = (yaw_of(node.pose.orientation) - start_yaw + math.pi) % (2 * math.pi) - math.pi
        print(f"final_delta_deg={math.degrees(delta):.3f}", flush=True)
        if not reached:
            raise SystemExit("angle below about 8 degrees")
    finally:
        node.zeros()
        node.gz.unsubscribe("/world/default/dynamic_pose/info")
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
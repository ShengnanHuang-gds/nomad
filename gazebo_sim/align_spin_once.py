#!/usr/bin/env python3
"""Bounded in-place Gazebo diagnostic turn for sensor capture."""

import argparse
import math
from pathlib import Path
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rosgraph_msgs.msg import Clock
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.twist_pb2 import Twist
from gz.transport13 import Node as GzNode

CMD = "/cmd_vel"
RESPONSE_WINDOW_NS = 1_000_000_000


def yaw_of(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


class Spin(Node):
    def __init__(self, world, model, entity_id):
        super().__init__("nomad_align_spin")
        self.scan = None
        self.clock = None
        self.pose = None
        self.odom = None
        self.gz_turn = None
        self.cmd = None
        self.clock_reversed = False
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Clock, "/clock", self.on_clock, qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos_profile_sensor_data)
        self.gz = GzNode()
        self.pose_topic = f"/world/{world}/dynamic_pose/info"

        def on_pose(msg):
            stamp = msg.header.stamp
            for pose in msg.pose:
                if pose.id == entity_id and pose.name == model:
                    ns = stamp.sec * 10**9 + stamp.nsec
                    if ns > 0 and (self.pose is None or ns != self.pose[0]):
                        self.pose = (ns, time.monotonic(), yaw_of(pose.orientation))
                    break

        if not self.gz.subscribe(Pose_V, self.pose_topic, on_pose):
            raise RuntimeError(f"could not subscribe to {self.pose_topic}")
        if not self.gz.subscribe(Twist, CMD, self.on_gz_command):
            raise RuntimeError(f"could not observe Gazebo {CMD}")

    def on_odom(self, msg):
        stamp = msg.header.stamp
        ns = stamp.sec * 10**9 + stamp.nanosec
        if ns > 0 and (self.odom is None or ns > self.odom[0]):
            self.odom = (ns, time.monotonic(), yaw_of(msg.pose.pose.orientation))

    def on_gz_command(self, msg):
        if abs(msg.angular.z) > 1e-6:
            self.gz_turn = (time.monotonic(), msg.angular.z)

    def on_scan(self, msg):
        vals = [v for v in msg.ranges if math.isfinite(v) and msg.range_min <= v <= msg.range_max]
        stamp = msg.header.stamp
        ns = stamp.sec * 10**9 + stamp.nanosec
        if ns > 0 and (self.scan is None or ns != self.scan[0]):
            self.scan = (ns, time.monotonic(), min(vals, default=0.0))

    def on_clock(self, msg):
        clock = msg.clock
        ns = clock.sec * 10**9 + clock.nanosec
        if self.clock is not None and ns < self.clock[0]:
            self.clock_reversed = True
        if ns > 0 and (self.clock is None or ns != self.clock[0]):
            self.clock = (ns, time.monotonic())

    def check(self):
        now = time.monotonic()
        if self.clock_reversed:
            raise RuntimeError("sim clock reversed")
        for name, stream in (("scan", self.scan), ("clock", self.clock),
                             ("model pose", self.pose), ("wheel odometry", self.odom)):
            if stream is None or now - stream[1] > 2:
                raise RuntimeError(f"{name} missing or stale")
        if any(abs(stream[0] - self.clock[0]) > 350_000_000 for stream in (self.scan, self.pose, self.odom)):
            raise RuntimeError("scan, model pose or wheel odometry is too far from /clock")
        if self.scan[2] <= 0.3:
            raise RuntimeError(f"scan clearance <= 0.3 m: {self.scan[2]:.3f}")
        owners = self.get_publishers_info_by_topic(CMD)
        own_name = self.get_name()
        own_count = sum(p.node_name == own_name and p.node_namespace == self.get_namespace() for p in owners)
        if len(owners) - own_count > 0 or own_count > (1 if self.cmd is not None else 0):
            raise RuntimeError("another cmd_vel publisher is present")
        if not any(s.node_name == "ros_gz_bridge" for s in self.get_subscriptions_info_by_topic(CMD)):
            raise RuntimeError("ros_gz_bridge cmd_vel subscriber is missing")

    def publish(self, angular):
        msg = TwistStamped()
        msg.header.stamp.sec, msg.header.stamp.nanosec = divmod(self.clock[0], 10**9)
        msg.header.frame_id = "base_link"
        msg.twist.angular.z = angular
        self.cmd.publish(msg)

    def hold(self, sim_seconds, deadline):
        start = self.clock[0]
        while self.clock[0] - start < sim_seconds * 10**9:
            self.tick(0.0, deadline)

    def tick(self, angular, deadline):
        if not rclpy.ok() or time.monotonic() >= deadline:
            raise RuntimeError("host timeout or ROS shutdown")
        self.check()
        if angular and not self.cmd.get_subscription_count():
            raise RuntimeError("ROS velocity publisher has no QoS-matched subscriber")
        self.publish(angular)
        rclpy.spin_once(self, timeout_sec=0.02)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("angular", type=float, help="signed angular speed in rad/s")
    parser.add_argument("--entity-id", type=int, required=True, help="Gazebo model entity ID")
    parser.add_argument("--world", default="default")
    parser.add_argument("--model", default="burger_cam")
    parser.add_argument("--target-deg", type=float, default=10.0)
    parser.add_argument("--wall-seconds", type=float, default=30.0)
    parser.add_argument("--wheel-state-log", type=Path,
                        help="save Harmonic ECS wheel targets and measured velocities during a short probe")
    args = parser.parse_args()
    if (args.entity_id <= 0 or not 0 < abs(args.angular) <= 0.12
            or not 8 <= args.target_deg <= 90 or not 0 < args.wall_seconds <= 210):
        parser.error("use a positive ID, angular speed within ±0.12 rad/s and nonzero, "
                     "target in [8, 90] deg, wall seconds in (0, 210]")
    motion_limit = min(16.0, math.radians(args.target_deg) / abs(args.angular) + 0.5)

    trace = None
    trace_file = None
    motion_start = motion_stop = None
    if args.wheel_state_log and (args.model != "burger_cam" or args.target_deg > 10):
        parser.error("--wheel-state-log expects a burger_cam turn of at most 10 degrees")

    rclpy.init()
    node = Spin(args.world, args.model, args.entity_id)
    try:
        ready_until = time.monotonic() + 8
        while rclpy.ok() and time.monotonic() < ready_until:
            rclpy.spin_once(node, timeout_sec=0.1)
            if (node.clock and node.scan and node.pose and node.odom
                    and node.count_subscribers(CMD)):
                break
        node.check()
        if args.wheel_state_log:
            from gazebo_wheel_state import WheelStateTrace

            trace_file = args.wheel_state_log.open("x", encoding="utf-8", newline="")
            trace = WheelStateTrace(args.world, args.model, args.entity_id)
            trace.worker.start()
            state_deadline = time.monotonic() + 8
            while rclpy.ok() and time.monotonic() < state_deadline and not trace.ready.is_set():
                rclpy.spin_once(node, timeout_sec=0.05)
            if not trace.ready.is_set():
                raise RuntimeError("wheel state service unavailable; no turn was commanded")
            node.check()
        node.cmd = node.create_publisher(TwistStamped, CMD, 10)
        deadline = time.monotonic() + args.wall_seconds
        node.hold(0.5, deadline)
        start_ns, _, start_yaw = node.pose
        odom_start = node.odom[2]
        wall_start = time.monotonic()
        motion_start = node.clock[0]
        direction = math.copysign(1, args.angular)
        response_checked = False
        while True:
            pose_ns, _, yaw = node.pose
            delta = math.degrees(math.remainder(yaw - start_yaw, 2 * math.pi))
            if pose_ns < start_ns or delta * direction < -2:
                raise RuntimeError(f"rotation/pose inconsistent with command: {delta:.2f} deg")
            sim_seconds = (node.clock[0] - motion_start) / 1e9
            if not response_checked and node.clock[0] - motion_start >= RESPONSE_WINDOW_NS:
                echo = node.gz_turn
                if echo is None or echo[0] < wall_start or not math.isclose(echo[1], args.angular, abs_tol=1e-6):
                    raise RuntimeError("ROS publisher matched, but the requested turn was not observed on Gazebo /cmd_vel")
                wheel_delta = math.degrees(math.remainder(node.odom[2] - odom_start, 2 * math.pi))
                print(f"gazebo_cmd_rad_s={echo[1]:+.3f} wheel_delta_deg={wheel_delta:+.3f} "
                      f"model_delta_deg={delta:+.3f}", flush=True)
                min_delta = min(0.5, math.degrees(abs(args.angular)) * 0.15)
                if delta * direction < min_delta:
                    if wheel_delta * direction < min_delta:
                        raise RuntimeError("Gazebo received velocity but wheels and body did not respond")
                    raise RuntimeError("wheel odometry turned but the Gazebo body did not respond")
                response_checked = True
            if delta * direction >= args.target_deg or sim_seconds >= motion_limit:
                break
            node.tick(args.angular, deadline)
        motion_stop = node.clock[0]
        node.publish(0.0)
        node.hold(0.5, deadline)
        final = math.degrees(math.remainder(node.pose[2] - start_yaw, 2 * math.pi))
        print(f"motion_start_ns={motion_start} motion_sim_s={sim_seconds:.3f} final_delta_deg={final:.3f}")
        if final * direction < args.target_deg - 2.0:
            raise SystemExit("target angle not reached")
    finally:
        if motion_start is not None and motion_stop is None:
            motion_stop = node.clock[0]
        try:
            if node.cmd is not None:
                for _ in range(20):
                    if not rclpy.ok():
                        break
                    node.publish(0.0)
                    time.sleep(0.04)
        finally:
            try:
                if trace is not None:
                    with trace_file:
                        trace.finish(trace_file, motion_start, motion_stop, args.angular)
            finally:
                node.gz.unsubscribe(node.pose_topic)
                node.gz.unsubscribe(CMD)
                node.destroy_node()
                rclpy.try_shutdown()


if __name__ == "__main__":
    main()

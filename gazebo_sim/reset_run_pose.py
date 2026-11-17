#!/usr/bin/env python3
"""Reset burger_cam to the first pose of a gazebo_sim house_run (gz set_pose)."""

from __future__ import annotations

import argparse
import math
import os
import pickle
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from record_house_multi import PLANS, set_pose  # noqa: E402
from gz_pose_utils import entities_from_ros_topics, list_gazebo_models  # noqa: E402


def pose_from_traj(run: str) -> tuple[float, float, float]:
    pkl = os.path.join(ROOT, run, "traj_data.pkl")
    if os.path.isfile(pkl):
        with open(pkl, "rb") as f:
            data = pickle.load(f)
        pos = data["position"][0]
        yaw = float(data["yaw"][0])
        return float(pos[0]), float(pos[1]), yaw
    if run in PLANS:
        x, y, yaw = PLANS[run]["pose"]
        return x, y, yaw
    raise SystemExit(f"no traj_data.pkl or PLANS entry for {run}")


def publish_stop_cmd_vel(duration_s: float = 2.5) -> None:
    """Silence any leftover /nomad or manual drive before spawn verify."""
    import rclpy
    from geometry_msgs.msg import TwistStamped
    from rclpy.node import Node

    class _Stop(Node):
        def __init__(self) -> None:
            super().__init__("reset_stop_cmd")
            self.pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)

        def zero(self) -> None:
            msg = TwistStamped()
            msg.header.frame_id = "base_link"
            msg.header.stamp = self.get_clock().now().to_msg()
            self.pub.publish(msg)

    rclpy.init()
    node = _Stop()
    t0 = __import__("time").time()
    try:
        while __import__("time").time() - t0 < duration_s:
            node.zero()
            rclpy.spin_once(node, timeout_sec=0.05)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def verify_odom_xy(
    expected_xy: tuple[float, float],
    max_err_m: float,
    settle_s: float = 3.0,
    *,
    fail_hint: str | None = None,
) -> tuple[float, float, float]:
    """Spin until /odom is close to expected (world vs odom frame must match recording)."""
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node

    class _WaitOdom(Node):
        def __init__(self):
            super().__init__("reset_verify_odom")
            self.xy: tuple[float, float] | None = None
            self.yaw: float | None = None
            self.create_subscription(Odometry, "/odom", self._cb, 10)

        def _cb(self, msg: Odometry):
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            self.xy = (float(p.x), float(p.y))
            self.yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
            )

    rclpy.init()
    node = _WaitOdom()
    t0 = __import__("time").time()
    err = float("inf")
    last: tuple[float, float] | None = None
    try:
        while __import__("time").time() - t0 < settle_s:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.xy is None:
                continue
            e = math.hypot(node.xy[0] - expected_xy[0], node.xy[1] - expected_xy[1])
            if e < err:
                err = e
                last = node.xy
            if err <= max_err_m:
                break
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if last is None:
        raise SystemExit("verify: no /odom received — is Gazebo + ROS bridge running?")
    print(f"verify odom=({last[0]:.3f}, {last[1]:.3f}) err_m={err:.3f} (max {max_err_m})")
    if err > max_err_m:
        hint = fail_hint or (
            f"odom {err:.2f}m from expected — set_pose likely ignored "
            f"(wrong model name, gz not running, or odom not updated after teleport)."
        )
        raise SystemExit(f"verify FAILED: {hint}")
    return last[0], last[1], err


def _yaw_err(a: float, b: float) -> float:
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def verify_odom_spawn_at_launch(
    teach_xy: tuple[float, float],
    expected_yaw: float,
    max_err_m: float,
    max_yaw_rad: float = 0.12,
    settle_s: float = 3.0,
) -> tuple[float, float, float]:
    """After launch_tb3_house_at_run: /odom pose is ~origin; teach.pkl is post–set_pose world odom."""
    hint = (
        "spawn-at-launch expects /odom near (0,0); robot already drove since spawn "
        "(prior eval, or pd_controller left running). "
        "Terminal 1: Ctrl+C → bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06 "
        "→ wait Entity creation successful → rerun holdout."
    )
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node

    class _WaitOdom(Node):
        def __init__(self):
            super().__init__("reset_verify_spawn")
            self.xy: tuple[float, float] | None = None
            self.yaw: float | None = None
            self.create_subscription(Odometry, "/odom", self._cb, 10)

        def _cb(self, msg: Odometry):
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            self.xy = (float(p.x), float(p.y))
            self.yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
            )

    rclpy.init()
    node = _WaitOdom()
    t0 = __import__("time").time()
    err = float("inf")
    yaw_err = float("inf")
    last: tuple[float, float] | None = None
    last_yaw: float | None = None
    try:
        while __import__("time").time() - t0 < settle_s:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.xy is None or node.yaw is None:
                continue
            e = math.hypot(node.xy[0], node.xy[1])
            ye = _yaw_err(node.yaw, expected_yaw)
            if e < err:
                err = e
                last = node.xy
            if ye < yaw_err:
                yaw_err = ye
                last_yaw = node.yaw
            if err <= max_err_m and yaw_err <= max_yaw_rad:
                break
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if last is None or last_yaw is None:
        raise SystemExit("verify: no /odom received — is Gazebo + ROS bridge running?")
    print(
        f"verify odom=({last[0]:.3f}, {last[1]:.3f}) yaw={math.degrees(last_yaw):.1f}° "
        f"err_m={err:.3f} yaw_err_deg={math.degrees(yaw_err):.1f} (max {max_err_m}m, "
        f"{math.degrees(max_yaw_rad):.1f}°)"
    )
    if err > max_err_m:
        raise SystemExit(f"verify FAILED: {hint}")
    if yaw_err > max_yaw_rad:
        raise SystemExit(
            "verify FAILED: spawn yaw mismatch — launch_tb3_house_at_run only sets x/y; "
            "run reset_run_pose with --skip-teleport --align-spawn-yaw (default on)."
        )
    print(
        f"spawn-at-launch OK: odom near origin + yaw (teach anchor {teach_xy[0]:.3f}, "
        f"{teach_xy[1]:.3f} in sim world; metrics use --spawn-at-launch in nomad_navigate)"
    )
    return last[0], last[1], err


def _odom_qos():
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

    return QoSProfile(
        depth=10,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
    )


def align_yaw_cmdvel(target_yaw: float, goal_rad: float = 0.12, wall_s: float | None = None) -> None:
    """Rotate in place via /cmd_vel until /odom yaw matches teach (works when gz set_pose is disconnected)."""
    import time

    import rclpy
    from geometry_msgs.msg import TwistStamped
    from nav_msgs.msg import Odometry
    from rclpy.node import Node

    max_w = 0.55
    min_wall = 45.0
    wall_cap = 150.0

    class _Spin(Node):
        def __init__(self) -> None:
            super().__init__("align_yaw_cmdvel")
            self.yaw: float | None = None
            self.pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
            self.create_subscription(Odometry, "/odom", self._cb, _odom_qos())

        def _cb(self, msg: Odometry) -> None:
            q = msg.pose.pose.orientation
            self.yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
            )

        def publish_twist(self, w: float) -> None:
            msg = TwistStamped()
            msg.header.frame_id = "base_link"
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = 0.0
            msg.twist.angular.z = float(w)
            self.pub.publish(msg)

    if rclpy.ok():
        rclpy.shutdown()
    rclpy.init()
    node = _Spin()
    t_start = time.time()
    deadline = t_start + (wall_s if wall_s is not None else wall_cap)
    last_log = 0.0
    yaw0: float | None = None
    try:
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            if node.yaw is None:
                if time.time() - last_log > 2.0:
                    print("  waiting for /odom...", flush=True)
                    last_log = time.time()
                continue
            err = (target_yaw - node.yaw + math.pi) % (2 * math.pi) - math.pi
            if yaw0 is None:
                yaw0 = node.yaw
                need_deg = abs(math.degrees(err))
                est = min(wall_cap, max(min_wall, need_deg / 55.0 * 60.0 + 20.0))
                if wall_s is None:
                    deadline = t_start + est
                print(
                    f"align_yaw_cmdvel: need ~{need_deg:.0f}° "
                    f"(timeout {est:.0f}s; Gazebo turns slowly)",
                    flush=True,
                )
            if time.time() - last_log > 1.5:
                left = max(0.0, deadline - time.time())
                print(
                    f"  yaw={math.degrees(node.yaw):.1f}° "
                    f"err={math.degrees(err):.1f}° t_left={left:.0f}s",
                    flush=True,
                )
                last_log = time.time()
            if abs(err) <= goal_rad:
                node.publish_twist(0.0)
                print(
                    f"align_yaw_cmdvel ok yaw={node.yaw:.3f} rad "
                    f"({math.degrees(node.yaw):.1f}°)",
                    flush=True,
                )
                break
            w = max(-max_w, min(max_w, 2.2 * err))
            node.publish_twist(w)
        else:
            node.publish_twist(0.0)
            yd = math.degrees(node.yaw) if node.yaw is not None else float("nan")
            raise SystemExit(
                f"align_yaw_cmdvel timeout at yaw={yd:.1f}° "
                f"(target {math.degrees(target_yaw):.1f}°). "
                "Re-run verify or increase time; kill pd_controller if err never changes."
            )
    finally:
        node.publish_twist(0.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def wait_odom(timeout_s: float = 10.0) -> bool:
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node

    class _O(Node):
        def __init__(self) -> None:
            super().__init__("wait_odom")
            self.ok = False
            self.create_subscription(
                Odometry, "/odom", lambda _m: setattr(self, "ok", True), _odom_qos()
            )

    rclpy.init()
    node = _O()
    t0 = __import__("time").time()
    try:
        while __import__("time").time() - t0 < timeout_s:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.ok:
                return True
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return False


def align_spawn_yaw(
    run: str,
    entity: str,
    *,
    use_gz: bool = False,
) -> None:
    """After spawn-at-launch: match teach heading so /camera matches teach0 (gz often broken in WSL)."""
    x, y, yaw = pose_from_traj(run)
    if not wait_odom(12.0):
        raise SystemExit(
            "no /odom — start terminal 1: bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06"
        )
    publish_stop_cmd_vel(1.0)
    print(
        f"align-spawn-yaw: teach yaw {yaw:.3f} rad ({math.degrees(yaw):.1f}°); "
        f"world anchor ({x:.2f}, {y:.2f})",
        flush=True,
    )
    if use_gz:
        from gz_pose_utils import set_robot_pose

        try:
            ent = set_robot_pose(x, y, yaw, entity=entity or None)
            print(f"align-spawn-yaw gz ok entity={ent}", flush=True)
            return
        except RuntimeError as err:
            print(f"WARN gz set_pose ignored ({err}); using /cmd_vel spin", flush=True)
    align_yaw_cmdvel(yaw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="house_run_00")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="after set_pose, check /odom is within --max-err-m of traj first pose",
    )
    parser.add_argument("--max-err-m", type=float, default=0.5)
    parser.add_argument("--settle-s", type=float, default=4.0)
    parser.add_argument(
        "--entity",
        default=os.environ.get("GZ_ROBOT_ENTITY", ""),
        help="Gazebo model name (default: auto-detect turtlebot3_burger_cam)",
    )
    parser.add_argument("--list-models", action="store_true", help="print gz models and exit")
    parser.add_argument(
        "--drive-fallback",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="if teleport fails, drive to start via /cmd_vel + /odom",
    )
    parser.add_argument(
        "--skip-teleport",
        action="store_true",
        help="only verify odom (use after launch_tb3_house_at_run.sh)",
    )
    parser.add_argument(
        "--align-spawn-yaw",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="after spawn-at-launch, match teach yaw (default: /cmd_vel spin, not gz)",
    )
    parser.add_argument(
        "--yaw-via-gz",
        action="store_true",
        help="try gz set_pose before cmd_vel (often fails when gz CLI disconnected)",
    )
    parser.add_argument(
        "--max-yaw-deg",
        type=float,
        default=7.0,
        help="max |odom_yaw - teach_yaw| when --skip-teleport --verify",
    )
    args = parser.parse_args()
    if args.list_models:
        models = list_gazebo_models() or entities_from_ros_topics()
        if not models:
            print("WARN: gz model -l empty; ros /model/* topics not found")
            raise SystemExit(1)
        print("\n".join(models))
        return
    x, y, yaw = pose_from_traj(args.run)
    print(f"set_pose {args.run}: x={x:.3f} y={y:.3f} yaw={yaw:.3f}")
    if not args.skip_teleport:
        try:
            if args.entity:
                from gz_pose_utils import set_robot_pose

                ent = set_robot_pose(x, y, yaw, entity=args.entity)
                print(f"teleport ok entity={ent}")
            else:
                set_pose(x, y, yaw)
                print("teleport ok")
        except RuntimeError as err:
            if not args.drive_fallback:
                raise
            print(f"WARN teleport failed: {err}", flush=True)
            print("WARN driving to teach start via /cmd_vel (needs Gazebo running)...", flush=True)
            import subprocess
            import sys

            script = os.path.join(ROOT, "drive_to_traj_start.py")
            rc = subprocess.run(
                [sys.executable, script, "--x", str(x), "--y", str(y), "--yaw", str(yaw)],
                check=False,
            ).returncode
            if rc != 0:
                raise SystemExit(
                    "drive_to_traj_start failed (house has walls; open-loop cannot cross rooms). "
                    "Restart terminal 1: bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06 "
                    "Then: reset_run_pose.py --run house_run_06 --skip-teleport --verify"
                ) from err
    else:
        print("skip teleport (spawn-at-launch mode)")
        publish_stop_cmd_vel(2.0)
        if args.align_spawn_yaw:
            align_spawn_yaw(args.run, args.entity, use_gz=args.yaw_via_gz)
            publish_stop_cmd_vel(1.5)
    if args.verify:
        if args.skip_teleport:
            verify_odom_spawn_at_launch(
                (x, y),
                yaw,
                args.max_err_m,
                max_yaw_rad=math.radians(args.max_yaw_deg),
                settle_s=args.settle_s,
            )
        else:
            verify_odom_xy((x, y), args.max_err_m, settle_s=args.settle_s)


if __name__ == "__main__":
    main()
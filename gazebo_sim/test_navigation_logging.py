"""Exercise production callbacks/controller with message fakes, without ROS.

AST extraction avoids importing unavailable ROS/model packages; the executed
methods are the actual source, not a second implementation of the controller.
"""

import ast
import csv
import math
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

from csv_log import CsvLog

ROOT = Path(__file__).parent


def twist():
    return NS(header=NS(stamp=NS(sec=12, nanosec=500000000), frame_id="base_link"),
              twist=NS(linear=NS(x=0.0), angular=NS(z=0.0)))


def production_definitions(filename, names, namespace):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if getattr(n, "name", "") in names
             or isinstance(n, ast.Assign)]
    # Both modules have postponed type annotations, preserve that behavior.
    import __future__
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / filename),
                 "exec", flags=__future__.annotations.compiler_flag), namespace)
    return namespace


class LoggingTest(unittest.TestCase):
    def test_csv_visible_before_close_and_not_truncated_on_close(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested/ticks.csv"
            log = CsvLog(path)
            log.write({"cmd_v": None, "wp_dy": -0.02})
            with path.open() as f:
                self.assertEqual(list(csv.DictReader(f)), [{"cmd_v": "", "wp_dy": "-0.02"}])
            log.write({"cmd_v": 0.0, "wp_dy": 0.0})
            log.close()
            with path.open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), 2)

    def test_controller_logs_every_command_with_matching_waypoint(self):
        ns = production_definitions("pd_controller_ros2.py",
                                    {"clip_angle", "pd_controller", "PdController"},
                                    {"math": math, "np": np, "time": time,
                                     "Node": object, "TwistStamped": twist})
        cls = ns["PdController"]
        node = cls.__new__(cls)
        node._waypoint = None
        node._waypoint_time = 0.0
        node._waypoint_mono = None
        node._waypoint_seq = 0
        node._reached = False
        published = []
        node._pub = NS(publish=published.append)
        node.get_clock = lambda: NS(now=lambda: NS(to_msg=lambda: twist().header.stamp))
        node.get_logger = lambda: NS(info=lambda *a: None)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "control.csv"
            node._command_log = CsvLog(path)
            node._tick()  # no waypoint
            node._on_waypoint(NS(data=[0.1, 0.01]))
            node._tick()  # clamped forward velocity
            node._on_waypoint(NS(data=[0.0, 0.0, 0.0, 1.0]))
            node._tick()  # pure spin; clamped angular velocity
            node._waypoint_mono -= 2
            node._tick()  # timeout stop
            node._on_reached(NS(data=True))
            node._tick()  # goal stop
            node._publish_command(twist(), "shutdown")
            with path.open() as f:
                rows = list(csv.DictReader(f))  # must be flushed while running
            node._command_log.close()
        self.assertEqual([r["reason"] for r in rows],
                         ["waiting_waypoint", "tracking", "tracking", "waypoint_timeout",
                          "reached_goal", "shutdown"])
        self.assertEqual(len(rows), len(published))
        for row, msg in zip(rows, published):
            self.assertEqual(float(row["cmd_v"]), msg.twist.linear.x)
            self.assertEqual(float(row["cmd_w"]), msg.twist.angular.z)
            self.assertEqual(float(row["cmd_stamp_ros_s"]), 12.5)
        self.assertEqual(rows[0]["wp_dx"], "")
        self.assertEqual(float(rows[1]["cmd_v"]), 0.2)
        self.assertEqual(float(rows[1]["wp_dy"]), 0.01)
        self.assertEqual(float(rows[2]["cmd_w"]), 1.5)
        self.assertEqual(float(rows[3]["cmd_w"]), 0.0)
        self.assertEqual(rows[2]["waypoint_seq"], rows[3]["waypoint_seq"])

    def test_navigation_callbacks_record_measured_and_commanded_velocity_separately(self):
        tree = ast.parse((ROOT / "nomad_navigate_ros2.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        methods = [n for n in cls.body if getattr(n, "name", "") in {"_on_odom", "_on_cmd_vel"}]
        import __future__
        ns = {"time": time, "math": math}
        exec(compile(ast.Module(body=methods, type_ignores=[]), "callbacks", "exec",
                     flags=__future__.annotations.compiler_flag), ns)
        node = NS(_last_xy=None, _path_m=0.0, _path_xy=[])
        odom = NS(header=twist().header,
                  pose=NS(pose=NS(position=NS(x=0.8, y=-0.4),
                                  orientation=NS(w=math.cos(0.1), z=math.sin(0.1), x=0, y=0))),
                  twist=NS(twist=NS(linear=NS(x=0.12), angular=NS(z=-0.25))))
        cmd = twist()
        cmd.twist.linear.x, cmd.twist.angular.z = 0.2, -0.3
        ns["_on_odom"](node, odom)
        ns["_on_cmd_vel"](node, cmd)
        self.assertAlmostEqual(node._odom_yaw, 0.2)
        self.assertEqual((node._odom_v, node._odom_w), (0.12, -0.25))
        self.assertEqual((node._cmd_v, node._cmd_w), (0.2, -0.3))
        self.assertEqual(node._odom_stamp, 12.5)
        self.assertIsNotNone(node._cmd_received_mono)


if __name__ == "__main__":
    unittest.main()

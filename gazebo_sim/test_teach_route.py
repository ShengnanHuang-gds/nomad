"""Ordered teacher-route diagnostics against the real PD control law.

The kinematic replay has no walls, camera, ROS or Gazebo physics; it verifies
the route state machine/control interface, not simulator success.
"""

import math
import ast
import pickle
import unittest
from types import SimpleNamespace
from pathlib import Path

import numpy as np

from episode_budget import timeout_reason
from teach_route import TeachRouteAssist
from test_navigation_logging import production_definitions


class TeachRouteTest(unittest.TestCase):
    def setUp(self):
        with open(Path(__file__).parent / "house_run_06/traj_data.pkl", "rb") as f:
            d = pickle.load(f)
        self.xy, self.yaw = d["position"], d["yaw"]
        ns = production_definitions("pd_controller_ros2.py", {"clip_angle", "pd_controller"},
                                    {"np": np, "math": math})
        self.pd = ns["pd_controller"]

    def test_four_turns_and_five_translation_legs(self):
        route = TeachRouteAssist(self.xy, self.yaw)
        self.assertEqual(route.legs, [("drive", 0, 8), ("spin", 8, 12),
                                     ("drive", 12, 22), ("spin", 22, 30),
                                     ("drive", 30, 38), ("spin", 38, 42),
                                     ("drive", 42, 51), ("spin", 51, 56),
                                     ("drive", 56, 62)])

    def test_cannot_skip_route_by_starting_at_final_position(self):
        route = TeachRouteAssist(self.xy, self.yaw)
        route.update(self.xy[-1], self.yaw[-1], 0.05)
        self.assertFalse(route.reached)
        self.assertEqual(route.leg, 0)
        # The production navigator must also ignore a false visual-node finish.
        tree = ast.parse((Path(__file__).parent / "nomad_navigate_ros2.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in cls.body if getattr(n, "name", "") == "_reached_goal")
        ns = {}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "goal_check", "exec"), ns)
        node = SimpleNamespace(_route_assist=route, closest_node=62, goal_node=62)
        self.assertFalse(ns["_reached_goal"](node))

    def test_no_odometry_means_zero_motion(self):
        wp, _ = TeachRouteAssist(self.xy, self.yaw).update(None, None, 0.05)
        self.assertEqual(self.pd(np.asarray(wp)), (0.0, 0.0))

    def test_corner_approach_slows_before_switching(self):
        route = TeachRouteAssist(self.xy, self.yaw)
        route.leg = 4
        wp, _ = route.update(self.xy[36], self.yaw[36], 0.05, proximity_m=0.4)
        v, _ = self.pd(np.asarray(wp))
        self.assertEqual(route.leg, 4)
        self.assertLessEqual(v, 0.08 + 1e-9)

    def test_recorded_near_obstacle_starts_known_turn_before_stop_threshold(self):
        import csv
        path = Path(__file__).parent / "episodes_eval_gpu/house_06_nomad_b40_teach_route_scan.ticks.csv"
        with path.open() as f:
            rows = list(csv.DictReader(f))
        row = rows[566]  # ~11 cm short of turn, laser still ~19.8 cm
        route = TeachRouteAssist(self.xy, self.yaw)
        route.leg = 4
        wp, goal = route.update((float(row['odom_x']), float(row['odom_y'])),
                                float(row['odom_yaw']), 0.05, float(row['scan_min']))
        self.assertGreater(float(row['scan_min']), 0.15)
        self.assertEqual((route.leg, route.phase, goal), (5, "spin", 42))
        self.assertEqual(wp[:2], [0.0, 0.0])
        self.assertLess(wp[3], 0)
        self.assertEqual(route.turn_entry_reason, "near_obstacle")
        self.assertLessEqual(route.turn_entry_error_m, 0.12)

    def test_near_obstacle_cannot_skip_distant_corner(self):
        route = TeachRouteAssist(self.xy, self.yaw)
        route.update(self.xy[5], self.yaw[5], 0.05, proximity_m=0.18)
        self.assertEqual(route.leg, 0)

    def test_final_endpoint_tolerance_is_not_relaxed_by_proximity(self):
        route = TeachRouteAssist(self.xy, self.yaw)
        route.leg = 8
        route.update(self.xy[61], self.yaw[61], 0.05, proximity_m=0.18)
        self.assertFalse(route.reached)
        self.assertEqual(route.leg, 8)

    def test_navigator_waits_for_fresh_scan_then_resumes(self):
        tree = ast.parse((Path(__file__).parent / "nomad_navigate_ros2.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in cls.body if getattr(n, "name", "") == "_teach_spin_waypoint")
        ns = {"MAX_V": 0.2}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "scan_guard", "exec"), ns)
        route = TeachRouteAssist(self.xy, self.yaw)
        route.leg = 4
        node = SimpleNamespace(_turn_assist=None, _route_assist=route, _spawn_at_launch=False,
                               _odom_xy=(2.08, -0.967), _odom_yaw=float(self.yaw[38]),
                               _odom_stamp=21.2, _scan_stamp=20.8, _scan_min=0.198,
                               args=SimpleNamespace(rate=4, visual_only=False))
        wp, _ = ns["_teach_spin_waypoint"](node, 38)
        self.assertEqual(route.phase, "wait_scan")
        self.assertEqual(self.pd(np.asarray(wp)), (0.0, 0.0))
        node._scan_stamp = 21.2
        ns["_teach_spin_waypoint"](node, 38)
        self.assertEqual(route.phase, "spin")

    def test_full_route_with_real_pd_at_normal_and_slow_simulation(self):
        for real_time_factor in (1.0, 0.11):
            with self.subTest(real_time_factor=real_time_factor):
                route = TeachRouteAssist(self.xy, self.yaw)
                x, y = map(float, self.xy[0])
                yaw = math.radians(-25.1)  # actual exit035 initial orientation
                wp = np.zeros(4)
                v = w = elapsed = path = 0.0
                next_nav = next_control = 0.0
                dt = 0.01
                legs_seen = set()
                while elapsed < 900 and not route.reached:
                    if elapsed >= next_nav:
                        wp, _ = route.update((x, y), yaw, 0.05)
                        next_nav += 0.25
                        legs_seen.add(route.leg)
                    if elapsed >= next_control:
                        v, w = self.pd(np.asarray(wp))
                        next_control += 1 / 9
                    sim_dt = dt * real_time_factor
                    x += v * math.cos(yaw) * sim_dt
                    y += v * math.sin(yaw) * sim_dt
                    yaw += w * sim_dt
                    path += abs(v) * sim_dt
                    elapsed += dt
                self.assertTrue(route.reached)
                self.assertLessEqual(route.endpoint_error_m, 0.04)
                self.assertGreater(path, 4.2)
                self.assertLess(path, 4.8)
                self.assertTrue(set(range(9)).issubset(legs_seen))
                self.assertLess(elapsed * real_time_factor, 60)

    def test_timeout_uses_sim_time_not_600_wall_ticks(self):
        self.assertEqual(timeout_reason(600, 16.3, 148.6, max_sim_s=60, max_wall_s=900), "")
        self.assertEqual(timeout_reason(2000, 60, 550, max_sim_s=60), "max_sim_seconds")
        self.assertEqual(timeout_reason(1000, 0, 900, max_wall_s=900), "max_wall_seconds")
        self.assertEqual(timeout_reason(600, 16.3, 148.6, max_ticks=600), "max_ticks")


if __name__ == "__main__":
    unittest.main()

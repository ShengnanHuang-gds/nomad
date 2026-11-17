"""ROS-free regressions using the actual held-out teacher route."""

import math
import pickle
import unittest
from pathlib import Path

from teach_turn import TeachTurnAssist


class TeachTurnTest(unittest.TestCase):
    def setUp(self):
        with open(Path(__file__).parent / "house_run_06/traj_data.pkl", "rb") as f:
            route = pickle.load(f)
        self.xy = route["position"]
        self.yaw = route["yaw"]
        self.assist = TeachTurnAssist(self.xy, self.yaw)

    def test_detect_all_four_turns(self):
        self.assertEqual(self.assist.turns, [(8, 12), (22, 30), (38, 42), (51, 56)])

    def test_straight_node_does_not_override_model(self):
        wp, goal = self.assist.update(5, self.xy[5], self.yaw[5] + 0.3, 0.05)
        self.assertIsNone(wp)
        self.assertIsNone(goal)

    def test_turn_latches_despite_localizer_retreat(self):
        for node in (8, 7, 6, 9, 10, 11):
            wp, goal = self.assist.update(node, self.xy[8], self.yaw[11], 0.05)
            self.assertEqual(goal, 13)
            self.assertEqual(wp[:2], [0, 0])
            self.assertGreater(wp[3], 0)  # still turn LEFT to 12 degrees
            self.assertEqual(self.assist.active, (8, 12))

    def test_visual_jump_far_from_corner_cannot_start_turn(self):
        wp, _ = self.assist.update(8, self.xy[3], self.yaw[3], 0.05)
        self.assertIsNone(wp)

    def test_exit_corrects_recorded_offset_and_releases(self):
        self.assist.update(8, self.xy[8], self.yaw[8], 0.05)
        # Burst's exit position is ~3 cm left of the teacher line.
        wp, goal = self.assist.update(11, (0.771, -0.440), self.yaw[12], 0.05)
        self.assertEqual(goal, 13)
        self.assertEqual(self.assist.phase, "exit")
        self.assertGreater(wp[0], 0)
        self.assertLess(wp[1], 0)  # correct toward the outgoing line
        self.assertIn(12, self.assist.completed)
        wp, _ = self.assist.update(11, self.xy[16], self.yaw[12], 0.05)
        self.assertIsNone(wp)
        # A stale visual match cannot replay the already completed turn.
        wp, goal = self.assist.update(9, self.xy[8], self.yaw[12], 0.05)
        self.assertIsNone(wp)
        self.assertIsNone(goal)  # do not force a passed exit image forever
        wp, goal = self.assist.update(22, self.xy[22], self.yaw[22], 0.05)
        self.assertEqual(goal, 31)
        self.assertLess(wp[3], 0)  # next turn is right

    def test_spin_only_mode(self):
        assist = TeachTurnAssist(self.xy, self.yaw, exit_m=0)
        assist.update(8, self.xy[8], self.yaw[8], 0.05)
        wp, goal = assist.update(11, self.xy[12], self.yaw[12], 0.05)
        self.assertIsNone(wp)
        self.assertEqual(goal, 13)
        self.assertIn(12, assist.completed)

    def test_wrapped_yaw(self):
        assist = TeachTurnAssist([(0, 0), (0, 0), (-0.12, 0)],
                                 [math.radians(170), math.radians(-175), math.pi])
        wp, _ = assist.update(0, (0, 0), math.radians(170), 0.05)
        self.assertGreater(wp[3], 0)  # +15 degrees across the wrap


if __name__ == "__main__":
    unittest.main()

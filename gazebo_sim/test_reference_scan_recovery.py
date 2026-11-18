import math
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from scan_diagnostics import SCAN_RECEIPT_STALE, scan_timing
from test_navigation_logging import production_definitions


class ReferenceScanRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.now = 2.03
        self.events = iter(())
        self.rclpy = SimpleNamespace(ok=lambda: True, spin_once=self.spin_once)
        ns = production_definitions(
            "record_house_multi.py", {"Recorder", "ScanReceiptTimeout"},
            {"__file__": __file__, "Node": object, "math": math, "os": os, "rclpy": self.rclpy,
             "time": SimpleNamespace(monotonic=lambda: self.now), "print": Mock(),
             "scan_timing": scan_timing, "SCAN_RECEIPT_STALE": SCAN_RECEIPT_STALE},
        )
        cls = ns["Recorder"]
        self.node = cls.__new__(cls)
        self.node.scan = (26_400_000_000, 0.0, 0.91)
        self.node.sync = SimpleNamespace(last_odom_stamp=26_600_000_000)
        self.node.odom_received_at = self.now
        self.node.reference_pose = Mock()
        self.node.count_publishers = Mock(return_value=1)
        self.node.publish_twist = Mock()
        self.node.save_ready = Mock()
        self.node.scan_pauses = self.node.scan_recoveries = 0

    def spin_once(self, node, timeout_sec):
        delay, stamp, distance = next(self.events, (timeout_sec, None, None))
        self.now += delay
        node.odom_received_at = self.now
        if stamp is not None:
            node.scan = (stamp, self.now, distance)

    def test_native_cadence_gap_pauses_then_allows_motion_on_a_later_tick(self):
        self.events = iter([(0, None, None), (0.06, 26_400_000_000, 0.91),
                            (0.06, 26_600_000_000, 0.91)])
        self.node.motion_tick(0.14, 0.0)
        self.assertEqual((self.node.scan_pauses, self.node.scan_recoveries), (1, 1))
        self.assertEqual([call.args for call in self.node.publish_twist.call_args_list],
                         [(0.0, 0.0), (0.0, 0.0)])
        self.node.motion_tick(0.14, 0.0)
        self.node.publish_twist.assert_called_with(0.14, 0.0)

    def test_scan_that_never_advances_leaves_the_robot_stopped(self):
        with self.assertRaisesRegex(RuntimeError, "stayed stopped"):
            self.node.motion_tick(0.14, 0.0)
        self.assertEqual((self.node.scan_pauses, self.node.scan_recoveries), (1, 0))
        self.assertTrue(self.node.publish_twist.called)
        self.assertTrue(all(call.args == (0.0, 0.0)
                            for call in self.node.publish_twist.call_args_list))

    def test_new_scan_with_nearby_obstacle_does_not_recover(self):
        self.events = iter([(0, None, None), (0.12, 26_600_000_000, 0.12)])
        with self.assertRaisesRegex(RuntimeError, "scan proximity"):
            self.node.motion_tick(0.14, 0.0)
        self.assertEqual(self.node.scan_recoveries, 0)
        self.node.publish_twist.assert_called_once_with(0.0, 0.0)

    def test_late_and_unsynchronized_scan_does_not_start_recovery(self):
        self.node.sync.last_odom_stamp = 26_800_000_000
        with self.assertRaisesRegex(RuntimeError, "scan_behind_odom"):
            self.node.motion_tick(0.14, 0.0)
        self.assertEqual(self.node.scan_pauses, 0)
        self.node.publish_twist.assert_not_called()


if __name__ == "__main__":
    unittest.main()

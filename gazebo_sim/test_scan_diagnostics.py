import math
import unittest
from types import SimpleNamespace as NS

from scan_diagnostics import scan_timing, summarize_scan


def scan(ranges, start=0, increment=math.pi/2):
    return NS(ranges=ranges, angle_min=start, angle_increment=increment,
              range_min=0.05, range_max=10.0, header=NS(frame_id="base_scan"))


class ScanDiagnosticsTest(unittest.TestCase):
    def test_scan_timing_distinguishes_missing_data_and_invalid_stamps(self):
        self.assertEqual(scan_timing(None, 5_000_000_000, 10)["issues"], ["no_scan_received"])
        invalid = scan_timing((0, 9.0, 0.8), 0, 10)
        self.assertEqual(invalid["issues"], ["invalid_scan_stamp", "no_valid_odom_stamp"])
        self.assertIsNone(invalid["scan_minus_odom_ns"])

    def test_scan_timing_reports_wall_age_and_signed_simulation_offset(self):
        odom_stamp = 5_000_000_000
        behind = scan_timing((4_640_000_000, 7.0, 0.8), odom_stamp, 10.0)
        self.assertEqual(behind["issues"], ["scan_receipt_over_2_wall_s_old", "scan_behind_odom"])
        self.assertEqual(behind["scan_minus_odom_ns"], -360_000_000)
        self.assertEqual(behind["receipt_age_wall_s"], 3.0)
        ahead = scan_timing((5_360_000_000, 9.0, 0.8), odom_stamp, 10.0)
        self.assertEqual(ahead["issues"], ["scan_ahead_of_odom"])

    def test_scan_timing_keeps_existing_cutoffs(self):
        at_limit = scan_timing((4_650_000_000, 8.0, 0.8), 5_000_000_000, 10.0)
        self.assertEqual(at_limit["issues"], [])

    def test_side_proximity_is_distinct_from_front_obstacle(self):
        result = summarize_scan(scan([1.0, 0.1469, 2.0, 0.8]))
        self.assertEqual(result["scan_min"], 0.1469)
        self.assertEqual(result["scan_min_angle_deg"], 90)
        self.assertEqual(result["scan_front_min"], 1.0)
        self.assertEqual(result["scan_left_min"], 0.1469)
        self.assertEqual(result["scan_right_min"], 0.8)
        self.assertEqual(result["scan_rear_min"], 2.0)
        self.assertEqual(result["scan_frame_id"], "base_scan")

    def test_invalid_ranges_do_not_become_fake_obstacles(self):
        result = summarize_scan(scan([float("nan"), float("inf"), 0.01, 10.0]))
        self.assertIsNone(result["scan_min"])
        self.assertIsNone(result["scan_front_min"])
        self.assertEqual(result["scan_valid_rays"], 0)

    def test_clockwise_scan_and_nonzero_start_angle(self):
        result = summarize_scan(scan([2, 0.12, 1, 3], start=math.pi, increment=-math.pi/2))
        self.assertEqual(result["scan_min_angle_deg"], 90)
        self.assertEqual(result["scan_left_min"], 0.12)
        self.assertEqual(result["scan_front_min"], 1)

    def test_summary_keeps_original_global_minimum(self):
        result = summarize_scan(scan([0.05, 0.3, 0.8, float("nan"), 11, 0.2], increment=0.25))
        self.assertEqual(result["scan_min"], 0.2)
        self.assertEqual(result["scan_valid_rays"], 3)


if __name__ == "__main__":
    unittest.main()

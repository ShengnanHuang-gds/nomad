import math
import unittest

from reference_map_pose import pose_at_images


class ReferenceMapPoseTest(unittest.TestCase):
    def test_interpolates_across_yaw_wrap_and_keeps_timestamp_support(self):
        a = (1_000_000_000, (1.0, 2.0, 0.01), (0.0, 0.0, math.radians(179)))
        b = (1_020_000_000, (2.0, 3.0, 0.01), (0.0, 0.0, math.radians(-179)))
        row, = pose_at_images([1_010_000_000], [a, b])
        self.assertTrue(row["tilt_ok"])
        self.assertEqual(row["gazebo_pose"]["position_xyz_m"], [1.5, 2.5, 0.01])
        self.assertAlmostEqual(abs(row["gazebo_pose"]["roll_pitch_yaw_deg"][2]), 180)
        self.assertEqual(row["gazebo_pose"]["before_stamp_ns"], a[0])
        self.assertEqual(row["gazebo_pose"]["after_stamp_ns"], b[0])

    def test_missing_bracket_and_tilt_at_a_measured_endpoint(self):
        a = (1_000_000_000, (0.0, 0.0, 0.01), (math.radians(-6), 0.0, 0.0))
        b = (1_020_000_000, (0.0, 0.0, 0.01), (0.0, 0.0, 0.0))
        outside, tilted, upright = pose_at_images([999_000_000, 1_010_000_000, b[0]], [a, b])
        self.assertIsNone(outside["gazebo_pose"])
        self.assertFalse(tilted["tilt_ok"])
        self.assertTrue(upright["tilt_ok"])

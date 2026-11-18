import math
import unittest

from route_frame_sync import RouteFrameSync


class RouteFrameSyncTest(unittest.TestCase):
    def setUp(self):
        self.sync = RouteFrameSync()

    def test_waits_for_both_odom_samples_and_interpolates_wrapped_yaw(self):
        self.sync.add_odom(1_000_000_000, (0.0, 1.0, math.radians(179)))
        self.sync.add_image(1_010_000_000, "frame")
        self.assertEqual(list(self.sync.paired()), [])

        self.sync.add_odom(1_020_000_000, (2.0, 3.0, math.radians(-179)))
        frame, = self.sync.paired()
        self.assertEqual(frame.image, "frame")
        self.assertEqual(frame.pose[:2], (1.0, 2.0))
        self.assertAlmostEqual(abs(frame.pose[2]), math.pi)
        self.assertEqual((frame.stamp, frame.odom_before, frame.odom_after),
                         (1_010_000_000, 1_000_000_000, 1_020_000_000))

    def test_rejects_unbracketed_stale_and_duplicate_images(self):
        self.sync.add_image(0, "unstamped")
        self.sync.add_image(900_000_000, "no pose before")
        self.sync.add_odom(1_000_000_000, (0.0, 0.0, 0.0))
        self.sync.add_image(1_010_000_000, "odom after too far")
        self.sync.add_odom(1_100_000_000, (2.0, 0.0, 0.0))
        self.sync.add_image(1_100_000_000, "same time")
        self.sync.add_image(1_100_000_000, "duplicate")

        frame, = self.sync.paired()
        self.assertEqual(frame.image, "same time")
        self.assertEqual(frame.odom_before, frame.odom_after)
        self.assertEqual(list(self.sync.paired()), [])

    def test_retains_pose_bracket_for_late_camera_callback(self):
        for offset in range(0, 400, 20):
            self.sync.add_odom(1_000_000_000 + offset * 1_000_000, (float(offset), 0.0, 0.0))
            self.assertEqual(list(self.sync.paired()), [])
        self.sync.add_image(1_030_000_000, "late camera delivery")
        frame, = self.sync.paired()
        self.assertEqual(frame.pose[0], 30.0)

    def test_reset_cannot_join_samples_from_different_runs(self):
        self.sync.add_image(1_000_000_000, "frame")
        self.sync.add_odom(1_000_000_000, (0.0, 0.0, 0.0))
        with self.assertRaisesRegex(RuntimeError, "camera time went backwards"):
            self.sync.add_image(100_000_000, "reset")
        with self.assertRaisesRegex(RuntimeError, "odometry time went backwards"):
            self.sync.add_odom(100_000_000, (0.0, 0.0, 0.0))

import unittest

from gazebo_wheel_state import summarize


class WheelResponseTest(unittest.TestCase):
    def test_zero_post_step_command_does_not_hide_measured_turn(self):
        rows = [
            {
                "sim_stamp_ns": stamp,
                "paused": False,
                "wheels": {
                    "wheel_left_joint": {"velocity_rad_s": -0.29, "post_step_velocity_cmd_rad_s": 0.0},
                    "wheel_right_joint": {"velocity_rad_s": 0.29, "post_step_velocity_cmd_rad_s": 0.0},
                },
            }
            for stamp in (200_000_000, 300_000_000)
        ]
        self.assertIn("responded in the requested direction", summarize(rows, 0, 1_000_000_000, 0.12))
        self.assertIn("opposite sign", summarize(rows, 0, 1_000_000_000, -0.12))

        for row in rows:
            for wheel in row["wheels"].values():
                wheel["velocity_rad_s"] = 0.028
        self.assertIn("little measured turning response", summarize(rows, 0, 1_000_000_000, 0.12))

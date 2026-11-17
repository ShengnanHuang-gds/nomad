import argparse
import ast
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from vision_debug import VisionDebug

ROOT = Path(__file__).parent


def method(name):
    tree = ast.parse((ROOT / "nomad_navigate_ros2.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            ns = {"argparse": argparse, "DEFAULT_RATE": 4, "IMAGE_TOPIC": "/camera/image_raw"}
            exec(compile(ast.Module(body=[node], type_ignores=[]), "visual_only", "exec"), ns)
            return ns[name]


class VisualOnlyTest(unittest.TestCase):
    def test_visual_mode_cannot_be_combined_with_either_teacher_mode(self):
        for flag in ("--teach-route", "--teach-yaw-spin"):
            with patch.object(sys, "argv", ["navigate", "--visual-only", flag]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    method("parse_args")()

    def test_visual_mode_never_reads_teacher_pose_or_odometry_for_override(self):
        node = SimpleNamespace(args=SimpleNamespace(visual_only=True))
        self.assertEqual(method("_teach_spin_waypoint")(node, 11), (None, None))

    def test_saved_context_matches_model_input_pixels_and_sampling_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            sink = VisionDebug(temp)
            images = [Image.new("RGB", (4, 3), color) for color in ("red", "blue")]
            meta = {"closest_node": 11, "dist_is_close": True,
                    "sampled_actions": [[[0.2, -0.01]]], "selected_sample": 0}
            sink.record(10, images, meta, goal_image=images[0])
            sink.record(11, images, meta)  # unchanged node/state: skip
            sink.record(20, images, meta)  # periodic sample
            rows = [json.loads(s) for s in (Path(temp) / "predictions.jsonl").read_text().splitlines()]
            self.assertEqual([r["tick"] for r in rows], [10, 20])
            self.assertEqual(rows[0]["sampled_actions"], meta["sampled_actions"])
            with Image.open(Path(temp) / rows[0]["goal_image"]) as saved:
                self.assertEqual(saved.tobytes(), images[0].tobytes())
            for name, original in zip(rows[0]["context_images"], images):
                with Image.open(Path(temp) / name) as saved:
                    self.assertEqual(saved.tobytes(), original.tobytes())


if __name__ == "__main__":
    unittest.main()

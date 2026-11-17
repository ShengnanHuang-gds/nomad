import importlib.util
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from visual_stage_data import VisualStageData, TRAIN_ROUTES, VALID_ROUTES, extract_verified_handoff
from visual_yaw_data import yaw_pairs, pair_weights, yaw_metrics

ROOT = Path(__file__).resolve().parents[1]


class YawDataTest(unittest.TestCase):
    def test_pairs_exclude_heldout_and_labels_reverse_correctly(self):
        with tempfile.TemporaryDirectory() as temp:
            extract_verified_handoff(ROOT / "gazebo_sim/training_handoff", temp)
            data = VisualStageData(Path(temp) / "dataset")
            train = yaw_pairs(data, TRAIN_ROUTES)
            valid = yaw_pairs(data, VALID_ROUTES)
            self.assertEqual((len(train), len(valid)), (6756, 1138))
            self.assertTrue({x[0] for x in train}.isdisjoint(x[0] for x in valid))
            values = {(r, a, b): t for r, a, b, t in train}
            for (r, a, b), t in values.items():
                self.assertAlmostEqual(math.sin(t), -math.sin(values[r, b, a]), places=10)
                self.assertAlmostEqual(math.cos(t), math.cos(values[r, b, a]), places=10)
            self.assertAlmostEqual(float(pair_weights(train).sum()), 1)
            with self.assertRaises(ValueError):
                yaw_pairs(data, ["house_run_06"])

    def test_metrics_wrap_angles_and_do_not_accept_missing_turn_coverage(self):
        result = yaw_metrics([-math.pi+0.05], [math.pi-0.05])
        self.assertAlmostEqual(result["mae_deg"], math.degrees(0.1))
        self.assertFalse(result["validation_gate_passed"])
        good = yaw_metrics([0.6, -0.6], [0.65, -0.65])
        self.assertTrue(good["validation_gate_passed"])
        wrong = yaw_metrics([-0.6, 0.6], [0.65, -0.65])
        self.assertFalse(wrong["validation_gate_passed"])


@unittest.skipUnless(importlib.util.find_spec("torch"), "Torch needed for tiny image-head tests")
class YawModelTest(unittest.TestCase):
    def build(self):
        import torch
        from visual_yaw import VisualYaw
        class Encoder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = torch.nn.Conv2d(6, 4, 1)
                self._avg_pooling = torch.nn.AdaptiveAvgPool2d(1)
                self._dropout = torch.nn.Identity()
                self._global_params = SimpleNamespace(include_top=True)
            def extract_features(self, x):
                return self.conv(x)
        base = torch.nn.Module()
        base.vision_encoder = torch.nn.Module()
        base.vision_encoder.goal_encoder = Encoder()
        base.vision_encoder.compress_goal_enc = torch.nn.Linear(4, 8)
        base.vision_encoder.goal_encoding_size = 8
        return base, VisualYaw.from_nomad(base)

    def test_output_is_unit_heading_and_image_swap_negates_angle(self):
        import torch
        torch.manual_seed(0)
        _, model = self.build()
        model.eval()
        a, b = torch.rand(3, 3, 4, 4), torch.rand(3, 3, 4, 4)
        forward, reverse = model(a, b), model(b, a)
        torch.testing.assert_close(forward.norm(dim=1), torch.ones(3))
        torch.testing.assert_close(forward[:, 0], reverse[:, 0])
        torch.testing.assert_close(forward[:, 1], -reverse[:, 1])
        torch.testing.assert_close(model(a, a)[:, 1], torch.zeros(3))

    def test_new_head_can_train_without_mutating_original_xy_model(self):
        import torch
        torch.manual_seed(1)
        base, model = self.build()
        before = {k: v.clone() for k, v in base.state_dict().items()}
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
        a, b = torch.rand(2, 3, 4, 4), torch.rand(2, 3, 4, 4)
        unit, raw = model(a, b, return_raw=True)
        target = torch.tensor([[0.5, 0.866], [0.5, -0.866]])
        loss = (raw-target).square().mean()+0.25*(1-(unit*target).sum(-1)).mean()
        optimizer.zero_grad()
        loss.backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.parameters()))
        optimizer.step()
        for key, value in base.state_dict().items():
            torch.testing.assert_close(value, before[key], rtol=0, atol=0)

    def test_only_predicted_large_heading_requests_in_place_rotation(self):
        from visual_yaw import heading_override
        wp, reason = heading_override([0.5, -math.sqrt(0.75)])
        self.assertEqual(wp[:2], [0, 0])
        self.assertEqual(reason, "align")
        self.assertLess(wp[3], 0)
        self.assertEqual(heading_override([1, 0]), (None, "model"))
        self.assertEqual(heading_override([float("nan"), 0])[1], "invalid")

    def test_xy_numerical_zero_stops_but_explicit_heading_still_turns(self):
        from test_navigation_logging import production_definitions
        ns = production_definitions("pd_controller_ros2.py", {"clip_angle", "pd_controller"},
                                    {"np": np, "math": math})
        self.assertEqual(ns["pd_controller"](np.asarray([0., 1e-12])), (0., 0.))
        v, w = ns["pd_controller"](np.asarray([0., 0., 0., -1.]))
        self.assertEqual(v, 0.)
        self.assertEqual(w, -1.5)


if __name__ == "__main__":
    unittest.main()

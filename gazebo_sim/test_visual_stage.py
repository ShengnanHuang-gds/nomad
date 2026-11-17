import ast
import copy
import importlib.util
import json
import os
import pickle
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from visual_stage_data import VisualStageData, extract_verified_handoff, audit_legacy_train_index
from train_visual_stage import train_step, finish_epoch

ROOT = Path(__file__).resolve().parents[1]


class VisualStageDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.bundle = Path(cls.temp.name)
        extract_verified_handoff(ROOT / "gazebo_sim/training_handoff", cls.bundle)
        cls.data = VisualStageData(cls.bundle / "dataset")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_new_split_ignores_leaked_legacy_cache(self):
        audit = audit_legacy_train_index(self.bundle)[0]
        self.assertEqual(audit["observations"], 264)
        self.assertEqual(audit["unexpected_routes"], ["house_run_06", "house_run_07"])
        self.assertEqual(audit["unexpected_observations"], 76)
        self.assertEqual(len(self.data.train), 161)
        self.assertEqual(len(self.data.valid), 27)
        self.assertEqual({r for r, _ in self.data.train}, {f"house_run_{i:02d}" for i in range(5)})
        self.assertEqual({r for r, _ in self.data.valid}, {"house_run_05"})
        self.assertTrue({r for r, _ in self.data.train}.isdisjoint(r for r, _ in self.data.valid))

    def test_labels_match_actual_deployment_training_source(self):
        # Execute the supplied production coordinate and label methods, not a copy.
        import __future__
        ns = {"np": np}
        for file, names in [("data_utils.py", {"yaw_rotmat", "to_local_coords"}),
                            ("vint_dataset.py", {"_compute_actions"})]:
            tree = ast.parse((self.bundle / "source" / file).read_text())
            nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in names]
            exec(compile(ast.Module(body=nodes, type_ignores=[]), file, "exec",
                         flags=__future__.annotations.compiler_flag), ns)
        obj = SimpleNamespace(len_traj_pred=8, waypoint_spacing=1, learn_angle=False,
                              normalize=True, num_action_params=2,
                              data_config={"metric_waypoint_spacing": 0.12})
        for route, node in self.data.train + self.data.valid:
            with (self.bundle / "dataset" / route / "traj_data.pkl").open("rb") as f:
                raw = pickle.load(f)
            expected, _ = ns["_compute_actions"](obj, raw, node, node+8)
            np.testing.assert_allclose(self.data.actions(route, node)/0.12, expected, atol=1e-12)

    def test_balancing_assigns_equal_total_weight_per_turn_class(self):
        totals = {}
        for item, weight in zip(self.data.train, self.data.sampling_weights()):
            label = self.data.turn_class(*item)
            totals[label] = totals.get(label, 0) + weight
        self.assertEqual(set(totals), {"left", "right", "straight"})
        for total in totals.values():
            self.assertAlmostEqual(total, 1)

    def test_modified_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "manifest.json").write_text(json.dumps({"archive": {"path": "data.tar.gz", "sha256": "0"*64}}))
            (path / "data.tar.gz").write_bytes(b"incorrect archive")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                extract_verified_handoff(path, path / "output")


@unittest.skipUnless(importlib.util.find_spec("torch"), "Torch required for tiny optimizer tests")
class VisualStageOptimizerTest(unittest.TestCase):
    def test_epoch_advances_scheduler_once_and_saved_state_matches(self):
        import torch
        model = torch.nn.Linear(1, 1)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=3)
        for epoch in range(3):
            for _ in range(2):
                optimizer.zero_grad()
                model(torch.ones(1, 1)).square().sum().backward()
                optimizer.step()
            state = finish_epoch(scheduler)
            self.assertEqual(state["last_epoch"], epoch+1)
            self.assertEqual(state["_last_lr"], [optimizer.param_groups[0]["lr"]])
        self.assertAlmostEqual(optimizer.param_groups[0]["lr"], 0)

    def test_training_step_updates_model_and_ema_with_real_gradients(self):
        import torch
        class TinyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.bias = torch.nn.Parameter(torch.zeros(2))
            def forward(self, name, **kw):
                if name == "vision_encoder":
                    return self.bias[None].expand(len(kw["obs_img"]), -1)
                if name == "dist_pred_net":
                    return kw["obsgoal_cond"].sum(-1, keepdim=True)
                return kw["sample"]*0.1 + self.bias[None, None]
        torch.manual_seed(1)
        model = TinyModel()
        ema = copy.deepcopy(model).requires_grad_(False)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
        scheduler = SimpleNamespace(config=SimpleNamespace(num_train_timesteps=10),
                                    add_noise=lambda target, noise, steps: target+noise*0.1)
        batch = (torch.zeros(2, 12, 4, 4), torch.zeros(2, 3, 4, 4),
                 torch.ones(2, 8, 2), torch.tensor([4., 8.]), torch.ones(2))
        result = train_step(model, ema, optimizer, batch, scheduler,
                            {"min": [-2.5, -4], "max": [5, 4]}, torch)
        self.assertEqual(result["action_examples"], 2)
        self.assertTrue(np.isfinite(result["loss"]))
        self.assertGreater(float(model.bias.detach().abs().sum()), 0)
        self.assertGreater(float(ema.bias.detach().abs().sum()), 0)
        self.assertIsNone(ema.bias.grad)


if __name__ == "__main__":
    unittest.main()

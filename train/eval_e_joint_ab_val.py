"""Val nav ADE for joint A/B: optional trainable path_head_linear.pth for arm B."""
from __future__ import annotations
import argparse
import json
import os
import numpy as np
import torch
from eval_e_path_adapt_val import ValNavEvaluator, load_manifest_csv, manifest_to_frames, past_rows_batch
from eval_by_distance import load_config, load_observation
from eval_goal_head import normalize_images
from train_e_dino import load_dino_head
from train_goal_dino import CACHE_DIR, load_cache
from e_path_joint_common import build_cond_blend_path, mu_from_frozen_wp
class JointValEvaluator(ValNavEvaluator):
    def __init__(self, *args, path_head_train: torch.nn.Linear | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.path_head_train = path_head_train
        if path_head_train is not None:
            self.path_head_train.eval()
    @torch.no_grad()
    def build_est_pos_batch(self, start: int, chunk_len: int) -> torch.Tensor:
        chunk = self.manifest[start : start + chunk_len]
        obs_list, goal_list = [], []
        curr_rows, goal_rows = [], []
        traj_names, curr_ts = [], []
        for m in chunk:
            traj, t, gt = m["traj_name"], int(m["curr_t"]), int(m["goal_t"])
            obs, goal, _a, _p = self._load_observation(self.dataset, traj, t, gt)
            obs_list.append(obs)
            goal_list.append(goal)
            curr_rows.append(int(m["cache_curr_row"]))
            goal_rows.append(int(m["cache_goal_row"]))
            traj_names.append(traj)
            curr_ts.append(t)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), self.device)
        past_rows = past_rows_batch(traj_names, curr_ts, self.rows, self.dataset.waypoint_spacing)
        cr = np.array(curr_rows, dtype=np.int64)
        gr = np.array(goal_rows, dtype=np.int64)
        mu = mu_from_frozen_wp(
            self.loc_model,
            self.dino_head,
            self.features,
            batch_obs,
            batch_goal,
            cr,
            gr,
            self.device,
            self.wp_head,
            wp_scale=self.goal_pos_args.wp_scale,
            past_rows=past_rows,
        )
        use_train = self.path_head_train is not None
        cond_path = build_cond_blend_path(
            mu,
            self.wp_head,
            self.path_head_train if use_train else None,
            self.features,
            cr,
            gr,
            past_rows,
            self.device,
            self.goal_pos_args.pos_dim,
            self.goal_pos_args.path_units,
            self.goal_pos_args.meters_per_unit,
            frozen_path_for_cond=not use_train,
        )
        return cond_path
def main_cli():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--manifest-csv", required=True)
    ap.add_argument("--dino-head", required=True)
    ap.add_argument("--wp-head", required=True)
    ap.add_argument("--path-head-train", default="", help="Linear state_dict .pth for arm B")
    ap.add_argument("--config-e-dino", default="config/nomad_e_dino_path.yaml")
    ap.add_argument("--config-b", default="config/nomad_b40.yaml")
    ap.add_argument("--path-units", default="dataset")
    ap.add_argument("--path-source", default="wp_poly")
    ap.add_argument("--path-gate", default="none")
    ap.add_argument("--goal-pos-mode", default="blend_path")
    ap.add_argument("--wp-scale", type=float, default=1.0)
    ap.add_argument("--pos-dim", type=int, default=18)
    ap.add_argument("--epoch", type=int, default=0)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args()
    config_e = load_config(args.config_e_dino)
    config_b = load_config(args.config_b)
    _p, rows, _meta = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(CACHE_DIR, "train", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(args.dino_head, device)
    wp_head, _ = load_dino_head(args.wp_head, device)
    path_head_train = None
    if args.path_head_train:
        st = torch.load(args.path_head_train, map_location="cpu", weights_only=False)
        from e_path_joint_common import clone_path_output_layer
        path_head_train = clone_path_output_layer(wp_head)
        path_head_train.load_state_dict(st)
        path_head_train.to(device)
    gargs = argparse.Namespace(
        pos_dim=args.pos_dim,
        wp_scale=args.wp_scale,
        goal_pos_mode=args.goal_pos_mode,
        path_gate=args.path_gate,
        path_source=args.path_source,
        path_units=args.path_units,
        meters_per_unit=0.12,
    )
    ev = JointValEvaluator(
        args.manifest_csv,
        config_b,
        config_e,
        dino_head,
        wp_head,
        None,
        features,
        rows,
        device,
        gargs,
        path_head_train=path_head_train,
    )
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "ema" in state:
        state = state["ema"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    metrics, _ = ev.eval_ema_state_dict(state, epoch=args.epoch, out_dir=args.out_dir)
    metrics["epoch"] = args.epoch
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics))
if __name__ == "__main__":
    main_cli()

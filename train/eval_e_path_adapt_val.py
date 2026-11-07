"""Nav ADE on fixed far-val manifest for E path-adapt C/T training (true_pos_prob=0)."""
from __future__ import annotations
import csv
import json
import os
from dataclasses import dataclass
import cv2  # noqa: F401
import numpy as np
import torch
from eval_by_distance import load_config
from eval_goal_head import load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import encode_cond, load_model, mean_ade_fde
from train_e_dino import build_e_model, estimated_goal_pos
from train_goal_head import B_CHECKPOINT
from vint_train.training.train_utils import append_goal_pos, get_action
def load_manifest_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def manifest_to_frames(manifest: list[dict]):
    out = []
    for m in manifest:
        out.append((m["traj_name"], int(m["curr_t"]), int(m["goal_t"])))
    return out
def past_rows_batch(traj_names, curr_ts, rows, spacing=1, n_past=3):
    """[B, n_past] cache row indices (same fallback as ViNTWithDinoRows)."""
    batch = []
    for traj, curr_t in zip(traj_names, curr_ts):
        pr = []
        for j in range(1, n_past + 1):
            t_past = curr_t - j * spacing
            key = (traj, t_past)
            if t_past < 0 or key not in rows:
                pr.append(int(rows[(traj, curr_t)]))
            else:
                pr.append(int(rows[key]))
        batch.append(pr)
    return torch.tensor(batch, dtype=torch.int64)
@torch.no_grad()
def diffuse_shared(model, scheduler, cond, noise, num_samples, device, generator):
    cond = cond.repeat_interleave(num_samples, dim=0)
    sample = noise.clone()
    for k in scheduler.timesteps:
        noise_pred = model(
            "noise_pred_net",
            sample=sample,
            timestep=k.unsqueeze(-1).repeat(sample.shape[0]).to(device),
            global_cond=cond,
        )
        sample = scheduler.step(
            model_output=noise_pred,
            timestep=k,
            sample=sample,
            generator=generator,
        ).prev_sample
    actions = get_action(sample)
    return actions.reshape(noise.shape[0] // num_samples, num_samples, -1, noise.shape[-1])
def chunk_seed(base_seed, chunk_index):
    return int(base_seed + chunk_index * 10007)
def pregenerate_noise(n, num_samples, horizon, batch_size, device, seed):
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    chunks = []
    for start in range(0, n, batch_size):
        bs = min(batch_size, n - start)
        chunks.append(torch.randn((bs * num_samples, horizon, 2), device=device))
    return chunks
def nav_ade_cm_per_frame(nav_samples, gt, meters):
    out = np.zeros(len(gt), dtype=np.float64)
    for i in range(len(gt)):
        ade_m, _ = mean_ade_fde(nav_samples[i], gt[i], meters)
        out[i] = ade_m * 100.0
    return out


def nav_ade_cm_decomposed_per_frame(nav_samples, gt, meters):
    """Per frame: mean over num_samples then mean over timesteps (front4/back4 split)."""
    n = len(gt)
    full = np.zeros(n, dtype=np.float64)
    front4 = np.zeros(n, dtype=np.float64)
    back4 = np.zeros(n, dtype=np.float64)
    for i in range(len(gt)):
        dist = np.linalg.norm((nav_samples[i] - gt[i][None, :, :]) * meters, axis=-1)
        full[i] = dist.mean() * 100.0
        front4[i] = dist[:, :4].mean() * 100.0
        back4[i] = dist[:, 4:].mean() * 100.0
    return full, front4, back4
def bootstrap_trajectory_pooled(delta_cm, traj_names, n_boot=10000, seed=20261104):
    delta_cm = np.asarray(delta_cm, dtype=np.float64)
    traj_names = np.asarray(traj_names)
    uniq = np.unique(traj_names)
    by_traj = {u: delta_cm[traj_names == u] for u in uniq}
    if len(uniq) < 2:
        m = float(delta_cm.mean()) if delta_cm.size else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        boots[b] = np.concatenate([by_traj[t] for t in pick]).mean()
    return float(delta_cm.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))
@dataclass
class ValNavEvaluator:
    manifest_csv: str
    config_b: dict
    config_e: dict
    dino_head: torch.nn.Module
    wp_head: torch.nn.Module
    wp_path_head: torch.nn.Module | None
    features: np.ndarray
    rows: dict
    device: torch.device
    goal_pos_args: object
    num_samples: int = 8
    batch_size: int = 8
    seed: int = 0
    def __post_init__(self):
        from eval_by_distance import load_observation
        self._load_observation = load_observation
        self.manifest = load_manifest_csv(self.manifest_csv)
        self.frames = manifest_to_frames(self.manifest)
        self.dataset = make_split_dataset(self.config_b, "train")
        self.meters = float(meters_per_unit(self.dataset))
        self.horizon = int(self.dataset.len_traj_pred)
        if hasattr(self.goal_pos_args, "meters_per_unit"):
            self.goal_pos_args.meters_per_unit = self.meters
        self.loc_model = load_frozen_nomad(self.config_b, B_CHECKPOINT, self.device)
        self.model, self.scheduler = build_e_model(self.config_e, self.goal_pos_args.pos_dim)
        self.model.to(self.device)
        self.noise_chunks = pregenerate_noise(
            len(self.frames),
            self.num_samples,
            self.horizon,
            self.batch_size,
            self.device,
            self.seed,
        )
    def _load_gt(self):
        gt = []
        for traj_name, t, goal_time in self.frames:
            _o, _g, actions, _p = self._load_observation(self.dataset, traj_name, t, goal_time)
            xy = np.asarray(actions, dtype=np.float32)[:, :2]
            gt.append(xy)
        return np.stack(gt, axis=0)
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
        return estimated_goal_pos(
            self.loc_model,
            self.dino_head,
            self.features,
            batch_obs,
            batch_goal,
            np.array(curr_rows, dtype=np.int64),
            np.array(goal_rows, dtype=np.int64),
            self.goal_pos_args.pos_dim,
            self.device,
            wp_head=self.wp_head,
            wp_path_head=self.wp_path_head,
            wp_scale=self.goal_pos_args.wp_scale,
            goal_pos_mode=self.goal_pos_args.goal_pos_mode,
            past_rows=past_rows,
            path_gate=self.goal_pos_args.path_gate,
            path_source=self.goal_pos_args.path_source,
            meters_per_unit=self.goal_pos_args.meters_per_unit,
            path_units=self.goal_pos_args.path_units,
        )
    def _subset_means(self, ade_pf, front4, back4):
        turn = np.asarray(
            [float(m.get("turn_strict", 0) or 0) > 0.5 for m in self.manifest], dtype=bool
        )
        out = {
            "nav_ade_cm": float(ade_pf.mean()),
            "ade_front4_cm": float(front4.mean()),
            "ade_back4_cm": float(back4.mean()),
            "n_val": int(len(ade_pf)),
        }
        if turn.any():
            out["nav_ade_turn_strict_cm"] = float(ade_pf[turn].mean())
            out["ade_front4_turn_strict_cm"] = float(front4[turn].mean())
            out["ade_back4_turn_strict_cm"] = float(back4[turn].mean())
            out["turn_strict_n"] = int(turn.sum())
        else:
            out["nav_ade_turn_strict_cm"] = float("nan")
            out["turn_strict_n"] = 0
        return out

    @torch.no_grad()
    def eval_ema_state_dict(self, state_dict, epoch: int = -1, out_dir: str = "") -> tuple[dict, str]:
        self.model.load_state_dict(state_dict, strict=True)
        self.model.eval()
        n = len(self.frames)
        gt = self._load_gt()
        preds = np.zeros((n, self.num_samples, self.horizon, 2), dtype=np.float32)
        for chunk_index, start in enumerate(range(0, n, self.batch_size)):
            chunk_len = min(self.batch_size, n - start)
            chunk = self.frames[start : start + chunk_len]
            obs_list, goal_list = [], []
            for traj_name, t, goal_time in chunk:
                obs, goal, _a, _p = self._load_observation(self.dataset, traj_name, t, goal_time)
                obs_list.append(obs)
                goal_list.append(goal)
            batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), self.device)
            est_pos = self.build_est_pos_batch(start, chunk_len)
            init_noise = self.noise_chunks[chunk_index].clone()
            gen = torch.Generator(device=self.device)
            gen.manual_seed(chunk_seed(self.seed, chunk_index))
            cond_goal, mask_goal = encode_cond(self.model, batch_obs, batch_goal, 0, self.device)
            cond_goal = append_goal_pos(cond_goal, est_pos, mask_goal)
            pred = diffuse_shared(
                self.model, self.scheduler, cond_goal, init_noise, self.num_samples, self.device, gen
            )
            preds[start : start + chunk_len] = pred[..., :2].detach().cpu().numpy()
        ade_pf, front4, back4 = nav_ade_cm_decomposed_per_frame(preds, gt, self.meters)
        metrics = self._subset_means(ade_pf, front4, back4)
        csv_path = ""
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            csv_path = os.path.join(out_dir, f"val_nav_ade_epoch{epoch}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                w = csv.DictWriter(
                    cf,
                    fieldnames=[
                        "order",
                        "traj_name",
                        "curr_t",
                        "goal_t",
                        "goal_step",
                        "turn_strict",
                        "nav_ade_cm",
                        "ade_front4_cm",
                        "ade_back4_cm",
                    ],
                )
                w.writeheader()
                for i, m in enumerate(self.manifest):
                    w.writerow(
                        {
                            "order": m.get("order", i),
                            "traj_name": m["traj_name"],
                            "curr_t": m["curr_t"],
                            "goal_t": m["goal_t"],
                            "goal_step": m.get("goal_step", ""),
                            "turn_strict": m.get("turn_strict", ""),
                            "nav_ade_cm": float(ade_pf[i]),
                            "ade_front4_cm": float(front4[i]),
                            "ade_back4_cm": float(back4[i]),
                        }
                    )
        metrics["per_frame_csv"] = csv_path
        return metrics, csv_path
def eval_checkpoint_file(
    ckpt_path: str,
    manifest_csv: str,
    dino_head_path: str,
    wp_head_path: str,
    wp_path_head_path: str,
    device: torch.device,
    config_e_path: str = "config/nomad_e_dino_path.yaml",
    config_b_path: str = "config/nomad_b40.yaml",
) -> float:
    """Standalone eval for init reference checkpoint."""
    from train_e_dino import load_dino_head
    from train_goal_dino import CACHE_DIR, load_cache
    import argparse
    config_e = load_config(config_e_path)
    config_b = load_config(config_b_path)
    _p, rows, _meta = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(CACHE_DIR, "train", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(dino_head_path, device)
    wp_head, _ = load_dino_head(wp_head_path, device)
    wp_path_head = None
    if wp_path_head_path:
        wp_path_head, _ = load_dino_head(wp_path_head_path, device)
    args = argparse.Namespace(
        pos_dim=18,
        wp_scale=1.0,
        goal_pos_mode="blend_path",
        path_gate="none",
        path_source="wp_poly",
        path_units="dataset",
        meters_per_unit=0.12,
    )
    ev = ValNavEvaluator(
        manifest_csv,
        config_b,
        config_e,
        dino_head,
        wp_head,
        wp_path_head,
        features,
        rows,
        device,
        args,
    )
    state = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    return ev.eval_ema_state_dict(state, epoch=-1, out_dir="")[0]["nav_ade_cm"]

def main_cli():
    import argparse
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ap = argparse.ArgumentParser(description="Val nav ADE for one E checkpoint (subprocess-safe)")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--manifest-csv", required=True)
    ap.add_argument("--dino-head", required=True)
    ap.add_argument("--wp-head", default="")
    ap.add_argument("--wp-path-head", default="")
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
    from train_e_dino import load_dino_head
    from train_goal_dino import CACHE_DIR, load_cache
    import argparse as apmod
    config_e = load_config(args.config_e_dino)
    config_b = load_config(args.config_b)
    _p, rows, _meta = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(CACHE_DIR, "train", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(args.dino_head, device)
    wp_head = None
    if args.wp_head:
        wp_head, _ = load_dino_head(args.wp_head, device)
    wp_path_head = None
    if args.wp_path_head:
        wp_path_head, _ = load_dino_head(args.wp_path_head, device)
    if args.goal_pos_mode in ("blend", "blend_path") and wp_head is None:
        raise ValueError(f"{args.goal_pos_mode} requires --wp-head")
    if args.goal_pos_mode == "goal_path" and args.pos_dim > 2 and wp_path_head is None:
        raise ValueError("goal_path pos_dim>2 requires --wp-path-head")
    gargs = apmod.Namespace(
        pos_dim=args.pos_dim,
        wp_scale=args.wp_scale,
        goal_pos_mode=args.goal_pos_mode,
        path_gate=args.path_gate,
        path_source=args.path_source,
        path_units=args.path_units,
        meters_per_unit=0.12,
    )
    ev = ValNavEvaluator(
        args.manifest_csv,
        config_b,
        config_e,
        dino_head,
        wp_head,
        wp_path_head,
        features,
        rows,
        device,
        gargs,
    )
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    metrics, csv_path = ev.eval_ema_state_dict(state, epoch=args.epoch, out_dir=args.out_dir)
    metrics["epoch"] = args.epoch
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics))


if __name__ == "__main__":
    main_cli()

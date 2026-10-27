"""Integrated kappa-blend inference: DINO goal + waypoint heads × B distance → E-oracle.

One class loads all weights and runs a single control step. Also benchmarks
wall-clock latency (breakdown + total Hz) and optionally checks ADE against the
locked far-frame blend recipe.

Run from train/:
    python -u infer_kappa_blend.py --bench
    python -u infer_kappa_blend.py --bench --check --n-check 64
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from cache_dino_features import IMAGENET_MEAN, IMAGENET_STD, tokens as dino_tokens
from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES
from eval_goal_head import (
    B_CHECKPOINT,
    load_frozen_nomad,
    make_split_dataset,
    meters_per_unit,
    normalize_images,
)
from eval_position_noise import diffuse, encode_cond, load_model
from adaptive_blend import angle_between_deg, blend_suppress_torch, suppress_from_wp_turn
from eval_waypoint_head import blend
from train_e_dino import DINO_BEST, load_dino_head
from vint_train.data.data_utils import IMAGE_ASPECT_RATIO, get_data_path
from vint_train.training.train_utils import append_goal_pos

WP_BEST = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
DINO_HUB = "dinov2_vits14_reg"
DINO_SIZE = (224, 168)  # W, H — matches cache / head meta
DINO_POOL = 2


class KappaBlendNavigator:
    """Deployable stack: frozen B distance + dual DINO heads + untrained E-oracle."""

    def __init__(
        self,
        device,
        config_b="config/nomad_b40.yaml",
        config_e="config/nomad_e_oracle.yaml",
        b_ckpt=B_CHECKPOINT,
        e_ckpt=E_CHECKPOINT,
        goal_head_ckpt=DINO_BEST,
        wp_head_ckpt=WP_BEST,
        wp_scale=1.0,
        gate_wp_lo=90.0,
        gate_wp_hi=90.0,
        gate_turn_weight=0.0,
        gate_cap=1.0,
        gate_turn_strict=None,
        load_dino=True,
        dino_half=True,
    ):
        self.device = torch.device(device)
        self.wp_scale = float(wp_scale)
        self.gate_wp_lo = float(gate_wp_lo)
        self.gate_wp_hi = float(gate_wp_hi)
        self.gate_turn_weight = float(gate_turn_weight)
        self.gate_cap = float(gate_cap)
        self.gate_turn_strict = gate_turn_strict
        self.config_b = load_config(config_b)
        self.config_e = load_config(config_e)
        self.context_size = int(self.config_b["context_size"])
        self.len_traj_pred = int(self.config_e["len_traj_pred"])
        self.num_diffusion_iters = int(self.config_e["num_diffusion_iters"])

        self.model_b = load_frozen_nomad(self.config_b, b_ckpt, self.device)
        self.model_e, self.scheduler = load_model(self.config_e, e_ckpt, self.device)
        self.goal_head, self.goal_meta = load_dino_head(goal_head_ckpt, self.device)
        self.wp_head, self.wp_meta = load_dino_head(wp_head_ckpt, self.device)
        if self.goal_meta["tokens"] != self.wp_meta["tokens"] or self.goal_meta["dim"] != self.wp_meta["dim"]:
            raise RuntimeError(f"head metas disagree: goal={self.goal_meta} wp={self.wp_meta}")

        self.dino = None
        self.dino_half = dino_half
        if load_dino:
            self.dino = torch.hub.load("facebookresearch/dinov2", DINO_HUB, trust_repo=True, skip_validation=True)
            self.dino = self.dino.to(self.device).eval()
            if dino_half:
                self.dino = self.dino.half()
            for p in self.dino.parameters():
                p.requires_grad_(False)
        self._mean = torch.tensor(IMAGENET_MEAN, device=self.device).view(1, 3, 1, 1)
        self._std = torch.tensor(IMAGENET_STD, device=self.device).view(1, 3, 1, 1)

    @torch.no_grad()
    def preprocess_dino(self, images):
        """PIL Image or list → [B, 3, H, W] ImageNet-normalized float (or half)."""
        if isinstance(images, Image.Image):
            images = [images]
        xs = []
        for img in images:
            if not isinstance(img, Image.Image):
                raise TypeError(f"expected PIL Image, got {type(img)}")
            img = img.convert("RGB")
            w, h = img.size
            if w > h:
                img = img.crop(
                    ((w - int(h * IMAGE_ASPECT_RATIO)) // 2, 0, (w + int(h * IMAGE_ASPECT_RATIO)) // 2, h)
                )
            img = img.resize(DINO_SIZE, Image.BICUBIC)
            x = torch.from_numpy(np.asarray(img, dtype=np.float32) / 255.0).permute(2, 0, 1)
            xs.append(x)
        batch = torch.stack(xs, dim=0).to(self.device)
        batch = (batch - self._mean) / self._std
        if self.dino_half:
            batch = batch.half()
        return batch

    @torch.no_grad()
    def encode_dino(self, images):
        if self.dino is None:
            raise RuntimeError("DINOv2 was not loaded; pass load_dino=True or supply tokens")
        x = self.preprocess_dino(images)
        feat = dino_tokens(self.dino, x, DINO_POOL).float()
        return feat

    @torch.no_grad()
    def b_steps(self, batch_obs, batch_goal):
        no_mask = torch.zeros(batch_obs.shape[0], dtype=torch.long, device=self.device)
        cond = self.model_b("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
        return self.model_b("dist_pred_net", obsgoal_cond=cond).squeeze(-1).clamp(min=0.0)

    @torch.no_grad()
    def blend_goal_pos(self, curr_tok, goal_tok, steps):
        g_out = self.goal_head(curr_tok, goal_tok)
        w_out = self.wp_head(curr_tok, goal_tok)
        g_dir, g_k = g_out[0], g_out[1]
        w_dir, w_k = w_out[0], w_out[1]
        if self.gate_turn_weight > 0 or self.gate_wp_lo < self.gate_wp_hi:
            wp_err = angle_between_deg(g_dir.detach().cpu().numpy(), w_dir.detach().cpu().numpy())
            turn = self.gate_turn_strict
            if turn is None:
                turn = np.zeros(len(wp_err), dtype=np.float32)
            elif not isinstance(turn, np.ndarray):
                turn = np.asarray(turn, dtype=np.float32)
            suppress = suppress_from_wp_turn(
                wp_err,
                turn,
                wp_lo=self.gate_wp_lo,
                wp_hi=self.gate_wp_hi,
                turn_weight=self.gate_turn_weight,
                cap=self.gate_cap,
            )
            d = blend_suppress_torch(g_dir, g_k, w_dir, w_k, torch.tensor(suppress, device=g_dir.device), self.wp_scale)
        else:
            r = g_k[:, None] * g_dir + (self.wp_scale * w_k)[:, None] * w_dir
            d = r / r.norm(dim=1, keepdim=True).clamp(min=1e-6)
        pos = d * steps.unsqueeze(-1)
        return pos, {
            "goal_dir": g_dir,
            "goal_kappa": g_k,
            "wp_dir": w_dir,
            "wp_kappa": w_k,
            "blend_dir": d,
            "steps": steps,
        }

    @torch.no_grad()
    def diffuse_actions(self, batch_obs, batch_goal, goal_pos, num_samples=1, seed=0):
        cond, mask = encode_cond(self.model_e, batch_obs, batch_goal, 0, self.device)
        cond = append_goal_pos(cond, goal_pos, mask)
        b = batch_obs.shape[0]
        gen = torch.Generator(device=self.device)
        gen.manual_seed(int(seed))
        noise = torch.randn(
            (b * num_samples, self.len_traj_pred, 2), device=self.device, generator=gen
        )
        return diffuse(self.model_e, self.scheduler, cond, noise, num_samples, self.device)

    @torch.no_grad()
    def step(
        self,
        obs_context_pils,
        goal_pil,
        batch_obs=None,
        batch_goal=None,
        curr_tok=None,
        goal_tok=None,
        num_samples=1,
        seed=0,
        profile=None,
    ):
        """One control step.

        Provide either PIL context+goal (live path) or prebuilt NoMaD tensors +
        optional precomputed DINO tokens (cache path for checks).
        obs_context_pils: list of context_size+1 PILs, oldest → current.
        """
        t0 = time.perf_counter()
        marks = {}

        if batch_obs is None or batch_goal is None:
            raise ValueError("batch_obs and batch_goal are required (NoMaD image tensors)")

        def mark(name):
            if profile is not None:
                marks[name] = time.perf_counter() - t0

        if curr_tok is None or goal_tok is None:
            if obs_context_pils is None or goal_pil is None:
                raise ValueError("need PIL frames or precomputed DINO tokens")
            # Current frame is the last in the context stack (matches training).
            curr_tok = self.encode_dino(obs_context_pils[-1])
            mark("dino_curr_ms")
            goal_tok = self.encode_dino(goal_pil)
            mark("dino_goal_ms")
        else:
            curr_tok = curr_tok.to(self.device).float()
            goal_tok = goal_tok.to(self.device).float()
            mark("dino_skip_ms")

        steps = self.b_steps(batch_obs, batch_goal)
        mark("b_distance_ms")
        goal_pos, aux = self.blend_goal_pos(curr_tok, goal_tok, steps)
        mark("heads_blend_ms")
        actions = self.diffuse_actions(batch_obs, batch_goal, goal_pos, num_samples=num_samples, seed=seed)
        mark("e_diffusion_ms")
        mark("total_ms")

        if profile is not None:
            # Convert cumulative marks into stage durations.
            keys = list(marks)
            prev = 0.0
            for k in keys:
                cum = marks[k]
                profile[k] = (cum - prev) * 1000.0
                prev = cum
            profile["total_ms"] = marks["total_ms"] * 1000.0

        return actions, goal_pos, aux


def _load_pils(dataset, traj_name, times):
    folder = dataset.data_folder
    return [Image.open(get_data_path(folder, traj_name, t)).convert("RGB") for t in times]


def _context_times(dataset, t):
    ws = dataset.waypoint_spacing
    return list(range(t - dataset.context_size * ws, t + 1, ws))


@torch.no_grad()
def bench(nav, dataset, moments, n, num_samples, seed, use_online_dino, out_dir):
    meters = meters_per_unit(dataset)
    device = nav.device
    # Prefer far goals — that is the deploy target for this stack.
    items = []
    for traj_name, t, goals in moments:
        g = [x[4] for x in goals if x[0] == "20-40"][0]
        items.append((traj_name, t, g))
        if len(items) >= n:
            break

    # Warmup
    traj_name, t, g = items[0]
    obs, goal, _a, _p = load_observation(dataset, traj_name, t, g)
    batch_obs, batch_goal = normalize_images(obs.unsqueeze(0), goal.unsqueeze(0), device)
    ctx = _load_pils(dataset, traj_name, _context_times(dataset, t))
    goal_pil = _load_pils(dataset, traj_name, [g])[0]
    for _ in range(3):
        if use_online_dino:
            nav.step(ctx, goal_pil, batch_obs, batch_goal, num_samples=num_samples, seed=seed)
        else:
            # Cache path warmup needs tokens — encode once via online if available.
            if nav.dino is not None:
                ct = nav.encode_dino(ctx[-1])
                gt = nav.encode_dino(goal_pil)
            else:
                raise RuntimeError("online DINO required for warmup without cache args")
            nav.step(None, None, batch_obs, batch_goal, curr_tok=ct, goal_tok=gt, num_samples=num_samples, seed=seed)

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    rows = []
    totals = []
    for i, (traj_name, t, g) in enumerate(tqdm(items, desc="bench")):
        obs, goal, _a, _p = load_observation(dataset, traj_name, t, g)
        batch_obs, batch_goal = normalize_images(obs.unsqueeze(0), goal.unsqueeze(0), device)
        ctx = _load_pils(dataset, traj_name, _context_times(dataset, t))
        goal_pil = _load_pils(dataset, traj_name, [g])[0]
        profile = {}
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        if use_online_dino:
            actions, goal_pos, aux = nav.step(
                ctx, goal_pil, batch_obs, batch_goal, num_samples=num_samples, seed=seed + i, profile=profile
            )
        else:
            ct = nav.encode_dino(ctx[-1])
            gt = nav.encode_dino(goal_pil)
            # Re-time with tokens precomputed so "cache mode" isolates policy.
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            profile = {}
            t0 = time.perf_counter()
            actions, goal_pos, aux = nav.step(
                None, None, batch_obs, batch_goal, curr_tok=ct, goal_tok=gt, num_samples=num_samples, seed=seed + i, profile=profile
            )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        wall = (time.perf_counter() - t0) * 1000.0
        totals.append(wall)
        row = {"i": i, "traj": traj_name, "wall_ms": wall, **profile}
        row["steps"] = float(aux["steps"][0].cpu())
        row["goal_pos_m"] = float(torch.norm(goal_pos[0]).cpu() * meters)
        rows.append(row)

    arr = np.array(totals)
    summary = {
        "n": len(totals),
        "num_samples": num_samples,
        "use_online_dino": use_online_dino,
        "wp_scale": nav.wp_scale,
        "device": str(nav.device),
        "wall_ms_mean": float(arr.mean()),
        "wall_ms_median": float(np.median(arr)),
        "wall_ms_p90": float(np.percentile(arr, 90)),
        "hz_mean": float(1000.0 / arr.mean()),
        "stages_ms_mean": {},
    }
    stage_keys = [k for k in rows[0] if k.endswith("_ms") and k != "wall_ms"]
    for k in stage_keys:
        summary["stages_ms_mean"][k] = float(np.mean([r[k] for r in rows]))

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "latency.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "per_frame": rows}, f, indent=2)
    print("\n[latency]")
    print(f"  n={summary['n']}  online_dino={use_online_dino}  num_samples={num_samples}")
    print(
        f"  wall mean/median/p90: {summary['wall_ms_mean']:.1f} / "
        f"{summary['wall_ms_median']:.1f} / {summary['wall_ms_p90']:.1f} ms "
        f"({summary['hz_mean']:.2f} Hz)"
    )
    for k, v in summary["stages_ms_mean"].items():
        print(f"  {k:<18} {v:6.1f} ms")
    print(f"Saved {os.path.abspath(os.path.join(out_dir, 'latency.json'))}")
    return summary


@torch.no_grad()
def check_ade(nav, dataset, moments, n, num_samples, seed):
    """Sanity: online blend ADE should match numpy blend × cached-style recipe on same frames."""
    from eval_testtime import rollout

    device = nav.device
    items = []
    for traj_name, t, goals in moments:
        g = [x[4] for x in goals if x[0] == "20-40"][0]
        items.append((traj_name, t, g))
        if len(items) >= n:
            break

    pos_online = []
    pos_numpy = []
    for traj_name, t, g in tqdm(items, desc="check-pos"):
        obs, goal, _a, true_pos = load_observation(dataset, traj_name, t, g)
        batch_obs, batch_goal = normalize_images(obs.unsqueeze(0), goal.unsqueeze(0), device)
        ctx = _load_pils(dataset, traj_name, _context_times(dataset, t))
        goal_pil = _load_pils(dataset, traj_name, [g])[0]
        _actions, goal_pos, aux = nav.step(ctx, goal_pil, batch_obs, batch_goal, num_samples=1, seed=0)
        pos_online.append(goal_pos[0].cpu().numpy())
        # Rebuild with numpy blend from aux (should be identical to torch path).
        gd = aux["goal_dir"].cpu().numpy()
        gk = aux["goal_kappa"].cpu().numpy()
        wd = aux["wp_dir"].cpu().numpy()
        wk = aux["wp_kappa"].cpu().numpy()
        st = aux["steps"].cpu().numpy()
        pos_numpy.append(blend(gd, gk, wd, nav.wp_scale * wk)[0] * st[0])

    pos_online = np.stack(pos_online).astype(np.float32)
    pos_numpy = np.stack(pos_numpy).astype(np.float32)
    delta = np.linalg.norm(pos_online - pos_numpy, axis=1).mean()
    print(f"[check] torch vs numpy blend pos L2 mean: {delta:.6f} (dataset units)")

    # Quick E-oracle ADE vs masked on this subset (smoke, not the locked table).
    true = np.stack([load_observation(dataset, n, t, g)[3][:2] for n, t, g in items]).astype(np.float32)
    am, ade = rollout(
        nav.model_e,
        nav.scheduler,
        dataset,
        items,
        {"kappa blend": pos_online, "true goal": true},
        device,
        num_samples,
        8,
        seed,
        "check",
    )
    use_b = float((am - ade["kappa blend"]).mean())
    use_t = float((am - ade["true goal"]).mean())
    print(f"[check] subset n={n}: blend use {100 * use_b:+.2f} cm ({100 * use_b / use_t:.0f}% of true)")
    return {"pos_l2": float(delta), "use_cm": 100 * use_b, "vs_true": use_b / use_t}


def main():
    parser = argparse.ArgumentParser(description="Integrated kappa-blend inference + latency")
    parser.add_argument("--bench", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--n-bench", type=int, default=50)
    parser.add_argument("--n-check", type=int, default=64)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--wp-scale", type=float, default=1.0)
    parser.add_argument("--gate-wp-lo", type=float, default=90.0, help="Deploy: goal-wp disagree deg; set lo<hi to enable")
    parser.add_argument("--gate-wp-hi", type=float, default=90.0)
    parser.add_argument("--gate-turn-weight", type=float, default=0.0, help="Requires gate_turn_strict at deploy time")
    parser.add_argument("--gate-cap", type=float, default=1.0)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--no-dino-half", action="store_true")
    parser.add_argument("--cache-only", action="store_true", help="Skip timing DINO (still loads it for check)")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--out-dir", default="logs/revalidation/infer_kappa_blend")
    parser.add_argument("--goal-head", default=DINO_BEST, help="DINO goal direction checkpoint (default: e60 best)")
    args = parser.parse_args()
    if not args.bench and not args.check:
        args.bench = True

    os.makedirs(args.out_dir, exist_ok=True)
    nav = KappaBlendNavigator(
        device=args.device,
        wp_scale=args.wp_scale,
        gate_wp_lo=args.gate_wp_lo,
        gate_wp_hi=args.gate_wp_hi,
        gate_turn_weight=args.gate_turn_weight,
        gate_cap=args.gate_cap,
        load_dino=True,
        dino_half=not args.no_dino_half,
        goal_head_ckpt=args.goal_head,
    )
    dataset = make_split_dataset(nav.config_b, "test")
    moments = load_paired_frames(args.frames)

    results = {}
    if args.bench:
        results["latency"] = bench(
            nav, dataset, moments, args.n_bench, args.num_samples, args.seed, use_online_dino=not args.cache_only, out_dir=args.out_dir
        )
    if args.check:
        results["check"] = check_ade(nav, dataset, moments, args.n_check, args.num_samples, args.seed)
    with open(os.path.join(args.out_dir, "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Done. Outputs in {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()

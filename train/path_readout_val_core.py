"""Shared logic for path readout validation v2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from path_end_dir_metrics import end_dir_err_deg, frac_above, path_ade_cm
from train_goal_dir import FAR_STEPS
from train_goal_dino import _parse_batch, draw, loader
from train_e_dino import load_dino_head

VAL_RNG_SEED = 1234
BOOTSTRAP_SEED = 12345
BOOTSTRAP_N = 2000


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checkpoint_info(path: str, label: str, note: str = "") -> dict:
    p = Path(path)
    state = torch.load(str(p), map_location="cpu", weights_only=False)
    args = state.get("args") or {}
    rec = {
        "label": label,
        "path": str(p).replace("\\", "/"),
        "sha256": sha256_file(str(p)),
        "epoch": int(state.get("epoch", -1)),
        "far_median_deg": float(state.get("far_median_deg", float("nan"))),
        "path_spatial": args.get("path_spatial", "") or "cls",
        "path_steps": int(args.get("path_steps", 0) or 0),
        "context": int(args.get("context", 0) or 0),
        "freeze_dir": bool(args.get("freeze_dir", False)),
        "note": note,
    }
    return rec


def frame_slot_for_pair_idx(pairs: dict, pair_idx: int) -> int:
    return int(np.searchsorted(pairs["starts"], pair_idx, side="right") - 1)


def build_manifest(pairs: dict, chosen: np.ndarray, rows: dict) -> list[dict]:
    inv = {v: k for k, v in rows.items()}
    manifest = []
    for order, pair_idx in enumerate(chosen.tolist()):
        pair_idx = int(pair_idx)
        curr_row = int(pairs["curr"][pair_idx])
        goal_row = int(pairs["goal"][pair_idx])
        step = int(pairs["steps"][pair_idx])
        traj, curr_t = inv[curr_row]
        traj_g, goal_t = inv[goal_row]
        if traj != traj_g:
            raise RuntimeError(f"traj mismatch pair {pair_idx}")
        slot = frame_slot_for_pair_idx(pairs, pair_idx)
        manifest.append(
            {
                "order": order,
                "pair_expand_idx": pair_idx,
                "frame_slot": slot,
                "traj_name": traj,
                "curr_t": int(curr_t),
                "goal_t": int(goal_t),
                "goal_step": step,
                "cache_curr_row": curr_row,
                "cache_goal_row": goal_row,
            }
        )
    return manifest


def manifest_stats(manifest: list[dict], pairs: dict) -> dict:
    steps = np.array([m["goal_step"] for m in manifest], dtype=np.int64)
    wind = np.array([float(pairs["winding"][m["pair_expand_idx"]]) for m in manifest])
    far = steps >= FAR_STEPS
    trajs = {m["traj_name"] for m in manifest}
    curr_keys = {(m["traj_name"], m["curr_t"]) for m in manifest}
    slots = {m["frame_slot"] for m in manifest}
    return {
        "n_samples": len(manifest),
        "n_unique_current_frames": len(curr_keys),
        "n_frame_slots": len(slots),
        "n_trajectories_in_manifest": len(trajs),
        "expected_frame_slots": len(pairs["starts"]),
        "goal_step_min": int(steps.min()) if len(steps) else 0,
        "goal_step_max": int(steps.max()) if len(steps) else 0,
        "goal_step_hist": {str(k): int(v) for k, v in zip(*np.unique(steps, return_counts=True))},
        "far_n": int(far.sum()),
        "winding_ge_45_n": int((wind >= 45.0).sum()),
        "winding_ge_90_n": int((wind >= 90.0).sum()),
        "turn_strict_n": int(sum(float(pairs["turn_strict"][m["pair_expand_idx"]]) > 0.5 for m in manifest)),
    }


def predict_path_samples(head, val_batches, device, meters_per_unit: float) -> dict:
    n = sum(len(b[0]) for b in val_batches)
    out = {
        "ade8_cm": np.full(n, np.nan),
        "ade_front4_cm": np.full(n, np.nan),
        "ade_back4_cm": np.full(n, np.nan),
        "ade_step8_cm": np.full(n, np.nan),
        "end_dir_err_deg": np.full(n, np.nan),
        "end_dir_valid": np.zeros(n, dtype=bool),
        "pred_polyline_turn_deg": np.full(n, np.nan),
    }
    off = 0
    head.eval()
    with torch.no_grad():
        for batch in val_batches:
            parsed = _parse_batch(batch, device)
            curr, goal, _target, _steps, ctx = parsed[:5]
            target_path, odom_t = parsed[10], parsed[11]
            if target_path is None:
                raise RuntimeError("target_path missing in batch")
            pred_out = head(curr, goal, ctx, odom=odom_t)
            path = pred_out[-1].float()
            bsz = path.shape[0]
            pred = path.cpu().numpy()
            gt = target_path.float().cpu().numpy()
            m = float(meters_per_unit)
            sl = slice(off, off + bsz)
            err = np.linalg.norm(pred - gt, axis=-1) * m * 100.0
            out["ade8_cm"][sl] = err.mean(axis=-1)
            out["ade_front4_cm"][sl] = err[:, :4].mean(axis=-1)
            out["ade_back4_cm"][sl] = err[:, 4:].mean(axis=-1)
            out["ade_step8_cm"][sl] = err[:, 7]
            ang, valid = end_dir_err_deg(pred[:, 7], gt[:, 7])
            out["end_dir_err_deg"][sl] = ang
            out["end_dir_valid"][sl] = valid
            if pred.shape[1] >= 3:
                dxy = pred[:, 1:] - pred[:, :-1]
                u = dxy / np.maximum(np.linalg.norm(dxy, axis=-1, keepdims=True), 1e-6)
                dot = np.clip((u[:, :-1] * u[:, 1:]).sum(-1), -1.0, 1.0)
                out["pred_polyline_turn_deg"][sl] = np.degrees(np.arccos(dot)).sum(axis=-1)
            off += bsz
    if off != n:
        raise RuntimeError(f"sample count mismatch {off} vs {n}")
    return out


def subset_mask(manifest, pairs, name: str) -> np.ndarray:
    n = len(manifest)
    m = np.zeros(n, dtype=bool)
    if name == "all":
        return np.ones(n, dtype=bool)
    for i, rec in enumerate(manifest):
        pi = rec["pair_expand_idx"]
        if name == "far":
            m[i] = rec["goal_step"] >= FAR_STEPS
        elif name == "winding_ge_45":
            m[i] = float(pairs["winding"][pi]) >= 45.0
        elif name == "winding_ge_90":
            m[i] = float(pairs["winding"][pi]) >= 90.0
        else:
            raise KeyError(name)
    return m


def summarize_subset(metrics: dict, mask: np.ndarray) -> dict:
    def stat(key, fn):
        x = metrics[key][mask]
        x = x[np.isfinite(x)]
        if x.size == 0:
            return {"mean": float("nan"), "median": float("nan"), "p90": float("nan"), "n": 0}
        return {
            "mean": float(x.mean()),
            "median": float(np.median(x)),
            "p90": float(np.percentile(x, 90)),
            "n": int(x.size),
        }

    end = metrics["end_dir_err_deg"][mask]
    ev = metrics["end_dir_valid"][mask]
    f45, c45, n45 = frac_above(end, 45.0, ev)
    f90, c90, n90 = frac_above(end, 90.0, ev)
    undef = int((~ev).sum())
    return {
        "ade8_cm": stat("ade8_cm", None),
        "ade_front4_cm": stat("ade_front4_cm", None),
        "ade_back4_cm": stat("ade_back4_cm", None),
        "ade_step8_cm": stat("ade_step8_cm", None),
        "end_dir_err_deg": stat("end_dir_err_deg", None),
        "end_dir_gt45_frac": f45,
        "end_dir_gt45_count": c45,
        "end_dir_gt45_denom": n45,
        "end_dir_gt90_frac": f90,
        "end_dir_gt90_count": c90,
        "end_dir_gt90_denom": n90,
        "end_dir_undefined_n": undef,
        "pred_polyline_turn_deg": stat("pred_polyline_turn_deg", None),
    }


def bootstrap_mean_diff(a: np.ndarray, b: np.ndarray, trajs: list[str], seed: int = BOOTSTRAP_SEED, n_boot: int = BOOTSTRAP_N):
    diff = b - a
    valid = np.isfinite(diff)
    diff = diff[valid]
    tr = np.array(trajs, dtype=object)[valid]
    uniq = np.unique(tr)
    by = {t: diff[tr == t] for t in uniq}
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        parts = [by[t] for t in pick]
        pooled = np.concatenate(parts)
        boots.append(float(pooled.mean()))
    boots = np.array(boots)
    return {
        "mean_diff": float(diff.mean()),
        "ci95_low": float(np.percentile(boots, 2.5)),
        "ci95_high": float(np.percentile(boots, 97.5)),
        "n_samples": int(diff.size),
        "n_trajectories": int(len(uniq)),
    }


def make_val_loader(cache_path, val_pairs, batch_size=512, context=2):
    chosen = draw(val_pairs, np.random.default_rng(VAL_RNG_SEED))
    batches = loader(cache_path, val_pairs, chosen, batch_size, False, 0, context)
    return chosen, batches
"""Scalar training target from success, path_odom_m, collision_count."""

from __future__ import annotations

import math
from typing import Any, Mapping


def task_reward(
    success: bool,
    path_odom_m: float,
    collision_count: int,
    ref_path_m: float | None = None,
    *,
    success_bonus: float = 1.0,
    fail_penalty: float = -1.0,
    collision_penalty: float = 0.35,
    path_penalty_per_m: float = 0.08,
    path_only_if_success: bool = True,
) -> float:
    """Higher is better. Used to weight BC samples and pick checkpoints."""
    r = success_bonus if success else fail_penalty
    r -= collision_penalty * float(max(0, collision_count))
    if path_only_if_success and not success:
        return r
    ref = ref_path_m if ref_path_m and ref_path_m > 0.1 else path_odom_m
    if ref > 0.1:
        r -= path_penalty_per_m * (float(path_odom_m) / ref)
    return r


def weight_from_reward(
    reward: float,
    *,
    temperature: float = 1.0,
    floor: float = 0.05,
    ceil: float = 3.0,
) -> float:
    if temperature <= 0:
        w = 1.0
    else:
        w = math.exp(reward / temperature)
    return float(min(ceil, max(floor, w)))


def episode_record(
    traj_name: str,
    success: bool,
    path_odom_m: float,
    collision_count: int,
    ref_path_m: float | None,
    reward_cfg: Mapping[str, Any],
) -> dict[str, Any]:
    kw = {k: reward_cfg[k] for k in reward_cfg if k != "temperature" and k != "weight_floor" and k != "weight_ceil"}
    reward = task_reward(
        success,
        path_odom_m,
        collision_count,
        ref_path_m,
        **kw,
    )
    w = weight_from_reward(
        reward,
        temperature=float(reward_cfg.get("temperature", 1.0)),
        floor=float(reward_cfg.get("weight_floor", 0.05)),
        ceil=float(reward_cfg.get("weight_ceil", 3.0)),
    )
    return {
        "traj": traj_name,
        "success": bool(success),
        "path_odom_m": float(path_odom_m),
        "collision_count": int(collision_count),
        "reward": float(reward),
        "weight": w,
    }
"""Align episode path_xy with teacher GT when using launch_tb3_house_at_run (spawn odom)."""

from __future__ import annotations

from typing import Any

import numpy as np


def teach_anchor_xy(ep: dict[str, Any], teach0: np.ndarray) -> np.ndarray:
    raw = ep.get("teach_anchor_xy")
    if raw and len(raw) >= 2:
        return np.asarray([float(raw[0]), float(raw[1])], dtype=np.float64)
    return teach0


def uses_spawn_odom(ep: dict[str, Any], path_xy: np.ndarray, teach0: np.ndarray) -> bool:
    if ep.get("spawn_at_launch") or ep.get("odom_frame") == "spawn_origin":
        return True
    if len(path_xy) == 0:
        return False
    reset_m = ep.get("reset_align_m")
    if reset_m is not None and float(reset_m) > 0.8:
        return False
    at_origin = float(np.linalg.norm(path_xy[0])) < 1.0
    teach_far = float(np.linalg.norm(teach0)) > 1.5
    raw_mismatch = float(np.linalg.norm(path_xy[0] - teach0)) > 3.0
    return at_origin and teach_far and raw_mismatch


def path_xy_world(ep: dict[str, Any], path_xy: np.ndarray, teach0: np.ndarray) -> np.ndarray:
    """path_xy in episode JSON is raw /odom; teacher GT is post-set_pose odom (world-aligned)."""
    if len(path_xy) == 0:
        return path_xy
    if not uses_spawn_odom(ep, path_xy, teach0):
        return path_xy
    anchor = teach_anchor_xy(ep, teach0)
    return path_xy + anchor
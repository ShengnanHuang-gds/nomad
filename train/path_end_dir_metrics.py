"""End-direction and path position metrics for frozen path-head validation."""
from __future__ import annotations

import numpy as np


def unit_xy(xy: np.ndarray, eps: float = 1e-8) -> tuple[np.ndarray, np.ndarray]:
    """Unit vectors and valid mask for last-dim=2 arrays."""
    xy = np.asarray(xy, dtype=np.float64)
    n = np.linalg.norm(xy, axis=-1)
    valid = n >= eps
    out = np.zeros_like(xy)
    if valid.any():
        out[valid] = xy[valid] / n[valid, None]
    return out, valid


def angle_deg_between(a: np.ndarray, b: np.ndarray, eps: float = 1e-8) -> tuple[np.ndarray, np.ndarray]:
    """Angle in degrees between 2D vectors (...,2). Returns (angle, valid)."""
    ua, va = unit_xy(a, eps)
    ub, vb = unit_xy(b, eps)
    valid = va & vb
    ang = np.full(a.shape[:-1], np.nan, dtype=np.float64)
    if valid.any():
        dot = np.clip((ua[valid] * ub[valid]).sum(-1), -1.0, 1.0)
        ang[valid] = np.degrees(np.arccos(dot))
    return ang, valid


def end_dir_err_deg(pred8: np.ndarray, gt8: np.ndarray, eps: float = 1e-8) -> tuple[np.ndarray, np.ndarray]:
    """Direction error at step 8 from robot origin."""
    return angle_deg_between(pred8, gt8, eps)


def frac_above(angles_deg: np.ndarray, threshold: float, valid: np.ndarray | None = None) -> tuple[float, int, int]:
    if valid is None:
        valid = np.isfinite(angles_deg)
    m = valid & np.isfinite(angles_deg)
    n = int(m.sum())
    if n == 0:
        return float("nan"), 0, 0
    frac = float((angles_deg[m] > threshold).mean())
    return frac, int((angles_deg[m] > threshold).sum()), n


def path_ade_cm(pred: np.ndarray, gt: np.ndarray, meters_per_unit: float) -> np.ndarray:
    """Per-sample mean L2 over steps, in cm."""
    err = np.linalg.norm(pred - gt, axis=-1) * float(meters_per_unit) * 100.0
    return err.mean(axis=-1)


def _self_test() -> None:
    z = np.array([[0.0, 0.0]])
    _, v = end_dir_err_deg(z, np.array([[1.0, 0.0]]))
    assert not v[0]
    a = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]])
    b = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    ang, v = end_dir_err_deg(a, b)
    assert v.all()
    assert abs(ang[0]) < 1e-6
    assert abs(ang[1] - 90.0) < 1e-5
    assert abs(ang[2] - 180.0) < 1e-5
    f45, _, n = frac_above(ang, 45.0, v)
    f90, _, _ = frac_above(ang, 90.0, v)
    assert n == 3 and abs(f45 - 2 / 3) < 1e-6 and abs(f90 - 1 / 3) < 1e-6
    print("path_end_dir_metrics self-test ok")


if __name__ == "__main__":
    _self_test()
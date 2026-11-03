"""Integrate per-step yaw deltas into a deploy WP unit direction (body +x forward)."""
import numpy as np
import torch

ODOM_YAW_SCALE_DEG = 45.0


def wrap_rad(d):
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def past_odom_yaw_feat(yaw, t, spacing, scale=ODOM_YAW_SCALE_DEG):
    """Signed past yaw over 1 and 2 spacings, scaled by 45 deg, clipped to [-4, 4]."""
    yaw = np.asarray(yaw, dtype=np.float64).reshape(-1)
    t = int(t)
    spacing = max(int(spacing), 1)
    t = min(max(t, 0), len(yaw) - 1)
    y_t = float(yaw[t])
    out = np.zeros(2, dtype=np.float32)
    for i, k in enumerate((1, 2)):
        t0 = t - k * spacing
        if t0 < 0:
            continue
        dy = wrap_rad(y_t - float(yaw[t0]))
        out[i] = np.clip(np.degrees(dy) / float(scale), -4.0, 4.0)
    return out


def odom_feats_for_items(dataset, items):
    spacing = int(getattr(dataset, "waypoint_spacing", 1))
    feats = np.zeros((len(items), 2), dtype=np.float32)
    for i, item in enumerate(items):
        name, t = item[0], int(item[1])
        traj = dataset._get_trajectory(name)
        feats[i] = past_odom_yaw_feat(traj["yaw"], t, spacing)
    return feats


def integrated_yaw_unit_direction(dyaw_rad, step_len=None, yaw_first=False):
    """dyaw_rad: (N, K) radians per step.

    Default matches deploy: each step is unit length, the step is taken at the
    current heading, then that step's dyaw is applied. The last dyaw therefore
    does not move the endpoint. step_len (N, K) replaces the unit length.
    yaw_first applies dyaw before the step (probe only; deploy leaves it false).
    """
    psi = torch.zeros(dyaw_rad.shape[0], device=dyaw_rad.device, dtype=dyaw_rad.dtype)
    x = torch.zeros_like(psi)
    y = torch.zeros_like(psi)
    for i in range(dyaw_rad.shape[1]):
        if yaw_first:
            psi = psi + dyaw_rad[:, i]
        if step_len is None:
            x = x + torch.cos(psi)
            y = y + torch.sin(psi)
        else:
            x = x + step_len[:, i] * torch.cos(psi)
            y = y + step_len[:, i] * torch.sin(psi)
        if not yaw_first:
            psi = psi + dyaw_rad[:, i]
    d = torch.stack([x, y], dim=-1)
    return d / d.norm(dim=-1, keepdim=True).clamp(min=1e-6)


def yaw_tensor_from_out(head, out):
    steps = int(getattr(head, "yaw_aux_steps", 0) or 0)
    if steps <= 0:
        return None
    for item in reversed(out):
        if isinstance(item, torch.Tensor) and item.ndim == 2 and item.shape[1] == steps:
            return item
    return None


def path_tensor_from_out(head, out):
    steps = int(getattr(head, "path_steps", 0) or 0)
    if steps <= 0:
        return None
    for item in reversed(out):
        if (
            isinstance(item, torch.Tensor)
            and item.ndim == 3
            and item.shape[-1] == 2
            and item.shape[1] == steps
        ):
            return item
    return None


def wp_direction_from_head(head, out, mode="auto"):
    """vm = endpoint head; path = normalize(last polyline point); yaw_integrated = integrate(yaw)."""
    d_vm, k = out[0], out[1]
    yaw = yaw_tensor_from_out(head, out)
    path = path_tensor_from_out(head, out)
    if mode == "auto":
        if path is not None:
            mode = "path"
        elif yaw is not None:
            mode = "yaw_integrated"
        else:
            mode = "vm"
    if mode == "path" and path is not None:
        d = path[:, -1].float()
        return d / d.norm(dim=-1, keepdim=True).clamp(min=1e-6), k
    if mode == "yaw_integrated" and yaw is not None:
        return integrated_yaw_unit_direction(yaw.float()), k
    return d_vm, k

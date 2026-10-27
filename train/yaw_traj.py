"""Integrate per-step yaw deltas into a deploy WP unit direction (body +x forward)."""
import torch


def integrated_yaw_unit_direction(dyaw_rad):
    """dyaw_rad: (N, K) radians per step; K unit forward steps."""
    psi = torch.zeros(dyaw_rad.shape[0], device=dyaw_rad.device, dtype=dyaw_rad.dtype)
    x = torch.zeros_like(psi)
    y = torch.zeros_like(psi)
    for i in range(dyaw_rad.shape[1]):
        x = x + torch.cos(psi)
        y = y + torch.sin(psi)
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


def wp_direction_from_head(head, out, mode="auto"):
    """vm = legacy endpoint head; yaw_integrated = deploy path for yaw-traj models."""
    d_vm, k = out[0], out[1]
    yaw = yaw_tensor_from_out(head, out)
    if mode == "auto":
        mode = "yaw_integrated" if yaw is not None else "vm"
    if mode == "yaw_integrated" and yaw is not None:
        return integrated_yaw_unit_direction(yaw.float()), k
    return d_vm, k
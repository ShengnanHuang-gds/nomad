"""Inference-time sector gating for PairTokenHead (left / center / right)."""

import numpy as np
import torch


def bearing_deg_xy(xy):
    return torch.rad2deg(torch.atan2(xy[..., 1], xy[..., 0]))


def sector_from_bearing_deg(bearing, mid_deg=15.0):
    labels = torch.ones_like(bearing, dtype=torch.long)
    labels = torch.where(bearing > mid_deg, torch.zeros_like(labels), labels)
    labels = torch.where(bearing < -mid_deg, torch.full_like(labels, 2), labels)
    return labels


def sector_center_bearing_deg(sector_id, mid_deg=15.0, snap_deg=None):
    if snap_deg is None:
        snap_deg = max(30.0, mid_deg * 2.0)
    centers = torch.tensor([snap_deg, 0.0, -snap_deg], device=sector_id.device, dtype=torch.float32)
    return centers[sector_id]


def direction_from_bearing_deg(bearing_deg):
    rad = torch.deg2rad(bearing_deg)
    return torch.stack([torch.cos(rad), torch.sin(rad)], dim=-1)


def apply_sector_gate(direction, sector_logits, mid_deg=15.0, snap_deg=None, min_conf=0.55, blend_on_mismatch=0.65):
    if sector_logits is None:
        return direction
    probs = torch.softmax(sector_logits.float(), dim=-1)
    conf, pred = probs.max(dim=-1)
    reg_b = bearing_deg_xy(direction.float())
    reg_sec = sector_from_bearing_deg(reg_b, mid_deg)
    use = (pred != reg_sec) & (conf >= min_conf)
    if not use.any():
        return direction
    center_b = sector_center_bearing_deg(pred, mid_deg, snap_deg)
    center_dir = direction_from_bearing_deg(center_b)
    w = (blend_on_mismatch * conf).unsqueeze(-1)
    out = direction.float().clone()
    mixed = (1.0 - w) * out + w * center_dir
    mixed = mixed / mixed.norm(dim=-1, keepdim=True).clamp(min=1e-6)
    out[use] = mixed[use]
    return out.to(dtype=direction.dtype)


def apply_sector_gate_numpy(direction, sector_logits, **kwargs):
    d = torch.from_numpy(np.asarray(direction, dtype=np.float32))
    s = torch.from_numpy(np.asarray(sector_logits, dtype=np.float32))
    return apply_sector_gate(d, s, **kwargs).numpy()
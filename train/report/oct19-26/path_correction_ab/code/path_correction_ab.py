"""Frozen pathact8 base + shared correction MLP (distance or direction branch).

Feature for correction is the same tensor fed to ``PairTokenHead.path_head``:
LayerNorm+Linear path input = CLS readout ``feat`` (256-d) when path_spatial!='lcr'
and odom is not concatenated (pathact8 checkpoint: Linear 256->16).
"""
from __future__ import annotations

import math
from typing import Literal, Tuple

import torch
import torch.nn as nn

from vint_train.models.nomad.pair_token_head import PairTokenHead

NEAR_ZERO_M = 1e-6
CorrectionMode = Literal["dist", "dir"]


class PathCorrectionNet(nn.Module):
    """Linear(D,128) -> GELU -> Linear(128,8); zero-init last layer."""

    def __init__(self, feat_dim: int, path_steps: int = 8):
        super().__init__()
        self.path_steps = int(path_steps)
        self.net = nn.Sequential(
            nn.Linear(feat_dim, 128),
            nn.GELU(),
            nn.Linear(128, self.path_steps),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        return self.net(feat)


def apply_distance_correction(p_base: torch.Tensor, log_scale: torch.Tensor) -> torch.Tensor:
    """p_base [B,K,2], log_scale [B,K] -> exp(s)*p_base (keeps direction)."""
    s = log_scale.unsqueeze(-1)
    return torch.exp(s) * p_base


def apply_direction_correction(p_base: torch.Tensor, theta: torch.Tensor) -> torch.Tensor:
    """Rotate each point by theta_k (radians); preserves norm."""
    c = torch.cos(theta)
    sn = torch.sin(theta)
    x, y = p_base[..., 0], p_base[..., 1]
    xr = c * x - sn * y
    yr = sn * x + c * y
    return torch.stack([xr, yr], dim=-1)


class FrozenPathAct8WithCorrection(nn.Module):
    """Wraps frozen PairTokenHead; only ``correction`` is trainable."""

    def __init__(self, base: PairTokenHead, mode: CorrectionMode):
        super().__init__()
        if mode not in ("dist", "dir"):
            raise ValueError(f"mode must be dist|dir, got {mode}")
        self.base = base
        self.mode: CorrectionMode = mode
        self.path_steps = int(base.path_steps)
        feat_dim = self._infer_path_in_dim(base)
        self.correction = PathCorrectionNet(feat_dim, self.path_steps)
        self._freeze_base()

    @staticmethod
    def _infer_path_in_dim(head: PairTokenHead) -> int:
        ph = head.path_head
        if ph is None:
            raise ValueError("base head has no path_head")
        if isinstance(ph, nn.Linear):
            return int(ph.in_features)
        if isinstance(ph, nn.Sequential):
            first = ph[0]
            if isinstance(first, nn.LayerNorm):
                lin = ph[1]
            else:
                lin = first
            if isinstance(lin, nn.Linear):
                return int(lin.in_features)
        raise RuntimeError("cannot infer path_head input dim")

    def _freeze_base(self) -> None:
        for p in self.base.parameters():
            p.requires_grad_(False)

    def train(self, mode: bool = True):
        super().train(mode)
        self.base.eval()
        return self

    @torch.no_grad()
    def forward_base_path_and_feat(
        self,
        curr: torch.Tensor,
        goal: torch.Tensor,
        ctx: torch.Tensor | None = None,
        odom: torch.Tensor | None = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns p_base [B,K,2] and path_head input features [B,D] (dataset units)."""
        self.base.eval()
        head = self.base
        parts = [head.cls.expand(len(curr), -1, -1)]
        parts.append(head.proj(curr) + head.pos + head.kind[0])
        parts.append(head.proj(goal) + head.pos + head.kind[1])
        if ctx is not None:
            for j in range(ctx.shape[1]):
                parts.append(head.proj(ctx[:, j]) + head.pos + head.kind[2 + j])
        x = head.encoder(torch.cat(parts, dim=1))
        feat = head.norm(x[:, 0])
        path_in = head._path_feat(x, feat, odom)
        path_xy = head.path_head(path_in)
        if head.path_res is not None:
            path_xy = path_xy + head.path_res(feat)
        path_xy = path_xy.view(-1, head.path_steps, 2)
        path_xy = head._rotate_path(path_xy, odom)
        return path_xy, path_in

    def forward(
        self,
        curr: torch.Tensor,
        goal: torch.Tensor,
        ctx: torch.Tensor | None = None,
        odom: torch.Tensor | None = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Returns p_corr, p_base, correction_raw [B,K]."""
        p_base, path_in = self.forward_base_path_and_feat(curr, goal, ctx, odom)
        p_base_d = p_base.detach()
        feat = path_in.detach()
        raw = self.correction(feat)
        if self.mode == "dist":
            p_corr = apply_distance_correction(p_base_d, raw)
        else:
            p_corr = apply_direction_correction(p_base_d, raw)
        return p_corr, p_base_d, raw

    def trainable_parameters(self):
        return self.correction.parameters()


def angular_alignment_error_deg(p: torch.Tensor, q: torch.Tensor, eps_m: float, meters: float) -> torch.Tensor:
    """Per-point angle between p and q (degrees); NaN where either radius < eps_m in meters."""
    rp = p.norm(dim=-1) * meters
    rq = q.norm(dim=-1) * meters
    ok = (rp >= eps_m) & (rq >= eps_m)
    cos = (p * q).sum(-1) / (p.norm(dim=-1) * q.norm(dim=-1)).clamp(min=1e-12)
    ang = torch.rad2deg(torch.acos(cos.clamp(-1, 1)))
    return torch.where(ok, ang, torch.full_like(ang, float("nan")))


def radius_ratio_error(p: torch.Tensor, q: torch.Tensor, eps_m: float, meters: float) -> torch.Tensor:
    """| |p|-|q| | in meters; NaN if either radius undefined."""
    rp = p.norm(dim=-1) * meters
    rq = q.norm(dim=-1) * meters
    ok = (rp >= eps_m) & (rq >= eps_m)
    err = (rp - rq).abs()
    return torch.where(ok, err, torch.full_like(err, float("nan")))


def count_trainable(model: FrozenPathAct8WithCorrection) -> int:
    return sum(p.numel() for p in model.correction.parameters() if p.requires_grad)


def base_frozen_grad_check(model: FrozenPathAct8WithCorrection) -> bool:
    for p in model.base.parameters():
        if p.requires_grad or (p.grad is not None and p.grad.abs().sum() > 0):
            return False
    return True

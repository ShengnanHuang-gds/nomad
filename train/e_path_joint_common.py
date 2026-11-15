"""Shared helpers: deploy pathact8 blend_path joint A/B (O frozen reference)."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from train_e_dino import (
    blend_torch,
    build_blend_path,
    forward_wp_head,
    path_tensor_from_out,
    path_xy_to_width,
    read_tokens,
    wp_direction_from_head,
)
from yaw_traj import path_tensor_from_out as path_from_out  # noqa: F401
PATH_STEPS = 8
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
def clone_path_output_layer(wp_head: nn.Module) -> nn.Linear:
    if not isinstance(wp_head.path_head, nn.Linear):
        raise ValueError("pathact8 deploy head must use single Linear path_head")
    lin = nn.Linear(wp_head.path_head.in_features, wp_head.path_head.out_features)
    lin.load_state_dict(copy.deepcopy(wp_head.path_head.state_dict()))
    return lin
def wp_path_input_features(
    wp_head: nn.Module,
    features,
    curr_rows,
    goal_rows,
    past_rows,
    device,
    wp_odom=None,
) -> torch.Tensor:
    """CLS path readout input (frozen encoder), shape [B, path_in]."""
    curr = read_tokens(features, curr_rows).to(device).float()
    goal = read_tokens(features, goal_rows).to(device).float()
    ctx = None
    wp_context = int(wp_head.kind.shape[0] - 2)
    if wp_context > 0:
        past = past_rows[:, :wp_context].detach().cpu().numpy()
        ctx = torch.stack(
            [read_tokens(features, past[:, j]).to(device).float() for j in range(wp_context)],
            dim=1,
        )
    with torch.no_grad():
        parts = [wp_head.cls.expand(len(curr), -1, -1)]
        parts.append(wp_head.proj(curr) + wp_head.pos + wp_head.kind[0])
        parts.append(wp_head.proj(goal) + wp_head.pos + wp_head.kind[1])
        if ctx is not None:
            for j in range(ctx.shape[1]):
                parts.append(wp_head.proj(ctx[:, j]) + wp_head.pos + wp_head.kind[2 + j])
        x = wp_head.encoder(torch.cat(parts, dim=1))
        feat = wp_head.norm(x[:, 0])
        path_in = wp_head._path_feat(x, feat, wp_odom)
    return path_in
def mu_from_frozen_wp(
    loc_model,
    dino_head,
    features,
    batch_obs,
    batch_goal,
    curr_rows,
    goal_rows,
    device,
    wp_head,
    wp_scale=1.0,
    past_rows=None,
    wp_odom=None,
):
    """2D mu only (blend_path), independent of path poly used in cond."""
    no_mask = torch.zeros(len(batch_obs), dtype=torch.long, device=device)
    with torch.no_grad():
        cond = loc_model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
        steps = loc_model("dist_pred_net", obsgoal_cond=cond).squeeze(-1).clamp(min=0.0)
        curr = read_tokens(features, curr_rows).to(device).float()
        goal = read_tokens(features, goal_rows).to(device).float()
        dino_out = dino_head(curr, goal)
        direction, kappa = dino_out[0], dino_out[1]
        w_out, w_dir, w_k = forward_wp_head(
            wp_head, features, curr_rows, goal_rows, past_rows, device, wp_odom=wp_odom
        )
        direction = blend_torch(direction, kappa, w_dir, w_k, wp_scale=wp_scale)
        return direction * steps.unsqueeze(-1)
def build_cond_blend_path(
    mu: torch.Tensor,
    wp_head_frozen: nn.Module,
    path_head_train: Optional[nn.Linear],
    features,
    curr_rows,
    goal_rows,
    past_rows,
    device,
    pos_dim: int,
    path_units: str,
    meters_per_unit: float,
    wp_odom=None,
    frozen_path_for_cond: bool = False,
):
    """Assemble [mu | 16D path] for cond_encoder. B uses trainable path_head_train."""
    if frozen_path_for_cond or path_head_train is None:
        with torch.no_grad():
            w_out, w_dir, _w_k = forward_wp_head(
                wp_head_frozen, features, curr_rows, goal_rows, past_rows, device, wp_odom=wp_odom
            )
            path_flat = build_blend_path(
                w_dir,
                pos_dim,
                path_gate="none",
                wp_out=w_out,
                wp_head=wp_head_frozen,
                path_source="wp_poly",
                meters_per_unit=meters_per_unit,
                path_units=path_units,
            )
    else:
        path_in = wp_path_input_features(
            wp_head_frozen, features, curr_rows, goal_rows, past_rows, device, wp_odom=wp_odom
        )
        path_xy = path_head_train(path_in).view(-1, PATH_STEPS, 2)
        if path_units == "meters":
            path_xy = path_xy / max(float(meters_per_unit), 1e-6)
        path_flat = path_xy.reshape(path_xy.shape[0], -1)
        if path_flat.shape[1] != pos_dim - 2:
            path_flat = path_xy_to_width(path_xy, pos_dim)
    return torch.cat([mu, path_flat], dim=-1)
def path_loss_smooth_l1(pred_xy: torch.Tensor, tgt_xy: torch.Tensor, beta: float = 1.0) -> torch.Tensor:
    """pred/tgt [B,8,2] in dataset units."""
    return F.smooth_l1_loss(pred_xy, tgt_xy, beta=beta, reduction="mean")
def gt_path_from_actions(actions: torch.Tensor, n_steps: int = PATH_STEPS) -> torch.Tensor:
    """GT local waypoint positions (dataset units), not deltas."""
    return actions[:, :n_steps, :2].float()
def save_joint_bundle(
    path: str,
    *,
    model_state,
    ema_state,
    path_head_state: Optional[dict],
    optimizer_state,
    scheduler_state,
    ema_step: int,
    epoch: int,
    global_step: int,
    meta: dict,
):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(
        {
            "model": model_state,
            "ema": ema_state,
            "path_head_train": path_head_state,
            "optimizer": optimizer_state,
            "scheduler": scheduler_state,
            "ema_step": ema_step,
            "epoch": epoch,
            "global_step": global_step,
            "meta": meta,
        },
        path,
    )
def load_joint_bundle(path: str, device):
    return torch.load(path, map_location=device, weights_only=False)
def mu_consistency_report(mu_a: torch.Tensor, mu_b: torch.Tensor) -> dict:
    d = (mu_a - mu_b).abs()
    return {
        "max_abs_diff": float(d.max().item()),
        "mean_abs_diff": float(d.mean().item()),
        "pass": bool(d.max().item() < 1e-5),
    }
def grad_check_path_head(path_head_train: nn.Linear, path_in: torch.Tensor, tgt: torch.Tensor, diffusion_term):
    """Returns dict of grad norms for L_path-only and L_diff-only."""
    out = {}
    path_head_train.zero_grad(set_to_none=True)
    path_xy = path_head_train(path_in).view(-1, PATH_STEPS, 2)
    lp = path_loss_smooth_l1(path_xy, tgt)
    lp.backward(retain_graph=True)
    g_path = path_head_train.weight.grad
    out["grad_path_only_norm"] = float(g_path.norm().item()) if g_path is not None else 0.0
    path_head_train.zero_grad(set_to_none=True)
    if diffusion_term is not None:
        diffusion_term.backward()
        g_diff = path_head_train.weight.grad
        out["grad_diff_only_norm"] = float(g_diff.norm().item()) if g_diff is not None else 0.0
    return out

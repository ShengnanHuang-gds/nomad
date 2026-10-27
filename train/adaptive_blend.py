"""Adaptive kappa blend: down-weight goal direction when co-visibility is low."""
import numpy as np

def angle_between_deg(d1, d2):
    d1 = d1 / np.maximum(np.linalg.norm(d1, axis=-1, keepdims=True), 1e-6)
    d2 = d2 / np.maximum(np.linalg.norm(d2, axis=-1, keepdims=True), 1e-6)
    c = np.clip((d1 * d2).sum(-1), -1.0, 1.0)
    return np.degrees(np.arccos(c))

def gate_ramp(x, lo, hi):
    return np.clip((x - lo) / max(hi - lo, 1e-6), 0.0, 1.0).astype(np.float32)

def gate_from_dyaw(abs_dyaw_deg, lo=30.0, hi=90.0):
    return gate_ramp(abs_dyaw_deg, lo, hi)

def gate_from_disagree(goal_dir, wp_dir, lo=25.0, hi=55.0):
    return gate_ramp(angle_between_deg(goal_dir, wp_dir), lo, hi)

def gate_from_orb(orb_matches, ref=20.0):
    m = np.asarray(orb_matches, dtype=np.float32)
    return np.clip(1.0 - m / max(ref, 1e-6), 0.0, 1.0)

def combine_gates(*gates, mode="max"):
    g = np.stack([np.asarray(x, dtype=np.float32) for x in gates], axis=0)
    if mode == "max":
        return g.max(axis=0)
    if mode == "mean":
        return g.mean(axis=0)
    raise ValueError(mode)

def gate_from_turn_strict(turn_strict, weight=1.0):
    t = np.asarray(turn_strict, dtype=np.float32).reshape(-1)
    return np.clip(t * float(weight), 0.0, 1.0).astype(np.float32)


def suppress_from_wp_turn(wp_err_deg, turn_strict, wp_lo=40.0, wp_hi=60.0, turn_weight=0.0, cap=1.0, mode="max"):
    """suppress in [0,1]: 0 = full kappa blend; 1 = goal direction only (waypoint weight zero)."""
    gates = [gate_ramp(np.asarray(wp_err_deg, dtype=np.float32), wp_lo, wp_hi)]
    if turn_weight > 0:
        gates.append(gate_from_turn_strict(turn_strict, turn_weight))
    s = combine_gates(*gates, mode=mode) if len(gates) > 1 else gates[0]
    return np.clip(s, 0.0, float(cap)).astype(np.float32)


def blend_suppress(goal_dir, goal_k, wp_dir, wp_k, suppress, wp_scale=1.0):
    """Down-weight waypoint kappa when suppress is high (hard turn / bad WP bearing)."""
    s = np.asarray(suppress, dtype=np.float32).reshape(-1, 1)
    kg = np.asarray(goal_k, dtype=np.float32).reshape(-1, 1)
    kw = np.asarray(wp_k, dtype=np.float32).reshape(-1, 1) * float(wp_scale) * (1.0 - s)
    r = kg * goal_dir + kw * wp_dir
    return (r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)).astype(np.float32)


def blend_gated(goal_dir, goal_k, wp_dir, wp_k, gate, wp_scale=1.0, wp_boost=1.0):
    """gate in [0,1]: 0 = standard kappa blend; higher -> more waypoint."""
    g = np.asarray(gate, dtype=np.float32).reshape(-1)
    kg = goal_k * (1.0 - g)
    kw = wp_k * wp_scale * (1.0 + g * wp_boost)
    r = kg[:, None] * goal_dir + kw[:, None] * wp_dir
    return (r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)).astype(np.float32)

def blend_suppress_torch(goal_dir, goal_k, wp_dir, wp_k, suppress, wp_scale=1.0):
    import torch
    s = suppress.reshape(-1, 1).float()
    kg = goal_k.reshape(-1, 1).float()
    kw = wp_k.reshape(-1, 1).float() * float(wp_scale) * (1.0 - s)
    r = kg * goal_dir + kw * wp_dir
    return r / r.norm(dim=-1, keepdim=True).clamp(min=1e-6)


def blend_gated_torch(goal_dir, goal_k, wp_dir, wp_k, gate, wp_scale=1.0, wp_boost=1.0):
    import torch
    g = gate.reshape(-1, 1).float()
    kg = goal_k.reshape(-1, 1) * (1.0 - g)
    kw = wp_k.reshape(-1, 1) * wp_scale * (1.0 + g * wp_boost)
    r = kg * goal_dir + kw * wp_dir
    return r / r.norm(dim=-1, keepdim=True).clamp(min=1e-6)

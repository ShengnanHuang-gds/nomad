"""Relative-yaw supervision and validation; never used to command a robot."""

import math

import numpy as np

from visual_stage_data import ALLOWED_ROUTES


def yaw_pairs(data, routes, max_gap=20):
    if not set(routes).issubset(ALLOWED_ROUTES):
        raise ValueError("Only training/validation routes 00-05 may supply yaw labels")
    pairs = []
    for route in routes:
        yaw = data.routes[route]["yaw"]
        for current in range(len(yaw)):
            for goal in range(max(0, current-max_gap), min(len(yaw), current+max_gap+1)):
                delta = (float(yaw[goal]-yaw[current])+math.pi) % (2*math.pi)-math.pi
                pairs.append((route, current, goal, delta))
    return pairs


def pair_weights(pairs):
    labels = ["same" if abs(p[3]) <= math.radians(5) else "left" if p[3] > 0 else "right" for p in pairs]
    counts = {label: labels.count(label) for label in set(labels)}
    weights = np.asarray([1/counts[label] for label in labels], dtype=float)
    return weights/weights.sum()


def yaw_metrics(prediction, target):
    prediction, target = np.asarray(prediction), np.asarray(target)
    errors = np.abs((prediction-target+np.pi) % (2*np.pi)-np.pi)
    large = (np.abs(target) >= math.radians(20)) & (np.abs(target) <= math.radians(160))
    sign_accuracy = float(np.mean(np.sign(prediction[large]) == np.sign(target[large]))) if large.any() else 0.0
    mae = float(np.degrees(errors).mean())
    p90 = float(np.percentile(np.degrees(errors), 90))
    return {"mae_deg": mae, "p90_deg": p90, "large_turn_sign_accuracy": sign_accuracy,
            "pair_count": len(target), "large_turn_pair_count": int(large.sum()),
            "selection_score": mae+0.25*p90,
            "validation_gate_passed": bool(mae <= 10 and p90 <= 20 and sign_accuracy >= 0.95)}

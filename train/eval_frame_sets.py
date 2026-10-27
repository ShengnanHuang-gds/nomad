"""Fixed frame definitions on the locked paired frames, shared by every model.

Turning frames come from the 8-step label only. The spread set is read from
the saved B Epoch 29 masked samples in the position-noise run, so it does not
change when a new model is evaluated.
"""

import numpy as np

PAIRED_FRAMES = "logs/nomad/nomad_b40_2026_09_29_16_35_23/eval_epoch20_paired/paired_frames.csv"
SPREAD_NPZ = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/eval_epoch29_position_noise/per_frame.npz"
NOISE_CURVE = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/eval_epoch29_position_noise/position_noise_curve.csv"

TURN_LOOSE = (0.15, 20.0)
TURN_STRICT = (0.30, 45.0)


def _scalar(value):
    return float(np.ravel(np.asarray(value, dtype=np.float64))[0])


def yaw_change_deg(dataset, traj_name, t):
    yaw = dataset._get_trajectory(traj_name)["yaw"]
    step = dataset.len_traj_pred * dataset.waypoint_spacing
    dy = _scalar(yaw[t + step]) - _scalar(yaw[t])
    dy = (dy + np.pi) % (2.0 * np.pi) - np.pi
    return float(np.degrees(dy))


def endpoint_lateral_m(dataset, traj_name, t, meters):
    actions, _goal_pos = dataset._compute_actions(dataset._get_trajectory(traj_name), t, t)
    return float(actions[-1, 1] * meters)


def frame_motion(dataset, moments, meters):
    lateral = np.array([endpoint_lateral_m(dataset, name, t, meters) for name, t, _goals in moments])
    yaw = np.array([yaw_change_deg(dataset, name, t) for name, t, _goals in moments])
    return lateral, yaw


def turning_mask(lateral, yaw, thresholds):
    lateral_m, yaw_deg = thresholds
    return (np.abs(lateral) >= lateral_m) | (np.abs(yaw) >= yaw_deg)


def load_spread(path, n):
    try:
        data = np.load(path)
    except FileNotFoundError:
        return None
    spread = np.asarray(data["spread"], dtype=bool)
    if spread.shape != (n,):
        raise RuntimeError(f"{path} has {spread.shape[0]} frames, expected {n}")
    return spread


def frame_sets(dataset, moments, meters, spread_path=SPREAD_NPZ):
    lateral, yaw = frame_motion(dataset, moments, meters)
    sets = {
        "all": np.ones(len(moments), dtype=bool),
        "turn 0.15m/20deg": turning_mask(lateral, yaw, TURN_LOOSE),
        "turn 0.30m/45deg": turning_mask(lateral, yaw, TURN_STRICT),
    }
    sets["straight (not 0.15m/20deg)"] = ~sets["turn 0.15m/20deg"]
    spread = load_spread(spread_path, len(moments))
    if spread is not None:
        sets["B masked spread"] = spread
    return sets, lateral, yaw

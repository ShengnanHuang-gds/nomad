"""Ceiling check: is the near waypoint a better condition than the far goal? No training.

On the locked far frames, E-oracle gets one of
  goal               the true far goal position (what it was trained on)
  endpoint           the true position after len_traj_pred steps (the last action label)
  endpoint dir x B   the endpoint bearing times B's goal distance (bearing only)
  DINO goal (direct) the DINO goal bearing times B's goal distance (the deployable reference)
The endpoint rows leak the label of the trajectory being scored, so they are ceilings only:
they say whether a head that predicts the near waypoint bearing could be worth training.

Run from train/:
    python -u eval_waypoint_oracle.py
"""

import argparse
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT, unit
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import make_split_dataset, meters_per_unit, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, rollout

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")


def main():
    parser = argparse.ArgumentParser(description="Near-waypoint ceiling check with E-oracle")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="Smoke tests: first k frames")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="logs/nomad_d/waypoint_oracle")
    args = parser.parse_args()

    device = torch.device(args.device)
    os.makedirs(args.output_dir, exist_ok=True)
    config_b = load_config(args.config_b)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    b_steps = (take("b_dist") / meters).astype(np.float32)

    goal_pos, endpoint = [], []
    for traj_name, t, g in far:
        _o, _g, actions, gp = load_observation(dataset, traj_name, t, g)
        goal_pos.append(gp)
        endpoint.append(actions[-1, :2])
    goal_pos = np.stack(goal_pos).astype(np.float32)
    endpoint = np.stack(endpoint).astype(np.float32)
    positions = {
        "goal": goal_pos,
        "endpoint": endpoint,
        "endpoint dir x B": (unit(endpoint) * b_steps[:, None]).astype(np.float32),
        "DINO goal (direct)": (take("dino_dir") * b_steps[:, None]).astype(np.float32),
    }
    if args.limit:
        far = far[: args.limit]
        positions = {k: v[: args.limit] for k, v in positions.items()}
        sets = {k: v[: args.limit] for k, v in sets.items()}

    eb = np.degrees(np.arctan2(positions["endpoint"][:, 1], positions["endpoint"][:, 0]))
    gb = np.degrees(np.arctan2(positions["goal"][:, 1], positions["goal"][:, 0]))
    print(f"median |goal bearing - endpoint bearing| on far frames: {np.median(np.abs((gb - eb + 180) % 360 - 180)):.1f} deg; "
          f"median endpoint distance {np.median(np.linalg.norm(positions['endpoint'], axis=1)) * meters:.2f} m")

    model_eo, sched_eo = load_model(load_config(args.config_e_oracle), E_CHECKPOINT, device)
    am, ade = rollout(model_eo, sched_eo, dataset, far, positions, device, args.num_samples, 8, args.seed + 1, "locked")
    rng = np.random.default_rng(args.seed + 2)
    rows = []
    print("\nLocked far frames. use = masked ADE - ADE (cm); kept vs the true far goal.")
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        gu = float((am[idx] - ade["goal"][idx]).mean())
        print(f"\n[{set_name}] n={len(idx)}")
        for k in positions:
            u = boot_mean(am[idx] - ade[k][idx], boot)
            print(f"  {k:<20} ADE {100 * ade[k][idx].mean():6.2f}  use {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  "
                  f"{100 * u[0] / gu:4.0f}% of goal")
            rows.append({"frames": set_name, "condition": k, "ade_cm": 100 * float(ade[k][idx].mean()),
                         "use_cm": 100 * u[0], "lo": 100 * u[1], "hi": 100 * u[2], "vs_goal": u[0] / gu})
    write_csv(os.path.join(args.output_dir, "waypoint_oracle.csv"), rows)
    print(f"Saved to {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()

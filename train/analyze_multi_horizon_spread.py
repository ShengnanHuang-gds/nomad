"""GT spread angle(d2,d8) and angle(d4,d8) on Val far — multi-horizon preflight."""
import json
import os
import numpy as np
from eval_by_distance import load_config
from eval_frame_sets import endpoint_lateral_m, turning_mask, yaw_change_deg, TURN_STRICT
from eval_goal_head import make_split_dataset, meters_per_unit
from train_goal_dir import FAR_STEPS
from train_goal_dino import DFT_VAL_LIST, build_pairs, draw, load_cache, _local_bearing_step

VAL_SEED = 1234
OUT = "logs/revalidation/multi_horizon_spread"


def angle_deg(a, b):
    a = a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-9)
    b = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-9)
    c = np.clip((a * b).sum(axis=-1), -1, 1)
    return np.degrees(np.arccos(c))


def main():
    config = load_config("config/nomad_b40.yaml")
    _, rows, _ = load_cache("logs/dino_cache/dinov2_vits14_reg", "train")
    with open(DFT_VAL_LIST) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    dataset = make_split_dataset(config, "train")
    meters = meters_per_unit(dataset)
    pairs = build_pairs(config, "train", rows, lambda t: t in val_trajs, 0.3, 2, "endpoint", (2, 4))
    chosen = draw(pairs, np.random.default_rng(VAL_SEED))
    chosen = chosen[pairs["steps"][chosen] >= FAR_STEPS]
    t8 = pairs["target"][chosen]
    ta = pairs["target_aux"][chosen]
    t2, t4 = ta[:, 0], ta[:, 1]
    d28 = angle_deg(t2, t8)
    d48 = angle_deg(t4, t8)
    row_to_key = {int(v): k for k, v in rows.items()}
    turn = np.zeros(len(chosen), dtype=bool)
    for i, j in enumerate(chosen):
        traj, curr = row_to_key[int(pairs["curr"][j])]
        lat = endpoint_lateral_m(dataset, traj, int(curr), meters)
        yaw = yaw_change_deg(dataset, traj, int(curr))
        turn[i] = turning_mask(np.array([lat]), np.array([yaw]), TURN_STRICT)[0]
    hard45 = np.zeros(len(chosen), dtype=bool)  # placeholder without model
    os.makedirs(OUT, exist_ok=True)
    rows_out = []
    for name, mask in [("all_far", np.ones(len(chosen), bool)), ("turn_strict", turn), ("non_turn", ~turn)]:
        m = mask
        rows_out.append({
            "subset": name,
            "n": int(m.sum()),
            "median_d28": float(np.median(d28[m])),
            "p90_d28": float(np.percentile(d28[m], 90)),
            "median_d48": float(np.median(d48[m])),
            "p90_d48": float(np.percentile(d48[m], 90)),
        })
    summary = {"n_far": len(chosen), "bins": rows_out}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    lines = ["=== Multi-horizon GT spread (Val far) ===", f"n={len(chosen)}"]
    for r in rows_out:
        lines.append(
            f"{r['subset']}: median d28={r['median_d28']:.1f} p90={r['p90_d28']:.1f} | "
            f"d48 med={r['median_d48']:.1f} p90={r['p90_d48']:.1f}"
        )
    with open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
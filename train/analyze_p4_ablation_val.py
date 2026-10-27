"""P4 ablation: Val WP metrics on full far (5110) and MH-filtered (2721)."""
import os
import numpy as np
import torch
from eval_by_distance import load_config
from eval_frame_sets import endpoint_lateral_m, turning_mask, yaw_change_deg, TURN_STRICT
from eval_goal_head import make_split_dataset, meters_per_unit
from eval_testtime import angle_err
from eval_waypoint_head import head_predict
from train_e_dino import load_dino_head
from train_goal_dir import FAR_STEPS
from train_goal_dino import DFT_VAL_LIST, build_pairs, draw, load_cache

VAL_SEED = 1234
CTX = 2
import glob

MODELS = {
    "ctx2": "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth",
    "p4_mh": "logs/nomad_d/p4_ctx2_multi_horizon_248_2026_10_25_10_25_34/dino_dir_best.pth",
    "p4b_masked": "logs/nomad_d/p4b_ctx2_masked_mh_248_2026_10_25_11_50_48/dino_dir_best.pth",
}
_ctrl = sorted(glob.glob("logs/nomad_d/p4_ctrl_ctx2_continue_15ep_*/dino_dir_best.pth"))
if _ctrl:
    MODELS["p4_ctrl15"] = _ctrl[-1]
OUT = "logs/revalidation/p4_ablation_val.txt"

def metrics(e, turn):
    return {
        "far_med": float(np.median(e)),
        "turn_med": float(np.median(e[turn])),
        "turn_p90": float(np.percentile(e[turn], 90)) if turn.any() else float("nan"),
        "gt45": float(100 * (e > 45).mean()),
        "nonturn_med": float(np.median(e[~turn])) if (~turn).any() else float("nan"),
    }

def eval_split(name, pairs, chosen, rows, row_to_key, dataset, meters, device):
    turn = np.zeros(len(chosen), bool)
    items = []
    for i, j in enumerate(chosen):
        traj, curr = row_to_key[int(pairs["curr"][j])]
        _, gt = row_to_key[int(pairs["goal"][j])]
        lat = endpoint_lateral_m(dataset, traj, int(curr), meters)
        yaw = yaw_change_deg(dataset, traj, int(curr))
        turn[i] = turning_mask(np.array([lat]), np.array([yaw]), TURN_STRICT)[0]
        items.append((traj, int(curr), int(gt)))
    target = pairs["target"][chosen]
    feats = np.load(os.path.join("logs/dino_cache/dinov2_vits14_reg", "train", "features.npy"), mmap_mode="r")
    rows_out = []
    for label, ck in MODELS.items():
        if not os.path.isfile(ck):
            continue
        head, _ = load_dino_head(ck, device)
        wp, _ = head_predict(head, items, rows, feats, device, 128)
        e = angle_err(wp, target)
        m = metrics(e, turn)
        m["model"] = label
        m["split"] = name
        m["n"] = len(chosen)
        rows_out.append(m)
    return rows_out

def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config("config/nomad_b40.yaml")
    _, rows, _ = load_cache("logs/dino_cache/dinov2_vits14_reg", "train")
    row_to_key = {int(v): k for k, v in rows.items()}
    with open(DFT_VAL_LIST) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    dataset = make_split_dataset(config, "train")
    meters = meters_per_unit(dataset)
    all_rows = []
    for split_name, multi in [("full_5110", ()), ("mh_2721", (2, 4))]:
        strict = split_name == "mh_2721" and bool(multi)
        pairs = build_pairs(
            config, "train", rows, lambda t: t in val_trajs, 0.3, CTX, "endpoint", multi, strict
        )
        chosen = draw(pairs, np.random.default_rng(VAL_SEED))
        chosen = chosen[pairs["steps"][chosen] >= FAR_STEPS]
        all_rows.extend(eval_split(split_name, pairs, chosen, rows, row_to_key, dataset, meters, device))
    lines = ["P4 Val ablation (seed 1234)", ""]
    for split in ("full_5110", "mh_2721"):
        lines.append(f"=== {split} ===")
        sub = [r for r in all_rows if r["split"] == split]
        for r in sub:
            lines.append(
                f"{r['model']}: n={r['n']} far={r['far_med']:.2f} turn_med={r['turn_med']:.2f} "
                f"turn_p90={r['turn_p90']:.2f} gt45={r['gt45']:.2f}% nonturn={r['nonturn_med']:.2f}"
            )
        lines.append("")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
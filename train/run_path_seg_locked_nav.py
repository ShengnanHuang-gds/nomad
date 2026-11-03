"""Post A/B: val summary + locked-1000 E-dino (full deploy + fixed baseline mu)."""
import csv
import json
import os
import subprocess
import sys

import cv2  # noqa: F401
import numpy as np
import torch

PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe" if os.path.isfile(r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe") else sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
AB_OUT = os.path.join(CWD, "logs/revalidation/path_seg_displacement_ab")
BASE_WP = os.path.join(CWD, "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth")
LOCKED_CSV = os.path.join(CWD, "logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv")
E_RUN = os.path.join(CWD, "logs/nomad/nomad_e_ft_pathact8")
DINO_PRED = os.path.join(CWD, "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz")
EVAL_OUT = os.path.join(AB_OUT, "locked_nav")


def py_env():
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    return env


def run_dir(tag):
    p = os.path.join(AB_OUT, f"{tag}_run_dir.txt")
    if not os.path.isfile(p):
        raise SystemExit(f"missing {p}")
    return open(p, encoding="utf-8").read().strip()


def val_summary(run_dir, label):
    rows = list(csv.DictReader(open(os.path.join(run_dir, "train_log.csv"), encoding="utf-8")))
    best = min(rows, key=lambda r: float(r["val_far_path_ade_cm"]))
    return {
        "label": label,
        "best_epoch": int(best["epoch"]),
        "best_far_path_ade_cm": float(best["val_far_path_ade_cm"]),
        "best_path_ade_cm": float(best["val_path_ade_cm"]),
        "best_path_turn_deg": float(best.get("val_path_turn_deg", "nan")),
    }


def eval_full_deploy(wp, sub):
    os.makedirs(EVAL_OUT, exist_ok=True)
    subprocess.run(
        [
            PY, "-u", "eval_e_dino.py",
            "--paired-frames", LOCKED_CSV,
            "--run-dir", E_RUN,
            "--checkpoint", "ema_latest.pth",
            "--wp-head", wp,
            "--goal-pos-mode", "blend_path",
            "--path-source", "wp_poly",
            "--path-units", "dataset",
        ],
        cwd=CWD,
        check=True,
        env=py_env(),
    )
    out = os.path.join(E_RUN, "eval_ema_latest")
    tag_path = os.path.join(EVAL_OUT, f"{sub}_eval_dir.txt")
    with open(tag_path, "w", encoding="utf-8") as f:
        f.write(out + chr(10))
    for r in csv.DictReader(open(os.path.join(out, "paired_far.csv"), encoding="utf-8")):
        if r.get("frames") == "all" and r.get("model") == "E-dino":
            return float(r["ade_m"]) * 100.0
    return None


@torch.no_grad()
def eval_fixed_mu(wp_new, label):
    from eval_by_distance import load_config, load_paired_frames
    from eval_e_dino import head_predict_wp_path, run_models
    from eval_goal_head import make_split_dataset, meters_per_unit
    from eval_position_noise import load_model
    from eval_waypoint_head import blend
    from revalidate import CACHE_ROOT
    from train_e_dino import load_dino_head
    from train_goal_dino import load_cache

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    pred = dict(np.load(DINO_PRED))
    far_mask = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][far_mask], kind="stable")
    dino_dir = pred["dino_dir"][far_mask][order].astype(np.float32)
    kappa = pred["dino_kappa"][far_mask][order].astype(np.float32)
    b_dist_m = pred["b_dist"][far_mask][order].astype(np.float32)

    dataset = make_split_dataset(load_config("config/nomad_b40.yaml"), "test")
    meters = float(meters_per_unit(dataset))
    b_steps = (b_dist_m / meters).astype(np.float32)
    far = load_paired_frames(LOCKED_CSV)
    _p, rows, _meta = load_cache(CACHE_ROOT, "test_paired")
    feats = np.load(os.path.join(CACHE_ROOT, "test_paired", "features.npy"), mmap_mode="r")

    wp_base, _ = load_dino_head(BASE_WP, device)
    wp_new_h, _ = load_dino_head(wp_new, device)
    wp_dir_b, wp_kappa_b, _ = head_predict_wp_path(wp_base, far, rows, feats, device)
    _wd, _wk, path_n = head_predict_wp_path(wp_new_h, far, rows, feats, device)

    mu = blend(dino_dir, kappa, wp_dir_b, wp_kappa_b, wp_scale=1.0) * b_steps[:, None]
    path_flat = path_n.astype(np.float32)[:, :8].reshape(len(far), -1)
    pos = np.concatenate([mu.astype(np.float32), path_flat], axis=1)

    config_ed = load_config("config/nomad_e_dino_path.yaml")
    model_ed, sched_ed = load_model(config_ed, os.path.join(E_RUN, "ema_latest.pth"), device)
    models = {"fixed_mu": (model_ed, sched_ed, pos.shape[1])}
    ade, *_ = run_models(models, dataset, far, {"fixed_mu": pos}, device, 8, 32)
    return {"label": label, "ade_fixed_mu_cm": float(ade["fixed_mu"].mean() * 100.0)}


def main():
    os.makedirs(EVAL_OUT, exist_ok=True)
    heads = [
        ("baseline_pathact8", BASE_WP, None),
        ("A_control", None, "A_control"),
        ("B_seg025", None, "B_seg025"),
    ]
    out = {"val": [], "locked_nav": []}
    for name, wp, tag in heads:
        if tag:
            rd = run_dir(tag)
            wp = os.path.join(rd, "dino_dir_best.pth")
            out["val"].append(val_summary(rd, name))
        row = {"label": name, "ade_full_deploy_cm": eval_full_deploy(wp, name), "fixed_mu": eval_fixed_mu(wp, name)}
        out["locked_nav"].append(row)
    path = os.path.join(EVAL_OUT, "summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

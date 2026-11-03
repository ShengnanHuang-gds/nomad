"""A/B path-seg displacement supervision (8 ep, seed 0)."""
import glob
import math
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

_NOMAD_PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
PY = _NOMAD_PY if os.path.isfile(_NOMAD_PY) else sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
OUT = "logs/revalidation/path_seg_displacement_ab"
BATCH = 128
EPOCHS = 8
SEED = 0


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    subprocess.run(cmd, cwd=CWD, check=True, env=env)


def count_train_frames():
    from eval_by_distance import load_config
    from train_goal_dino import build_pairs, load_cache

    config = load_config("config/nomad_b40.yaml")
    with open(os.path.join(CWD, "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/val_trajectories.txt")) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    _cache, rows, _meta = load_cache(os.path.join("logs/dino_cache/dinov2_vits14_reg"), "train")
    train_pairs = build_pairs(
        config, "train", rows, lambda t: t not in val_trajs, 0.3, 2, "endpoint",
        (), False, None, 0, 8, 0,
    )
    n = len(train_pairs["starts"])
    steps = math.ceil(n / BATCH)
    print(f"train endpoint frames={n} batch_size={BATCH} batches_per_epoch={steps} total_updates={steps * EPOCHS}")
    return n, steps


def train_group(tag, seg_lambda, run_name):
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint", "--context", "2", "--init", INIT,
        "--run-name", run_name, "--epochs", str(EPOCHS), "--warmup-epochs", "1",
        "--batch-size", str(BATCH), "--max-batches", "0", "--seed", str(SEED),
        "--path-steps", "8", "--path-lambda", "1.0", "--path-dir-lambda", "1.0",
        "--path-smooth-lambda", "0", "--path-seg-lambda", str(seg_lambda),
        "--path-seg-beta", "1.0", "--freeze-dir", "--lr", "1e-4", "--encoder-lr", "1e-5",
        "--weight-decay", "0.05", "--select-metric", "path", "--n-sectors", "0",
    ]
    t0 = time.time()
    run(cmd)
    print(f"group {tag} train minutes", (time.time() - t0) / 60.0, flush=True)
    found = glob.glob(os.path.join(CWD, "logs", "nomad_d", run_name + "_*"))
    rd = max(found, key=os.path.getmtime) if found else None
    if rd is None:
        raise SystemExit(f"missing run dir for {tag}")
    os.makedirs(os.path.join(CWD, OUT), exist_ok=True)
    with open(os.path.join(CWD, OUT, f"{tag}_run_dir.txt"), "w", encoding="utf-8") as f:
        f.write(rd + chr(10))
    return rd


def main():
    os.makedirs(os.path.join(CWD, OUT), exist_ok=True)
    count_train_frames()
    train_group("A_control", 0.0, "nomad_dino_wp_pathseg_a")
    train_group("B_seg025", 0.25, "nomad_dino_wp_pathseg_b")
    print("done; next: python run_path_seg_locked_nav.py", flush=True)


if __name__ == "__main__":
    main()

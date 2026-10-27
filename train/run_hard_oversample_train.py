"""Hard frame oversampling (x3) from turnhard + locked eval."""
import glob
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

PY = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_turnhard_2026_10_26_10_04_05/dino_dir_best.pth"
RUN = "nomad_dino_wp_ctx2_hard_os3"
HARD_CSV = "logs/revalidation/hard_pairs/hard_pairs_train.csv"
OUT = "logs/revalidation/wp_hard_oversample"


def latest():
    d = glob.glob(os.path.join(CWD, "logs", "nomad_d", RUN + "_*"))
    return max(d, key=os.path.getmtime) if d else None


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=CWD, check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.isfile(os.path.join(CWD, HARD_CSV)):
        run([PY, "-u", "mine_hard_pairs.py", "--split", "train"])
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint",
        "--context", "2",
        "--init", INIT,
        "--run-name", RUN,
        "--epochs", "12",
        "--hard-pairs-csv", HARD_CSV,
        "--hard-frame-boost", "3.0",
        "--hard-pairs-turn-only",
        "--turn-strict-weight", "3.0",
        "--hard-bearing-deg", "30",
        "--hard-weight", "2.5",
        "--turn-winding-deg", "45",
        "--turn-weight", "2.0",
    ]
    t0 = time.time()
    run(cmd)
    print("train min", (time.time() - t0) / 60.0, flush=True)
    rd = latest()
    run([PY, "-u", "eval_waypoint_head.py", "--run-dir", rd, "--skip-tune"])
    run([PY, "-u", "eval_blend_ablation.py", "--run-dir", rd])
    open(os.path.join(OUT, "run_dir.txt"), "w").write(rd + "\n")
    print("done", rd, flush=True)


if __name__ == "__main__":
    main()
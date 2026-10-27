"""Multi-horizon 4,6 WP train from turnhard + locked eval."""
import glob
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

PY = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_turnhard_2026_10_26_10_04_05/dino_dir_best.pth"
RUN = "nomad_dino_wp_ctx2_mh46"
OUT = "logs/revalidation/wp_mh46"


def latest():
    d = glob.glob(os.path.join(CWD, "logs", "nomad_d", RUN + "_*"))
    return max(d, key=os.path.getmtime) if d else None


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=CWD, check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint",
        "--context", "2",
        "--init", INIT,
        "--run-name", RUN,
        "--epochs", "12",
        "--multi-horizon", "4,6",
        "--multi-horizon-lambda", "0.4",
        "--multi-horizon-strict",
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
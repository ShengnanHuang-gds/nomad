"""Yaw-traj WP: deploy dir = integrate(yaw). ctx2 init 18ep then scratch 30ep + eval."""
import glob
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

PY = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
CTX2 = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
OUT = "logs/revalidation/wp_yawtraj"

COMMON = [
    "--target", "endpoint",
    "--context", "2",
    "--yaw-aux-steps", "8",
    "--yaw-aux-lambda", "0.3",
    "--yaw-integrate-lambda", "0.25",
    "--turn-strict-weight", "3.0",
    "--hard-bearing-deg", "30",
    "--hard-weight", "2.5",
    "--turn-winding-deg", "45",
    "--turn-weight", "2.0",
]

RUNS = [
    ("nomad_dino_wp_yawtraj_ctx2_18", 18, CTX2),
    ("nomad_dino_wp_yawtraj_scratch30", 30, None),
]


def latest(prefix):
    d = glob.glob(os.path.join(CWD, "logs", "nomad_d", prefix + "_*"))
    return max(d, key=os.path.getmtime) if d else None


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=CWD, check=True)


def train_eval(run_name, epochs, init):
    cmd = [PY, "-u", "train_goal_dino.py", "--run-name", run_name, "--epochs", str(epochs)] + COMMON
    if init:
        cmd += ["--init", init]
    t0 = time.time()
    run(cmd)
    print(f"train {run_name} min", (time.time() - t0) / 60.0, flush=True)
    rd = latest(run_name)
    run([PY, "-u", "eval_waypoint_head.py", "--run-dir", rd, "--skip-tune"])
    run([PY, "-u", "eval_blend_ablation.py", "--run-dir", rd])
    return rd


def main():
    os.makedirs(OUT, exist_ok=True)
    lines = []
    for run_name, epochs, init in RUNS:
        print("===", run_name, "epochs", epochs, "init", init or "none", "===", flush=True)
        rd = train_eval(run_name, epochs, init)
        lines.append(f"{run_name}\t{rd}\n")
    with open(os.path.join(OUT, "run_dirs.txt"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
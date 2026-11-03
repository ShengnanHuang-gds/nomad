"""New 8-step path_head: ViNT action units, freeze dir/kappa, init turnhard.

Select on far path ADE. Diagnose vs GT 8-step after train. E-FT is a follow-up.
"""
import glob
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

_NOMAD_PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
PY = _NOMAD_PY if os.path.isfile(_NOMAD_PY) else sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_turnhard_2026_10_26_10_04_05/dino_dir_best.pth"
RUN = "nomad_dino_wp_ctx2_pathact8"
OUT = "logs/revalidation/path_head_action8"
REF = "GT turn ~47 deg / ray vsGT 24cm / old pathpoly vsGT 18cm but 128 deg wiggly"


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    subprocess.run(cmd, cwd=CWD, check=True, env=env)


def latest():
    found = glob.glob(os.path.join(CWD, "logs", "nomad_d", RUN + "_*"))
    return max(found, key=os.path.getmtime) if found else None


def main():
    os.makedirs(os.path.join(CWD, OUT), exist_ok=True)
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint",
        "--context", "2",
        "--init", INIT,
        "--run-name", RUN,
        "--epochs", "12",
        "--n-sectors", "0",
        "--path-steps", "8",
        "--path-lambda", "1.0",
        "--path-dir-lambda", "0.0",
        "--path-smooth-lambda", "0.1",
        "--freeze-dir",
        "--lr", "3e-4",
        "--encoder-lr", "1e-4",
        "--select-metric", "path",
        "--turn-strict-weight", "3.0",
        "--hard-bearing-deg", "30",
        "--hard-weight", "2.5",
        "--turn-winding-deg", "45",
        "--turn-weight", "2.0",
        "--curvature-tiers", "1,1.5,3",
    ]
    t0 = time.time()
    run(cmd)
    print("train min", (time.time() - t0) / 60.0, flush=True)
    rd = latest()
    if rd is None:
        raise SystemExit("missing run dir")
    open(os.path.join(CWD, OUT, "run_dir.txt"), "w", encoding="utf-8").write(rd + "\n")
    wp = os.path.join(rd, "dino_dir_best.pth")
    run([PY, "-u", "diagnose_path_vs_gt.py", "--wp", wp, "--units", "dataset"])
    print("compare vs", REF, flush=True)
    print("done", rd, flush=True)
    print("next: E-FT from E-oracle, blend_path18 wp_poly --path-units dataset", flush=True)


if __name__ == "__main__":
    main()

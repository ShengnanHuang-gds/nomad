# -*- coding: utf-8 -*-
"""A/B: CLS->8pt (A) vs 8 step queries (B). Same init, budget, path losses; frozen dir/kappa."""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import cv2  # noqa: F401

_NOMAD_PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
PY = _NOMAD_PY if os.path.isfile(_NOMAD_PY) else sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
OUT = os.path.join(CWD, "logs/revalidation/path_readout_ab")
RUN_A = "nomad_dino_wp_ctx2_pathreadout_A_cls"
RUN_B = "nomad_dino_wp_ctx2_pathreadout_B_stepq"


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    subprocess.run(cmd, cwd=CWD, check=True, env=env)


def latest(run_name):
    found = glob.glob(os.path.join(CWD, "logs", "nomad_d", run_name + "_*"))
    return max(found, key=os.path.getmtime) if found else None


def train_run(run_name, path_spatial: str):
    cmd = [
        PY,
        "-u",
        "train_goal_dino.py",
        "--target",
        "endpoint",
        "--context",
        "2",
        "--init",
        INIT,
        "--run-name",
        run_name,
        "--epochs",
        "12",
        "--n-sectors",
        "0",
        "--path-steps",
        "8",
        "--path-spatial",
        path_spatial,
        "--path-lambda",
        "1.0",
        "--path-dir-lambda",
        "0.0",
        "--path-smooth-lambda",
        "0.1",
        "--freeze-dir",
        "--lr",
        "3e-4",
        "--encoder-lr",
        "1e-4",
        "--select-metric",
        "path",
        "--turn-strict-weight",
        "3.0",
        "--hard-bearing-deg",
        "30",
        "--hard-weight",
        "2.5",
        "--turn-winding-deg",
        "45",
        "--turn-weight",
        "2.0",
        "--curvature-tiers",
        "1,1.5,3",
    ]
    t0 = time.time()
    run(cmd)
    print(f"{run_name} train min", (time.time() - t0) / 60.0, flush=True)
    rd = latest(run_name)
    if rd is None:
        raise SystemExit(f"missing run dir for {run_name}")
    return os.path.join(rd, "dino_dir_best.pth")


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "init_checkpoint": INIT,
        "recipe_note": "Same as pathact8-style: endpoint ctx2, path_lambda=1, smooth=0.1, freeze-dir, 12ep",
        "group_A": "path_spatial='' (CLS linear 8*2)",
        "group_B": "path_spatial=step_query (8 learnable queries, shared Linear->2)",
    }
    wp_a = train_run(RUN_A, "")
    wp_b = train_run(RUN_B, "step_query")
    meta["checkpoint_A"] = wp_a
    meta["checkpoint_B"] = wp_b
    run(
        [
            PY,
            "-u",
            "eval_path_readout_val.py",
            "--wp-a",
            wp_a,
            "--wp-b",
            wp_b,
            "--out",
            os.path.join(OUT, "val_metrics.csv"),
        ]
    )
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("done", OUT, flush=True)


if __name__ == "__main__":
    main()

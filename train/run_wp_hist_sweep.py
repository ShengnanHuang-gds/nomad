"""Train/eval 3-frame history WP variants (init from deploy ctx2)."""
import argparse
import glob
import os
import subprocess
import sys
import time

import cv2  # noqa: F401

INIT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
PY = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))

EXPERIMENTS = [
    {
        "name": "nomad_dino_wp_hist3",
        "extra": [],
    },
    {
        "name": "nomad_dino_wp_hist3_turnhard",
        "extra": [
            "--turn-strict-weight", "3.0",
            "--hard-bearing-deg", "30",
            "--hard-weight", "2.5",
            "--turn-winding-deg", "45",
            "--turn-weight", "2.0",
        ],
    },
    {
        "name": "nomad_dino_wp_hist3_turnlight",
        "extra": ["--turn-strict-weight", "2.0"],
    },
]


def latest_run(prefix):
    dirs = glob.glob(os.path.join(CWD, "logs", "nomad_d", prefix + "_*"))
    if prefix == "nomad_dino_wp_hist3":
        dirs = [
            d
            for d in dirs
            if "_turnhard_" not in os.path.basename(d) and "_turnlight_" not in os.path.basename(d)
        ]
    return max(dirs, key=os.path.getmtime) if dirs else None


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=CWD, check=True)


def train_one(exp, epochs, skip_train):
    prefix = exp["name"]
    if skip_train:
        rd = latest_run(prefix)
        if not rd:
            raise SystemExit("missing run for " + prefix)
        return rd
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint",
        "--context", "3",
        "--init", INIT,
        "--run-name", prefix,
        "--epochs", str(epochs),
    ] + exp["extra"]
    t0 = time.time()
    run(cmd)
    print("train %.1f min" % ((time.time() - t0) / 60.0), flush=True)
    rd = latest_run(prefix)
    if not rd:
        raise SystemExit("no run dir after " + prefix)
    return rd


def eval_run(rd):
    run([PY, "-u", "eval_waypoint_head.py", "--run-dir", rd, "--skip-tune"])
    run([PY, "-u", "eval_blend_ablation.py", "--run-dir", rd])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--only", default="", help="comma names e.g. hist3,turnhard,turnlight")
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--skip-eval", action="store_true")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    for exp in EXPERIMENTS:
        key = exp["name"].replace("nomad_dino_wp_", "")
        if only and key not in only and exp["name"] not in only:
            continue
        print("\n===", exp["name"], "===", flush=True)
        rd = train_one(exp, args.epochs, args.skip_train)
        if not args.skip_eval:
            eval_run(rd)
    if not args.skip_eval:
        run([PY, "-u", "summarize_wp_hist_sweep.py"])


if __name__ == "__main__":
    main()
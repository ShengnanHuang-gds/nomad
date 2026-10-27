"""~2h autonomous batch: trains + eval sweeps."""
import argparse
import glob
import os
import subprocess
import sys
import time
from datetime import datetime

import cv2  # noqa: F401

PY = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(CWD, "logs/revalidation/afternoon_2026_10_26")
INIT_CTX2 = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
INIT_HIST3_TH = "logs/nomad_d/nomad_dino_wp_hist3_turnhard_2026_10_26_11_54_24/dino_dir_best.pth"
LOG = os.path.join(OUT, "batch.log")

BASELINES = [
    "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44",
    "logs/nomad_d/nomad_dino_wp_hist_ctx2_turnhard_2026_10_26_10_04_05",
    "logs/nomad_d/nomad_dino_wp_hist3_turnhard_2026_10_26_11_54_24",
]

TRAINS = [
    {
        "name": "nomad_dino_wp_ctx2_hard45",
        "init": INIT_CTX2,
        "args": [
            "--context", "2",
            "--hard-bearing-deg", "42",
            "--hard-weight", "3.5",
            "--turn-strict-weight", "3.0",
            "--turn-winding-deg", "45",
            "--turn-weight", "2.5",
        ],
        "epochs": 12,
    },
    {
        "name": "nomad_dino_wp_ctx2_curvtier",
        "init": INIT_CTX2,
        "args": [
            "--context", "2",
            "--curvature-tiers", "1,2,4",
            "--turn-strict-weight", "2.5",
            "--turn-winding-deg", "40",
            "--turn-weight", "2.0",
        ],
        "epochs": 12,
    },
    {
        "name": "nomad_dino_wp_hist3_th_cont",
        "init": INIT_HIST3_TH,
        "args": ["--context", "3", "--turn-strict-weight", "3.0", "--hard-bearing-deg", "30", "--hard-weight", "2.5", "--turn-winding-deg", "45", "--turn-weight", "2.0"],
        "epochs": 6,
    },
    {
        "name": "nomad_dino_wp_ctx2_ft_hist3th",
        "init": INIT_HIST3_TH,
        "args": ["--context", "2", "--turn-strict-weight", "3.0", "--hard-bearing-deg", "30", "--hard-weight", "2.5"],
        "epochs": 10,
    },
]


def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd):
    log("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=CWD, check=True)


def latest(prefix):
    dirs = glob.glob(os.path.join(CWD, "logs", "nomad_d", prefix + "_*"))
    return max(dirs, key=os.path.getmtime) if dirs else None


def eval_run(rd):
    run([PY, "-u", "eval_waypoint_head.py", "--run-dir", rd, "--skip-tune"])
    run([PY, "-u", "eval_blend_ablation.py", "--run-dir", rd])
    run([PY, "-u", "eval_kappa_wp_scale.py", "--run-dir", rd])


def train_one(spec):
    cmd = [
        PY, "-u", "train_goal_dino.py",
        "--target", "endpoint",
        "--init", spec["init"],
        "--run-name", spec["name"],
        "--epochs", str(spec["epochs"]),
    ] + spec["args"]
    t0 = time.time()
    run(cmd)
    log("train %s done %.1f min" % (spec["name"], (time.time() - t0) / 60))
    rd = latest(spec["name"])
    if not rd:
        raise SystemExit("missing run " + spec["name"])
    eval_run(rd)
    return rd


def summarize():
    import csv
    import numpy as np
    from eval_testtime import angle_err

    lines = ["=== Afternoon batch %s ===" % datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    all_runs = list(BASELINES)
    for spec in TRAINS:
        rd = latest(spec["name"])
        if rd:
            all_runs.append(rd)
    for rd in all_runs:
        tag = os.path.basename(rd)
        wp = os.path.join(rd, "eval_waypoint", "locked_per_frame.npz")
        ab = os.path.join(rd, "eval_blend_ablation", "ablation.csv")
        if not os.path.isfile(wp) or not os.path.isfile(ab):
            lines.append(tag + ": incomplete")
            continue
        e = angle_err(np.load(wp)["wp_dir"], np.load(wp)["endpoint"])
        with open(ab, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        kap = {r["frames"]: float(r["use_cm"]) for r in rows if r["condition"] == "kappa blend"}
        sup = {r["frames"]: float(r["use_cm"]) for r in rows if "deploy w35-55" in r.get("condition", "")}
        lines.append(
            "%s | med %.2f | kap all %+.2f turn %+.2f | deploy-sup %s"
            % (tag, float(np.median(e)), kap.get("all", 0), kap.get("turn 0.30m/45deg", 0), sup.get("all", "n/a"))
        )
    lines.append("")
    lines.append("See constrained_fallback/ and per-run eval_kappa_wp_scale/")
    text = "\n".join(lines) + "\n"
    open(os.path.join(OUT, "summary_cn.txt"), "w", encoding="utf-8").write(text)
    print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--max-hours", type=float, default=2.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t_end = time.time() + args.max_hours * 3600
    log("batch start max_hours=%.1f" % args.max_hours)
    run([PY, "-u", "eval_constrained_fallback.py"])
    if not args.skip_train:
        for spec in TRAINS:
            if time.time() > t_end - 600:
                log("time budget: skip remaining trains")
                break
            try:
                train_one(spec)
            except Exception as ex:
                log("FAIL %s: %s" % (spec["name"], ex))
    for rd in BASELINES:
        if os.path.isdir(os.path.join(CWD, rd)):
            try:
                run([PY, "-u", "eval_kappa_wp_scale.py", "--run-dir", rd])
            except Exception as ex:
                log("kappa scale skip %s: %s" % (rd, ex))
    summarize()
    log("batch done")


if __name__ == "__main__":
    main()
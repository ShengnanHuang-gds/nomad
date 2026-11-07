"""Compile R2/R18 deliverables after training (no re-train)."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from eval_e_path_adapt_val import bootstrap_trajectory_pooled
from r2_r18_common import align_paired_ade, bootstrap_traj_pooled_pairs, load_val_rows, manifest_units_note

CWD = Path(__file__).resolve().parent
OUT = CWD / "logs/revalidation/r2_r18_fair_2026-11-07"
RUN_R2 = CWD / "logs/nomad/nomad_e_r2_fair_20261107"
RUN_R18 = CWD / "logs/nomad/nomad_e_r18_fair_20261107"
MANIFEST = OUT / "val_far_manifest_seed20261107.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pick_best(run_dir: Path) -> dict | None:
    best = None
    for ep in range(8):
        jf = run_dir / f"val_nav_epoch{ep}.json"
        if not jf.is_file():
            continue
        with open(jf, encoding="utf-8") as f:
            m = json.load(f)
        if best is None or m["nav_ade_cm"] < best["nav_ade_cm"]:
            best = {"epoch": ep, **m}
    if best:
        ck = run_dir / f"ema_{best['epoch']}.pth"
        best["checkpoint"] = str(ck)
        best["sha256"] = sha256_file(ck) if ck.is_file() else ""
    return best


def subset_means_from_csv(csv_path: str) -> dict:
    rows = load_val_rows(csv_path)
    nav = np.array([float(r["nav_ade_cm"]) for r in rows])
    f4 = np.array([float(r["ade_front4_cm"]) for r in rows])
    b4 = np.array([float(r["ade_back4_cm"]) for r in rows])
    turn = np.array([float(r.get("turn_strict", 0) or 0) > 0.5 for r in rows])
    o = {"nav_ade_cm": float(nav.mean()), "ade_front4_cm": float(f4.mean()), "ade_back4_cm": float(b4.mean()), "n": len(rows)}
    if turn.any():
        o["nav_ade_turn_strict_cm"] = float(nav[turn].mean())
        o["ade_front4_turn_strict_cm"] = float(f4[turn].mean())
        o["ade_back4_turn_strict_cm"] = float(b4[turn].mean())
        o["turn_strict_n"] = int(turn.sum())
    return o


def epoch_table(run_dir: Path) -> list[dict]:
    log = run_dir / "train_log.csv"
    rows = []
    if log.is_file():
        rows = list(csv.DictReader(open(log, encoding="utf-8")))
    per_ep = []
    for ep in range(8):
        jf = run_dir / f"val_nav_epoch{ep}.json"
        if jf.is_file():
            with open(jf, encoding="utf-8") as f:
                val = json.load(f)
        else:
            val = {}
        tr = next((r for r in rows if str(r.get("epoch")) == str(ep)), {})
        per_ep.append({"epoch": ep, "train": tr, "val": val})
    return per_ep


def main():
    os.makedirs(OUT, exist_ok=True)
    b2 = pick_best(RUN_R2) if RUN_R2.is_dir() else None
    b18 = pick_best(RUN_R18) if RUN_R18.is_dir() else None
    paired = {}
    if b2 and b18 and b2.get("per_frame_csv") and b18.get("per_frame_csv"):
        p2 = Path(b2["per_frame_csv"])
        p18 = Path(b18["per_frame_csv"])
        if not p2.is_absolute():
            p2 = CWD / p2
        if not p18.is_absolute():
            p18 = CWD / p18
        ade2, ade18, trajs = align_paired_ade(str(p2), str(p18))
        delta = ade2 - ade18
        m, lo, hi = bootstrap_traj_pooled_pairs(delta, np.array(trajs))
        # legacy bootstrap on same deltas for cross-check
        m2, lo2, hi2 = bootstrap_trajectory_pooled(delta, trajs)
        paired = {
            "n_pairs": len(delta),
            "delta_r2_minus_r18_cm_mean": m,
            "ci95_lo": lo,
            "ci95_hi": hi,
            "bootstrap_trajectory_pooled_check": {"mean": m2, "lo": lo2, "hi": hi2},
            "positive_improvement": m > 0 and lo > 0,
        }
    summary = {
        "manifest": str(MANIFEST),
        "manifest_units": manifest_units_note(str(MANIFEST)),
        "R2": {"run_dir": str(RUN_R2), "best": b2, "epochs": epoch_table(RUN_R2)},
        "R18": {"run_dir": str(RUN_R18), "best": b18, "epochs": epoch_table(RUN_R18)},
        "paired_all": paired,
        "resume_policy": "No strict resume in this run; partial ema_latest resume is disabled in launcher",
    }
    with open(OUT / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    if b2 and b18:
        with open(OUT / "main_results.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "method",
                    "cond_dim",
                    "val_nav_ade_cm",
                    "turn_strict_ade_cm",
                    "front4_cm",
                    "back4_cm",
                    "best_epoch",
                    "checkpoint",
                ]
            )
            for label, b, dim in [("R2", b2, 2), ("R18", b18, 18)]:
                w.writerow(
                    [
                        label,
                        dim,
                        b.get("nav_ade_cm"),
                        b.get("nav_ade_turn_strict_cm"),
                        b.get("ade_front4_cm"),
                        b.get("ade_back4_cm"),
                        b.get("epoch"),
                        b.get("checkpoint"),
                    ]
                )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

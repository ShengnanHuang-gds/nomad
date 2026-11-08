"""Aggregate R2/R18 fair ablation across training seeds 0,1,2 (val manifest fixed)."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np

from r2_r18_common import align_paired_ade

CWD = Path(__file__).resolve().parent
OUT = CWD / "logs/revalidation/r2_r18_fair_2026-11-07"
BASE = "20261107"

SEED_RUNS = {
    0: ("nomad_e_r2_fair_20261107", "nomad_e_r18_fair_20261107"),
    1: (f"nomad_e_r2_fair_{BASE}_seed1", f"nomad_e_r18_fair_{BASE}_seed1"),
    2: (f"nomad_e_r2_fair_{BASE}_seed2", f"nomad_e_r18_fair_{BASE}_seed2"),
}


def best_val(run_name: str) -> dict | None:
    run_dir = CWD / "logs/nomad" / run_name
    best = None
    for ep in range(8):
        jf = run_dir / f"val_nav_epoch{ep}.json"
        if not jf.is_file():
            continue
        with open(jf, encoding="utf-8") as f:
            m = json.load(f)
        if best is None or m["nav_ade_cm"] < best["nav_ade_cm"]:
            best = {"epoch": ep, **m, "checkpoint": str(run_dir / f"ema_{ep}.pth")}
    return best


def paired_deltas_at_best(r2_run: str, r18_run: str) -> dict | None:
    b2, b18 = best_val(r2_run), best_val(r18_run)
    if not b2 or not b18:
        return None
    p2 = b2.get("per_frame_csv", "")
    p18 = b18.get("per_frame_csv", "")
    if not p2 or not p18:
        return None
    if not Path(p2).is_absolute():
        p2 = str(CWD / p2)
    if not Path(p18).is_absolute():
        p18 = str(CWD / p18)
    ade2, ade18, _ = align_paired_ade(p2, p18)
    d_nav = ade2 - ade18
    rows2 = {int(r["order"]): r for r in csv.DictReader(open(p2, encoding="utf-8"))}
    rows18 = {int(r["order"]): r for r in csv.DictReader(open(p18, encoding="utf-8"))}
    turn = np.array([float(rows2[o].get("turn_strict", 0) or 0) > 0.5 for o in sorted(rows2)])
    f2 = np.array([float(rows2[o]["ade_front4_cm"]) for o in sorted(rows2)])
    f18 = np.array([float(rows18[o]["ade_front4_cm"]) for o in sorted(rows18)])
    b2v = np.array([float(rows2[o]["ade_back4_cm"]) for o in sorted(rows2)])
    b18v = np.array([float(rows18[o]["ade_back4_cm"]) for o in sorted(rows18)])
    return {
        "r2_nav": float(ade2.mean()),
        "r18_nav": float(ade18.mean()),
        "delta_nav": float(d_nav.mean()),
        "delta_turn": float((ade2[turn] - ade18[turn]).mean()) if turn.any() else float("nan"),
        "delta_front4": float((f2 - f18).mean()),
        "delta_back4": float((b2v - b18v).mean()),
        "r2_epoch": b2["epoch"],
        "r18_epoch": b18["epoch"],
    }


def main():
    rows = []
    deltas = []
    r2_navs, r18_navs = [], []
    for seed, (r2, r18) in SEED_RUNS.items():
        p = paired_deltas_at_best(r2, r18)
        if not p:
            rows.append({"train_seed": seed, "status": "incomplete", "r2_run": r2, "r18_run": r18})
            continue
        deltas.append(p["delta_nav"])
        r2_navs.append(p["r2_nav"])
        r18_navs.append(p["r18_nav"])
        rows.append({"train_seed": seed, "status": "ok", "r2_run": r2, "r18_run": r18, **p})
    summary = {
        "per_seed": rows,
        "r2_ade_mean": float(np.mean(r2_navs)) if r2_navs else float("nan"),
        "r2_ade_std": float(np.std(r2_navs, ddof=0)) if len(r2_navs) > 1 else float("nan"),
        "r18_ade_mean": float(np.mean(r18_navs)) if r18_navs else float("nan"),
        "r18_ade_std": float(np.std(r18_navs, ddof=0)) if len(r18_navs) > 1 else float("nan"),
        "delta_nav_mean": float(np.mean(deltas)) if deltas else float("nan"),
        "delta_nav_std": float(np.std(deltas, ddof=0)) if len(deltas) > 1 else float("nan"),
        "delta_nav_min": float(min(deltas)) if deltas else float("nan"),
        "delta_nav_max": float(max(deltas)) if deltas else float("nan"),
        "n_complete_seeds": len(deltas),
        "same_direction_all": all(d > 0 for d in deltas) if len(deltas) >= 2 else None,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(OUT / "multiseed_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(OUT / "multiseed_table.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "train_seed",
                "r2_epoch",
                "r2_nav_ade_cm",
                "r18_epoch",
                "r18_nav_ade_cm",
                "delta_nav",
                "delta_turn",
                "delta_front4",
                "delta_back4",
            ],
            extrasaction="ignore",
        )
        w.writeheader()
        for r in rows:
            if r.get("status") != "ok":
                continue
            w.writerow(
                {
                    "train_seed": r["train_seed"],
                    "r2_epoch": r["r2_epoch"],
                    "r2_nav_ade_cm": r["r2_nav"],
                    "r18_epoch": r["r18_epoch"],
                    "r18_nav_ade_cm": r["r18_nav"],
                    "delta_nav": r["delta_nav"],
                    "delta_turn": r["delta_turn"],
                    "delta_front4": r["delta_front4"],
                    "delta_back4": r["delta_back4"],
                }
            )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

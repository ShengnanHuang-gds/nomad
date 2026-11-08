"""Train R2/R18 fair ablation for additional seeds (1,2); do not touch seed0 runs."""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone

from run_r2_r18_fair_ablation import (
    CONFIG_R18,
    CONFIG_R2,
    CWD,
    OUT,
    train_arm,
    write_report,
)

SEEDS = (1, 2)
BASE = "20261107"
MANIFEST = os.path.join(OUT, f"val_far_manifest_seed{BASE}.csv")
EXCLUDE = os.path.join(OUT, "exclude_val_trajs.txt")


def run_name(arm: str, seed: int) -> str:
    tag = "r2" if arm == "R2" else "r18"
    return f"nomad_e_{tag}_fair_{BASE}_seed{seed}"


def is_complete(seed: int) -> dict:
    out = {}
    for arm in ("R2", "R18"):
        rn = run_name(arm, seed)
        log = os.path.join(CWD, "logs", "nomad", rn, "train_log.csv")
        n = 0
        if os.path.isfile(log):
            with open(log, encoding="utf-8") as f:
                n = sum(1 for r in csv.DictReader(f) if str(r.get("epoch", "")).isdigit())
        out[arm] = {"run_name": rn, "epochs_in_log": n, "complete": n >= 8}
    return out


def audit_all() -> dict:
    report = {"seed0_note": "nomad_e_r2_fair_20261107 / nomad_e_r18_fair_20261107 (unchanged)"}
    for s in SEEDS:
        report[f"seed{s}"] = is_complete(s)
    return report


def train_seed(seed: int) -> None:
    st = is_complete(seed)
    if st["R2"]["complete"] and st["R18"]["complete"]:
        print(f"seed {seed}: both arms complete, skip training")
        return
    if not st["R2"]["complete"]:
        train_arm("R2", "goal", 2, CONFIG_R2, run_name("R2", seed), MANIFEST, EXCLUDE, train_seed=seed)
    if not st["R18"]["complete"]:
        train_arm("R18", "goal_path", 18, CONFIG_R18, run_name("R18", seed), MANIFEST, EXCLUDE, train_seed=seed)


def main():
    import argparse

    ap = argparse.ArgumentParser(description="R2/R18 seed repeat (1,2 only)")
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    audit = audit_all()
    audit_path = os.path.join(OUT, "seed_repeat_audit.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "audited_at_utc": datetime.now(timezone.utc).isoformat(),
                "seeds_requested": args.seeds,
                "status": audit,
                "val_manifest": MANIFEST,
                "val_eval_seed": 0,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    if args.audit_only:
        return
    for s in args.seeds:
        if s == 0:
            print("skip seed 0 (frozen)")
            continue
        train_seed(s)
    if args.report_only:
        for s in args.seeds:
            if s == 0:
                continue
            write_report(
                os.path.join(CWD, "logs", "nomad", run_name("R2", s)),
                os.path.join(CWD, "logs", "nomad", run_name("R18", s)),
                MANIFEST,
            )
            src = os.path.join(OUT, "summary.json")
            if os.path.isfile(src):
                dst = os.path.join(OUT, f"summary_seed{s}.json")
                with open(src, encoding="utf-8") as inf, open(dst, "w", encoding="utf-8") as outf:
                    outf.write(inf.read())
        from r2_r18_multiseed_report import main as multiseed_main

        multiseed_main()


if __name__ == "__main__":
    main()

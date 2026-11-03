# -*- coding: utf-8 -*-
"""Goal-image sensitivity on fixed 13 val cases (frozen pathact8, path head only)."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import pickle
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

from eval_by_distance import load_config
from eval_e_dino import head_predict_wp_path
from train_e_dino import load_dino_head
from train_goal_dino import CACHE_DIR, MAX_STEPS, MIN_STEPS, go_stanford_meters_per_unit, load_cache
from turn_match_viz import list_v1_cases, load_rgb_crop

import run_turn_visual_correspondence_v3 as tv3

DEFAULT_WP = tv3.DEFAULT_WP
V1_CASES = tv3.V1_CASES
OUT_DIR = Path("logs/revalidation/goal_sensitivity_pathact8_val13")
HORIZON = 8


def git_short():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def ckpt_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_max_goal_map(config):
    from diagnose_turn_visual_correspondence import load_index

    by_traj = load_index(config, split="train")
    out = {}
    for traj, entries in by_traj.items():
        for curr, max_goal in entries:
            out[(traj, int(curr))] = int(max_goal)
    return out


def legal_goal_ks(data_folder, traj, curr, spacing, mpu, max_goal, rows, min_goal_m=0.3):
    with open(os.path.join(data_folder, traj, "traj_data.pkl"), "rb") as f:
        td = pickle.load(f)
    pos = np.asarray(td["position"], dtype=np.float64).reshape(-1, 2)
    yaw = td["yaw"]
    y0 = float(np.ravel(yaw[int(curr)])[0])
    c, s = np.cos(y0), np.sin(y0)
    after_k = HORIZON * spacing
    legal = []
    for k in range(MIN_STEPS, min(MAX_STEPS, max_goal) + 1):
        if k <= after_k:
            continue
        gt = curr + k
        if gt >= len(pos):
            continue
        if (traj, gt) not in rows:
            continue
        d = pos[gt] - pos[curr]
        local = np.array([d[0] * c + d[1] * s, -d[0] * s + d[1] * c], dtype=np.float32)
        if float(np.linalg.norm(local)) < min_goal_m:
            continue
        legal.append(k)
    return legal


def pick_alt_ks(legal, baseline_k, n=3):
    alts = [k for k in legal if k != baseline_k]
    if not alts:
        return []
    if len(alts) <= n:
        return sorted(alts)
    qs = np.quantile(alts, [0.25, 0.5, 0.75])
    picked = []
    used = set()
    for q in qs:
        cand = sorted(alts, key=lambda k: (abs(k - q), k))
        for k in cand:
            if k not in used:
                used.add(k)
                picked.append(k)
                break
    for k in sorted(alts):
        if len(picked) >= n:
            break
        if k not in used:
            picked.append(k)
    return sorted(picked)[:n]


def step8_dir_delta_deg(pred_a, pred_b):
    u = lambda v: v / max(np.linalg.norm(v), 1e-6)
    return float(
        np.degrees(
            np.arccos(np.clip(float(u(pred_a[-1]) @ u(pred_b[-1])), -1.0, 1.0))
        )
    )


def build_report(rows_by_case, meta):
    lines = [
        "# 目标图像敏感性诊断（13 验证案例）",
        "",
        "## 代码事实",
        "",
        f"- Checkpoint: `{meta['checkpoint']}` (sha256[:16]={meta['checkpoint_sha256_16']})",
        f"- Git: `{meta['git_commit']}`",
        f"- 命令: `{meta['command']}`",
        "- 冻结 pathact8 路径头；固定 curr、t-1、t-2；**仅更换同轨迹合法 goal**",
        f"- 合法 goal 索引间隔 k∈[{MIN_STEPS}, min({MAX_STEPS}, max_goal)]；附加 goal 要求 **k > {HORIZON}×spacing**",
        "- 同一条轨迹上 GT 八步路径不变；本实验看 goal 距离/外观变化下的输出，**不是分岔意图实验**",
        "",
        "## 逐例简答",
        "",
    ]
    for key, rows in rows_by_case.items():
        tag, traj, t = key
        orig = [r for r in rows if r["is_original_goal"] == 1][0]
        alts = [r for r in rows if r["is_original_goal"] == 0]
        ade_spread = max(r["path_ade_cm"] for r in rows) - min(r["path_ade_cm"] for r in rows)
        shift_max = max(r["mean_pos_shift_vs_orig_cm"] for r in rows)
        lines.append(f"### {tag} — {traj} t={t}")
        lines.append(f"- **【实验观察】** 共 {len(rows)} 个 goal（原 goal Δidx={orig['goal_k_index_steps']}）")
        lines.append(
            f"- **【代码事实】** 原 goal ADE={orig['path_ade_cm']:.2f} cm，dir_err={orig['dir_err_deg']:.1f}°；"
            f"换 goal 后 ADE 极差≈{ade_spread:.2f} cm，八点均位移相对原 goal 最大≈{shift_max:.2f} cm"
        )
        if shift_max < 2.0 and ade_spread < 3.0:
            ans = "预测对 goal 变化**几乎不变**（就本例数值而言）"
        elif shift_max > 15.0 or ade_spread > 15.0:
            ans = "预测对 goal 变化**明显**"
        else:
            ans = "预测有**中等幅度**变化"
        lines.append(f"- **【实验观察】** {ans}")
        bad_dir = orig["dir_err_deg"] > 45
        if bad_dir:
            alts_bad = sum(1 for r in alts if r["dir_err_deg"] > 45)
            lines.append(
                f"- **【实验观察】** 原 goal 方向误差已大（{orig['dir_err_deg']:.0f}°）；"
                f"换 goal 后 {alts_bad}/{len(alts)} 个附加 goal 仍 >45°"
            )
        lines.append("")
    lines.extend(
        [
            "## 研究推断（弱）",
            "",
            "- 输出变化小 **不能** 单独证明模型忽略 goal；变化大 **不能** 单独证明模型理解 goal。",
            "",
            "## 尚不能回答",
            "",
            "- 13 例无法推断总体因果；单个 goal 低 ADE 不是可部署成绩。",
            "",
            "## 总问",
            "",
            "见 meta.json 中 `summary_verdict`（由 CSV 自动汇总）。",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def summarize_verdict(all_rows):
    by_case = {}
    for r in all_rows:
        key = (r["tag"], r["traj_name"], int(r["t"]))
        by_case.setdefault(key, []).append(r)
    sensitive = 0
    flat = 0
    for rows in by_case.values():
        shifts = [float(x["mean_pos_shift_vs_orig_cm"]) for x in rows if not x["is_original_goal"]]
        if not shifts:
            continue
        if max(shifts) < 3.0:
            flat += 1
        elif max(shifts) > 12.0:
            sensitive += 1
    n = len(by_case)
    if sensitive > flat and sensitive >= n // 3:
        return "cases_mixed_but_goal_sensitivity_visible"
    if flat >= n // 2:
        return "mostly_insensitive_in_these_13"
    return "mixed_inconclusive_13_cases"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "cases").mkdir(exist_ok=True)
    config = load_config("config/nomad_b40.yaml")
    data_folder = config["datasets"]["go_stanford"]["data_folder"]
    spacing = int(config["datasets"]["go_stanford"].get("waypoint_spacing", 1))
    mpu = float(go_stanford_meters_per_unit(config))
    max_goal_map = load_max_goal_map(config)
    cache_path, rows, _ = load_cache(CACHE_DIR, "train")
    feats = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    head, _ = load_dino_head(DEFAULT_WP, device)
    head.eval()

    case_list = list_v1_cases(V1_CASES)
    all_rows = []
    rows_by_case = {}

    for spec in case_list:
        traj, t, tag = spec["traj"], spec["t"], spec["tag"]
        row = tv3.load_sample_row(traj, t)
        if row is None:
            raise SystemExit(f"missing sample row {traj} t={t}")
        goal_t_orig = int(row["goal_t"])
        baseline_k = goal_t_orig - t
        max_goal = max_goal_map[(traj, t)]
        legal = legal_goal_ks(data_folder, traj, t, spacing, mpu, max_goal, rows)
        if baseline_k not in legal and baseline_k >= MIN_STEPS:
            legal = sorted(set(legal) | {baseline_k})
        alt_ks = pick_alt_ks(legal, baseline_k, n=3)
        goal_specs = [(baseline_k, goal_t_orig, True)] + [(k, t + k, False) for k in alt_ks]

        with open(os.path.join(data_folder, traj, "traj_data.pkl"), "rb") as f:
            traj_data = pickle.load(f)
        gt = tv3.gt_path_8(traj_data, t, spacing, mpu)
        gt_m = gt * mpu

        preds = {}
        for k, gt_idx, _ in goal_specs:
            items = [(traj, t, gt_idx)]
            _, _, p1 = head_predict_wp_path(head, items, rows, feats, device)
            _, _, p2 = head_predict_wp_path(head, items, rows, feats, device)
            if not np.allclose(p1, p2):
                raise RuntimeError(f"non-deterministic {traj} t={t} goal={gt_idx}")
            preds[gt_idx] = p1[0].astype(np.float32)
        base_pred = preds[goal_t_orig]

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(gt_m[:, 0], gt_m[:, 1], "k-o", ms=5, label="GT 8-step")
        for k, gt_idx, is_orig in goal_specs:
            pm = preds[gt_idx] * mpu
            ax.plot(
                pm[:, 0],
                pm[:, 1],
                "-o",
                ms=3,
                label=f"goal {gt_idx} Δidx={k}" + (" *orig" if is_orig else ""),
            )
        ax.set_aspect("equal")
        ax.legend(fontsize=7)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title(f"{tag} | {traj} t={t}")
        fig.savefig(OUT_DIR / "cases" / f"{tag}_{traj}_t{t}_paths.png", dpi=120, bbox_inches="tight")
        plt.close(fig)

        case_rows = []
        for k, gt_idx, is_orig in goal_specs:
            pred = preds[gt_idx]
            f4, b4 = tv3.path_parts(pred, gt, mpu)
            rec = {
                "tag": tag,
                "traj_name": traj,
                "t": t,
                "goal_t": gt_idx,
                "goal_k_index_steps": k,
                "is_original_goal": int(is_orig),
                "path_ade_cm": tv3.path_ade_cm(pred, gt, mpu),
                "path_ade_front4_cm": f4,
                "path_ade_back4_cm": b4,
                "dir_err_deg": tv3.dir_err_deg(pred, gt),
                "mean_pos_shift_vs_orig_cm": tv3.path_ade_cm(pred, base_pred, mpu),
                "step8_dir_shift_vs_orig_deg": step8_dir_delta_deg(pred, base_pred),
            }
            all_rows.append(rec)
            case_rows.append(rec)
        rows_by_case[(tag, traj, t)] = case_rows

    fields = list(all_rows[0].keys())
    with open(OUT_DIR / "goal_sensitivity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    cmd = f"{sys.executable} run_goal_sensitivity_val13.py"
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_short(),
        "checkpoint": DEFAULT_WP,
        "checkpoint_sha256_16": ckpt_sha256(Path(DEFAULT_WP)),
        "command": cmd,
        "determinism": "head_predict_wp_path twice per goal; allclose enforced",
        "summary_verdict": summarize_verdict(all_rows),
    }
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (OUT_DIR / "REPORT.md").write_text(build_report(rows_by_case, meta), encoding="utf-8")
    (OUT_DIR / "determinism_check.txt").write_text("all goals passed double forward allclose\n", encoding="utf-8")
    print("wrote", OUT_DIR, "verdict=", meta["summary_verdict"])


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Path readout A/B validation v2."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone

import cv2  # noqa: F401
import numpy as np
import torch

from eval_by_distance import load_config
from path_readout_val_core import (
    BOOTSTRAP_N,
    VAL_RNG_SEED,
    bootstrap_mean_diff,
    build_manifest,
    checkpoint_info,
    make_val_loader,
    manifest_stats,
    predict_path_samples,
    subset_mask,
    summarize_subset,
)
from train_e_dino import load_dino_head
from train_goal_dino import (
    CACHE_DIR,
    DFT_VAL_LIST,
    build_pairs,
    go_stanford_meters_per_unit,
    load_cache,
)


def flatten_summary(sm: dict) -> dict:
    flat = {}
    for k, v in sm.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                flat[f"{k}_{kk}"] = vv
        else:
            flat[k] = v
    return flat


def write_errata_v1(v1_dir: str) -> None:
    path = os.path.join(v1_dir, "val_metrics.ERRATA.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "# val_metrics.csv (v1) — known issues\n\n"
            "- Sample index: `np.arange(len(starts))` instead of `draw(val_pairs, rng(1234))`.\n"
            "- Turn wrong-way: mean cosine, not end-direction error >45/>90 fraction.\n\n"
            "Use `path_readout_ab_v2/` for conclusions.\n"
        )


def write_report_zh(out_dir: str, summary: dict, boot: dict, mstats: dict) -> None:
    a = summary.get("A_cls", {}).get("all", {}).get("all", {})
    b = summary.get("B_step_query", {}).get("all", {}).get("all", {})
    lines = [
        "# 路径头读出 A/B 验证报告（v2）",
        "",
        "## 协议",
        f"- 配对：`draw(val_pairs, np.random.default_rng({VAL_RNG_SEED}))`，与 `train_goal_dino` 验证一致；`flip=False`。",
        "- 转弯子集：GT 未来 8 步路径 **累计绝对 yaw**（`winding`），非 `turn_strict`。",
        "- far：`goal_step >= 20`（与训练 FAR_STEPS 一致，步数非米）。",
        "- 末端方向误差：预测/ GT 第 8 点相对当前原点的夹角；>45° / >90° 为比例。",
        "",
        "## 清单规模",
        f"- 验证样本数：{mstats['n_samples']}",
        f"- 唯一当前帧：{mstats['n_unique_current_frames']}（应等于 frame_slots {mstats['n_frame_slots']}）",
        f"- 轨迹数（manifest 内）：{mstats['n_trajectories_in_manifest']}（DFT 列表 {mstats.get('dft_val_list_traj_count','?')} 条）",
        f"- far n={mstats['far_n']}；winding≥45° n={mstats['winding_ge_45_n']}；≥90° n={mstats['winding_ge_90_n']}",
        "",
        "## 全体（ade8 cm，越小越好）",
        f"- A：{a.get('ade8_cm_mean', float('nan')):.3f}",
        f"- B：{b.get('ade8_cm_mean', float('nan')):.3f}",
        "",
        "## 回答",
        "1. **B 是否优于 A（正确清单）**：见 summary.csv；配对 bootstrap 见 paired_bootstrap.json。",
        "2. **转弯方向 vs 转弯位置**：对比 winding≥45 子集的 end_dir 与 ade8/back4。",
        "3. **前四/后四退化**：看 ade_front4 / ade_back4 子集均值。",
        "4. **是否值得 Locked 导航**：仅当转弯位置+方向均有稳定改善时再考虑；本报告不含导航 ADE。",
        "",
        "## 区分",
        "- **代码事实**：v2 修复 draw 与末端方向比例。",
        "- **实验事实**：上表数字来自固定 ckpt 冻结前向。",
        "- **推断**：是否进下游需结合子集与 CI，不能由 path ADE 直接等同导航。",
    ]
    with open(os.path.join(out_dir, "REPORT_zh.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", default="logs/revalidation/path_readout_ab/meta.json")
    parser.add_argument("--out", default="logs/revalidation/path_readout_ab_v2")
    parser.add_argument("--ref-init", default="")
    args = parser.parse_args()

    train_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(train_dir)
    os.makedirs(args.out, exist_ok=True)
    write_errata_v1(os.path.join(train_dir, "logs/revalidation/path_readout_ab"))

    with open(args.meta, encoding="utf-8") as f:
        meta_ab = json.load(f)
    wp_a = os.path.join(train_dir, meta_ab["checkpoint_A"].replace("/", os.sep))
    wp_b = os.path.join(train_dir, meta_ab["checkpoint_B"].replace("/", os.sep))
    wp_ref = args.ref_init or meta_ab.get("init_checkpoint", "")
    if wp_ref and not os.path.isabs(wp_ref):
        wp_ref = os.path.join(train_dir, wp_ref.replace("/", os.sep))

    ckpt_specs = [
        (wp_a, "A_cls", "CLS path_head from continued pathact8 init."),
        (wp_b, "B_step_query", "step_query layers re-init; dir/kappa frozen from init."),
    ]
    if wp_ref and os.path.isfile(wp_ref):
        ckpt_specs.append((wp_ref, "ref_pathact8_init", "Pre-A/B pathact8 best checkpoint."))

    ckpts = [checkpoint_info(p, lab, note) for p, lab, note in ckpt_specs if os.path.isfile(p)]
    with open(os.path.join(args.out, "checkpoints.json"), "w", encoding="utf-8") as f:
        json.dump({"checkpoints": ckpts, "meta_ab": meta_ab}, f, indent=2, ensure_ascii=False)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config = load_config("config/nomad_b40.yaml")
    meters = float(go_stanford_meters_per_unit(config))
    cache_path, rows, _ = load_cache(CACHE_DIR, "train")
    with open(DFT_VAL_LIST, encoding="utf-8") as f:
        val_trajs = {line.strip() for line in f if line.strip()}

    val_pairs = build_pairs(
        config, "train", rows, lambda t: t in val_trajs, 0.3, 2, "endpoint", path_steps=8
    )
    chosen, val_batches = make_val_loader(cache_path, val_pairs, batch_size=512, context=2)
    manifest = build_manifest(val_pairs, chosen, rows)
    mstats = manifest_stats(manifest, val_pairs)
    mstats["dft_val_list_traj_count"] = len(val_trajs)
    mstats["draw_seed"] = VAL_RNG_SEED

    with open(os.path.join(args.out, "val_pair_manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    with open(os.path.join(args.out, "manifest_stats.json"), "w", encoding="utf-8") as f:
        json.dump(mstats, f, indent=2, ensure_ascii=False)

    wind = np.array([float(val_pairs["winding"][m["pair_expand_idx"]]) for m in manifest])
    far_m = np.array([m["goal_step"] >= 20 for m in manifest])
    trajs = [m["traj_name"] for m in manifest]

    per_model = {}
    for ck in ckpts:
        head, _ = load_dino_head(ck["path"], device)
        metrics = predict_path_samples(head, val_batches, device, meters)
        per_model[ck["label"]] = metrics
        ps = []
        for i, rec in enumerate(manifest):
            ps.append(
                {
                    **rec,
                    "winding_deg": wind[i],
                    "far": int(far_m[i]),
                    "ade8_cm": metrics["ade8_cm"][i],
                    "ade_front4_cm": metrics["ade_front4_cm"][i],
                    "ade_back4_cm": metrics["ade_back4_cm"][i],
                    "ade_step8_cm": metrics["ade_step8_cm"][i],
                    "end_dir_err_deg": metrics["end_dir_err_deg"][i],
                    "end_dir_valid": int(metrics["end_dir_valid"][i]),
                    "pred_polyline_turn_deg": metrics["pred_polyline_turn_deg"][i],
                }
            )
        with open(
            os.path.join(args.out, f"per_sample_{ck['label']}.csv"),
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            w = csv.DictWriter(f, fieldnames=list(ps[0].keys()))
            w.writeheader()
            w.writerows(ps)

    subsets = ["all", "far", "winding_ge_45", "winding_ge_90"]
    summary_rows = []
    summary_nested = {}
    for label, metrics in per_model.items():
        summary_nested[label] = {}
        for sub in subsets:
            sm = summarize_subset(metrics, subset_mask(manifest, val_pairs, sub))
            summary_nested[label][sub] = sm
            row = {"model": label, "subset": sub, **flatten_summary(sm)}
            summary_rows.append(row)

    with open(os.path.join(args.out, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_nested, f, indent=2, ensure_ascii=False)

    boot = {}
    if "A_cls" in per_model and "B_step_query" in per_model:
        a, b = per_model["A_cls"], per_model["B_step_query"]
        for key, arr_key in [
            ("ade8_cm", "ade8_cm"),
            ("ade_back4_cm", "ade_back4_cm"),
            ("ade8_winding45", None),
            ("end_dir_gt90_pp", None),
        ]:
            if key == "ade8_winding45":
                mask = subset_mask(manifest, val_pairs, "winding_ge_45")
                boot[key] = bootstrap_mean_diff(
                    a["ade8_cm"][mask],
                    b["ade8_cm"][mask],
                    list(np.array(trajs)[mask]),
                )
            elif key == "end_dir_gt90_pp":
                ia = ((a["end_dir_err_deg"] > 90.0) & a["end_dir_valid"]).astype(np.float64)
                ib = ((b["end_dir_err_deg"] > 90.0) & b["end_dir_valid"]).astype(np.float64)
                boot[key] = bootstrap_mean_diff(ia, ib, trajs)
                boot[key]["mean_diff_pp"] = float(boot[key]["mean_diff"] * 100.0)
            else:
                boot[key] = bootstrap_mean_diff(a[arr_key], b[arr_key], trajs)
        with open(os.path.join(args.out, "paired_bootstrap.json"), "w", encoding="utf-8") as f:
            json.dump(boot, f, indent=2)

    cmd = (
        f"cd {train_dir}\n"
        f"set PYTHONPATH=../diffusion_policy\n"
        f"python -u eval_path_readout_val_v2.py --meta {args.meta} --out {args.out}\n"
    )
    with open(os.path.join(args.out, "eval_command.txt"), "w", encoding="utf-8") as f:
        f.write(cmd)

    flat_summary = {}
    for label in summary_nested:
        flat_summary[label] = {sub: flatten_summary(summary_nested[label][sub]) for sub in summary_nested[label]}
    write_report_zh(args.out, flat_summary, boot, mstats)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
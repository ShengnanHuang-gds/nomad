"""Regenerate 13 case figures + CSV/report for turn visual diagnostic v2 (fixed correspondence lines)."""

from __future__ import annotations



import csv

import json

import os

import pickle

import re

import subprocess

import sys

from datetime import datetime, timezone

from pathlib import Path



import cv2  # noqa: F401

import matplotlib.pyplot as plt

import numpy as np

import torch



from eval_by_distance import load_config

from eval_e_dino import head_predict_wp_path

from train_e_dino import load_dino_head

from train_goal_dino import (

    CACHE_DIR,

    DFT_VAL_LIST,

    MAX_STEPS,

    go_stanford_meters_per_unit,

    load_cache,


    path_winding_deg,

)

from turn_match_viz import (

    PATCH_GH,

    PATCH_GW,

    bidirectional_consistent_stats,

    draw_cross_image_lines,

    legacy_bidirectional_mean_max,

    list_v1_cases,

    load_rgb_crop,

    mutual_consistent_pairs,

    patch_grid,

    select_curr_patches_for_display,

    similarity_hist_curr,

)



DEFAULT_WP = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"

V1_DIR = Path("logs/revalidation/turn_visual_correspondence_val200")

OUT_DIR = Path("logs/revalidation/turn_visual_correspondence_val200_v2")

V1_SAMPLES = V1_DIR / "samples.csv"

V1_CASES = V1_DIR / "cases"

CONTEXT = 2

DISPLAY_LINES = 10

DISPLAY_SEED = 20261103





def git_short():

    try:

        return (

            subprocess.check_output(

                ["git", "rev-parse", "--short", "HEAD"],

                cwd=Path(__file__).resolve().parent,

                stderr=subprocess.DEVNULL,

            )

            .decode()

            .strip()

        )

    except (subprocess.CalledProcessError, FileNotFoundError):

        return "unknown"





def wrap_dyaw_deg(yaw_arr, i0, i1):

    i0, i1 = int(min(i0, i1)), int(max(i0, i1))

    total_signed = 0.0

    total_abs = 0.0

    for i in range(i0, i1):

        y0 = float(np.ravel(yaw_arr[i])[0])

        y1 = float(np.ravel(yaw_arr[i + 1])[0])

        dy = (y1 - y0 + np.pi) % (2 * np.pi) - np.pi

        total_signed += np.degrees(dy)

        total_abs += abs(np.degrees(dy))

    return total_abs, total_signed





def gt_path_8(traj, curr, spacing, mpu, min_goal_m=0.3):

    pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)

    yaw = traj["yaw"]

    y0 = float(np.ravel(yaw[int(curr)])[0])

    c, s = np.cos(y0), np.sin(y0)

    pts = []

    for st in range(1, 9):

        gi = min(int(curr) + st * spacing, len(pos) - 1)

        d = pos[gi] - pos[int(curr)]

        local = np.array([d[0] * c + d[1] * s, -d[0] * s + d[1] * c], dtype=np.float32)

        pts.append(local / max(mpu, 1e-6))

    path = np.stack(pts, axis=0)

    if float(np.linalg.norm(path[-1] * mpu)) < min_goal_m:

        return None

    return path





def path_ade_cm(pred, gt, meters):

    return float(np.linalg.norm(pred - gt, axis=-1).mean() * meters * 100.0)





def path_parts(pred, gt, meters):

    k = 4

    return path_ade_cm(pred[:k], gt[:k], meters), path_ade_cm(pred[k:], gt[k:], meters)





def dir_err_deg(pred, gt):

    u = lambda v: v / max(np.linalg.norm(v), 1e-6)

    return float(np.degrees(np.arccos(np.clip(float(u(pred[-1]) @ u(gt[-1])), -1.0, 1.0))))





def motion_class(hist_abs_deg, future_wind_deg, hist_thresh=12.0, future_thresh=45.0):

    if hist_abs_deg >= hist_thresh:

        return "A_hist_already_turning"

    if future_wind_deg >= future_thresh:

        return "B_future_turn_soon"

    return "C_other_or_unclear"





def load_sample_row(traj, t):

    with open(V1_SAMPLES, encoding="utf-8") as f:

        for row in csv.DictReader(f):

            if row["traj_name"] == traj and int(row["t"]) == t:

                return row

    return None





def draw_case_v2(rec, data_folder, feats, rows, out_png, out_legacy_png):

    t_far, t_near, t_cur, t_goal = rec["t_far"], rec["t_near"], rec["t"], rec["goal_t"]

    imgs = {

        "far": load_rgb_crop(data_folder, rec["traj"], t_far),

        "near": load_rgb_crop(data_folder, rec["traj"], t_near),

        "curr": load_rgb_crop(data_folder, rec["traj"], t_cur),

        "goal": load_rgb_crop(data_folder, rec["traj"], t_goal),

    }

    p_far, _ = patch_grid(feats[rows[(rec["traj"], t_far)]])

    p_near, _ = patch_grid(feats[rows[(rec["traj"], t_near)]])

    p_curr, _ = patch_grid(feats[rows[(rec["traj"], t_cur)]])

    sim_near = similarity_hist_curr(p_near.reshape(-1, p_near.shape[-1]), p_curr)
    sim_far = similarity_hist_curr(p_far.reshape(-1, p_far.shape[-1]), p_curr)

    curr_show = select_curr_patches_for_display(seed=DISPLAY_SEED + rec["t"])



    fig = plt.figure(figsize=(16, 12))

    gs = fig.add_gridspec(3, 4, height_ratios=[1.0, 1.2, 1.0])

    for col, (name, tt) in enumerate(

        [("t-2", t_far), ("t-1", t_near), ("curr", t_cur), ("goal", t_goal)]

    ):

        ax = fig.add_subplot(gs[0, col])

        ax.imshow(imgs[{"t-2": "far", "t-1": "near", "curr": "curr", "goal": "goal"}[name]])

        ax.set_title(f"{name}  index={tt}\n(goal gap={t_goal - t_cur})")

        ax.axis("off")



    ax_old = fig.add_subplot(gs[1, 0])

    ax_old.imshow(imgs["curr"])

    ax_old.set_title("DEPRECATED v1 overlay\n(fixed-length segments;\nNOT valid correspondence)")

    ax_old.axis("off")

    h, w = imgs["curr"].shape[:2]

    for gi in range(PATCH_GH):

        for gj in range(PATCH_GW):

            pi = gi * PATCH_GW + gj

            cx, cy = (gj + 0.5) * w / PATCH_GW, (gi + 0.5) * h / PATCH_GH

            ax_old.plot([cx, cx - 0.12 * w], [cy, cy], "c-", alpha=0.35, lw=0.7)

            ax_old.plot([cx, cx - 0.06 * w], [cy, cy - 0.04 * h], "y-", alpha=0.45, lw=0.7)



    rule = (

        f"Lines: skyblue=curr->hist NN; lime=bidirectional consistent. "

        f"Show {len(curr_show)} curr patches (linspace+seed {DISPLAY_SEED}+t)."

    )

    for ax_col, (title, im_l, im_r, sim) in zip(

        [fig.add_subplot(gs[1, 1]), fig.add_subplot(gs[1, 2])],

        [

            ("t-2 | curr", imgs["far"], imgs["curr"], sim_far),

            ("t-1 | curr", imgs["near"], imgs["curr"], sim_near),

        ],

    ):

        ax_col.set_xlim(0, w * 2)

        ax_col.set_ylim(h, 0)

        ax_col.imshow(im_l, extent=(0, w, h, 0))

        ax_col.imshow(im_r, extent=(w, 2 * w, h, 0))

        nn_h = sim.argmax(axis=0)

        mutual = {c for _h, c, _ in mutual_consistent_pairs(sim)}

        for c in curr_show:

            h_idx = int(nn_h[c])

            x0, y0 = patch_center(rec, c, w, h, 0)

            x1, y1 = patch_center(rec, h_idx, w, h, w)

            col = "lime" if c in mutual else "deepskyblue"

            ax_col.plot([x0, x1], [y0, y1], color=col, lw=0.9, alpha=0.85)

        ax_col.set_title(title + "\n" + rule, fontsize=8)

        ax_col.axis("off")



    ax_note = fig.add_subplot(gs[1, 3])

    ax_note.axis("off")

    ax_note.text(

        0,

        1,

        "Match legend:\n- NOT overlap rate\n- NN may hit repeat texture\n- v1 left panel deprecated",

        va="top",

        fontsize=9,

    )



    ax_p = fig.add_subplot(gs[2, :2])

    gt_m = rec["gt_m"]

    pred_m = rec["pred_m"]

    ax_p.plot(gt_m[:, 0], gt_m[:, 1], "k-o", ms=4, label="GT 8-step (m)")

    ax_p.plot(pred_m[:, 0], pred_m[:, 1], "r-o", ms=4, label="pred (m)")

    ax_p.axhline(0, color="gray", lw=0.4)

    ax_p.axvline(0, color="gray", lw=0.4)

    ax_p.set_aspect("equal")

    ax_p.legend(fontsize=8)

    ax_p.set_xlabel("x (m)")

    ax_p.set_ylabel("y (m)")



    ax_s = fig.add_subplot(gs[2, 2:])

    ax_s.axis("off")

    txt = (

        f"{rec['tag']} | {rec['traj']} t={rec['t']}\n"

        f"goal_t={rec['goal_t']} (delta={rec['goal_k']} idx)\n"

        f"pathADE={rec['path_ade_cm']:.2f}cm  F4={rec['f4']:.2f} B4={rec['b4']:.2f}  dir={rec['dir_err']:.1f}deg\n"

        f"future wind={rec['future_wind']:.1f}deg  hist |dy| t-2..t={rec['hist_abs_yaw']:.1f}deg\n"

        f"legacy mutual_mean_max (v1 name): near={rec['legacy_near']:.3f} far={rec['legacy_far']:.3f}\n"

        f"true mutual pairs: near n={rec['near_cons_n']} mean={rec['near_cons_mean']:.3f} | "

        f"far n={rec['far_cons_n']} mean={rec['far_cons_mean']:.3f}\n"

        f"motion class: {rec['motion_class']}"

    )

    ax_s.text(0, 1, txt, va="top", fontsize=9, family="monospace")



    fig.suptitle(f"Turn visual diagnostic v2 — {rec['tag']}", fontsize=11)

    fig.tight_layout()

    fig.savefig(out_png, dpi=130, bbox_inches="tight")

    plt.close(fig)

    fig.savefig(out_legacy_png, dpi=130, bbox_inches="tight")





def patch_center(rec, patch_index, w, h, x0):

    gj = patch_index % PATCH_GW

    gi = patch_index // PATCH_GW

    return x0 + (gj + 0.5) * w / PATCH_GW, (gi + 0.5) * h / PATCH_GH





CASE_NOTES = {

    ("sim12h_1_6", 21): {

        "visible_ref": "观察：室内外衔接处可见墙/门廊结构在 t-1 与 curr 仍部分重叠；t-2 视角差更大。",

        "match_quality": "匹配：lime 线多落在大块垂直结构；地面/重复纹理区域 NN 易漂移。",

        "hist_motion": "历史 t-2→t 累计 |Δyaw| 较小；未来八步 winding 高 → 属 B 类为主。",

        "goal_cue": "goal 帧为更远前视，含通道/转角远端线索，但非当前 patch 对齐目标。",

        "error_type": "误差：中等 ADE，前后半段均有一定偏差，更像转弯形状而非纯距离。",

        "obs_vs_spec": "推测：失败部分来自未来弯折几何，不能仅归因历史视野丢失。",

    },

}





def default_notes(rec):

    return {

        "visible_ref": "需结合 case 图目视：共同参照是否连续（报告级概括，非自动判定）。",

        "match_quality": "skyblue=单向 NN；lime=双向一致。高相似度不等于物理同一物。",

        "hist_motion": f"hist_abs={rec['hist_abs_yaw']:.1f}deg future_wind={rec['future_wind']:.1f}deg class={rec['motion_class']}",

        "goal_cue": f"goal index {rec['goal_t']} (offset {rec['goal_k']} from curr).",

        "error_type": f"ADE={rec['path_ade_cm']:.1f}cm F4={rec['f4']:.1f} B4={rec['b4']:.1f} dir={rec['dir_err']:.1f}deg",

        "obs_vs_spec": "以下‘推测’仅为解释假设，非模型内部注意力。",

    }





def build_report(cases, meta):

    lines = [

        "# 转弯视觉对应诊断 v2（13 案例修正图）",

        "",

        "## 代码事实",

        "",

        "- ctx2 历史帧：**t-1**、**t-2**（帧索引步长 1）；goal token：**curr + goal_k**，goal_k=min(39,max_goal)。",

        "- 预处理：4:3 中心裁 → 224×168；特征为 DINO cache **6×8 patch tokens**（不含 CLS 的匹配）。",

        "- **legacy_mutual_mean_max_cos（v1 列名）** = hist→curr 与 curr→hist **单向 max-cos 均值的平均**；",

        "  **不是**双向一致匹配率；v2 另报 **n_consistent / mean_consistent_cos**（h→c 且 c→h 互 argmax）。",

        "- v1 `draw_case` 中固定方向短线 **已弃用**；v2 图左列标注 DEPRECATED。",

        "- 展示连线：对每个案例取 10 个 curr patch（linspace 均匀 + 固定 seed 补齐），不按相似度排序挑选。",

        "",

        "## 图像观察（13 例摘要见 cases/*.png 与 case_notes.json）",

        "",

    ]

    for rec in cases:

        key = (rec["traj"], rec["t"])

        notes = {**default_notes(rec), **CASE_NOTES.get(key, {})}

        lines.append(f"### {rec['tag']} — {rec['traj']} t={rec['t']}")

        for i, (q, k) in enumerate(

            [

                ("1.共同参照", "visible_ref"),

                ("2.匹配合理性", "match_quality"),

                ("3.历史运动", "hist_motion"),

                ("4.目标线索", "goal_cue"),

                ("5.误差类型", "error_type"),

                ("6.观察/推测", "obs_vs_spec"),

            ],

            1,

        ):

            lines.append(f"- **{q}**：{notes[k]}")

        lines.append("")

    lines.extend(

        [

            "## 研究推断（弱）",

            "",

            "- 在 sharp 失败/成功对比中，**legacy mutual 指标差值很小**；双向一致配对数亦未见稳定分离 → ",

            "  **不支持**“失败=历史参照更少”的单一叙事。",

            "- t-1 相对 t-2 的 NN 相似度在 v1 全体仍更高；描述性上 **较近历史更易匹配**，≠ 真实 overlap 率。",

            "",

            "## 尚不能判断",

            "",

            "- 不能从 patch 线推断模型注意力；不能证明因果。",

            "- 13 例不足以做回归；未控全部混淆因子。",

            "",

            "## 总问",

            "",

            "**更提示哪类问题？** 现有 13 例中 **B（未来将要转弯 / 目标条件）与路径几何** 与失败更一致；",

            "**反例**：高 legacy 匹配仍高 ADE（如 counter_high_match_high_ade）；",

            "**历史运动 alone（A）** 不能解释全部 sharp_bad。",

            "结论：**目前无法单一区分**，略倾向 **未来转向/目标利用 + 轨迹形状** 而非单纯历史视野重叠减少。",

            "",

            f"- checkpoint: `{meta['checkpoint']}`",

            f"- git: {meta['git_commit']}",

            f"- command: `{meta['command']}`",

        ]

    )

    return "\n".join(lines)





def main():

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "cases").mkdir(exist_ok=True)

    case_list = list_v1_cases(V1_CASES)

    config = load_config("config/nomad_b40.yaml")

    data_folder = config["datasets"]["go_stanford"]["data_folder"]

    spacing = int(config["datasets"]["go_stanford"].get("waypoint_spacing", 1))

    horizon = int(config["len_traj_pred"])

    mpu = float(go_stanford_meters_per_unit(config))

    cache_path, rows, cache_meta = load_cache(CACHE_DIR, "train")

    feats = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")



    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    head, _ = load_dino_head(DEFAULT_WP, device)



    records = []

    for spec in case_list:

        traj, t, tag = spec["traj"], spec["t"], spec["tag"]

        row = load_sample_row(traj, t)

        if row is None:

            raise SystemExit(f"missing sample row {traj} t={t}")

        t_near, t_far = t - 1, t - 2

        goal_t = int(row["goal_t"])

        goal_k = goal_t - t

        with open(os.path.join(data_folder, traj, "traj_data.pkl"), "rb") as f:

            traj_data = pickle.load(f)

        gt = gt_path_8(traj_data, t, spacing, mpu)

        items = [(traj, t, goal_t)]

        _, _, pred = head_predict_wp_path(head, items, rows, feats, device)

        pred = pred[0].astype(np.float32)

        gt_m = gt * mpu

        pred_m = pred * mpu

        future_wind = float(path_winding_deg(traj_data, t, spacing, horizon))

        hist_abs, hist_net = wrap_dyaw_deg(traj_data["yaw"], t_far, t)

        fut_abs, fut_net = wrap_dyaw_deg(

            traj_data["yaw"],

            t,

            min(t + horizon * spacing, len(traj_data["yaw"]) - 1),

        )

        p_near, _ = patch_grid(feats[rows[(traj, t_near)]])

        p_far, _ = patch_grid(feats[rows[(traj, t_far)]])

        p_curr, _ = patch_grid(feats[rows[(traj, t)]])

        sim_near = similarity_hist_curr(p_near.reshape(-1, p_near.shape[-1]), p_curr)

        sim_far = similarity_hist_curr(p_far.reshape(-1, p_far.shape[-1]), p_curr)

        leg_near = legacy_bidirectional_mean_max(sim_near)

        leg_far = legacy_bidirectional_mean_max(sim_far)

        con_near = bidirectional_consistent_stats(sim_near)

        con_far = bidirectional_consistent_stats(sim_far)

        f4, b4 = path_parts(pred, gt, mpu)

        rec = {

            "tag": tag,

            "traj": traj,

            "t": t,

            "t_near": t_near,

            "t_far": t_far,

            "goal_t": goal_t,

            "goal_k": goal_k,

            "future_wind": future_wind,

            "future_abs_yaw_deg": fut_abs,

            "future_net_yaw_deg": fut_net,

            "hist_abs_yaw": hist_abs,

            "hist_net_yaw_deg": hist_net,

            "motion_class": motion_class(hist_abs, future_wind),

            "gt_path_len_m": float(np.linalg.norm(np.diff(gt_m, axis=0), axis=1).sum()),

            "path_ade_cm": path_ade_cm(pred, gt, mpu),

            "f4": f4,

            "b4": b4,

            "dir_err": dir_err_deg(pred, gt),

            "legacy_near": leg_near["legacy_mutual_mean_max_cos"],

            "legacy_far": leg_far["legacy_mutual_mean_max_cos"],

            "near_cons_n": con_near["n_consistent"],

            "near_cons_mean": con_near["mean_consistent_cos"],

            "far_cons_n": con_far["n_consistent"],

            "far_cons_mean": con_far["mean_consistent_cos"],

            "gt_m": gt_m,

            "pred_m": pred_m,

            "v1_legacy_mutual_near": float(row["match_near_mutual_mean_max_cos"]),

        }

        out_png = OUT_DIR / "cases" / f"{tag}_{traj}_t{t}_v2.png"

        legacy = OUT_DIR / "cases" / f"{tag}_{traj}_t{t}_v1_style_DEPRECATED.png"

        draw_case_v2(rec, data_folder, feats, rows, out_png, legacy)

        records.append(rec)



    csv_path = OUT_DIR / "case_stats.csv"

    fields = [

        "tag",

        "traj_name",

        "t",

        "t_hist_near",

        "t_hist_far",

        "goal_t",

        "goal_k_index_steps",

        "motion_class",

        "hist_abs_yaw_t-2_to_t_deg",

        "hist_net_yaw_t-2_to_t_deg",

        "future_winding_8step_deg",

        "future_abs_yaw_deg",

        "future_net_yaw_deg",

        "gt_path_len_m",

        "path_ade_cm",

        "path_ade_front4_cm",

        "path_ade_back4_cm",

        "dir_err_deg",

        "legacy_mutual_mean_max_cos_near",

        "legacy_mutual_mean_max_cos_far",

        "v1_csv_legacy_mutual_near",

        "bidirectional_consistent_count_near",

        "bidirectional_consistent_mean_cos_near",

        "bidirectional_consistent_count_far",

        "bidirectional_consistent_mean_cos_far",

    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:

        w = csv.DictWriter(f, fieldnames=fields)

        w.writeheader()

        for r in records:

            w.writerow(

                {

                    "tag": r["tag"],

                    "traj_name": r["traj"],

                    "t": r["t"],

                    "t_hist_near": r["t_near"],

                    "t_hist_far": r["t_far"],

                    "goal_t": r["goal_t"],

                    "goal_k_index_steps": r["goal_k"],

                    "motion_class": r["motion_class"],

                    "hist_abs_yaw_t-2_to_t_deg": f"{r['hist_abs_yaw']:.3f}",

                    "hist_net_yaw_t-2_to_t_deg": f"{r['hist_net_yaw_deg']:.3f}",

                    "future_winding_8step_deg": f"{r['future_wind']:.3f}",

                    "future_abs_yaw_deg": f"{r['future_abs_yaw_deg']:.3f}",

                    "future_net_yaw_deg": f"{r['future_net_yaw_deg']:.3f}",

                    "gt_path_len_m": f"{r['gt_path_len_m']:.4f}",

                    "path_ade_cm": f"{r['path_ade_cm']:.4f}",

                    "path_ade_front4_cm": f"{r['f4']:.4f}",

                    "path_ade_back4_cm": f"{r['b4']:.4f}",

                    "dir_err_deg": f"{r['dir_err']:.3f}",

                    "legacy_mutual_mean_max_cos_near": f"{r['legacy_near']:.5f}",

                    "legacy_mutual_mean_max_cos_far": f"{r['legacy_far']:.5f}",

                    "v1_csv_legacy_mutual_near": f"{r['v1_legacy_mutual_near']:.5f}",

                    "bidirectional_consistent_count_near": r["near_cons_n"],

                    "bidirectional_consistent_mean_cos_near": f"{r['near_cons_mean']:.5f}",

                    "bidirectional_consistent_count_far": r["far_cons_n"],

                    "bidirectional_consistent_mean_cos_far": f"{r['far_cons_mean']:.5f}",

                }

            )



    cmd = f"{sys.executable} run_turn_visual_correspondence_v2.py"

    meta = {

        "timestamp_utc": datetime.now(timezone.utc).isoformat(),

        "git_commit": git_short(),

        "checkpoint": DEFAULT_WP,

        "v1_reference_dir": str(V1_DIR),

        "command": cmd,

        "display_line_rule": (

            f"Up to {DISPLAY_LINES} curr patches: linspace over 48 grid cells, "

            f"supplemented by rng seed {DISPLAY_SEED}+t; not ranked by match score."

        ),

        "legacy_metric_note": (

            "legacy_mutual_mean_max_cos is the average of two directional mean-max cosines; "

            "not bidirectional-consistency rate."

        ),

    }

    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:

        json.dump(meta, f, indent=2, ensure_ascii=False)

    report = build_report(records, meta)

    with open(OUT_DIR / "REPORT.md", "w", encoding="utf-8") as f:

        f.write(report)

    print("wrote", OUT_DIR)





if __name__ == "__main__":

    main()


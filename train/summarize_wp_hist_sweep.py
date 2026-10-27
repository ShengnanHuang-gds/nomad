import csv
import glob
import json
import os

import cv2  # noqa: F401
import numpy as np
from eval_testtime import angle_err

OUT = "logs/revalidation/wp_input_sweep/summary.txt"
OUT_CN = "logs/revalidation/wp_input_sweep/summary_cn.txt"
LABELS = [
    ("deploy 2-frame", "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44"),
    ("turnhard 2-frame", "logs/nomad_d/nomad_dino_wp_hist_ctx2_turnhard_2026_10_26_10_04_05"),
    ("hist3 plain", "nomad_dino_wp_hist3"),
    ("hist3+turnhard", "nomad_dino_wp_hist3_turnhard"),
    ("hist3+light turn", "nomad_dino_wp_hist3_turnlight"),
]


def latest(p):
    if os.path.isdir(p):
        return p
    dirs = glob.glob(os.path.join("logs", "nomad_d", p + "_*"))
    if p == "nomad_dino_wp_hist3":
        dirs = [
            d
            for d in dirs
            if "_turnhard_" not in os.path.basename(d) and "_turnlight_" not in os.path.basename(d)
        ]
    return max(dirs, key=os.path.getmtime) if dirs else None


def angles(rd):
    wp = np.load(os.path.join(rd, "eval_waypoint", "locked_per_frame.npz"))
    e = angle_err(wp["wp_dir"], wp["endpoint"])
    return float(e.mean()), float(np.median(e)), float((e > 45).mean() * 100)


def blend(rd):
    path = os.path.join(rd, "eval_blend_ablation", "ablation.csv")
    if not os.path.isfile(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {r["frames"]: float(r["use_cm"]) for r in rows if r["condition"] == "kappa blend"}


def main():
    lines = ["=== More history experiments (locked 1000) ===", ""]
    cn = [
        "=== 多一帧历史（3帧）实验 — 固定约1000张评测 ===",
        "指标：走路收益 use_cm（越大越好）；方向误差（越小越好）；弯路段子集同理。",
        "",
    ]
    rows = []
    for lab, key in LABELS:
        rd = latest(key)
        if not rd:
            lines.append(lab + ": missing")
            cn.append(lab + "：未完成")
            continue
        m, med, p45 = angles(rd)
        b = blend(rd)
        all_cm = b.get("all", float("nan"))
        turn_cm = b.get("turn 0.30m/45deg", float("nan"))
        lines.append(
            "%s: avg %.2f med %.2f | >45deg %.1f%% | blend all %+.2f | curvy-block %+.2f"
            % (lab, m, med, p45, all_cm, turn_cm)
        )
        cn.append(
            "%s | 平均角误差 %.2f° 中位 %.2f° | 大偏差(>45°) %.1f%% | 全量融合 %+.2f cm | 弯路段 %+.2f cm | %s"
            % (lab, m, med, p45, all_cm, turn_cm, os.path.basename(rd))
        )
        rows.append({"label": lab, "run_dir": rd, "mean": m, "median": med, "gt45": p45, "blend": b})
    cn.extend(
        [
            "",
            "结论（相对当前线上 2 帧）：",
            "- 只加第 3 帧、不加弯路段加权：全量融合约 +2.84 cm，略好于 +2.80，但平均方向略差、>45° 略多。",
            "- 3 帧 + 与 turnhard 相同加权：全量约 +2.93 cm、弯路段约 +3.92 cm，与 2 帧 turnhard 几乎持平；中位角误差略好于 2 帧 turnhard。",
            "- 3 帧 + 轻度弯路段加权：与「纯 3 帧」数值相同（本次 run），融合收益一般。",
            "- 建议：仍用 2 帧线上配置；若换 checkpoint，3 帧 turnhard 可作为备选，但收益不是质变。",
        ]
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    text = "\n".join(lines) + "\n"
    print(text)
    open(OUT, "w", encoding="utf-8").write(text)
    open(OUT_CN, "w", encoding="utf-8").write("\n".join(cn) + "\n")
    json.dump(rows, open(OUT.replace(".txt", ".json"), "w"), indent=2)


if __name__ == "__main__":
    main()
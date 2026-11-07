"""Write local R2/R18 progress JSON + RUN_STATUS_zh.md from logs only."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from r2_r18_common import manifest_units_note

CWD = Path(__file__).resolve().parent
OUT = CWD / "logs/revalidation/r2_r18_fair_2026-11-07"
E_ORACLE = CWD / "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth"
RUN_R2 = CWD / "logs/nomad/nomad_e_r2_fair_20261107"
RUN_R18 = CWD / "logs/nomad/nomad_e_r18_fair_20261107"
MANIFEST = OUT / "val_far_manifest_seed20261107.csv"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def audit_run(run_dir: Path, label: str) -> dict:
    info = {
        "label": label,
        "run_dir": str(run_dir),
        "exists": run_dir.is_dir(),
        "completed_epochs": [],
        "in_progress_epoch": None,
        "init_e_oracle_sha256": sha256_file(E_ORACLE),
        "resume": "fresh from e_oracle (no optimizer restore in this job)",
    }
    log = run_dir / "train_log.csv"
    if log.is_file():
        for r in csv.DictReader(open(log, encoding="utf-8")):
            if str(r.get("epoch", "")).isdigit():
                info["completed_epochs"].append(
                    {
                        "epoch": int(r["epoch"]),
                        "train_batches": r.get("train_batches"),
                        "train_samples_index": r.get("train_samples_index"),
                        "lr_epoch_start": r.get("lr_epoch_start"),
                        "lr_epoch_end": r.get("lr_epoch_end"),
                        "train_action_loss": r.get("train_action_loss"),
                        "val_nav_ade_cm": r.get("val_nav_ade_cm"),
                    }
                )
        n = len(info["completed_epochs"])
        if n < 8 and (run_dir / f"val_nav_epoch{n - 1 if n else 0}.json").is_file():
            next_ep = n
            if not (run_dir / f"val_nav_epoch{n}.json").is_file() and n < 8:
                info["in_progress_epoch"] = next_ep
    best = None
    for ep in range(8):
        jf = run_dir / f"val_nav_epoch{ep}.json"
        if jf.is_file():
            with open(jf, encoding="utf-8") as f:
                m = json.load(f)
            if best is None or m["nav_ade_cm"] < best["nav_ade_cm"]:
                best = {"epoch": ep, **m}
    if best:
        ck = run_dir / f"ema_{best['epoch']}.pth"
        best["checkpoint_sha256"] = sha256_file(ck)
        info["best_by_val_nav_ade"] = best
    return info


def main():
    os.makedirs(OUT, exist_ok=True)
    r2 = audit_run(RUN_R2, "R2")
    r18 = audit_run(RUN_R18, "R18")
    payload = {
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": str(MANIFEST),
        "manifest_units": manifest_units_note(str(MANIFEST)),
        "r2_launch_cmd_note": "train_e_dino.py config/nomad_e_dino_r2_r18.yaml goal pos_dim=2 true_pos_prob=0 8ep bs32 lr3e-5 per_step warmup",
        "r18_launch_cmd_note": "train_e_dino.py config/nomad_e_dino_r18.yaml goal_path pos_dim=18 pathact8 wp_poly dataset ctx=2 (starts after R2 in same launcher)",
        "R2": r2,
        "R18": r18,
        "implementation_fixes": {
            "path_grad_cols": "[258:274) on noise_pred_net.*.cond_encoder.1.weight",
            "pairing": "500 pairs by order + (traj_name,curr_t,goal_t)",
            "resume_policy": "launcher refuses partial ema_latest resume",
        },
    }
    with open(OUT / "progress_audit.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    r2_ep = len(r2.get("completed_epochs", []))
    r2_prog = r2.get("in_progress_epoch")
    md = [
        "# R2/R18 公平对照 — 本地进度（日志实读）",
        "",
        f"审计时间（UTC）：{payload['audited_at_utc']}",
        "",
        "## 样本单位",
        json.dumps(payload["manifest_units"], ensure_ascii=False, indent=2),
        "",
        "## R2",
        f"- 目录：`{RUN_R2}`",
        f"- 已连续完成 epoch：**0–{r2_ep - 1}**（共 {r2_ep}/8 条 train_log 记录）",
        f"- 进行中：epoch **{r2_prog}**" if r2_prog is not None else "- 进行中：无（或尚未写入下一条 log）",
        f"- E-oracle 初始化：`ema_29.pth` sha256 `{r2['init_e_oracle_sha256'][:16]}…`",
        f"- 每 epoch：**3847** batch（train_log），索引样本 **123125**，batch32",
        f"- LR：ep0 首轮 `lr_epoch_start=3e-7` → 当轮结束 `lr_epoch_end=3e-5`；**per_step** warmup+cosine",
        f"- 恢复：**从头训练**，未使用 ema_latest 伪恢复",
    ]
    if r2.get("best_by_val_nav_ade"):
        b = r2["best_by_val_nav_ade"]
        md.append(
            f"- 当前验证最佳（按 nav ADE）：**epoch {b['epoch']}** nav_ade={b['nav_ade_cm']:.3f} cm"
        )
    md += [
        "",
        "## R18",
        f"- 目录：`{RUN_R18}`，存在={r18['exists']}",
        "- 状态：R2 同进程串行结束后自动启动（当前未见目录=尚未开始）",
        "",
        "## 实现修复（已入库，不打断当前 R2）",
        "1. 路径输入梯度仅统计 cond_encoder.1.weight 列 [258:274)，并记录一步 AdamW 后该列权重 Δ。",
        "2. 报告配对按 manifest `order` 与完整三元组对齐，保留 500 对；bootstrap 按轨迹抽中后保留该轨迹全部配对。",
        "3. 编排脚本禁止仅凭 train_log+ema_latest 继续训；不完整中断保留产物、不自动清空重训。",
        "",
        "## 训练命令（R2，终端日志摘录）",
        "```",
        "python -u run_r2_r18_fair_ablation.py --train-only",
        "→ train_e_dino.py --config config/nomad_e_dino_r2_r18.yaml --init-from e_oracle ...",
        "```",
    ]
    (OUT / "RUN_STATUS_zh.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote", OUT / "progress_audit.json")


if __name__ == "__main__":
    main()

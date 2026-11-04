"""C/T navigation path-adapt experiment: smoke, manifest, train, val, report.
C: mu(old deploy) + path(pathact8)
T: mu(same old deploy) + path(A_cls) via --wp-path-head
"""
from __future__ import annotations
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import cv2  # noqa: F401
import numpy as np
import torch
CWD = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(CWD, "logs/revalidation/e_path_adapt_ct")
MANIFEST_SEED = 20261104
MANIFEST_MAX = 500
WP_O = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
WP_A = "logs/nomad_d/nomad_dino_wp_ctx2_pathreadout_A_cls_2026_11_03_23_38_31/dino_dir_best.pth"
INIT_E = "logs/nomad/nomad_e_ft_pathact8/ema_latest.pth"
DINO = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
CKPT_MANIFEST = "logs/revalidation/path_readout_ab_v2/checkpoints.json"
_NOMAD_PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
PY = _NOMAD_PY if os.path.isfile(_NOMAD_PY) else sys.executable
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()
def run_cmd(cmd, cwd=CWD):
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    env["PYTHONPATH"] = root if not env.get("PYTHONPATH") else root + os.pathsep + env["PYTHONPATH"]
    subprocess.run(cmd, cwd=cwd, check=True, env=env)
def build_far_val_manifest(out_csv: str) -> dict:
    from eval_by_distance import load_config
    from path_readout_val_core import build_manifest
    from train_goal_dir import FAR_STEPS
    from train_goal_dino import CACHE_DIR, DFT_VAL_LIST, build_pairs, load_cache
    config = load_config("config/nomad_b40.yaml")
    cache_path, rows, _ = load_cache(CACHE_DIR, "train")
    with open(os.path.join(CWD, DFT_VAL_LIST), encoding="utf-8") as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    val_pairs = build_pairs(
        config, "train", rows, lambda t: t in val_trajs, 0.3, 2, "endpoint", path_steps=8
    )
    steps = np.asarray(val_pairs["steps"], dtype=np.int64)
    far_idx = np.where(steps >= FAR_STEPS)[0]
    rng = np.random.default_rng(MANIFEST_SEED)
    if len(far_idx) > MANIFEST_MAX:
        chosen = np.sort(rng.choice(far_idx, size=MANIFEST_MAX, replace=False))
    else:
        chosen = np.sort(far_idx)
    manifest = build_manifest(val_pairs, chosen, rows)
    for m in manifest:
        pi = int(m["pair_expand_idx"])
        m["turn_strict"] = float(val_pairs["turn_strict"][pi])
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    fields = list(manifest[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(manifest)
    stats = {
        "n": len(manifest),
        "seed": MANIFEST_SEED,
        "far_steps_ge": int(FAR_STEPS),
        "goal_step_min": int(min(int(m["goal_step"]) for m in manifest)),
        "goal_step_max": int(max(int(m["goal_step"]) for m in manifest)),
        "turn_strict_n": int(sum(float(m["turn_strict"]) > 0.5 for m in manifest)),
    }
    return stats
def run_smoke(manifest_csv: str) -> dict:
    from eval_by_distance import load_config
    from eval_goal_head import make_split_dataset, meters_per_unit, normalize_images
    from train_e_dino import build_e_model, estimated_goal_pos, forward_wp_head, load_dino_head
    from train_goal_dino import CACHE_DIR, DFT_VAL_LIST, load_cache
    from eval_goal_head import load_frozen_nomad, B_CHECKPOINT
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_e = load_config("config/nomad_e_dino_path.yaml")
    config_b = load_config("config/nomad_b40.yaml")
    _p, rows, _ = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(CACHE_DIR, "train", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(DINO, device)
    wp_o, _ = load_dino_head(WP_O, device)
    wp_a, _ = load_dino_head(WP_A, device)
    loc_model = load_frozen_nomad(config_b, B_CHECKPOINT, device)
    manifest = list(csv.DictReader(open(manifest_csv, encoding="utf-8")))
    m = manifest[:8]
    from eval_by_distance import load_observation
    from eval_e_path_adapt_val import past_rows_batch
    ds = make_split_dataset(config_b, "train")
    meters = float(meters_per_unit(ds))
    obs_list, goal_list = [], []
    curr_rows, goal_rows, traj_names, curr_ts = [], [], [], []
    for row in m:
        traj, t, gt = row["traj_name"], int(row["curr_t"]), int(row["goal_t"])
        obs, goal, _a, gp = load_observation(ds, traj, t, gt)
        obs_list.append(obs)
        goal_list.append(goal)
        curr_rows.append(int(row["cache_curr_row"]))
        goal_rows.append(int(row["cache_goal_row"]))
        traj_names.append(traj)
        curr_ts.append(t)
    batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
    past = past_rows_batch(traj_names, curr_ts, rows, ds.waypoint_spacing)
    curr_np = np.array(curr_rows, dtype=np.int64)
    goal_np = np.array(goal_rows, dtype=np.int64)
    base_kw = dict(
        loc_model=loc_model,
        dino_head=dino_head,
        features=features,
        batch_obs=batch_obs,
        batch_goal=batch_goal,
        curr_rows=curr_np,
        goal_rows=goal_np,
        pos_dim=18,
        device=device,
        wp_head=wp_o,
        wp_scale=1.0,
        goal_pos_mode="blend_path",
        past_rows=past,
        path_gate="none",
        path_source="wp_poly",
        meters_per_unit=meters,
        path_units="dataset",
    )
    pos_c = estimated_goal_pos(**base_kw, wp_path_head=None)
    pos_t = estimated_goal_pos(**base_kw, wp_path_head=wp_a)
    mu_diff = float(torch.max(torch.abs(pos_c[:, :2] - pos_t[:, :2])).item())
    path_diff = float(torch.max(torch.abs(pos_c[:, 2:] - pos_t[:, 2:])).item())
    gp_t = torch.tensor(np.stack([load_observation(ds, r["traj_name"], int(r["curr_t"]), int(r["goal_t"]))[3] for r in m]))
    pos_gt = pos_c.clone()
    pos_gt[:, :2] = gp_t.to(device).float()[:, :2]
    act = torch.stack(
        [
            torch.tensor(load_observation(ds, r["traj_name"], int(r["curr_t"]), int(r["goal_t"]))[2][:, :2].reshape(-1))
            for r in m
        ]
    ).to(device).float()
    pos_gt[:, 2 : 2 + act.shape[1]] = act
    pos_c_gt = pos_c.clone()
    pos_t_gt = pos_t.clone()
    pos_c_gt[:, :2] = pos_gt[:, :2]
    pos_t_gt[:, :2] = pos_gt[:, :2]
    pos_c_gt[:, 2:] = pos_gt[:, 2:]
    pos_t_gt[:, 2:] = pos_gt[:, 2:]
    gt_match_c_t = float(torch.max(torch.abs(pos_c_gt - pos_t_gt)).item())
    ctx_info_o = forward_wp_head(wp_o, features, curr_np, goal_np, past, device)
    ctx_info_a = forward_wp_head(wp_a, features, curr_np, goal_np, past, device)
    wp_context = int(wp_o.kind.shape[0] - 2)
    model_a, _ = build_e_model(config_e, 18)
    model_b, _ = build_e_model(config_e, 18)
    st = torch.load(os.path.join(CWD, INIT_E), map_location="cpu", weights_only=False)
    model_a.load_state_dict(st, strict=True)
    model_b.load_state_dict(st, strict=True)
    init_diff = max(
        float((pa - pb).abs().max().item())
        for pa, pb in zip(model_a.state_dict().values(), model_b.state_dict().values())
        if torch.is_floating_point(pa)
    )
    head_grad = sum(
        1
        for h in (dino_head, wp_o, wp_a)
        for p in h.parameters()
        if p.requires_grad
    )
    ok = (
        mu_diff < 1e-4
        and path_diff > 1e-5
        and gt_match_c_t < 1e-5
        and wp_context == 2
        and init_diff < 1e-6
        and head_grad == 0  # all condition heads frozen
    )
    return {
        "max_mu_C_minus_T": mu_diff,
        "max_path_C_minus_T": path_diff,
        "max_GT_cond_C_minus_T": gt_match_c_t,
        "wp_context_frames": wp_context,
        "init_weight_max_diff": init_diff,
        "frozen_head_tensors_with_grad": head_grad,
        "passed": ok,
    }
def train_group(label: str, wp_path_head: str, manifest_csv: str, run_name: str) -> str:
    run_dir = os.path.join(CWD, "logs", "nomad", run_name)
    log_path = os.path.join(run_dir, "train_log.csv")
    start_epoch = 0
    init_ckpt = INIT_E
    if os.path.isfile(log_path):
        rows = [r for r in csv.DictReader(open(log_path, encoding="utf-8")) if r.get("epoch", "").strip().isdigit()]
        done = len(rows)
        if done >= 8:
            print(f"{label}: already finished ({done} epochs in train_log.csv)")
            return run_dir
        if done > 0:
            start_epoch = done
            while start_epoch > 0 and not os.path.isfile(
                os.path.join(run_dir, f"ema_{start_epoch - 1}.pth")
            ):
                start_epoch -= 1
            if start_epoch <= 0:
                start_epoch = 0
                init_ckpt = INIT_E
            else:
                init_ckpt = os.path.join("logs", "nomad", run_name, f"ema_{start_epoch - 1}.pth")
            print(f"{label}: resume from epoch {start_epoch} using {init_ckpt}")
    elif os.path.isfile(os.path.join(run_dir, "ema_0.pth")) and os.path.isfile(
        os.path.join(run_dir, "val_nav_epoch0.json")
    ):
        start_epoch = 1
        init_ckpt = os.path.join("logs", "nomad", run_name, "ema_0.pth")
        print(f"{label}: resume after epoch-0 val fix from {init_ckpt}")
    cmd = [
        PY,
        "-u",
        "train_e_dino.py",
        "--config",
        "config/nomad_e_dino_path.yaml",
        "--init-ckpt",
        init_ckpt,
        "--goal-pos-mode",
        "blend_path",
        "--path-source",
        "wp_poly",
        "--path-units",
        "dataset",
        "--path-gate",
        "none",
        "--pos-dim",
        "18",
        "--dino-head",
        DINO,
        "--wp-head",
        WP_O,
        "--epochs",
        "8",
        "--lr",
        "3e-5",
        "--warmup-epochs",
        "1",
        "--true-pos-prob",
        "0.2",
        "--batch-size",
        "32",
        "--seed",
        "0",
        "--num-workers",
        "0",
        "--exclude-val-list",
        "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/val_trajectories.txt",
        "--val-manifest-csv",
        manifest_csv,
        "--run-name",
        run_name,
    ]
    if start_epoch > 0:
        cmd.extend(["--start-epoch", str(start_epoch)])
    if wp_path_head:
        cmd.extend(["--wp-path-head", wp_path_head])
    run_cmd(cmd)
    return os.path.join(CWD, "logs", "nomad", run_name)
def pick_best_run(run_dir: str) -> dict:
    log_path = os.path.join(run_dir, "train_log.csv")
    rows = list(csv.DictReader(open(log_path, encoding="utf-8")))
    best = min(rows, key=lambda r: float(r["val_nav_ade_cm"]))
    ep = int(best["epoch"])
    ckpt = os.path.join(run_dir, f"ema_{ep}.pth")
    return {
        "epoch": ep,
        "val_nav_ade_cm": float(best["val_nav_ade_cm"]),
        "checkpoint": ckpt,
        "sha256": sha256_file(ckpt),
    }
def summarize_report(out_dir: str, ref_ade: float, best_c: dict, best_t: dict, manifest_stats: dict, smoke: dict):
    c_ade = best_c["val_nav_ade_cm"]
    t_ade = best_t["val_nav_ade_cm"]
    imp_ct = c_ade - t_ade
    lines = [
        "# 导航模型适配更新路径 — C/T 对照",
        "",
        "## Checkpoint（固定）",
        f"- pathact8 WP: `{WP_O}` sha256 `{sha256_file(os.path.join(CWD, WP_O))}`",
        f"- A_cls WP: `{WP_A}` sha256 `{sha256_file(os.path.join(CWD, WP_A))}`",
        f"- E init: `{INIT_E}` sha256 `{sha256_file(os.path.join(CWD, INIT_E))}`",
        "",
        "## 验证清单",
        f"- seed={MANIFEST_SEED}, n={manifest_stats['n']}, goal_step>={manifest_stats['far_steps_ge']}",
        "",
        "## 导航 ADE（cm，val manifest，true_pos_prob=0）",
        f"| 模型 | ADE |",
        f"|------|-----|",
        f"| 原 E init（未再训） | {ref_ade:.4f} |",
        f"| C 继续训练 | {c_ade:.4f} |",
        f"| T 路径适配 | {t_ade:.4f} |",
        "",
        f"- C−T（正值= T 更好）: **{imp_ct:+.4f} cm**",
        "",
        "## 说明",
        "- 训练排除 DFT val 轨迹；验证仅用 manifest 上 far 样本（步数≥20，非米）。",
        "- **共同 init E** 曾在全 train 索引上微调，可能见过 val 轨迹 → 本轮为**微调验证**，非严格未见域泛化。",
        "- T 的 μ 始终来自 pathact8 部署分支；仅 16 维路径来自 A_cls。",
        "",
        f"smoke_check passed={smoke.get('passed')}",
    ]
    with open(os.path.join(out_dir, "REPORT_zh.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
def main():
    os.makedirs(OUT, exist_ok=True)
    manifest_csv = os.path.join(OUT, f"val_far_manifest_seed{MANIFEST_SEED}.csv")
    mstats = build_far_val_manifest(manifest_csv)
    with open(os.path.join(OUT, "manifest_stats.json"), "w", encoding="utf-8") as f:
        json.dump(mstats, f, indent=2)
    smoke = run_smoke(manifest_csv)
    with open(os.path.join(OUT, "smoke_check.json"), "w", encoding="utf-8") as f:
        json.dump(smoke, f, indent=2)
    if not smoke["passed"]:
        print("SMOKE FAILED", smoke)
        sys.exit(1)
    from eval_e_path_adapt_val import eval_checkpoint_file
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ref_ade = eval_checkpoint_file(
        os.path.join(CWD, INIT_E),
        manifest_csv,
        os.path.join(CWD, DINO),
        os.path.join(CWD, WP_O),
        "",
        device,
    )
    with open(os.path.join(OUT, "ref_init_e_val.json"), "w", encoding="utf-8") as f:
        json.dump({"nav_ade_cm": ref_ade}, f, indent=2)
    t0 = time.time()
    run_c = train_group("C", "", manifest_csv, "nomad_e_path_adapt_C")
    run_t = train_group("T", WP_A, manifest_csv, "nomad_e_path_adapt_T")
    best_c = pick_best_run(run_c)
    best_t = pick_best_run(run_t)
    from eval_e_path_adapt_val import bootstrap_trajectory_pooled, load_manifest_csv, ValNavEvaluator
    import argparse
    # paired bootstrap C vs T on best-epoch per-frame CSVs
    c_csv = os.path.join(run_c, f"val_nav_ade_epoch{best_c['epoch']}.csv")
    t_csv = os.path.join(run_t, f"val_nav_ade_epoch{best_t['epoch']}.csv")
    c_ade = {int(r["order"]): float(r["nav_ade_cm"]) for r in csv.DictReader(open(c_csv, encoding="utf-8"))}
    t_ade = {int(r["order"]): float(r["nav_ade_cm"]) for r in csv.DictReader(open(t_csv, encoding="utf-8"))}
    orders = sorted(c_ade.keys())
    delta = np.array([c_ade[o] - t_ade[o] for o in orders], dtype=np.float64)
    manifest = load_manifest_csv(manifest_csv)
    traj_names = np.array([manifest[i]["traj_name"] for i in range(len(manifest))])
    boot_m, boot_lo, boot_hi = bootstrap_trajectory_pooled(delta, traj_names)
    summary = {
        "ref_init_e_nav_ade_cm": ref_ade,
        "C": best_c,
        "T": best_t,
        "improvement_C_minus_T_cm": float(delta.mean()),
        "bootstrap_C_minus_T": {"mean": boot_m, "ci95_lo": boot_lo, "ci95_hi": boot_hi},
        "minutes_total": (time.time() - t0) / 60,
        "manifest_stats": mstats,
        "smoke": smoke,
    }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    summarize_report(OUT, ref_ade, best_c, best_t, mstats, smoke)
    print(json.dumps(summary, indent=2))
if __name__ == "__main__":
    main()

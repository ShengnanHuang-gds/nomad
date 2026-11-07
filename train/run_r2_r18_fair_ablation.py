"""Fair R2 (2D mu) vs R18 (mu + frozen pathact8 path) ablation   preflight, train, report.

R2: goal_pos_mode=goal, pos_dim=2, pure DINO_dir * B_dist (no kappa, no path).
R18: goal_pos_mode=goal_path, pos_dim=18, same mu + wp_poly 16D from frozen pathact8 (ctx=2).

No Locked eval. Shared val manifest seed=20261107, shared diffusion noise in val subprocess.
"""
from __future__ import annotations

import argparse
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
import torch.nn.functional as F

CWD = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(CWD, "logs/revalidation/r2_r18_fair_2026-11-07")
MANIFEST_SEED = 20261107
MANIFEST_MAX = 500
VAL_EVAL_SEED = 0
DINO = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
PATHACT8 = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
E_ORACLE = "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth"
CONFIG_R2 = "config/nomad_e_dino_r2_r18.yaml"
CONFIG_R18 = "config/nomad_e_dino_r18.yaml"
RUN_R2 = "nomad_e_r2_fair_20261107"
RUN_R18 = "nomad_e_r18_fair_20261107"
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


def build_val_manifest(out_csv: str) -> dict:
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
    exclude_txt = os.path.join(OUT, "exclude_val_trajs.txt")
    with open(exclude_txt, "w", encoding="utf-8") as f:
        for t in sorted(val_trajs):
            f.write(t + "\n")
    stats = {
        "n": len(manifest),
        "seed": MANIFEST_SEED,
        "far_steps_ge": int(FAR_STEPS),
        "goal_step_min": int(min(int(m["goal_step"]) for m in manifest)),
        "goal_step_max": int(max(int(m["goal_step"]) for m in manifest)),
        "turn_strict_n": int(sum(float(m["turn_strict"]) > 0.5 for m in manifest)),
        "exclude_val_list": exclude_txt,
        "note": "Val trajectories held out of training via DFT_VAL_LIST; label as finetune-val not strict OOD.",
    }
    with open(os.path.join(OUT, "manifest_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats


def verify_lr_schedule_cpu() -> dict:
    from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR

    steps_per_epoch = 100
    total_epochs = 8
    total_steps = steps_per_epoch * total_epochs
    warmup_steps = steps_per_epoch
    p = torch.nn.Parameter(torch.zeros(1))
    opt = torch.optim.AdamW([p], lr=3e-5)
    sched_warm = LinearLR(opt, start_factor=1e-2, end_factor=1.0, total_iters=warmup_steps)
    sched_cos = CosineAnnealingLR(opt, T_max=max(total_steps - warmup_steps, 1))
    sched = SequentialLR(opt, schedulers=[sched_warm, sched_cos], milestones=[warmup_steps])
    lrs = []
    for _ in range(total_steps):
        lrs.append(float(opt.param_groups[0]["lr"]))
        opt.step()
        sched.step()
    return {
        "lr_step0": lrs[0],
        "lr_step1": lrs[1],
        "lr_end_warmup": lrs[warmup_steps - 1],
        "lr_after_warmup": lrs[warmup_steps],
        "lr_final": lrs[-1],
        "epoch0_has_positive_lr": lrs[0] > 0 and lrs[steps_per_epoch - 1] > 0,
    }


def run_preflight(manifest_csv: str) -> dict:
    from eval_by_distance import load_config, load_observation
    from eval_e_path_adapt_val import past_rows_batch
    from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images
    from eval_position_noise import encode_cond
    from train_e_dino import (
        E_ORACLE_CHECKPOINT,
        build_e_model,
        estimated_goal_pos,
        load_dino_head,
        load_expand_cond,
    )
    from train_goal_dino import CACHE_DIR, load_cache
    from vint_train.training.train_utils import append_goal_pos, normalize_data, ACTION_STATS, get_delta
    from vint_train.visualizing.visualize_utils import from_numpy

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    config_r2 = load_config(CONFIG_R2)
    config_r18 = load_config(CONFIG_R18)
    config_b = load_config("config/nomad_b40.yaml")
    _p, rows, _ = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(CACHE_DIR, "train", "features.npy"), mmap_mode="r")
    dino_head, _ = load_dino_head(DINO, device)
    path_head, _ = load_dino_head(PATHACT8, device)
    loc_model = load_frozen_nomad(config_b, B_CHECKPOINT, device)
    ds = make_split_dataset(config_b, "train")
    meters = float(meters_per_unit(ds))

    manifest = list(csv.DictReader(open(manifest_csv, encoding="utf-8")))[:16]
    obs_list, goal_list, action_list = [], [], []
    curr_rows, goal_rows, traj_names, curr_ts = [], [], [], []
    for row in manifest:
        traj, t, gt = row["traj_name"], int(row["curr_t"]), int(row["goal_t"])
        obs, goal, actions, _gp = load_observation(ds, traj, t, gt)
        obs_list.append(obs)
        goal_list.append(goal)
        action_list.append(torch.as_tensor(actions, dtype=torch.float32))
        curr_rows.append(int(row["cache_curr_row"]))
        goal_rows.append(int(row["cache_goal_row"]))
        traj_names.append(traj)
        curr_ts.append(t)
    batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
    past = past_rows_batch(traj_names, curr_ts, rows, ds.waypoint_spacing)
    cr = np.array(curr_rows, dtype=np.int64)
    gr = np.array(goal_rows, dtype=np.int64)
    base = dict(
        loc_model=loc_model,
        dino_head=dino_head,
        features=features,
        batch_obs=batch_obs,
        batch_goal=batch_goal,
        curr_rows=cr,
        goal_rows=gr,
        device=device,
        past_rows=past,
        path_gate="none",
        path_source="wp_poly",
        meters_per_unit=meters,
        path_units="dataset",
        wp_scale=1.0,
    )
    mu_r2 = estimated_goal_pos(**base, pos_dim=2, goal_pos_mode="goal", wp_head=None, wp_path_head=None)
    pos_r18 = estimated_goal_pos(
        **base, pos_dim=18, goal_pos_mode="goal_path", wp_head=None, wp_path_head=path_head
    )
    mu_match = float(torch.max(torch.abs(mu_r2 - pos_r18[:, :2])).item())
    path_nnz = float(pos_r18[:, 2:].abs().max().item())
    wp_ctx = int(path_head.kind.shape[0] - 2)

    model_r2, sched = build_e_model(config_r2, 2)
    model_r18, _ = build_e_model(config_r18, 18)
    st = torch.load(os.path.join(CWD, E_ORACLE), map_location="cpu", weights_only=False)
    if isinstance(st, dict) and "state_dict" in st:
        st = st["state_dict"]
    model_r2.load_state_dict(st, strict=True)
    load_expand_cond(model_r18, os.path.join(CWD, E_ORACLE), 2, 18, device, label="e_oracle")
    model_r2.to(device).eval()
    model_r18.to(device).eval()

    with torch.no_grad():
        est2 = mu_r2
        est18 = pos_r18
        gm = torch.zeros(len(batch_obs), dtype=torch.long, device=device)
        c2 = append_goal_pos(
            encode_cond(model_r2, batch_obs, batch_goal, 0, device)[0], est2, gm
        )
        c18 = append_goal_pos(
            encode_cond(model_r18, batch_obs, batch_goal, 0, device)[0], est18, gm
        )
        actions_b = torch.stack(action_list)
        deltas = get_delta(actions_b)
        naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
        noise = torch.randn_like(naction)
        ts = torch.tensor([5] * len(batch_obs), device=device)
        noisy = sched.add_noise(naction, noise, ts)
        p2 = model_r2("noise_pred_net", sample=noisy, timestep=ts, global_cond=c2)
        p18 = model_r18("noise_pred_net", sample=noisy, timestep=ts, global_cond=c18)
        init_pred_diff = float((p2 - p18).abs().max().item())

    frozen_grad = sum(
        1
        for h in (dino_head, path_head, loc_model.vision_encoder, loc_model.dist_pred_net)
        for p in h.parameters()
        if p.requires_grad
    )
    train_r18 = [p for p in model_r18.noise_pred_net.parameters() if p.requires_grad]
    model_r18.noise_pred_net.train()
    gm = torch.zeros(len(batch_obs), dtype=torch.long, device=device)
    with torch.no_grad():
        obsgoal = model_r18(
            "vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=gm
        )
        est = estimated_goal_pos(
            loc_model,
            dino_head,
            features,
            batch_obs,
            batch_goal,
            cr,
            gr,
            18,
            device,
            wp_path_head=path_head,
            goal_pos_mode="goal_path",
            past_rows=past,
            path_source="wp_poly",
            path_units="dataset",
            meters_per_unit=meters,
        )
        cond = append_goal_pos(obsgoal, est, gm)
    actions_b = torch.stack(action_list)
    deltas = get_delta(actions_b)
    naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
    noise = torch.randn_like(naction)
    ts = torch.randint(0, sched.config.num_train_timesteps, (len(batch_obs),), device=device)
    noisy = sched.add_noise(naction, noise, ts)
    pred = model_r18("noise_pred_net", sample=noisy, timestep=ts, global_cond=cond)
    loss = F.mse_loss(pred, noise)
    loss.backward()

    from r2_r18_common import path_cond_grad_and_delta



    path_grad_info = path_cond_grad_and_delta(model_r18, model_r2)

    path_col_grad = float(path_grad_info["path_input_grad_max"])

    opt = torch.optim.AdamW(train_r18, lr=3e-5)

    w_path_before = {

        name: p[:, 258:274].detach().clone()

        for name, p in model_r18.noise_pred_net.named_parameters()

        if name.endswith("cond_encoder.1.weight") and p.shape[1] >= 274

    }

    opt.step()

    path_delta_max = 0.0

    for name, p in model_r18.noise_pred_net.named_parameters():

        if name in w_path_before:

            path_delta_max = max(

                path_delta_max, float((p[:, 258:274] - w_path_before[name]).abs().max().item())

            )

    path_grad_info["path_weight_delta_max_after_one_step"] = path_delta_max

    nav_grad = float(max(p.grad.abs().max().item() for p in train_r18 if p.grad is not None))



    lr_cpu = verify_lr_schedule_cpu()
    checks = {
        "mu_r2_r18_max_diff": mu_match,
        "r18_path_max_abs": path_nnz,
        "wp_context_frames": wp_ctx,
        "init_noise_pred_max_diff": init_pred_diff,
        "frozen_heads_with_grad": frozen_grad,
        "r18_path_input_grad_max": path_col_grad,
        "r18_path_cond_columns": path_grad_info,
        "noise_pred_grad_max": nav_grad,
        "r2_cond_shape": list(est2.shape),
        "r18_cond_shape": list(est18.shape),
        "e_oracle_sha256": sha256_file(os.path.join(CWD, E_ORACLE)),
        "pathact8_sha256": sha256_file(os.path.join(CWD, PATHACT8)),
        "dino_sha256": sha256_file(os.path.join(CWD, DINO)),
        "lr_schedule_cpu": lr_cpu,
    }
    checks["passed"] = (
        mu_match < 1e-5
        and path_nnz > 1e-6
        and wp_ctx == 2
        and init_pred_diff < 2e-4
        and frozen_grad == 0
        and path_col_grad > 0
        and nav_grad > 0
        and lr_cpu["epoch0_has_positive_lr"]
        and checks["r2_cond_shape"] == [len(manifest), 2]
        and checks["r18_cond_shape"] == [len(manifest), 18]
    )
    with open(os.path.join(OUT, "preflight.json"), "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)
    return checks


def train_arm(label: str, goal_mode: str, pos_dim: int, config: str, run_name: str, manifest_csv: str, exclude_txt: str):
    run_dir = os.path.join(CWD, "logs", "nomad", run_name)
    log_path = os.path.join(run_dir, "train_log.csv")
    start_epoch = 0
    if os.path.isfile(log_path):
        rows = [r for r in csv.DictReader(open(log_path, encoding="utf-8")) if str(r.get("epoch", "")).isdigit()]
        start_epoch = len(rows)
        if start_epoch >= 8:
            print(f"{label}: already finished 8 epochs")
            return run_dir

    cmd = [
        PY,
        "-u",
        "train_e_dino.py",
        "--config",
        config,
        "--init-from",
        "e_oracle",
        "--checkpoint-e-oracle",
        E_ORACLE,
        "--goal-pos-mode",
        goal_mode,
        "--pos-dim",
        str(pos_dim),
        "--true-pos-prob",
        "0",
        "--epochs",
        "8",
        "--batch-size",
        "32",
        "--lr",
        "3e-5",
        "--warmup-epochs",
        "1",
        "--lr-schedule",
        "per_step",
        "--reset-train-rng-after-init",
        "--seed",
        "0",
        "--num-workers",
        "2",
        "--run-name",
        run_name,
        "--dino-head",
        DINO,
        "--exclude-val-list",
        exclude_txt,
        "--val-manifest-csv",
        manifest_csv,
    ]
    if goal_mode == "goal_path":
        cmd.extend(
            [
                "--wp-path-head",
                PATHACT8,
                "--path-source",
                "wp_poly",
                "--path-units",
                "dataset",
            ]
        )
    if start_epoch > 0:

        raise SystemExit(

            f"{label}: train_log has {start_epoch} completed epoch(s) under {run_dir}. "

            "Refusing ema_latest-only resume (need model+optimizer+scheduler+EMA step count+RNG). "

            "If training is still running in another process, do not start a second job. "

            "If the run stopped mid-way, keep artifacts and restore manually; this launcher will not auto-retrain."

        )

    run_cmd(cmd)
    return run_dir


def pick_best_epoch(run_dir: str) -> dict:
    best = None
    for ep in range(8):
        jf = os.path.join(run_dir, f"val_nav_epoch{ep}.json")
        if not os.path.isfile(jf):
            continue
        with open(jf, encoding="utf-8") as f:
            m = json.load(f)
        if best is None or m["nav_ade_cm"] < best["nav_ade_cm"]:
            best = {"epoch": ep, **m}
    if best:
        best["checkpoint"] = os.path.join(run_dir, f"ema_{best['epoch']}.pth")
        best["sha256"] = sha256_file(best["checkpoint"])
    return best or {}


def write_report(r2_dir: str, r18_dir: str, manifest_csv: str):

    from r2_r18_common import align_paired_ade, bootstrap_traj_pooled_pairs, manifest_units_note



    b2 = pick_best_epoch(r2_dir)

    b18 = pick_best_epoch(r18_dir)

    r2_ep = b2.get("per_frame_csv", "")

    r18_ep = b18.get("per_frame_csv", "")

    paired = {"delta_r2_minus_r18_cm": float("nan"), "ci95_lo": float("nan"), "ci95_hi": float("nan")}

    if r2_ep and r18_ep and os.path.isfile(r2_ep) and os.path.isfile(r18_ep):

        r2_ep = r2_ep if os.path.isabs(r2_ep) else os.path.join(CWD, r2_ep)

        r18_ep = r18_ep if os.path.isabs(r18_ep) else os.path.join(CWD, r18_ep)

        ade2, ade18, trajs = align_paired_ade(r2_ep, r18_ep)

        d = ade2 - ade18

        m, lo, hi = bootstrap_traj_pooled_pairs(d, np.array(trajs))

        paired = {

            "delta_r2_minus_r18_cm_mean": m,

            "ci95_lo": lo,

            "ci95_hi": hi,

            "n_pairs": len(d),

            "align_key": "(traj_name,curr_t,goal_t) via manifest order",

        }

    summary = {

        "R2": {"run_dir": r2_dir, "best": b2, "condition": "2D mu only"},

        "R18": {"run_dir": r18_dir, "best": b18, "condition": "2D mu + pathact8 16D"},

        "paired_all": paired,

        "manifest_csv": manifest_csv,

        "manifest_units": manifest_units_note(manifest_csv),

        "val_noise_seed": VAL_EVAL_SEED,

    }

    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:

        json.dump(summary, f, indent=2)

    rows = [

        ["method", "cond_dim", "val_nav_ade_cm", "turn_strict_ade_cm", "front4_cm", "back4_cm", "best_epoch", "checkpoint"],

        [

            "R2",

            2,

            b2.get("nav_ade_cm"),

            b2.get("nav_ade_turn_strict_cm"),

            b2.get("ade_front4_cm"),

            b2.get("ade_back4_cm"),

            b2.get("epoch"),

            b2.get("checkpoint"),

        ],

        [

            "R18",

            18,

            b18.get("nav_ade_cm"),

            b18.get("nav_ade_turn_strict_cm"),

            b18.get("ade_front4_cm"),

            b18.get("ade_back4_cm"),

            b18.get("epoch"),

            b18.get("checkpoint"),

        ],

    ]

    with open(os.path.join(OUT, "main_results.csv"), "w", newline="", encoding="utf-8-sig") as f:

        csv.writer(f).writerows(rows)

    print(json.dumps(summary, indent=2))





def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--train-only", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    manifest = os.path.join(OUT, f"val_far_manifest_seed{MANIFEST_SEED}.csv")
    if not args.report_only:
        stats = build_val_manifest(manifest)
        print("manifest", stats)
    if not args.train_only and not args.report_only:
        pf = run_preflight(manifest)
        print("preflight", json.dumps(pf, indent=2))
        if not pf.get("passed"):
            raise SystemExit("Preflight failed   fix implementation before 8-epoch training.")
        if args.preflight_only:
            return
    if not args.report_only:
        exclude = os.path.join(OUT, "exclude_val_trajs.txt")
        train_arm("R2", "goal", 2, CONFIG_R2, RUN_R2, manifest, exclude)
        train_arm("R18", "goal_path", 18, CONFIG_R18, RUN_R18, manifest, exclude)
    write_report(
        os.path.join(CWD, "logs/nomad", RUN_R2),
        os.path.join(CWD, "logs/nomad", RUN_R18),
        manifest,
    )


if __name__ == "__main__":
    main()

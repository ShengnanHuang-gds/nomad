"""Orchestrate O baseline + grad checks + joint A/B fine-tune + report."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import numpy as np
import torch
from e_path_joint_common import (
    build_cond_blend_path,
    clone_path_output_layer,
    grad_check_path_head,
    gt_path_from_actions,
    mu_consistency_report,
    mu_from_frozen_wp,
    path_loss_smooth_l1,
    sha256_file,
    wp_path_input_features,
)
from eval_by_distance import load_config
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, meters_per_unit, normalize_images
from train_e_dino import ViNTWithDinoRows, append_goal_pos, build_e_model, get_delta, load_dino_head
from train_goal_dino import CACHE_DIR, load_cache
from vint_train.training.train_utils import ACTION_STATS, normalize_data
from vint_train.visualizing.visualize_utils import from_numpy
TRAIN_ROOT = os.path.dirname(os.path.abspath(__file__))
VAL_MANIFEST = os.path.join(
    TRAIN_ROOT, "logs", "revalidation", "r2_r18_fair_2026-11-07", "val_far_manifest_seed20261107.csv"
)
OUT_ROOT = os.path.join(TRAIN_ROOT, "logs", "revalidation", "e_path_joint_ab_2026-11-08")
E_INIT = os.path.join(TRAIN_ROOT, "logs", "nomad", "nomad_e_ft_pathact8", "ema_latest.pth")
WP_HEAD = os.path.join(
    TRAIN_ROOT,
    "logs",
    "nomad_d",
    "nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32",
    "dino_dir_best.pth",
)
DINO_HEAD = os.path.join(
    TRAIN_ROOT, "logs", "nomad_d", "nomad_dino_dir_e60_2026_10_13_19_29_06", "dino_dir_best.pth"
)
def dp_env():
    env = os.environ.copy()
    dp = os.path.join(os.path.dirname(TRAIN_ROOT), "diffusion_policy")
    env["PYTHONPATH"] = dp if not env.get("PYTHONPATH") else dp + os.pathsep + env["PYTHONPATH"]
    return env
def run_eval_o(out_dir: str, tag: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    val_json = os.path.join(out_dir, f"val_{tag}.json")
    cmd = [
        sys.executable,
        "-u",
        os.path.join(TRAIN_ROOT, "eval_e_path_adapt_val.py"),
        "--checkpoint",
        E_INIT,
        "--manifest-csv",
        VAL_MANIFEST,
        "--dino-head",
        DINO_HEAD,
        "--wp-head",
        WP_HEAD,
        "--config-e-dino",
        "config/nomad_e_dino_path.yaml",
        "--config-b",
        "config/nomad_b40.yaml",
        "--path-units",
        "dataset",
        "--path-source",
        "wp_poly",
        "--path-gate",
        "none",
        "--goal-pos-mode",
        "blend_path",
        "--wp-scale",
        "1.0",
        "--pos-dim",
        "18",
        "--epoch",
        "-1",
        "--out-dir",
        out_dir,
        "--out-json",
        val_json,
    ]
    subprocess.run(cmd, cwd=TRAIN_ROOT, check=True, env=dp_env())
    with open(val_json, encoding="utf-8") as f:
        return json.load(f)
def train_arm(arm: str, run_dir: str, skip: bool = False) -> int:
    if skip:
        return 0
    cmd = [
        sys.executable,
        "-u",
        os.path.join(TRAIN_ROOT, "train_e_joint_path_ab.py"),
        "--arm",
        arm,
        "--init-ckpt",
        E_INIT,
        "--dino-head",
        DINO_HEAD,
        "--wp-head",
        WP_HEAD,
        "--checkpoint-b",
        B_CHECKPOINT,
        "--val-manifest-csv",
        VAL_MANIFEST,
        "--run-dir",
        run_dir,
        "--epochs",
        "8",
        "--batch-size",
        "32",
        "--seed",
        "0",
        "--reset-train-rng-after-init",
        "--true-pos-prob",
        "0",
        "--goal-mask-prob",
        "0",
    ]
    return subprocess.run(cmd, cwd=TRAIN_ROOT, env=dp_env()).returncode
def mu_and_grad_checks(device):
    config = load_config(os.path.join(TRAIN_ROOT, "config", "nomad_e_dino_path.yaml"))
    cache_path, rows, meta = load_cache(CACHE_DIR, "train")
    features = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")
    wp_head, _ = load_dino_head(WP_HEAD, device)
    dino_head, _ = load_dino_head(DINO_HEAD, device)
    loc_model = load_frozen_nomad(load_config(os.path.join(TRAIN_ROOT, "config", "nomad_b40.yaml")), B_CHECKPOINT, device)
    data_config = config["datasets"]["go_stanford"]
    dataset = ViNTWithDinoRows(
        data_folder=data_config["data_folder"],
        data_split_folder=data_config["train"],
        dataset_name="go_stanford",
        image_size=config["image_size"],
        waypoint_spacing=data_config.get("waypoint_spacing", 1),
        min_dist_cat=config["distance"]["min_dist_cat"],
        max_dist_cat=config["distance"]["max_dist_cat"],
        min_action_distance=config["action"]["min_dist_cat"],
        max_action_distance=config["action"]["max_dist_cat"],
        negative_mining=data_config.get("negative_mining", True),
        len_traj_pred=config["len_traj_pred"],
        learn_angle=config["learn_angle"],
        context_size=config["context_size"],
        context_type=config.get("context_type", "temporal"),
        end_slack=data_config.get("end_slack", 0),
        goals_per_obs=data_config.get("goals_per_obs", 1),
        normalize=config["normalize"],
        goal_type=config.get("goal_type", "image"),
        dino_rows=rows,
    )
    meters = float(meters_per_unit(dataset))
    loader = torch.utils.data.DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0)
    batch = next(iter(loader))
    (
        obs_image,
        goal_image,
        actions,
        _d,
        _gp,
        _i,
        action_mask,
        curr_rows,
        goal_rows,
        past_rows,
    ) = batch
    batch_obs, batch_goal = normalize_images(obs_image, goal_image, device)
    mu_o = mu_from_frozen_wp(
        loc_model, dino_head, features, batch_obs, batch_goal, curr_rows, goal_rows, device, wp_head,
        past_rows=past_rows,
    )
    path_train = clone_path_output_layer(wp_head).to(device)
    mu_b = mu_from_frozen_wp(
        loc_model, dino_head, features, batch_obs, batch_goal, curr_rows, goal_rows, device, wp_head,
        past_rows=past_rows,
    )
    mu_report = mu_consistency_report(mu_o, mu_b)
    cond_frozen = build_cond_blend_path(
        mu_o, wp_head, None, features, curr_rows, goal_rows, past_rows, device, 18, "dataset", meters, frozen_path_for_cond=True
    )
    cond_b = build_cond_blend_path(
        mu_b, wp_head, path_train, features, curr_rows, goal_rows, past_rows, device, 18, "dataset", meters, frozen_path_for_cond=False
    )
    init_match = float((cond_frozen - cond_b).abs().max().item()) < 1e-5
    path_in = wp_path_input_features(wp_head, features, curr_rows, goal_rows, past_rows, device)
    tgt = gt_path_from_actions(actions.to(device))
    if wp_head.path_units if hasattr(wp_head, "path_units") else False:
        pass
    model, noise_sched = build_e_model(config, 18)
    st = torch.load(E_INIT, map_location="cpu", weights_only=False)
    model.load_state_dict(st, strict=True)
    model.to(device)
    model.vision_encoder.eval()
    model.dist_pred_net.eval()
    with torch.no_grad():
        obsgoal_cond = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=torch.zeros(len(batch_obs), dtype=torch.long, device=device))
    est_pos = build_cond_blend_path(
        mu_b, wp_head, path_train, features, curr_rows, goal_rows, past_rows, device, 18, "dataset", meters, frozen_path_for_cond=False
    )
    diffusion_cond = append_goal_pos(obsgoal_cond, est_pos, torch.zeros(len(batch_obs), dtype=torch.long, device=device))
    deltas = get_delta(actions)
    naction = from_numpy(normalize_data(deltas, ACTION_STATS)).to(device)
    noise = torch.randn_like(naction)
    t = torch.randint(0, noise_sched.config.num_train_timesteps, (naction.shape[0],), device=device)
    noisy = noise_sched.add_noise(naction, noise, t)
    pred = model("noise_pred_net", sample=noisy, timestep=t, global_cond=diffusion_cond)
    loss_diff = torch.nn.functional.mse_loss(pred, noise)
    path_train2 = clone_path_output_layer(wp_head).to(device)
    path_in2 = wp_path_input_features(wp_head, features, curr_rows, goal_rows, past_rows, device)
    lp = path_loss_smooth_l1(path_train2(path_in2).view(-1, 8, 2), tgt)
    lp.backward()
    g_lp = float(path_train2.weight.grad.norm().item())
    path_train.zero_grad(set_to_none=True)
    loss_diff.backward()
    g_diff = path_train.weight.grad
    grad_diff_norm = float(g_diff.norm().item()) if g_diff is not None else 0.0
    frozen_n = 0
    for p in wp_head.parameters():
        if p.grad is not None:
            frozen_n += 1
    return {
        "mu_consistency": mu_report,
        "cond_init_match_frozen_vs_train_layer": init_match,
        "grad_path_only_norm": g_lp,
        "grad_diff_only_norm": grad_diff_norm,
        "frozen_wp_grad_tensors": frozen_n,
    }
def bootstrap_mean_delta(deltas, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    deltas = np.asarray(deltas, dtype=np.float64)
    if len(deltas) == 0:
        return {"mean": float("nan"), "ci95_low": float("nan"), "ci95_high": float("nan")}
    boots = []
    for _ in range(n_boot):
        samp = rng.choice(deltas, size=len(deltas), replace=True)
        boots.append(float(samp.mean()))
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots))]
    return {"mean": float(deltas.mean()), "ci95_low": lo, "ci95_high": hi}
def load_per_frame_ade(csv_path: str) -> np.ndarray:
    import csv as csvmod
    ades = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csvmod.DictReader(f):
            ades.append(float(row.get("ade_pf_cm", row.get("nav_ade_cm", row.get("ade_cm", "nan")))))
    return np.asarray(ades, dtype=np.float64)
def compile_report(o_json, dir_a, dir_b, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(dir_a, "summary.json"), encoding="utf-8") as f:
        sa = json.load(f)
    with open(os.path.join(dir_b, "summary.json"), encoding="utf-8") as f:
        sb = json.load(f)
    best_a = int(sa["best_epoch"])
    best_b = int(sb["best_epoch"])
    eval_a = json.load(open(os.path.join(dir_a, f"val_nav_epoch{best_a}.json"), encoding="utf-8"))
    eval_b = json.load(open(os.path.join(dir_b, f"val_nav_epoch{best_b}.json"), encoding="utf-8"))
    ade_o = float(o_json["nav_ade_cm"])
    ade_a = float(eval_a["nav_ade_cm"])
    ade_b = float(eval_b["nav_ade_cm"])
    pf_o = load_per_frame_ade(o_json.get("per_frame_csv", ""))
    pf_a = load_per_frame_ade(eval_a.get("per_frame_csv", ""))
    pf_b = load_per_frame_ade(eval_b.get("per_frame_csv", ""))
    n = min(len(pf_o), len(pf_a), len(pf_b))
    pf_o, pf_a, pf_b = pf_o[:n], pf_a[:n], pf_b[:n]
    report = {
        "O_nav_ade_cm": ade_o,
        "A_nav_ade_cm": ade_a,
        "B_nav_ade_cm": ade_b,
        "A_best_epoch": best_a,
        "B_best_epoch": best_b,
        "delta_A_minus_O": ade_a - ade_o,
        "delta_B_minus_O": ade_b - ade_o,
        "delta_B_minus_A": ade_b - ade_a,
        "bootstrap_A_minus_O": bootstrap_mean_delta(pf_a - pf_o),
        "bootstrap_B_minus_A": bootstrap_mean_delta(pf_b - pf_a),
        "bootstrap_B_minus_O": bootstrap_mean_delta(pf_b - pf_o),
        "success_B_better_than_O_and_A": bool(ade_b < ade_o and ade_b < ade_a),
        "init_hashes": {
            "E_init_sha256": sha256_file(E_INIT),
            "WP_sha256": sha256_file(WP_HEAD),
        },
    }
    with open(os.path.join(out_dir, "OAB_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    md = os.path.join(out_dir, "OAB_REPORT_zh.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# 八步路径输出层 + 扩散联合微调 O/A/B\n\n")
        f.write("| 方法 | 选中 epoch | 验证集最终轨迹 ADE (cm) | 相对 O | 相对 A |\n")
        f.write("|------|------------|-------------------------|--------|--------|\n")
        f.write(
            f"| O (冻结) | — | {ade_o:.4f} | — | — |\n"
            f"| A (仅 UNet) | {best_a} | {ade_a:.4f} | {ade_a - ade_o:+.4f} | — |\n"
            f"| B (UNet+path) | {best_b} | {ade_b:.4f} | {ade_b - ade_o:+.4f} | {ade_b - ade_a:+.4f} |\n\n"
        )
        bbo = report["bootstrap_B_minus_O"]
        f.write(
            f"**结论（描述性）**：联合微调是否降低最终轨迹 ADE："
            f"{'是' if report['success_B_better_than_O_and_A'] else '否'}。"
            f"B−O bootstrap 均值 {bbo['mean']:+.4f} cm，95% 区间 [{bbo['ci95_low']:+.4f}, {bbo['ci95_high']:+.4f}]（同验证集、选模后 bootstrap，非独立测试）。\n"
        )
    print(json.dumps(report, indent=2))
    return report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-train-a", action="store_true")
    ap.add_argument("--skip-train-b", action="store_true")
    ap.add_argument("--only-report", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT_ROOT, exist_ok=True)
    for p in (E_INIT, WP_HEAD, DINO_HEAD, VAL_MANIFEST):
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
    audit = {
        "E_init": E_INIT,
        "E_sha256": sha256_file(E_INIT),
        "WP": WP_HEAD,
        "WP_sha256": sha256_file(WP_HEAD),
        "val_manifest": VAL_MANIFEST,
        "note_locked_17.75cm": "historical Locked 1000 reference, not this 500-pair val protocol",
    }
    with open(os.path.join(OUT_ROOT, "init_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    if not args.only_report:
        print("=== O baseline val ===")
        o_json = run_eval_o(OUT_ROOT, "O_baseline")
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        checks = mu_and_grad_checks(device)
        with open(os.path.join(OUT_ROOT, "preflight_checks.json"), "w", encoding="utf-8") as f:
            json.dump(checks, f, indent=2)
        print("preflight:", json.dumps(checks))
        if not checks["mu_consistency"]["pass"]:
            raise RuntimeError("mu consistency failed")
        if checks["grad_diff_only_norm"] <= 0 or checks.get("grad_path_only_norm", 0) <= 0:
            raise RuntimeError("B path head gradient check failed")
        dir_a = os.path.join(OUT_ROOT, "arm_a")
        dir_b = os.path.join(OUT_ROOT, "arm_b")
        if train_arm("a", dir_a, skip=args.skip_train_a) != 0:
            raise RuntimeError("arm A training failed")
        if train_arm("b", dir_b, skip=args.skip_train_b) != 0:
            raise RuntimeError("arm B training failed")
    else:
        o_json = json.load(open(os.path.join(OUT_ROOT, "val_O_baseline.json"), encoding="utf-8"))
    compile_report(
        o_json,
        os.path.join(OUT_ROOT, "arm_a"),
        os.path.join(OUT_ROOT, "arm_b"),
        OUT_ROOT,
    )
if __name__ == "__main__":
    main()

"""Local 8-point path direction x distance Oracle diagnostic (locked far 1000).

Reuses pathact8_residual_export/full1000 NPZ; fixed mu_units and E checkpoint.
Four conditions: PP, GP (true dir), PG (true dist), GG (full GT path).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2  # noqa: F401
import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation
from eval_goal_head import make_split_dataset, meters_per_unit, normalize_images
from eval_position_noise import diffuse, encode_cond, load_model, mean_ade_fde
from vint_train.training.train_utils import append_goal_pos

DEFAULT_EXPORT = "logs/revalidation/pathact8_residual_export/full1000"
DEFAULT_OUT = "logs/revalidation/path_local_dir_dist_2x2"
NEAR_ZERO_M = 1e-6
BOOT_SEED = 20261103
BOOT_N = 10000

CONDITIONS = {
    "PP": ("预测路径", "预测路径"),
    "GP": ("真实方向", "预测距离"),
    "PG": ("预测方向", "真实距离"),
    "GG": ("真实方向", "真实距离"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_commit_short():
    root = Path(__file__).resolve().parent
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def scene_bucket(strict_turn, loose_turn):
    if bool(strict_turn):
        return "strict_turn"
    if not bool(loose_turn):
        return "strict_straight"
    return "middle"


def build_oracle_paths(path_pred, path_gt, meters_per_u):
    """path_pred/gt [N,H,2] dataset units. Returns dict of paths + skip counts."""
    eps_u = NEAR_ZERO_M / meters_per_u
    pred = np.asarray(path_pred, dtype=np.float64)
    gt = np.asarray(path_gt, dtype=np.float64)
    n, h, _ = pred.shape
    rP = np.linalg.norm(pred, axis=-1)
    rG = np.linalg.norm(gt, axis=-1)
    uP = np.zeros_like(pred)
    uG = np.zeros_like(gt)
    uP_ok = rP >= eps_u
    uG_ok = rG >= eps_u
    uP[uP_ok] = pred[uP_ok] / rP[uP_ok, None]
    uG[uG_ok] = gt[uG_ok] / rG[uG_ok, None]

    pp = pred.copy()
    gg = gt.copy()
    gp = pred.copy()
    pg = pred.copy()
    gp_skip = 0
    pg_skip = 0
    for i in range(n):
        for k in range(h):
            if uG_ok[i, k]:
                gp[i, k] = rP[i, k] * uG[i, k]
            else:
                gp_skip += 1
            if uP_ok[i, k]:
                pg[i, k] = rG[i, k] * uP[i, k]
            else:
                pg_skip += 1
    return {
        "PP": pp.astype(np.float32),
        "GP": gp.astype(np.float32),
        "PG": pg.astype(np.float32),
        "GG": gg.astype(np.float32),
        "gp_direction_undefined_points": int(gp_skip),
        "pg_direction_undefined_points": int(pg_skip),
        "total_points": int(n * h),
    }


def e_dino_from(mu_units, path_n_h_2):
    flat = path_n_h_2.reshape(path_n_h_2.shape[0], -1)
    return np.concatenate([mu_units.astype(np.float32), flat.astype(np.float32)], axis=1)


def frame_ade_cm(pred_s_h_2, gt_h_2, meters):
    ade_m, _ = mean_ade_fde(pred_s_h_2, gt_h_2, meters)
    return float(ade_m) * 100.0


def pregenerate_noise(n, num_samples, horizon, batch_size, device, seed):
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    chunks = []
    for start in range(0, n, batch_size):
        bs = min(batch_size, n - start)
        chunks.append(torch.randn((bs * num_samples, horizon, 2), device=device))
    return chunks


@torch.no_grad()
def sample_nav_shared_noise(model, scheduler, dataset, far, e_dino_pos, device, num_samples, batch_size, noise_chunks):
    horizon = dataset.len_traj_pred
    n = len(far)
    preds = np.zeros((n, num_samples, horizon, 2), dtype=np.float32)
    chunk_idx = 0
    for start in tqdm(range(0, n, batch_size), desc="E-dino nav", leave=False):
        chunk = far[start : start + batch_size]
        obs_list, goal_list = [], []
        for traj_name, t, goal_time in chunk:
            obs, goal, _a, _p = load_observation(dataset, traj_name, t, goal_time)
            obs_list.append(obs)
            goal_list.append(goal)
        batch_obs, batch_goal = normalize_images(torch.stack(obs_list), torch.stack(goal_list), device)
        noise = noise_chunks[chunk_idx]
        chunk_idx += 1
        cond_goal, mask_goal = encode_cond(model, batch_obs, batch_goal, 0, device)
        pos = torch.tensor(e_dino_pos[start : start + len(chunk)], dtype=torch.float32, device=device)
        cond_goal = append_goal_pos(cond_goal, pos, mask_goal)
        pred_goal = diffuse(model, scheduler, cond_goal, noise, num_samples, device)
        preds[start : start + len(chunk)] = pred_goal[..., :2].detach().cpu().numpy()
    return preds


def bootstrap_paired_ci(delta_cm, n_boot=BOOT_N, seed=BOOT_SEED):
    v = np.asarray(delta_cm, dtype=np.float64)
    if v.size < 2:
        return float(v.mean()) if v.size else float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    boots = v[idx].mean(axis=1)
    return float(v.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def subset_stats(ade_cm, mask, baseline_cm):
    if mask.sum() == 0:
        return {"n": 0, "ade_cm": float("nan"), "delta_vs_pp_cm": float("nan")}
    sub = ade_cm[mask]
    base = baseline_cm[mask]
    return {"n": int(mask.sum()), "ade_cm": float(sub.mean()), "delta_vs_pp_cm": float(sub.mean() - base.mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", default=DEFAULT_EXPORT)
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--num-samples", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    export_dir = args.export_dir
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    meta_path = os.path.join(export_dir, "meta.json")
    npz_path = os.path.join(export_dir, "residual_export.npz")
    with open(meta_path, encoding="utf-8") as f:
        meta_export = json.load(f)
    z = np.load(npz_path, allow_pickle=True)
    meters = float(z["meters_per_unit"])
    path_pred = z["path_cond"]
    path_gt = z["gt_actions"]
    mu = z["mu_units"]
    strict_turn = z["strict_turn"]
    loose_turn = z["loose_turn"]
    traj = z["traj_name"]
    t_arr = z["t"]
    goal_t = z["goal_time"]

    far = [(str(traj[i]), int(t_arr[i]), int(goal_t[i])) for i in range(len(traj))]
    oracle = build_oracle_paths(path_pred, path_gt, meters)

    e_pos = {k: e_dino_from(mu, oracle[k]) for k in ("PP", "GP", "PG", "GG")}

    ma = meta_export["args"]
    config_b = ma["config_b"]
    ckpt_b = ma["checkpoint_b"]
    config_e = ma["config_e_dino"]
    run_dir = ma["run_dir"]
    ckpt_e = ma["checkpoint"]

    cmd_parts = [
        sys.executable,
        os.path.basename(__file__),
        f"--export-dir={export_dir}",
        f"--out-dir={out_dir}",
        f"--seed={args.seed}",
        f"--num-samples={args.num_samples}",
        f"--batch-size={args.batch_size}",
    ]
    eval_cmd = " ".join(cmd_parts)
    with open(os.path.join(out_dir, "eval_command.txt"), "w", encoding="utf-8") as f:
        f.write(eval_cmd + "\n")
        f.write(f"PYTHONPATH=../diffusion_policy (cwd=train)\n")
        f.write(f"seed={args.seed} num_samples={args.num_samples} batch_size={args.batch_size}\n")
        f.write(f"shared_noise_across_conditions=True\n")
        f.write(f"near_zero_direction_threshold_m={NEAR_ZERO_M}\n")

    if args.dry_run:
        print("dry-run OK", oracle["gp_direction_undefined_points"], oracle["pg_direction_undefined_points"])
        return

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    dataset = make_split_dataset(load_config(config_b), "test")
    model, scheduler = load_model(load_config(config_e), os.path.join(run_dir, ckpt_e), device)

    noise_chunks = pregenerate_noise(
        len(far), args.num_samples, dataset.len_traj_pred, args.batch_size, device, args.seed
    )

    nav = {}
    ade_cm = {}
    for key in ("PP", "GP", "PG", "GG"):
        nav[key] = sample_nav_shared_noise(
            model, scheduler, dataset, far, e_pos[key], device, args.num_samples, args.batch_size, noise_chunks
        )
        ade_cm[key] = np.zeros(len(far), dtype=np.float64)
        for i in range(len(far)):
            ade_cm[key][i] = frame_ade_cm(nav[key][i], path_gt[i], meters)

    pp_ref = nav["PP"]
    stored = z["nav_pred_samples"]
    max_diff = float(np.max(np.abs(pp_ref - stored)))
    mean_pp = float(ade_cm["PP"].mean())

    buckets = {}
    for name in ("all", "strict_turn", "strict_straight", "middle"):
        if name == "all":
            mask = np.ones(len(far), dtype=bool)
        else:
            mask = np.array([scene_bucket(strict_turn[i], loose_turn[i]) == name for i in range(len(far))])
        buckets[name] = mask

    rows = []
    for key in ("PP", "GP", "PG", "GG"):
        dir_src, dist_src = CONDITIONS[key]
        mean_ade = float(ade_cm[key].mean())
        delta = mean_ade - float(ade_cm["PP"].mean())
        rows.append(
            {
                "condition": key,
                "path_direction_source": dir_src,
                "path_distance_source": dist_src,
                "ade_cm": mean_ade,
                "delta_vs_pp_cm": delta,
            }
        )

    ade_pp = float(ade_cm["PP"].mean())
    ade_gp = float(ade_cm["GP"].mean())
    ade_pg = float(ade_cm["PG"].mean())
    ade_gg = float(ade_cm["GG"].mean())
    decomp = {
        "dir_only_from_pp_cm": ade_gp - ade_pp,
        "dist_only_from_pp_cm": ade_pg - ade_pp,
        "dir_when_dist_is_gt_cm": ade_gg - ade_pg,
        "dist_when_dir_is_gt_cm": ade_gg - ade_gp,
        "interaction_cm": ade_gg - ade_pg - ade_gp + ade_pp,
        "interaction_formula": "I = ADE(GG) - ADE(PG) - ADE(GP) + ADE(PP)",
    }

    boot = {}
    for label, delta_vec in [
        ("GP_minus_PP", ade_cm["GP"] - ade_cm["PP"]),
        ("PG_minus_PP", ade_cm["PG"] - ade_cm["PP"]),
        ("GG_minus_PG", ade_cm["GG"] - ade_cm["PG"]),
        ("GG_minus_GP", ade_cm["GG"] - ade_cm["GP"]),
        ("interaction_frame", ade_cm["GG"] - ade_cm["PG"] - ade_cm["GP"] + ade_cm["PP"]),
    ]:
        m, lo, hi = bootstrap_paired_ci(delta_vec)
        boot[label] = {"mean_cm": m, "ci95_lo_cm": lo, "ci95_hi_cm": hi}

    subset_table = {}
    for bname, mask in buckets.items():
        subset_table[bname] = {}
        base = ade_cm["PP"]
        for key in ("PP", "GP", "PG", "GG"):
            subset_table[bname][key] = subset_stats(ade_cm[key], mask, base)

    per_frame = {
        "traj_name": traj,
        "t": t_arr,
        "goal_time": goal_t,
        "strict_turn": strict_turn,
        "loose_turn": loose_turn,
        "ade_pp_cm": ade_cm["PP"],
        "ade_gp_cm": ade_cm["GP"],
        "ade_pg_cm": ade_cm["PG"],
        "ade_gg_cm": ade_cm["GG"],
        "nav_pp": pp_ref,
        "nav_gp": nav["GP"],
        "nav_pg": nav["PG"],
        "nav_gg": nav["GG"],
        "path_pp": oracle["PP"],
        "path_gp": oracle["GP"],
        "path_pg": oracle["PG"],
        "path_gg": oracle["GG"],
        "gt_actions": path_gt,
        "mu_units": mu,
        "meters_per_unit": meters,
    }
    np.savez_compressed(os.path.join(out_dir, "per_frame_diagnosis.npz"), **per_frame)

    out_meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": os.path.basename(__file__),
        "git_commit": git_commit_short(),
        "export_dir": export_dir,
        "export_meta_sha256": sha256_file(meta_path),
        "residual_export_sha256": sha256_file(npz_path),
        "eval_command": eval_cmd,
        "seed": args.seed,
        "num_samples": args.num_samples,
        "batch_size": args.batch_size,
        "shared_noise": True,
        "near_zero_m": NEAR_ZERO_M,
        "oracle_skip_points": {
            "GP_kept_pred_because_gt_direction_undefined": oracle["gp_direction_undefined_points"],
            "PG_kept_pred_because_pred_direction_undefined": oracle["pg_direction_undefined_points"],
        },
        "checkpoint_hashes": meta_export.get("files", {}),
        "mean_ade_cm": {k: float(ade_cm[k].mean()) for k in ade_cm},
        "pp_vs_export_nav_max_abs_diff": max_diff,
        "export_mean_ade_edino_cm": meta_export.get("mean_ade_edino_cm"),
        "this_round_pp_cm": mean_pp,
        "main_table": rows,
        "decomposition": decomp,
        "bootstrap_paired_n": BOOT_N,
        "bootstrap_seed": BOOT_SEED,
        "bootstrap": boot,
        "subsets": subset_table,
        "score_definition": meta_export.get("score_definition"),
        "note_oracle": (
            "Oracle path input swaps for diagnosis only; not deployable gain. "
            "PP is this-round baseline with shared-noise 4-condition protocol."
        ),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(out_meta, f, indent=2, ensure_ascii=False)

    lines = []
    lines.append("# Local 8-point path direction × distance (locked far 1000)\n")
    lines.append(f"- Round PP baseline: **{mean_pp:.2f} cm** (do not merge with other noise draws)\n")
    lines.append(f"- PP vs export nav_pred_samples max |diff|: {max_diff:.3e}\n")
    lines.append(
        f"- GP/PG points kept at pred (undefined dir): GP={oracle['gp_direction_undefined_points']}, "
        f"PG={oracle['pg_direction_undefined_points']} / {oracle['total_points']}\n\n"
    )
    lines.append("## Main table\n\n")
    lines.append("| 条件 | 路径方向来源 | 路径距离来源 | ADE (cm) | Δ vs 本轮PP (cm) |\n")
    lines.append("|---|---|---|---:|---:|\n")
    for r in rows:
        lines.append(
            f"| {r['condition']} | {r['path_direction_source']} | {r['path_distance_source']} | "
            f"{r['ade_cm']:.2f} | {r['delta_vs_pp_cm']:+.2f} |\n"
        )
    lines.append("\n## Decomposition (cm)\n\n")
    for k, v in decomp.items():
        if k != "interaction_formula":
            lines.append(f"- {k}: {v:+.3f}\n")
    lines.append(f"- {decomp['interaction_formula']}\n\n")
    lines.append("## Bootstrap 95% CI (paired frame, cm)\n\n")
    for label, b in boot.items():
        lines.append(f"- {label}: {b['mean_cm']:+.3f} [{b['ci95_lo_cm']:+.3f}, {b['ci95_hi_cm']:+.3f}]\n")
    lines.append("\n## Subsets (ADE cm / Δ vs PP cm)\n\n")
    for bname in ("all", "strict_turn", "strict_straight", "middle"):
        lines.append(f"### {bname}\n\n")
        for key in ("PP", "GP", "PG", "GG"):
            s = subset_table[bname][key]
            lines.append(f"- {key}: n={s['n']} ade={s['ade_cm']:.2f} Δ={s['delta_vs_pp_cm']:+.2f}\n")
        lines.append("\n")
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(json.dumps({"mean_pp_cm": mean_pp, "rows": rows, "decomp": decomp, "max_diff_pp": max_diff}, indent=2))


if __name__ == "__main__":
    main()
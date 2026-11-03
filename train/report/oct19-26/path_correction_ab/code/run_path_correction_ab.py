"""Prepare path correction A/B experiment: stats, checks, config (does not train)."""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys

import cv2  # noqa: F401

from eval_by_distance import load_config
# path_correction_ab imported by check script only
from train_goal_dino import CACHE_DIR, DFT_VAL_LIST, build_pairs, load_cache

PY = (
    r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
    if os.path.isfile(r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe")
    else sys.executable
)
CWD = os.path.dirname(os.path.abspath(__file__))
INIT = os.path.join(CWD, "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth")
OUT = os.path.join(CWD, "logs/revalidation/path_correction_radial_dir_ab")
E_RUN = os.path.join(CWD, "logs/nomad/nomad_e_ft_pathact8")
FRAMES_LOCKED = os.path.join(CWD, "logs/revalidation/eval_audit_pathact8_far/paired_frames_far_20-40.csv")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def count_train_stats():
    config = load_config(os.path.join(CWD, "config/nomad_b40.yaml"))
    cache_path, rows, meta = load_cache(CACHE_DIR, "train")
    with open(os.path.join(CWD, DFT_VAL_LIST)) as f:
        val_trajs = {line.strip() for line in f if line.strip()}
    train_pairs = build_pairs(
        config,
        "train",
        rows,
        lambda t: t not in val_trajs,
        0.0,
        2,
        "endpoint",
        (),
        False,
        None,
        0,
        8,
        0,
    )
    n_frames = len(train_pairs["starts"])
    batch = 128
    epochs = 8
    steps = math.ceil(n_frames / batch)
    return {
        "train_endpoint_frames": n_frames,
        "batch_size": batch,
        "epochs": epochs,
        "batches_per_epoch": steps,
        "total_optimizer_steps_per_group": steps * epochs,
        "correction_trainable_params_each": 256 * 128 + 128 + 128 * 8 + 8,
        "val_trajectories": len(val_trajs),
        "cache_flip": meta.get("flip"),
    }


def py_env():
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    return env


def main():
    os.makedirs(OUT, exist_ok=True)
    stats = count_train_stats()
    init_sha = sha256_file(INIT) if os.path.isfile(INIT) else "MISSING"

    check_out = os.path.join(OUT, "consistency_checks.json")
    cmd_check = [PY, "-u", os.path.join(CWD, "check_path_correction_ab.py"), "--init", INIT, "--out", check_out]
    print("+", " ".join(cmd_check), flush=True)
    subprocess.run(cmd_check, cwd=CWD, check=True, env=py_env())

    with open(check_out, encoding="utf-8") as f:
        checks = json.load(f)

    train_common = [
        PY,
        "-u",
        "train_path_correction_ab.py",
        "--init",
        INIT,
        "--batch-size",
        "128",
        "--epochs",
        "8",
        "--seed",
        "0",
        "--max-batches",
        "0",
        "--lr",
        "1e-4",
        "--weight-decay",
        "0.05",
        "--context",
        "2",
        "--path-steps",
        "8",
    ]

    cmd_a = train_common + ["--correction-mode", "dist", "--run-name", "nomad_dino_wp_pathcorr_dist"]
    cmd_b = train_common + ["--correction-mode", "dir", "--run-name", "nomad_dino_wp_pathcorr_dir"]

    md = []
    md.append("# Path correction A/B (frozen pathact8)\n\n")
    md.append("## Hypothesis / prior\n\n")
    md.append(
        "Locked Oracle: local **direction** swap ~4.39 cm vs **distance** ~1.42 cm (upper bound only).\n\n"
    )
    md.append("## Frozen stack\n\n")
    md.append("| Module | Status |\n|---|---|\n")
    md.append("| DINOv2 token cache (inputs) | frozen (precomputed) |\n")
    md.append("| `PairTokenHead.proj/encoder/norm` | frozen |\n")
    md.append("| `PairTokenHead.out` (dir/κ) | frozen |\n")
    md.append("| `PairTokenHead.path_head` (Linear 256→16) | frozen, always `eval()` |\n")
    md.append("| Correction MLP | **trainable** (only params with grad) |\n")
    md.append("| Diffusion E / B | not loaded in this train script |\n\n")

    md.append("## Feature tap (correction input)\n\n")
    md.append(
        "Tensor **`path_in`** = `PairTokenHead._path_feat(x, feat, odom)` immediately before `path_head`.\n"
        "For pathact8 checkpoint: **256-d CLS** (`feat = norm(encoder CLS)`) — same as `path_head.weight` in_features.\n"
        "Not endpoint μ, not GT path, not diffusion cond.\n\n"
    )

    md.append("## Branches (zero-init ⇒ identity)\n\n")
    md.append("| Group | Param | Update |\n|---|---|---|\n")
    md.append("| **A dist** | `s_k = MLP(path_in)_k` | `p_k = exp(s_k) * p_base_k` |\n")
    md.append("| **B dir** | `θ_k = MLP(path_in)_k` (rad) | `p_k = R(θ_k) p_base_k` |\n\n")
    md.append("Shared MLP: Linear(D,128)→GELU→Linear(128,8); **no dropout**; last layer 0-init.\n\n")

    md.append("## Training (identical except `--correction-mode`)\n\n")
    md.append(f"- Init: `{INIT}` sha256=`{init_sha}`\n")
    md.append(f"- Train endpoint frames: **{stats['train_endpoint_frames']}**\n")
    md.append(f"- Batches/epoch: **{stats['batches_per_epoch']}** (= ceil(frames/128))\n")
    md.append(f"- Updates/group (8 ep): **{stats['total_optimizer_steps_per_group']}**\n")
    md.append(f"- Trainable params/group: **{stats['correction_trainable_params_each']}**\n")
    md.append("- Loss: SmoothL1 on 8 (x,y) vs GT, β=1.0, dataset units; mean over K and xy\n")
    md.append("- Sample weight: `steps / FAR_STEPS` (same as path term in `train_goal_dino`, no extra turn/tail weights)\n")
    md.append("- Optim: AdamW lr=1e-4 wd=0.05; grad clip 1.0; warmup 1 epoch linear then cosine\n")
    md.append("- Select **`dino_dir_best.pth` by lowest val far path ADE** (`far_path_ade_cm`)\n\n")

    md.append("### Commands (not auto-run)\n\n")
    md.append("```powershell\n")
    md.append(f"cd {CWD}\n")
    md.append("$env:PYTHONPATH=\"../diffusion_policy\"\n")
    md.append("# A — distance correction\n")
    md.append(" ".join(str(x) for x in cmd_a) + "\n")
    md.append("# B — direction correction\n")
    md.append(" ".join(str(x) for x in cmd_b) + "\n")
    md.append("```\n\n")

    md.append("## Consistency checks\n\n")
    md.append(f"- Report: `{os.path.relpath(check_out, CWD)}`\n")
    md.append(f"- All passed: **{checks.get('ok')}**\n\n")

    md.append("## Downstream nav eval (prepare only — two protocols)\n\n")
    md.append(
        "Use frozen E checkpoint `logs/nomad/nomad_e_ft_pathact8/ema_latest.pth`, "
        "locked CSV `paired_frames_far_20-40.csv`, num_samples=8, batch_size=8, seed=0, **shared noise** across models.\n\n"
    )
    md.append("### Protocol 1 — fixed μ, swap 16-d path only\n\n")
    md.append(
        "Keep exported **`mu_units`** from baseline; build `e_dino_pos = concat(mu, flat(corrected_path))`. "
        "Does not recompute κ-blend from WP/DINO.\n\n"
    )
    md.append("```powershell\n")
    md.append("# After training — placeholder entrypoint (to implement before running locked1000):\n")
    md.append("python eval_path_correction_locked_nav.py \\\n")
    md.append("  --mode fixed_mu \\\n")
    md.append("  --wp-base logs/nomad_d/.../pathact8/dino_dir_best.pth \\\n")
    md.append("  --wp-corr-a logs/nomad_d/nomad_dino_wp_pathcorr_dist_*/dino_dir_best.pth \\\n")
    md.append("  --wp-corr-b logs/nomad_d/nomad_dino_wp_pathcorr_dir_*/dino_dir_best.pth \\\n")
    md.append(f"  --e-run {os.path.relpath(E_RUN, CWD)} \\\n")
    md.append(f"  --frames {os.path.relpath(FRAMES_LOCKED, CWD)} \\\n")
    md.append("  --seed 0 --num-samples 8 --batch-size 8\n")
    md.append("```\n\n")

    md.append("### Protocol 2 — full deploy (κ from corrected path endpoint dir)\n\n")
    md.append(
        "Recompute blend μ via existing `blend()` using **corrected path last-point direction** "
        "(κ from frozen dir heads — **not recalibrated**; document κ source in run meta).\n\n"
    )
    md.append("```powershell\n")
    md.append("python eval_path_correction_locked_nav.py \\\n")
    md.append("  --mode deploy_blend \\\n")
    md.append("  --goal-pos-mode blend_path --path-source wp_poly \\\n")
    md.append("  ... (same wp/e/frames/seed/noise flags as protocol 1)\n")
    md.append("```\n\n")

    md.append("## Success criteria (later)\n\n")
    md.append("- Val path ADE improves vs frozen base on far + turn buckets\n")
    md.append("- Locked1000 **path quality and nav ADE** both improve under each protocol\n")
    md.append("- Do not claim win from train loss alone\n")

    cfg_path = os.path.join(OUT, "experiment_config.md")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(md)

    bundle = {
        "stats": stats,
        "init_sha256": init_sha,
        "checks_ok": checks.get("ok"),
        "checks": checks,
        "train_commands": {"A_dist": cmd_a, "B_dir": cmd_b},
    }
    with open(os.path.join(OUT, "setup_summary.json"), "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(json.dumps(bundle, indent=2))
    print("wrote", cfg_path)


if __name__ == "__main__":
    main()

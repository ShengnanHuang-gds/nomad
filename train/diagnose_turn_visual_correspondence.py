"""Val-set diagnostic: turn severity vs 8-step path error vs cross-frame DINO patch matching.



No training, no nav diffusion. Uses frozen pathact8 ctx2 checkpoint + train-split DINO cache.

"""

from __future__ import annotations



import argparse

import csv

import json

import os

import pickle

import subprocess

import sys

from dataclasses import dataclass

from datetime import datetime, timezone

from pathlib import Path



import cv2  # noqa: F401

import matplotlib.pyplot as plt

import numpy as np

import torch

from PIL import Image



from eval_by_distance import load_config

from eval_e_dino import head_predict_wp_path

from train_e_dino import load_dino_head, read_tokens

from train_goal_dino import (

    CACHE_DIR,

    DFT_VAL_LIST,

    MAX_STEPS,

    MIN_STEPS,

    frame_turn_strict,

    go_stanford_meters_per_unit,

    load_cache,

    path_winding_deg,

)

from turn_match_viz import (
    draw_cross_image_lines,
    select_curr_patches_for_display,
    similarity_hist_curr,
)
from vint_train.data.data_utils import IMAGE_ASPECT_RATIO, get_data_path



DEFAULT_WP = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"

OUT_ROOT = "logs/revalidation/turn_visual_correspondence_val200"

SAMPLE_SEED = 20261103

CONTEXT = 2

PATCH_GW = 8

PATCH_GH = 6





def git_short():

    try:

        return (

            subprocess.check_output(

                ["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parent, stderr=subprocess.DEVNULL

            )

            .decode()

            .strip()

        )

    except (subprocess.CalledProcessError, FileNotFoundError):

        return "unknown"





def load_index(config, split="train"):

    data_config = config["datasets"]["go_stanford"]

    index_path = os.path.join(

        data_config[split],

        f"dataset_dist_{config['distance']['min_dist_cat']}_to_{config['distance']['max_dist_cat']}"

        f"_context_{config.get('context_type', 'temporal')}_n{config['context_size']}"

        f"_slack_{data_config.get('end_slack', 0)}_pred_{config['len_traj_pred']}.pkl",

    )

    with open(index_path, "rb") as f:

        index_to_data, _goals = pickle.load(f)

    by_traj = {}

    for traj_name, curr, max_goal in index_to_data:

        by_traj.setdefault(traj_name, []).append((int(curr), int(max_goal)))

    return by_traj





def gt_path_8(traj, curr, spacing, path_steps, meters_per_unit, min_goal_m=0.3):

    pos = np.asarray(traj["position"], dtype=np.float64).reshape(-1, 2)

    yaw = traj["yaw"]

    curr = int(curr)

    y0 = float(np.ravel(yaw[curr])[0])

    c, s = np.cos(y0), np.sin(y0)

    pts = []

    for st in range(1, path_steps + 1):

        gi = min(curr + st * spacing, len(pos) - 1)

        d = pos[gi] - pos[curr]

        local = np.array([d[0] * c + d[1] * s, -d[0] * s + d[1] * c], dtype=np.float32)

        pts.append(local / max(meters_per_unit, 1e-6))

    path = np.stack(pts, axis=0)

    end = path[-1] * meters_per_unit

    if float(np.linalg.norm(end)) < min_goal_m:

        return None

    return path





def path_length_m(path_ds, meters_per_unit):

    d = np.diff(path_ds, axis=0) * meters_per_unit

    return float(np.linalg.norm(d, axis=1).sum())





def path_ade_cm(pred, gt, meters):

    return float(np.linalg.norm(pred - gt, axis=-1).mean() * meters * 100.0)





def path_ade_parts(pred, gt, meters):

    k = pred.shape[0] // 2

    return path_ade_cm(pred[:k], gt[:k], meters), path_ade_cm(pred[k:], gt[k:], meters)





def dir_err_deg(pred, gt):

    def u(v):

        n = np.linalg.norm(v)

        return v / max(n, 1e-6)



    return float(np.degrees(np.arccos(np.clip(float(u(pred[-1]) @ u(gt[-1])), -1.0, 1.0))))





def turn_group(winding_deg):

    if winding_deg < 30.0:

        return "straight"

    if winding_deg < 45.0:

        return "moderate_turn"

    return "sharp_turn"





def load_rgb_crop(data_folder, traj, t, size=(224, 168)):

    img = Image.open(get_data_path(data_folder, traj, t)).convert("RGB")

    w, h = img.size

    if w > h:

        img = img.crop(((w - int(h * IMAGE_ASPECT_RATIO)) // 2, 0, (w + int(h * IMAGE_ASPECT_RATIO)) // 2, h))

    img = img.resize(size, Image.BICUBIC)

    return np.asarray(img)





def patch_grid(tokens_row):

    """tokens_row: [49, dim] -> normalized patch vectors [48, dim] and 6x8 grid."""

    p = np.asarray(tokens_row[1:], dtype=np.float32)

    n = np.linalg.norm(p, axis=1, keepdims=True)

    p = p / np.maximum(n, 1e-6)

    return p, p.reshape(PATCH_GH, PATCH_GW, -1)





def cross_frame_match_metrics(patches_hist, patches_curr):

    """Descriptive NN cosine stats (not 'overlap rate'). patches: [48, d]."""

    sim = patches_hist @ patches_curr.T

    hist_to_curr = sim.max(axis=1)

    curr_to_hist = sim.max(axis=0)

    return {

        "hist_to_curr_mean_max_cos": float(hist_to_curr.mean()),

        "hist_to_curr_median_max_cos": float(np.median(hist_to_curr)),

        "curr_to_hist_mean_max_cos": float(curr_to_hist.mean()),

        "curr_to_hist_median_max_cos": float(np.median(curr_to_hist)),

        "mutual_mean_max_cos": float(0.5 * (hist_to_curr.mean() + curr_to_hist.mean())),

    }





@dataclass

class FrameRec:

    traj: str

    t: int

    t_hist_near: int

    t_hist_far: int

    goal_t: int

    winding_deg: float

    turn_strict: bool

    turn_group: str

    gt_path_len_m: float

    path_ade_cm: float

    path_ade_front4_cm: float

    path_ade_back4_cm: float

    dir_err_deg: float

    match_near: dict

    match_far: dict





def enumerate_val_candidates(config, rows, val_trajs, path_steps=8, min_goal_m=0.3):

    data_config = config["datasets"]["go_stanford"]

    data_folder = data_config["data_folder"]

    spacing = int(data_config.get("waypoint_spacing", 1))

    horizon = int(config["len_traj_pred"])

    mpu = float(go_stanford_meters_per_unit(config))

    by_traj = load_index(config, "train")

    out = []

    for traj_name in sorted(val_trajs):

        if traj_name not in by_traj:

            continue

        with open(os.path.join(data_folder, traj_name, "traj_data.pkl"), "rb") as f:

            traj = pickle.load(f)

        for curr, max_goal in by_traj[traj_name]:

            if curr - CONTEXT < 0:

                continue

            keys_needed = [(traj_name, curr - j) for j in range(0, CONTEXT + 1)]

            goal_k = min(MAX_STEPS, max_goal)

            goal_t = curr + goal_k

            keys_needed.append((traj_name, goal_t))

            if any(k not in rows for k in keys_needed):

                continue

            gt = gt_path_8(traj, curr, spacing, path_steps, mpu, min_goal_m)

            if gt is None:

                continue

            wind = float(path_winding_deg(traj, curr, spacing, horizon))

            strict = bool(frame_turn_strict(traj, curr, spacing, horizon, mpu))

            out.append(

                {

                    "traj": traj_name,

                    "t": curr,

                    "t_near": curr - 1,

                    "t_far": curr - 2,

                    "goal_t": goal_t,

                    "goal_k": goal_k,

                    "winding_deg": wind,

                    "turn_strict": strict,

                    "turn_group": turn_group(wind),

                    "gt_path": gt.astype(np.float32),

                    "gt_path_len_m": path_length_m(gt, mpu),

                }

            )

    return out, mpu, spacing, data_folder





def stratified_sample(candidates, n_max, seed):

    rng = np.random.default_rng(seed)

    by_group = {"straight": [], "moderate_turn": [], "sharp_turn": []}

    for c in candidates:

        by_group[c["turn_group"]].append(c)

    per = max(1, n_max // 3)

    picked = []

    used_traj_frames = {}



    def ok_traj(c):

        key = c["traj"]

        last = used_traj_frames.get(key, -10_000)

        if c["t"] - last < 15:

            return False

        return True



    for g in ("straight", "moderate_turn", "sharp_turn"):

        pool = by_group[g]

        rng.shuffle(pool)

        pool.sort(key=lambda x: x["winding_deg"])

        n_want = min(per, len(pool))

        if n_want == 0:

            continue

        idxs = np.linspace(0, len(pool) - 1, num=min(n_want * 3, len(pool)), dtype=int)

        for i in idxs:

            if len([p for p in picked if p["turn_group"] == g]) >= n_want:

                break

            c = pool[int(i)]

            if not ok_traj(c):

                continue

            picked.append(c)

            used_traj_frames[c["traj"]] = c["t"]

    if len(picked) < n_max:

        rest = [c for c in candidates if c not in picked]

        rng.shuffle(rest)

        for c in rest:

            if len(picked) >= n_max:

                break

            if ok_traj(c):

                picked.append(c)

                used_traj_frames[c["traj"]] = c["t"]

    return picked[:n_max]





def pick_viz_cases(records):

    sharp = [r for r in records if r.turn_group == "sharp_turn"]

    straight = [r for r in records if r.turn_group == "straight"]

    if not sharp:

        sharp = records

    sharp = sorted(sharp, key=lambda r: r.path_ade_cm)

    med = np.median([r.path_ade_cm for r in sharp])

    good = [r for r in sharp if r.path_ade_cm <= med]

    bad = [r for r in sharp if r.path_ade_cm > med]

    cases = []

    for bucket, tag, k in (

        (good, "sharp_good", 4),

        (bad, "sharp_bad", 4),

        (straight, "straight_ref", 3),

    ):

        bucket = sorted(bucket, key=lambda r: -r.winding_deg)

        cases.extend((r, f"{tag}_{i}") for i, r in enumerate(bucket[:k]))

    # counterexample: high mutual match, high ADE among sharp

    sharp_sorted = sorted(sharp, key=lambda r: r.match_near["mutual_mean_max_cos"], reverse=True)

    for r in sharp_sorted:

        if r.path_ade_cm >= med and r not in [c[0] for c in cases]:

            cases.append((r, "counter_high_match_high_ade"))

            break

    for r in sorted(sharp, key=lambda r: r.path_ade_cm, reverse=True):

        if r.match_near["mutual_mean_max_cos"] < np.percentile([x.match_near["mutual_mean_max_cos"] for x in sharp], 25):

            if r not in [c[0] for c in cases]:

                cases.append((r, "counter_low_match_high_ade"))

                break

    # dedupe

    seen = set()

    out = []

    for r, tag in cases:

        key = (r.traj, r.t)

        if key in seen:

            continue

        seen.add(key)

        out.append((r, tag))

    return out[:20]





def draw_case(rec, tag, data_folder, feats, rows, out_path):
    """Deprecated v1 stub lines + cross-image patch correspondence (v2 layout)."""
    display_seed = 20261103
    t_far, t_near, t_curr, t_goal = rec.t_hist_far, rec.t_hist_near, rec.t, rec.goal_t
    imgs = {
        "far": load_rgb_crop(data_folder, rec.traj, t_far),
        "near": load_rgb_crop(data_folder, rec.traj, t_near),
        "curr": load_rgb_crop(data_folder, rec.traj, t_curr),
        "goal": load_rgb_crop(data_folder, rec.traj, t_goal),
    }
    _, p_far = patch_grid(feats[rows[(rec.traj, t_far)]])
    _, p_near = patch_grid(feats[rows[(rec.traj, t_near)]])
    p_curr, _ = patch_grid(feats[rows[(rec.traj, t_curr)]])

    sim_near = similarity_hist_curr(p_near, p_curr)
    sim_far = similarity_hist_curr(p_far, p_curr)
    curr_show = select_curr_patches_for_display(seed=display_seed + rec.t)

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 4, height_ratios=[1.0, 1.05, 0.85])
    for col, (name, tt) in enumerate(
        [("far", t_far), ("near", t_near), ("curr", t_curr), ("goal", t_goal)]
    ):
        ax = fig.add_subplot(gs[0, col])
        ax.imshow(imgs[name])
        gap = tt - t_curr if name == "goal" else None
        title = f"{name} index={tt}"
        if gap is not None:
            title += f"\ngoal gap={gap} idx steps"
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    ax_old = fig.add_subplot(gs[1, 0])
    ax_old.imshow(imgs["curr"])
    h, w = imgs["curr"].shape[:2]
    cell_w, cell_h = w / PATCH_GW, h / PATCH_GH
    for gi in range(PATCH_GH):
        for gj in range(PATCH_GW):
            cx, cy = (gj + 0.5) * cell_w, (gi + 0.5) * cell_h
            ax_old.plot([cx, cx - 0.15 * w], [cy, cy], "c-", alpha=0.35, lw=0.8)
            ax_old.plot([cx, cx - 0.08 * w], [cy, cy - 0.05 * h], "y-", alpha=0.5, lw=0.8)
    ax_old.set_title(
        "DEPRECATED v1 overlay\n(fixed-length segments; NOT valid correspondence)",
        fontsize=8,
    )
    ax_old.axis("off")

    rule = (
        f"Show {len(curr_show)} curr patches: linspace over 48 cells + "
        f"rng seed {display_seed}+t; not ranked by match score."
    )
    for ax_col, (title, sim) in enumerate(
        [("t-2 | curr", sim_far), ("t-1 | curr", sim_near)], start=1
    ):
        ax_l = fig.add_subplot(gs[1, ax_col * 2 - 1])
        ax_r = fig.add_subplot(gs[1, ax_col * 2])
        hist_key = "far" if ax_col == 1 else "near"
        draw_cross_image_lines(
            ax_l, ax_r, imgs[hist_key], imgs["curr"], sim, curr_show, show_mutual=True
        )
        ax_l.set_title(title + "\n" + rule, fontsize=7)

    ax_note = fig.add_subplot(gs[1, 3])
    ax_note.axis("off")
    ax_note.text(
        0,
        1,
        "Match legend:\n"
        "- NOT overlap rate; lines are not model attention.\n"
        "- skyblue: curr->hist NN\n"
        "- lime: bidirectional consistent (mutual argmax)\n"
        "- legacy mutual_mean_max_cos = mean of two directional\n"
        "  mean-max cosines (v1 name); not mutual-pair rate.",
        va="top",
        fontsize=8,
    )

    axp = fig.add_subplot(gs[2, :2])
    gt = getattr(rec, "_gt", None)
    pred = getattr(rec, "_pred", None)
    if gt is not None and pred is not None:
        axp.plot(gt[:, 0], gt[:, 1], "k-o", label="GT 8-step", ms=4)
        axp.plot(pred[:, 0], pred[:, 1], "r-o", label="pred", ms=4)
        axp.axhline(0, color="gray", lw=0.5)
        axp.axvline(0, color="gray", lw=0.5)
        axp.set_aspect("equal")
        axp.legend(fontsize=8)
        axp.set_xlabel("dataset units (robot x)")
        axp.set_ylabel("dataset units (robot y)")
    axs = fig.add_subplot(gs[2, 2:])
    axs.axis("off")
    axs.text(
        0,
        1,
        f"{tag} | {rec.traj} t={rec.t}\n"
        f"pathADE={rec.path_ade_cm:.2f}cm | legacy mutual_near="
        f"{rec.match_near['mutual_mean_max_cos']:.3f} far="
        f"{rec.match_far['mutual_mean_max_cos']:.3f}\n"
        f"wind={rec.winding_deg:.1f} deg (future 8-step winding label)",
        va="top",
        fontsize=9,
        family="monospace",
    )

    fig.suptitle(f"Turn visual case — {tag}", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)



def analyze_trends(records):

    """Descriptive comparisons within similar turn + path length."""

    rows_out = {}

    sharp = [r for r in records if r.winding_deg >= 45.0]

    if len(sharp) >= 8:

        med_ade = np.median([r.path_ade_cm for r in sharp])

        good = [r for r in sharp if r.path_ade_cm <= med_ade]

        bad = [r for r in sharp if r.path_ade_cm > med_ade]

        for label, subset in (("sharp_good", good), ("sharp_bad", bad)):

            rows_out[label] = {

                "n": len(subset),

                "match_near_mutual_mean": float(np.mean([r.match_near["mutual_mean_max_cos"] for r in subset])),

                "match_far_mutual_mean": float(np.mean([r.match_far["mutual_mean_max_cos"] for r in subset])),

                "path_ade_cm_mean": float(np.mean([r.path_ade_cm for r in subset])),

                "gt_path_len_m_mean": float(np.mean([r.gt_path_len_m for r in subset])),

            }

        # length-matched within sharp: quartile bins

        lens = np.array([r.gt_path_len_m for r in sharp])

        q25, q75 = np.percentile(lens, [25, 75])

        mid = [r for r in sharp if q25 <= r.gt_path_len_m <= q75]

        if len(mid) >= 6:

            med = np.median([r.path_ade_cm for r in mid])

            g = [r for r in mid if r.path_ade_cm <= med]

            b = [r for r in mid if r.path_ade_cm > med]

            rows_out["sharp_midlen_good_vs_bad"] = {

                "good_n": len(g),

                "bad_n": len(b),

                "good_match_near": float(np.mean([r.match_near["mutual_mean_max_cos"] for r in g])) if g else float("nan"),

                "bad_match_near": float(np.mean([r.match_near["mutual_mean_max_cos"] for r in b])) if b else float("nan"),

            }

    near_mean = float(np.mean([r.match_near["mutual_mean_max_cos"] for r in records]))

    far_mean = float(np.mean([r.match_far["mutual_mean_max_cos"] for r in records]))

    rows_out["all_near_vs_far_mutual_mean"] = {"near": near_mean, "far": far_mean, "delta_near_minus_far": near_mean - far_mean}

    # counterexamples

    med_ade_all = np.median([r.path_ade_cm for r in records])

    high_ade = [r for r in records if r.path_ade_cm >= np.percentile([x.path_ade_cm for x in records], 75)]

    high_match = [r for r in high_ade if r.match_near["mutual_mean_max_cos"] >= np.median([x.match_near["mutual_mean_max_cos"] for x in records])]

    rows_out["counter_high_ade_with_median_or_higher_match"] = {

        "count": len(high_match),

        "of_high_ade": len(high_ade),

    }

    return rows_out





def main():

    ap = argparse.ArgumentParser(description=__doc__)

    ap.add_argument("--wp", default=DEFAULT_WP)

    ap.add_argument("--out-dir", default=OUT_ROOT)

    ap.add_argument("--max-frames", type=int, default=200)

    ap.add_argument("--seed", type=int, default=SAMPLE_SEED)

    ap.add_argument("--min-goal-m", type=float, default=0.3)

    args = ap.parse_args()



    out_dir = Path(args.out_dir)

    (out_dir / "cases").mkdir(parents=True, exist_ok=True)



    config = load_config("config/nomad_b40.yaml")

    cache_path, rows, meta = load_cache(CACHE_DIR, "train")

    feats = np.load(os.path.join(cache_path, "features.npy"), mmap_mode="r")

    with open(DFT_VAL_LIST, encoding="utf-8") as f:

        val_trajs = {line.strip() for line in f if line.strip()}



    candidates, meters, spacing, data_folder = enumerate_val_candidates(

        config, rows, val_trajs, path_steps=8, min_goal_m=args.min_goal_m

    )

    sample = stratified_sample(candidates, args.max_frames, args.seed)



    items = [(c["traj"], c["t"], c["goal_t"]) for c in sample]

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    head, ckpt_meta = load_dino_head(args.wp, device)

    _wd, _k, pred_paths = head_predict_wp_path(head, items, rows, feats, device)



    records = []

    for i, c in enumerate(sample):

        gt = c["gt_path"]

        pred = pred_paths[i].astype(np.float32)

        ade = path_ade_cm(pred, gt, meters)

        f4, b4 = path_ade_parts(pred, gt, meters)

        p_near, _ = patch_grid(feats[rows[(c["traj"], c["t_near"])]])

        p_far, _ = patch_grid(feats[rows[(c["traj"], c["t_far"])]])

        p_curr, _ = patch_grid(feats[rows[(c["traj"], c["t"])]])

        rec = FrameRec(

            traj=c["traj"],

            t=c["t"],

            t_hist_near=c["t_near"],

            t_hist_far=c["t_far"],

            goal_t=c["goal_t"],

            winding_deg=c["winding_deg"],

            turn_strict=c["turn_strict"],

            turn_group=c["turn_group"],

            gt_path_len_m=c["gt_path_len_m"],

            path_ade_cm=ade,

            path_ade_front4_cm=f4,

            path_ade_back4_cm=b4,

            dir_err_deg=dir_err_deg(pred, gt),

            match_near=cross_frame_match_metrics(p_near, p_curr),

            match_far=cross_frame_match_metrics(p_far, p_curr),

        )

        rec._gt = gt  # noqa: SLF001

        rec._pred = pred  # noqa: SLF001

        records.append(rec)



    csv_path = out_dir / "samples.csv"

    fieldnames = [

        "sample_id",

        "traj_name",

        "t",

        "t_hist_near",

        "t_hist_far",

        "goal_t",

        "turn_group",

        "winding_deg",

        "turn_strict",

        "gt_path_len_m",

        "path_ade_cm",

        "path_ade_front4_cm",

        "path_ade_back4_cm",

        "dir_err_deg",

        "match_near_mutual_mean_max_cos",

        "match_far_mutual_mean_max_cos",

        "match_near_hist_to_curr_mean",

        "match_far_hist_to_curr_mean",

    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:

        w = csv.DictWriter(cf, fieldnames=fieldnames)

        w.writeheader()

        for i, r in enumerate(records):

            w.writerow(

                {

                    "sample_id": i,

                    "traj_name": r.traj,

                    "t": r.t,

                    "t_hist_near": r.t_hist_near,

                    "t_hist_far": r.t_hist_far,

                    "goal_t": r.goal_t,

                    "turn_group": r.turn_group,

                    "winding_deg": f"{r.winding_deg:.3f}",

                    "turn_strict": int(r.turn_strict),

                    "gt_path_len_m": f"{r.gt_path_len_m:.4f}",

                    "path_ade_cm": f"{r.path_ade_cm:.4f}",

                    "path_ade_front4_cm": f"{r.path_ade_front4_cm:.4f}",

                    "path_ade_back4_cm": f"{r.path_ade_back4_cm:.4f}",

                    "dir_err_deg": f"{r.dir_err_deg:.3f}",

                    "match_near_mutual_mean_max_cos": f"{r.match_near['mutual_mean_max_cos']:.5f}",

                    "match_far_mutual_mean_max_cos": f"{r.match_far['mutual_mean_max_cos']:.5f}",

                    "match_near_hist_to_curr_mean": f"{r.match_near['hist_to_curr_mean_max_cos']:.5f}",

                    "match_far_hist_to_curr_mean": f"{r.match_far['hist_to_curr_mean_max_cos']:.5f}",

                }

            )



    trends = analyze_trends(records)

    viz = pick_viz_cases(records)

    for r, tag in viz:

        draw_case(r, tag, data_folder, feats, rows, out_dir / "cases" / f"{tag}_{r.traj}_t{r.t}.png")



    group_counts = {}

    traj_set = set()

    for r in records:

        group_counts[r.turn_group] = group_counts.get(r.turn_group, 0) + 1

        traj_set.add(r.traj)



    meta = {

        "timestamp_utc": datetime.now(timezone.utc).isoformat(),

        "git_commit": git_short(),

        "checkpoint": args.wp,

        "checkpoint_note": ckpt_meta,

        "dino_cache": cache_path,

        "dino_cache_meta": meta,

        "val_list": DFT_VAL_LIST,

        "sample_seed": args.seed,

        "max_frames": args.max_frames,

        "n_sampled": len(records),

        "n_trajectories": len(traj_set),

        "group_counts": group_counts,

        "sampling_rule": (

            "DFT val trajectories only; endpoint-style frames with ctx t-1,t-2; "

            "goal token at curr+min(39,max_goal); stratified ~1/3 straight/moderate/sharp by path_winding_deg; "

            "max 1 frame per traj per 15 index steps when possible."

        ),

        "match_metric_definitions": {

            "patch_tokens": "DINO cache tokens [1+48,384], 6x8 grid after pool=2; exclude CLS",

            "hist_to_curr_mean_max_cos": "mean over hist patches of max cosine to any curr patch",

            "curr_to_hist_mean_max_cos": "mean over curr patches of max cosine to any hist patch",

            "mutual_mean_max_cos": "average of the two directional means above",

            "not_overlap_rate": "These are descriptive NN similarities, not calibrated visible overlap.",

        },

        "descriptive_trends": trends,

    }

    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:

        json.dump(meta, f, indent=2)



    report = write_report(records, trends, meta, args)

    with open(out_dir / "REPORT.md", "w", encoding="utf-8") as f:

        f.write(report)

    print(report)

    print(f"wrote {out_dir}")





def write_report(records, trends, meta, args):

    lines = [

        "# Turn vs visual correspondence diagnostic (val, N≤200)",

        "",

        "## 代码事实",

        "",

        "- **历史帧**：ctx2 使用 **t−1** 与 **t−2**（数据集帧索引，一步一格；**未**按 `waypoint_spacing` 乘间隔）。",

        "  见 `train_goal_dino.build_pairs` / `eval_e_dino.head_predict_wp_path`（`curr-j`, j=1..context）。",

        "- **边界**：依赖 pickle 索引与 `context_size=3` 的 ViNT 索引；本脚本要求 `curr≥2` 且 cache 含对应 key，否则跳过。",

        "- **图像预处理**：与 `cache_dino_features.FrameImages` 一致——宽图中心裁 **4:3**，再 **224×168** BICUBIC，ImageNet 归一化后进 DINO；",

        "  本诊断读 **预缓存 tokens**（`logs/dino_cache/dinov2_vits14_reg/train/features.npy`）。",

        "- **八步头**：`PairTokenHead` 将 **curr / goal / 两帧 ctx** 的 DINO token（每帧 1 CLS + 6×8 patch）投影后加 `pos`/`kind`，",

        "  经 **4 层 TransformerEncoder** 自注意力混合；pathact8 的 8 点路径来自 **CLS 特征** 的 `path_head`（非 lcr 空间读出）。",

        "  **保留** patch 级 token 与网格位置；跨帧交互在 transformer 内完成，并非“无时序建模”。",

        f"- **Checkpoint**：`{args.wp}`（冻结推理，无训练）。",

        "",

        "## 抽样",

        "",

        f"- seed={args.seed}, n={len(records)}, trajectories={meta['n_trajectories']}, groups={meta['group_counts']}.",

        f"- {meta['sampling_rule']}",

        "",

        "## 观察结果（描述性）",

        "",

    ]

    if "sharp_good" in trends:

        sg, sb = trends["sharp_good"], trends["sharp_bad"]

        lines.append(

            f"- 急转弯子集（winding≥45°）按 path ADE 中位数分好/差："

            f"好组 mutual_match_near≈{sg['match_near_mutual_mean']:.3f} (n={sg['n']}), "

            f"差组≈{sb['match_near_mutual_mean']:.3f} (n={sb['n']}); "

            f"平均 path ADE {sg['path_ade_cm_mean']:.2f} vs {sb['path_ade_cm_mean']:.2f} cm。"

        )

    nvf = trends.get("all_near_vs_far_mutual_mean", {})

    lines.append(

        f"- 全体样本：**较近历史 t−1** 的平均 mutual NN cosine ≈ {nvf.get('near', float('nan')):.3f}，"

        f"**较远 t−2** ≈ {nvf.get('far', float('nan')):.3f}（差 {nvf.get('delta_near_minus_far', float('nan')):+.3f}）。"

    )

    ce = trends.get("counter_high_ade_with_median_or_higher_match", {})

    lines.append(

        f"- 高 path ADE（≥p75）且匹配度不低于全体中位数的样本：{ce.get('count', 0)}/{ce.get('of_high_ade', 0)}。"

    )

    lines.extend(

        [

            "",

            "## 研究推断（弱，非因果）",

            "",

            "- 若在相近转弯子集内“差预测”组的 patch NN 相似度系统性更低，则与“参照减少”**一致**，但也可由纹理重复、",

            "  运动模糊、遮挡或 **路径长度/动力学** 混淆；本批未做偏相关控制。",

            "- 若 t−1 一致高于 t−2，则支持“**较近历史**通常保留更多可匹配外观”，但不等于 overlap 率。",

            "",

            "## 尚不能判断",

            "",

            "- 不能证明视野重叠减少 **导致** 八步失败；样本≤200，未控 path length 的回归。",

            "- 不能推荐具体新结构；证据不足以在“改历史采样”与“加强已有 transformer 交互”之间下定论。",

            "",

            "## 问题简答",

            "",

        ]

    )

    q1 = "证据不一致或弱：见 sharp_good vs sharp_bad 与 midlen 子表（meta.json descriptive_trends）。"

    q2 = f"较近帧 t−1 的 mutual NN cosine 平均更高（Δ={nvf.get('delta_near_minus_far', float('nan')):+.3f}），符合“较近历史更易匹配”的描述趋势。"

    q3 = f"存在反例：至少 {ce.get('count', 0)} 个高 ADE 样本仍有不低于中位的匹配度（见 cases/counter_*）。"

    q4 = "证据不足，暂不优先二选一；若需工程试探，可先试 **历史采样/间距**（代价低），因 head 内已有 4 层跨 token 交互。"

    q5 = "样本有限，仅报告描述性趋势；见 `samples.csv` 与 `cases/`。"

    for i, ans in enumerate([q1, q2, q3, q4, q5], 1):

        lines.append(f"{i}. {ans}")

    lines.append("")

    lines.append("## 交付文件")

    lines.append("- `samples.csv`, `meta.json`, `cases/*.png`, 本报告。")

    return "\n".join(lines)





if __name__ == "__main__":

    main()


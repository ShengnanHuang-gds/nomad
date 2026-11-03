"""Cross-frame DINO patch matching and figure helpers for turn correspondence diagnostic."""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from vint_train.data.data_utils import IMAGE_ASPECT_RATIO, get_data_path

PATCH_GW = 8
PATCH_GH = 6


def load_rgb_crop(data_folder, traj, t, size=(224, 168)):
    img = Image.open(get_data_path(data_folder, traj, t)).convert("RGB")
    w, h = img.size
    if w > h:
        img = img.crop(((w - int(h * IMAGE_ASPECT_RATIO)) // 2, 0, (w + int(h * IMAGE_ASPECT_RATIO)) // 2, h))
    img = img.resize(size, Image.BICUBIC)
    return np.asarray(img)


def patch_grid(tokens_row):
    p = np.asarray(tokens_row[1:], dtype=np.float32)
    p = p / np.maximum(np.linalg.norm(p, axis=1, keepdims=True), 1e-6)
    return p, p.reshape(PATCH_GH, PATCH_GW, -1)


def similarity_hist_curr(patches_hist, patches_curr):
    return patches_hist @ patches_curr.T


def nn_hist_to_curr(sim):
    return sim.argmax(axis=0)


def nn_curr_to_hist(sim):
    return sim.argmax(axis=1)


def mutual_consistent_pairs(sim):
    nn_c2h = nn_curr_to_hist(sim)
    nn_h2c = nn_hist_to_curr(sim)
    out = []
    for c in range(sim.shape[1]):
        h = int(nn_c2h[c])
        if int(nn_h2c[h]) == c:
            out.append((h, c, float(sim[h, c])))
    return out


def legacy_bidirectional_mean_max(sim):
    h2c = sim.max(axis=1)
    c2h = sim.max(axis=0)
    return {
        "hist_to_curr_mean_max_cos": float(h2c.mean()),
        "curr_to_hist_mean_max_cos": float(c2h.mean()),
        "legacy_mutual_mean_max_cos": float(0.5 * (h2c.mean() + c2h.mean())),
    }


def bidirectional_consistent_stats(sim):
    pairs = mutual_consistent_pairs(sim)
    if not pairs:
        return {"n_consistent": 0, "mean_consistent_cos": float("nan")}
    cos = [p[2] for p in pairs]
    return {"n_consistent": len(pairs), "mean_consistent_cos": float(np.mean(cos))}


def patch_center_xy(patch_index, img_w, img_h):
    gj = patch_index % PATCH_GW
    gi = patch_index // PATCH_GW
    cell_w, cell_h = img_w / PATCH_GW, img_h / PATCH_GH
    return (gj + 0.5) * cell_w, (gi + 0.5) * cell_h


def select_curr_patches_for_display(n_patches=48, max_lines=10, seed=0):
    """Deterministic display set: evenly spaced curr patch indices (not similarity-ranked)."""
    rng = np.random.default_rng(seed)
    evenly = np.unique(np.linspace(0, n_patches - 1, num=min(max_lines, n_patches), dtype=int))
    if len(evenly) < max_lines:
        extra = rng.choice(n_patches, size=max_lines - len(evenly), replace=False)
        evenly = np.unique(np.concatenate([evenly, extra]))
    return sorted(evenly.tolist())[:max_lines]


def draw_cross_image_lines(ax_left, ax_right, img_left, img_right, sim, curr_indices, show_mutual=True):
    ax_left.imshow(img_left)
    ax_right.imshow(img_right)
    ax_left.axis("off")
    ax_right.axis("off")
    h, w = img_left.shape[:2]
    nn_h = nn_curr_to_hist(sim)
    mutual = {c for h, c, _ in mutual_consistent_pairs(sim)}
    for c in curr_indices:
        h_idx = int(nn_h[c])
        x0, y0 = patch_center_xy(c, w, h)
        x1, y1 = patch_center_xy(h_idx, w, h)
        color = "lime" if (show_mutual and c in mutual) else "deepskyblue"
        ax_left.plot([x0, w + x1], [y0, y1], color=color, lw=0.9, alpha=0.85)
    ax_right.imshow(img_right)
    for c in curr_indices:
        h_idx = int(nn_h[c])
        x1, y1 = patch_center_xy(h_idx, w, h)
        ax_right.plot(x1, y1, "o", color="white", ms=2)


def parse_case_stem(stem: str):
    base, tstr = stem.rsplit("_t", 1)
    t = int(tstr)
    for p in ("counter_high_match_high_ade", "counter_low_match_high_ade"):
        if base.startswith(p + "_"):
            return p, base[len(p) + 1 :], t
    m = re.match(r"^(sharp_good|sharp_bad|straight_ref)_\d+_(.+)$", base)
    if not m:
        raise ValueError(stem)
    return m.group(1), m.group(2), t


def list_v1_cases(cases_dir: Path):
    out = []
    for f in sorted(cases_dir.glob("*.png")):
        tag, traj, t = parse_case_stem(f.stem)
        out.append({"tag": tag, "traj": traj, "t": t, "v1_png": str(f)})
    return out

"""Cross-frame DINO patch matching (S[h,c] = cos(hist h, curr c)) and figure helpers."""

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
        img = img.crop(
            ((w - int(h * IMAGE_ASPECT_RATIO)) // 2, 0, (w + int(h * IMAGE_ASPECT_RATIO)) // 2, h)
        )
    img = img.resize(size, Image.BICUBIC)
    return np.asarray(img)


def patch_grid(tokens_row):
    p = np.asarray(tokens_row[1:], dtype=np.float32)
    p = p / np.maximum(np.linalg.norm(p, axis=1, keepdims=True), 1e-6)
    return p, p.reshape(PATCH_GH, PATCH_GW, -1)


def similarity_hist_curr(patches_hist, patches_curr):
    """Return S with shape (n_hist, n_curr), S[h,c] = cosine(hist h, curr c)."""
    return patches_hist @ patches_curr.T


def hist_to_curr_nn(sim: np.ndarray) -> np.ndarray:
    """For each hist row h, argmax over c. Shape (n_hist,)."""
    return sim.argmax(axis=1)


def curr_to_hist_nn(sim: np.ndarray) -> np.ndarray:
    """For each curr column c, argmax over h. Shape (n_curr,)."""
    return sim.argmax(axis=0)


# Backward-compatible aliases (deprecated names; semantics fixed in v3)
def nn_hist_to_curr(sim):
    return hist_to_curr_nn(sim)


def nn_curr_to_hist(sim):
    return curr_to_hist_nn(sim)


def mutual_consistent_pairs(sim: np.ndarray):
    """Return list of (h, c, S[h,c]) with c = hist_to_curr[h] and h = curr_to_hist[c]."""
    h2c = hist_to_curr_nn(sim)
    c2h = curr_to_hist_nn(sim)
    out = []
    for h in range(sim.shape[0]):
        c = int(h2c[h])
        if int(c2h[c]) == h:
            out.append((h, c, float(sim[h, c])))
    return out


def legacy_bidirectional_mean_max(sim):
    h2c_max = sim.max(axis=1)
    c2h_max = sim.max(axis=0)
    return {
        "hist_to_curr_mean_max_cos": float(h2c_max.mean()),
        "curr_to_hist_mean_max_cos": float(c2h_max.mean()),
        "legacy_mutual_mean_max_cos": float(0.5 * (h2c_max.mean() + c2h_max.mean())),
    }


def bidirectional_consistent_stats(sim):
    pairs = mutual_consistent_pairs(sim)
    if not pairs:
        return {"n_consistent": 0, "mean_consistent_cos": float("nan")}
    cos = [p[2] for p in pairs]
    return {"n_consistent": len(pairs), "mean_consistent_cos": float(np.mean(cos))}


def patch_center_xy(patch_index, img_w, img_h, x_offset=0.0):
    gj = patch_index % PATCH_GW
    gi = patch_index // PATCH_GW
    cell_w, cell_h = img_w / PATCH_GW, img_h / PATCH_GH
    return x_offset + (gj + 0.5) * cell_w, (gi + 0.5) * cell_h


def select_curr_patches_for_display(n_patches=48, max_lines=10, seed=0):
    """Deterministic display set: evenly spaced curr patch indices (not similarity-ranked)."""
    rng = np.random.default_rng(seed)
    evenly = np.unique(
        np.linspace(0, n_patches - 1, num=min(max_lines, n_patches), dtype=int)
    )
    if len(evenly) < max_lines:
        extra = rng.choice(n_patches, size=max_lines - len(evenly), replace=False)
        evenly = np.unique(np.concatenate([evenly, extra]))
    return sorted(evenly.tolist())[:max_lines]


def draw_cross_image_lines(ax, img_hist, img_curr, sim, curr_indices, show_mutual=True):
    """Side-by-side hist (left) | curr (right) with lines h->c using true patch centers."""
    h_img, w = img_hist.shape[:2]
    ax.set_xlim(0, w * 2)
    ax.set_ylim(h_img, 0)
    ax.imshow(img_hist, extent=(0, w, h_img, 0))
    ax.imshow(img_curr, extent=(w, 2 * w, h_img, 0))
    c2h = curr_to_hist_nn(sim)
    mutual_c = {c for _h, c, _ in mutual_consistent_pairs(sim)}
    for c in curr_indices:
        h_idx = int(c2h[c])
        x_h, y_h = patch_center_xy(h_idx, w, h_img, x_offset=0.0)
        x_c, y_c = patch_center_xy(c, w, h_img, x_offset=w)
        color = "lime" if (show_mutual and c in mutual_c) else "deepskyblue"
        ax.plot([x_h, x_c], [y_h, y_c], color=color, lw=0.9, alpha=0.85)
    ax.axis("off")


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
        if "_v2" in f.stem or "DEPRECATED" in f.stem:
            continue
        tag, traj, t = parse_case_stem(f.stem)
        out.append({"tag": tag, "traj": traj, "t": t, "v1_png": str(f)})
    return out

"""Cache frozen DINOv2 tokens for every GoStanford frame of one split.

Each 160x120 jpg is center-cropped to 4:3 (a no-op here), resized to
--width x --height (multiples of 14), ImageNet-normalized and passed through
DINOv2. Per frame we keep the CLS token plus the patch grid average-pooled by
--pool, stored as float16 in features.npy [N, 1 + tokens, dim]. With --flip a
second array features_flip.npy holds the same for the horizontally mirrored
image, so the head can train with mirror augmentation (bearing y -> -y).

--frames-only restricts the test split to the locked paired frames (current
frame, its context_size past frames and every goal frame), which is all the
evaluation needs.

Run from train/:
    python -u cache_dino_features.py --split train --flip
    python -u cache_dino_features.py --split test --frames-only
"""

import argparse
import json
import os
import pickle

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES
from vint_train.data.data_utils import IMAGE_ASPECT_RATIO, get_data_path

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
CACHE_ROOT = "logs/dino_cache"


class FrameImages(Dataset):
    def __init__(self, data_folder, keys, size):
        self.data_folder = data_folder
        self.keys = keys
        self.size = size
        self.mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
        self.std = torch.tensor(IMAGENET_STD).view(3, 1, 1)

    def __len__(self):
        return len(self.keys)

    def __getitem__(self, i):
        traj_name, t = self.keys[i]
        img = Image.open(get_data_path(self.data_folder, traj_name, t)).convert("RGB")
        w, h = img.size
        if w > h:
            img = img.crop(((w - int(h * IMAGE_ASPECT_RATIO)) // 2, 0, (w + int(h * IMAGE_ASPECT_RATIO)) // 2, h))
        img = img.resize(self.size, Image.BICUBIC)
        x = torch.from_numpy(np.asarray(img, dtype=np.float32) / 255.0).permute(2, 0, 1)
        return (x - self.mean) / self.std


def split_keys(config, split):
    data_config = config["datasets"]["go_stanford"]
    with open(os.path.join(data_config[split], "traj_names.txt")) as f:
        traj_names = [line.strip() for line in f if line.strip()]
    keys = []
    for traj_name in traj_names:
        with open(os.path.join(data_config["data_folder"], traj_name, "traj_data.pkl"), "rb") as f:
            n = len(pickle.load(f)["position"])
        keys += [(traj_name, t) for t in range(n)]
    return keys


def paired_keys(path, context):
    keys = set()
    for traj_name, t, goals in load_paired_frames(path):
        keys.update((traj_name, t - j) for j in range(context + 1))
        keys.update((traj_name, g[4]) for g in goals)
    return sorted(keys)


@torch.no_grad()
def tokens(model, x, pool):
    out = model.forward_features(x)
    cls = out["x_norm_clstoken"][:, None]
    patches = out["x_norm_patchtokens"]
    b, _n, d = patches.shape
    gh, gw = x.shape[2] // 14, x.shape[3] // 14
    grid = patches.transpose(1, 2).reshape(b, d, gh, gw)
    grid = F.avg_pool2d(grid, pool).flatten(2).transpose(1, 2)
    return torch.cat([cls, grid], dim=1)


def main():
    parser = argparse.ArgumentParser(description="Cache frozen DINOv2 tokens per frame")
    parser.add_argument("--config", default="config/nomad_b40.yaml")
    parser.add_argument("--split", choices=("train", "test"), required=True)
    parser.add_argument("--model", default="dinov2_vits14_reg")
    parser.add_argument("--width", type=int, default=224)
    parser.add_argument("--height", type=int, default=168)
    parser.add_argument("--pool", type=int, default=2)
    parser.add_argument("--flip", action="store_true")
    parser.add_argument("--frames-only", action="store_true", help="Only the locked paired frames")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--cache-root", default=CACHE_ROOT)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--num-workers", type=int, default=4)
    args = parser.parse_args()
    if args.width % 14 or args.height % 14:
        raise ValueError("--width and --height must be multiples of 14")

    config = load_config(args.config)
    keys = paired_keys(args.frames, config["context_size"]) if args.frames_only else split_keys(config, args.split)
    name = f"{args.split}_paired" if args.frames_only else args.split
    out_dir = os.path.join(args.cache_root, args.model, name)
    os.makedirs(out_dir, exist_ok=True)

    device = torch.device("cuda:0")
    model = torch.hub.load("facebookresearch/dinov2", args.model, trust_repo=True, skip_validation=True)
    model = model.to(device).eval().half()
    loader = DataLoader(
        FrameImages(config["datasets"]["go_stanford"]["data_folder"], keys, (args.width, args.height)),
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    n_tokens = 1 + (args.height // 14 // args.pool) * (args.width // 14 // args.pool)
    dim = model.embed_dim
    arrays = {"features": np.lib.format.open_memmap(
        os.path.join(out_dir, "features.npy"), mode="w+", dtype=np.float16, shape=(len(keys), n_tokens, dim)
    )}
    if args.flip:
        arrays["features_flip"] = np.lib.format.open_memmap(
            os.path.join(out_dir, "features_flip.npy"), mode="w+", dtype=np.float16, shape=(len(keys), n_tokens, dim)
        )
    print(f"{len(keys)} frames -> {out_dir} [{n_tokens} tokens x {dim}] flip={args.flip}")

    start = 0
    for x in tqdm(loader, desc=f"DINOv2 {args.split}"):
        x = x.to(device).half()
        stop = start + len(x)
        arrays["features"][start:stop] = tokens(model, x, args.pool).cpu().numpy()
        if args.flip:
            arrays["features_flip"][start:stop] = tokens(model, torch.flip(x, dims=[3]), args.pool).cpu().numpy()
        start = stop
    for array in arrays.values():
        array.flush()
    with open(os.path.join(out_dir, "keys.pkl"), "wb") as f:
        pickle.dump(keys, f)
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(
            {
                "model": args.model,
                "width": args.width,
                "height": args.height,
                "pool": args.pool,
                "grid": [args.height // 14 // args.pool, args.width // 14 // args.pool],
                "tokens": n_tokens,
                "dim": dim,
                "flip": args.flip,
                "frames": len(keys),
            },
            f,
            indent=2,
        )
    print("done")


if __name__ == "__main__":
    main()

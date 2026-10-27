"""Confidence-weighted geometric guidance at sampling time. No training.

E-oracle stays trained on clean positions. At every DDPM step the noise prediction is
  eps = eps_base + w * (eps_pos - eps_base),   w = w_max * kappa / (kappa + c)   (c = 0: w = w_max)
eps_pos: E-oracle given the DINO bearing x B distance.
eps_base: "mask" = E-oracle with the goal masked (classifier-free guidance style), or
          "B"    = baseline B given the goal image (no position).
w = 1 is the plain direct test; w < 1 leans on the base when DINO is unsure; w > 1 amplifies.

Tuning: the clean tuning set of revalidate.py (test-split trajectories unused by the locked
frames). The best config then runs once on the locked far frames next to the plain direct
test and E-oracle with the true position. Shared noise per batch, RNG reseeded per config.

Run from train/:
    python -u eval_guidance.py
"""

import argparse
import itertools
import os

import numpy as np
import torch
from tqdm import tqdm

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images, write_csv
from eval_position_noise import boot_mean, encode_cond, load_model, mean_ade_fde, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS
from revalidate import CACHE_ROOT, dino_and_b, tune_items
from train_e_dino import DINO_BEST, load_dino_head
from train_goal_dino import load_cache
from vint_train.training.train_utils import append_goal_pos, get_action

SET_NAMES = ("all", "turn 0.30m/45deg", "B masked spread")


def weights(kappa, w_max, c):
    return (w_max * (kappa / (kappa + c) if c > 0 else np.ones_like(kappa))).astype(np.float32)


@torch.no_grad()
def guided_rollout(model_eo, sched, model_b, dataset, items, pos_units, kappa, configs, device, num_samples, batch_size, seed, desc):
    """configs: name -> (base, w_max, c); special names "true" (pos_units_true needed) handled by caller.

    Returns E-oracle masked ADE and ADE per config (meters).
    """
    meters = meters_per_unit(dataset)
    n = len(items)
    ade_mask = np.zeros(n)
    ade = {name: np.zeros(n) for name in configs}
    need_b = any(cfg[0] == "B" for cfg in configs.values())
    for b_idx, start in enumerate(tqdm(range(0, n, batch_size), desc=desc, leave=False)):
        chunk = items[start : start + batch_size]
        obs_l, goal_l, gt_l = [], [], []
        for traj_name, t, g in chunk:
            obs, goal, actions, _p = load_observation(dataset, traj_name, t, g)
            obs_l.append(obs)
            goal_l.append(goal)
            gt_l.append(actions[:, :2])
        batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
        b = len(chunk)
        gen = torch.Generator(device=device).manual_seed(seed * 100003 + b_idx)
        noise = torch.randn((b * num_samples, dataset.len_traj_pred, 2), device=device, generator=gen)
        cond_goal, mask_goal = encode_cond(model_eo, batch_obs, batch_goal, 0, device)
        cond_mask, mask_mask = encode_cond(model_eo, batch_obs, batch_goal, 1, device)
        cond_mask = append_goal_pos(cond_mask, torch.zeros((b, 2), device=device), mask_mask)
        rep = lambda x: x.repeat_interleave(num_samples, dim=0)
        cond_mask_r = rep(cond_mask)
        cond_b_r = rep(encode_cond(model_b, batch_obs, batch_goal, 0, device)[0]) if need_b else None

        def sample(eps_fn, reseed):
            torch.manual_seed(reseed)
            x = noise.clone()
            for k in sched.timesteps:
                ts = k.unsqueeze(-1).repeat(x.shape[0]).to(device)
                x = sched.step(model_output=eps_fn(x, ts), timestep=k, sample=x).prev_sample
            return get_action(x).reshape(b, num_samples, -1, 2)

        reseed = seed * 7919 + b_idx
        pred = sample(lambda x, ts: model_eo("noise_pred_net", sample=x, timestep=ts, global_cond=cond_mask_r), reseed)
        for i, gt in enumerate(gt_l):
            ade_mask[start + i] = mean_ade_fde(pred[i], gt, meters)[0]
        for name, (base, w_max, c) in configs.items():
            pos = torch.tensor(pos_units[name][start : start + b] if isinstance(pos_units, dict) else pos_units[start : start + b], device=device)
            cond_pos_r = rep(append_goal_pos(cond_goal, pos, mask_goal))
            w = torch.tensor(weights(kappa[start : start + b], w_max, c), device=device)
            w_r = rep(w).view(-1, 1, 1)

            def eps_fn(x, ts, cond_pos_r=cond_pos_r, base=base, w_r=w_r):
                eps_p = model_eo("noise_pred_net", sample=x, timestep=ts, global_cond=cond_pos_r)
                if base is None:
                    return eps_p
                if base == "mask":
                    eps_b = model_eo("noise_pred_net", sample=x, timestep=ts, global_cond=cond_mask_r)
                else:
                    eps_b = model_b("noise_pred_net", sample=x, timestep=ts, global_cond=cond_b_r)
                return eps_b + w_r * (eps_p - eps_b)

            pred = sample(eps_fn, reseed)
            for i, gt in enumerate(gt_l):
                ade[name][start + i] = mean_ade_fde(pred[i], gt, meters)[0]
    return ade_mask, ade


def main():
    parser = argparse.ArgumentParser(description="Confidence-weighted guidance with the DINO estimate")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--n-tune", type=int, default=600)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--tune-from-locked", action="store_true", help="Smoke tests only")
    parser.add_argument("--skip-test", action="store_true")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="logs/nomad_d/guidance")
    args = parser.parse_args()

    device = torch.device(args.device)
    os.makedirs(args.output_dir, exist_ok=True)
    config_b = load_config(args.config_b)
    config_eo = load_config(args.config_e_oracle)
    dataset = make_split_dataset(config_b, "test")
    meters = meters_per_unit(dataset)
    moments = load_paired_frames(args.frames)
    locked_trajs = {t for t, _, _ in moments}
    if args.tune_from_locked:
        items = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments][: args.n_tune]
        cache_name = "test_paired"
    else:
        items = tune_items(dataset, locked_trajs, args.n_tune, seed=2468)
        cache_name = "test"
    _p, rows, _m = load_cache(CACHE_ROOT, cache_name)
    features = np.load(os.path.join(CACHE_ROOT, cache_name, "features.npy"), mmap_mode="r")
    head, _hm = load_dino_head(DINO_BEST, device)
    b_frozen = load_frozen_nomad(config_b, B_CHECKPOINT, device)
    est = dino_and_b(items, dataset, b_frozen, head, rows, features, device)
    del b_frozen, head

    model_eo, sched_eo = load_model(config_eo, E_CHECKPOINT, device)
    model_b, _sb = load_model(config_b, B_CHECKPOINT, device)
    pos = (est["dir"] * est["steps"][:, None]).astype(np.float32)
    true_pos = est["target"].astype(np.float32)

    grid = {f"{base} w={w:g} c={c:g}": (base, w, c)
            for base, w, c in itertools.product(("mask", "B"), (1.0, 1.25, 1.5, 2.0), (0.0, 1.0, 3.0, 10.0))
            if not (w == 1.0 and c == 0.0)}
    configs = {"plain": (None, 1.0, 0.0), **grid}
    am, ade = guided_rollout(model_eo, sched_eo, model_b, dataset, items, pos, est["kappa"], configs, device,
                             args.num_samples, args.batch_size, args.seed, "tune: guidance grid")
    am_t, ade_t = guided_rollout(model_eo, sched_eo, model_b, dataset, items, true_pos, est["kappa"], {"true": (None, 1.0, 0.0)},
                                 device, args.num_samples, args.batch_size, args.seed, "tune: true")
    true_use = 100 * float((am_t - ade_t["true"]).mean())
    rows_t = sorted(({"config": k, "base": v[0], "w_max": v[1], "c": v[2], "tune_use_cm": 100 * float((am - ade[k]).mean())}
                     for k, v in configs.items()), key=lambda r: -r["tune_use_cm"])
    plain_use = next(r["tune_use_cm"] for r in rows_t if r["config"] == "plain")
    print(f"\n[tuning] true {true_use:+.2f} cm, plain direct {plain_use:+.2f} cm ({100 * plain_use / true_use:.0f}%). Top 8:")
    for r in rows_t[:8]:
        print(f"  {r['config']:<20} {r['tune_use_cm']:+.2f}  ({100 * r['tune_use_cm'] / true_use:.0f}% of true)")
    write_csv(os.path.join(args.output_dir, "tune_guidance_grid.csv"), rows_t)
    best = rows_t[0]
    if args.skip_test or args.tune_from_locked:
        return
    if best["config"] == "plain":
        print("plain direct test wins on the tuning set; nothing new to test")
        return

    sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
    far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
    pred = dict(np.load(DINO_TEST_PREDICTIONS))
    fm = pred["group"] == "20-40"
    order = np.argsort(pred["frame_index"][fm], kind="stable")
    take = lambda key: pred[key][fm][order]
    steps = take("b_dist") / meters
    test_pos = {"true": (take("target") / meters).astype(np.float32),
                "plain": (take("dino_dir") * steps[:, None]).astype(np.float32)}
    test_pos[best["config"]] = test_pos["plain"]
    test_cfg = {"true": (None, 1.0, 0.0), "plain": (None, 1.0, 0.0), best["config"]: configs[best["config"]]}
    am, ade = guided_rollout(model_eo, sched_eo, model_b, dataset, far, test_pos, take("dino_kappa"), test_cfg, device,
                             args.num_samples, 8, args.seed + 1, "locked")
    rng = np.random.default_rng(args.seed + 2)
    lines = []
    for set_name in SET_NAMES:
        idx = np.flatnonzero(sets[set_name])
        boot = subset_index(len(idx), args.bootstrap, rng)
        tu = float((am[idx] - ade["true"][idx]).mean())
        for k in test_cfg:
            u = boot_mean(am[idx] - ade[k][idx], boot)
            lines.append(f"  [{set_name}] {k:<20} use {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  kept {100 * u[0] / tu:.0f}%")
    d = boot_mean((am - ade[best["config"]]) - (am - ade["plain"]), subset_index(len(far), args.bootstrap, rng))
    lines.append(f"  paired {best['config']} - plain: {100 * d[0]:+.2f} [{100 * d[1]:+.2f}, {100 * d[2]:+.2f}] cm")
    text = f"selected on the tuning set: {best['config']}\n" + "\n".join(lines)
    print("\n[locked]\n" + text)
    with open(os.path.join(args.output_dir, "locked_guidance.txt"), "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()

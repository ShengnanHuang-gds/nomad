"""Re-select test-time settings and checkpoints on a clean tuning set.

The earlier selections used held-out *training* trajectories, which E-oracle (and
every model initialized from it or from B) had trained on, so goal use there was tiny
and the rankings were noise. The tuning set here comes from test-split trajectories
that no locked paired frame uses, so no model has seen them and they are disjoint
from the locked test frames. Far goals only (20-39 steps).

Tasks on the tuning set (goal use = masked ADE - ADE, shared noise per batch):
  testtime  E-oracle with the plain DINO bearing x B distance under the bearing-shrink /
            distance-scale grid of eval_testtime.py; the best config then runs once on
            the locked frames next to the plain direct test.
  e_runs    E-mu, E-musigma and the two E-oracle fine-tunes over their saved epochs,
            fed DINO bearing x B distance (+ sigma for E-musigma).
  geo_runs  the NoMaD-Geo groups over ema_0..ema_9, fed their own estimate.
Writes revalidation/selection.json (best checkpoint per run) and the tuning tables;
the queue then evaluates each selected checkpoint once on the locked frames.

Run from train/:
    python -u revalidate.py
"""

import argparse
import itertools
import json
import os

import numpy as np
import torch

from eval_by_distance import load_config, load_observation, load_paired_frames
from eval_d_direct import E_CHECKPOINT
from eval_frame_sets import PAIRED_FRAMES, SPREAD_NPZ, frame_sets
from eval_goal_head import B_CHECKPOINT, encode, load_frozen_nomad, make_split_dataset, meters_per_unit, normalize_images, write_csv
from eval_position_noise import boot_mean, load_model, subset_index
from eval_testtime import DINO_TEST_PREDICTIONS, angle_err, config_name, rollout, transform
from train_e_dino import DINO_BEST, load_dino_head, read_tokens
from train_geo import build_geo
from train_goal_dino import load_cache

OUTPUT_DIR = "logs/revalidation"
CACHE_ROOT = "logs/dino_cache/dinov2_vits14_reg"
FAR_MIN, FAR_MAX = 20, 39
E_RUNS = [
    ("E-mu (from B)", "logs/nomad/nomad_e_dino_d2_2026_10_19_09_37_58", "config/nomad_e_dino_mu.yaml", [0, 5, 10, 15, 20, 25, 29]),
    ("E-musigma (from B)", "logs/nomad/nomad_e_dino_d3_2026_10_14_00_10_38", "config/nomad_e_dino.yaml", [0, 5, 10, 15, 20, 25, 29]),
    ("FT true0 (from E-oracle)", "logs/nomad/nomad_e_dino_ft_oracle_true0", "config/nomad_e_dino_mu.yaml", list(range(10))),
    ("FT true50 (from E-oracle)", "logs/nomad/nomad_e_dino_ft_oracle_true50", "config/nomad_e_dino_mu.yaml", list(range(10))),
]
GEO_PREFIXES = ["geo_g1_true50_stop", "geo_g2_true50_shuf10_stop", "geo_g3_true50_shuf10_thru", "geo_g4_true95_shuf5_stop"]


def latest_dir(root, prefix):
    dirs = sorted(
        (d for d in os.listdir(root) if d.startswith(prefix) and os.path.isdir(os.path.join(root, d))),
        key=lambda d: os.path.getmtime(os.path.join(root, d)),
    )
    return os.path.join(root, dirs[-1]) if dirs else None


def tune_items(dataset, locked_trajs, n, seed):
    rng = np.random.default_rng(seed)
    entries = [e for e in dataset.index_to_data if e[0] not in locked_trajs and e[2] >= FAR_MIN]
    pick = rng.choice(len(entries), size=min(n, len(entries)), replace=False)
    items = []
    for i in sorted(pick):
        traj_name, t, max_goal = entries[i]
        items.append((traj_name, t, t + int(rng.integers(FAR_MIN, min(FAR_MAX, max_goal) + 1))))
    return items


def load_images(dataset, chunk, device):
    obs_l, goal_l, pos_l = [], [], []
    for traj_name, t, g in chunk:
        obs, goal, _a, goal_pos = load_observation(dataset, traj_name, t, g)
        obs_l.append(obs)
        goal_l.append(goal)
        pos_l.append(goal_pos)
    batch_obs, batch_goal = normalize_images(torch.stack(obs_l), torch.stack(goal_l), device)
    return batch_obs, batch_goal, np.stack(pos_l)


@torch.no_grad()
def dino_and_b(items, dataset, model_b, head, rows, features, device, batch_size=64):
    out = {k: [] for k in ("dir", "kappa", "steps", "target")}
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        batch_obs, batch_goal, target = load_images(dataset, chunk, device)
        steps = model_b("dist_pred_net", obsgoal_cond=encode(model_b, batch_obs, batch_goal)).squeeze(-1).clamp(min=0)
        d, k = head(
            read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float(),
            read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float(),
        )
        out["dir"].append(d.cpu().numpy())
        out["kappa"].append(k.cpu().numpy())
        out["steps"].append(steps.cpu().numpy())
        out["target"].append(target)
    return {k: np.concatenate(v) for k, v in out.items()}


@torch.no_grad()
def geo_estimate(model, items, dataset, rows, features, device, batch_size=64):
    out = []
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        batch_obs, batch_goal, _t = load_images(dataset, chunk, device)
        no_mask = torch.zeros(len(chunk), dtype=torch.long, device=device)
        cond = model("vision_encoder", obs_img=batch_obs, goal_img=batch_goal, input_goal_mask=no_mask)
        pos, std, _d, _k, _s = model.estimate_goal(
            cond,
            read_tokens(features, [rows[(c[0], c[1])] for c in chunk]).to(device).float(),
            read_tokens(features, [rows[(c[0], c[2])] for c in chunk]).to(device).float(),
        )
        out.append(torch.cat([pos, std.unsqueeze(-1)], dim=-1).cpu().numpy())
    return np.concatenate(out).astype(np.float32)


def use_cm(ade_mask, ade):
    return 100.0 * float((ade_mask - ade).mean())


def main():
    parser = argparse.ArgumentParser(description="Re-select settings and checkpoints on a clean tuning set")
    parser.add_argument("--config-b", default="config/nomad_b40.yaml")
    parser.add_argument("--config-e-oracle", default="config/nomad_e_oracle.yaml")
    parser.add_argument("--n-tune", type=int, default=600)
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-epochs-per-run", type=int, default=0, help="Smoke tests: keep the first k epochs per run")
    parser.add_argument("--tune-from-locked", action="store_true", help="Smoke tests: tune on locked frames with the paired cache")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--frames", default=PAIRED_FRAMES)
    parser.add_argument("--spread", default=SPREAD_NPZ)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
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
        if any(t in locked_trajs for t, _, _ in items):
            raise RuntimeError("tuning frames overlap the locked trajectories")
    _path, rows, _meta = load_cache(CACHE_ROOT, cache_name)
    features = np.load(os.path.join(CACHE_ROOT, cache_name, "features.npy"), mmap_mode="r")
    print(f"tuning frames {len(items)} from {len({t for t, _, _ in items})} trajectories (cache {cache_name})")

    head, _hm = load_dino_head(DINO_BEST, device)
    model_b = load_frozen_nomad(config_b, B_CHECKPOINT, device)
    est = dino_and_b(items, dataset, model_b, head, rows, features, device)
    del model_b, head
    print(
        f"tuning set: DINO bearing median {np.median(angle_err(est['dir'], est['target'])):.1f} deg, "
        f"share above 45 deg {100 * (angle_err(est['dir'], est['target']) > 45).mean():.0f}%, "
        f"B distance ratio {np.median(est['steps'] / np.linalg.norm(est['target'], axis=1)):.2f}"
    )
    selection = {}
    run = lambda model, sched, positions, tag: rollout(
        model, sched, dataset, items, positions, device, args.num_samples, args.batch_size, args.seed, tag
    )

    # ---- test-time grid with E-oracle ----
    model_eo, sched_eo = load_model(config_eo, E_CHECKPOINT, device)
    grid = list(itertools.product((1.0, 0.85, 0.7), (0.0, 1.0, 3.0, 10.0), (1.0, 0.85, 0.7)))
    positions = {config_name("plain", *g): transform(est["dir"], est["kappa"], est["steps"], *g) for g in grid}
    positions["true"] = est["target"].astype(np.float32)
    ade_mask, ade = run(model_eo, sched_eo, positions, "tune: test-time grid")
    true_use = use_cm(ade_mask, ade["true"])
    plain = config_name("plain", 1.0, 0.0, 1.0)
    rows_tt = sorted(
        ({"config": config_name("plain", *g), "a": g[0], "c": g[1], "m": g[2], "tune_use_cm": use_cm(ade_mask, ade[config_name("plain", *g)])} for g in grid),
        key=lambda r: -r["tune_use_cm"],
    )
    print(f"\n[test-time] tuning use: true {true_use:+.2f} cm, plain direct {use_cm(ade_mask, ade[plain]):+.2f} cm "
          f"({100 * use_cm(ade_mask, ade[plain]) / true_use:.0f}% of true). Top 5:")
    for r in rows_tt[:5]:
        print(f"  {r['config']:<26} {r['tune_use_cm']:+.2f}  ({100 * r['tune_use_cm'] / true_use:.0f}%)")
    write_csv(os.path.join(args.output_dir, "tune_testtime_grid.csv"), rows_tt)
    best_tt = rows_tt[0]
    selection["testtime"] = {**best_tt, "tune_true_use_cm": true_use, "tune_plain_use_cm": use_cm(ade_mask, ade[plain])}
    reference = {"E-oracle true": true_use, "E-oracle + DINO direct": use_cm(ade_mask, ade[plain])}

    # locked test, once, for the selected test-time config
    if best_tt["config"] != plain and not args.tune_from_locked:
        sets, _l, _y = frame_sets(dataset, moments, meters, args.spread)
        far = [(n, t, [g[4] for g in goals if g[0] == "20-40"][0]) for n, t, goals in moments]
        pred = dict(np.load(DINO_TEST_PREDICTIONS))
        fm = pred["group"] == "20-40"
        order = np.argsort(pred["frame_index"][fm], kind="stable")
        take = lambda key: pred[key][fm][order]
        steps = take("b_dist") / meters
        test_pos = {
            "true": (take("target") / meters).astype(np.float32),
            "direct (plain)": transform(take("dino_dir"), take("dino_kappa"), steps, 1.0, 0.0, 1.0),
            "selected": transform(take("dino_dir"), take("dino_kappa"), steps, best_tt["a"], best_tt["c"], best_tt["m"]),
        }
        am, a = rollout(model_eo, sched_eo, dataset, far, test_pos, device, args.num_samples, 8, args.seed + 1, "locked: test-time")
        rng = np.random.default_rng(args.seed + 2)
        lines = []
        for set_name in ("all", "turn 0.30m/45deg", "B masked spread"):
            idx = np.flatnonzero(sets[set_name])
            boot = subset_index(len(idx), args.bootstrap, rng)
            tu = float((am[idx] - a["true"][idx]).mean())
            for k in test_pos:
                u = boot_mean(am[idx] - a[k][idx], boot)
                lines.append(f"  [{set_name}] {k:<16} use {100 * u[0]:+.2f} [{100 * u[1]:+.2f}, {100 * u[2]:+.2f}]  kept {100 * u[0] / tu:.0f}%")
        d = boot_mean((am - a["selected"]) - (am - a["direct (plain)"]), subset_index(len(far), args.bootstrap, rng))
        lines.append(f"  paired selected - direct (plain): {100 * d[0]:+.2f} [{100 * d[1]:+.2f}, {100 * d[2]:+.2f}] cm")
        print(f"\n[test-time] locked frames, selected {best_tt['config']}:\n" + "\n".join(lines))
        with open(os.path.join(args.output_dir, "locked_testtime.txt"), "w") as f:
            f.write(f"selected {best_tt['config']}\n" + "\n".join(lines) + "\n")
    elif best_tt["config"] == plain:
        print("\n[test-time] the plain direct test wins on the tuning set; nothing new to test on the locked frames")
    del model_eo
    torch.cuda.empty_cache() if device.type == "cuda" else None

    # ---- E runs: epoch sweep ----
    sigma = (est["steps"] / np.maximum(np.sqrt(est["kappa"]), 1e-3)).clip(max=40.0)
    mu = (est["dir"] * est["steps"][:, None]).astype(np.float32)
    rows_e = []
    for name, run_dir, cfg_path, epochs in E_RUNS:
        if not os.path.isdir(run_dir):
            print(f"[skip] {name}: {run_dir} missing")
            continue
        cfg = load_config(cfg_path)
        pos = mu if int(cfg.get("goal_pos_dim", 2)) == 2 else np.concatenate([mu, sigma[:, None].astype(np.float32)], axis=1)
        if args.max_epochs_per_run:
            epochs = epochs[: args.max_epochs_per_run]
        best = None
        for e in epochs:
            path = os.path.join(run_dir, f"ema_{e}.pth")
            if not os.path.exists(path):
                continue
            model, sched = load_model(cfg, path, device)
            am, a = run(model, sched, {"est": pos}, f"tune: {name} ema_{e}")
            u = use_cm(am, a["est"])
            rows_e.append({"run": name, "epoch": e, "tune_use_cm": u, "tune_kept": u / true_use})
            print(f"  {name:<28} ema_{e:<3} tuning use {u:+.2f} cm ({100 * u / true_use:.0f}% of E-oracle true)")
            if best is None or u > best[1]:
                best = (e, u)
            del model
        if best is not None:
            selection[name] = {"kind": "e", "run_dir": run_dir, "config": cfg_path, "checkpoint": f"ema_{best[0]}.pth",
                               "tune_use_cm": best[1]}
    write_csv(os.path.join(args.output_dir, "tune_e_epochs.csv"), rows_e)

    # ---- NoMaD-Geo runs: epoch sweep ----
    rows_g = []
    for prefix in GEO_PREFIXES:
        run_dir = latest_dir("logs/nomad_geo", prefix)
        if run_dir is None:
            print(f"[skip] {prefix}: no run")
            continue
        with open(os.path.join(run_dir, "geo_meta.json")) as f:
            meta = json.load(f)
        epochs = list(range(10))[: args.max_epochs_per_run or None]
        best = None
        for e in epochs:
            path = os.path.join(run_dir, f"ema_{e}.pth")
            if not os.path.exists(path):
                continue
            model, sched = build_geo(config_eo, {"meta": meta["head_meta"], "args": meta["head_args"]})
            model.load_state_dict(torch.load(path, map_location="cpu", weights_only=False), strict=True)
            model.to(device).eval()
            pos = geo_estimate(model, items, dataset, rows, features, device)
            am, a = run(model, sched, {"own": pos}, f"tune: {prefix} ema_{e}")
            u = use_cm(am, a["own"])
            rows_g.append({"run": prefix, "epoch": e, "tune_use_cm": u, "tune_kept": u / true_use})
            print(f"  {prefix:<28} ema_{e:<3} tuning use {u:+.2f} cm ({100 * u / true_use:.0f}% of E-oracle true)")
            if best is None or u > best[1]:
                best = (e, u)
            del model
        if best is not None:
            selection[prefix] = {"kind": "geo", "run_dir": run_dir, "checkpoint": f"ema_{best[0]}.pth", "tune_use_cm": best[1]}
    write_csv(os.path.join(args.output_dir, "tune_geo_epochs.csv"), rows_g)

    selection["_reference_tune_use_cm"] = reference
    with open(os.path.join(args.output_dir, "selection.json"), "w") as f:
        json.dump(selection, f, indent=2)
    print(f"\nSelection written to {os.path.abspath(os.path.join(args.output_dir, 'selection.json'))}")
    for k, v in selection.items():
        if isinstance(v, dict) and "checkpoint" in v:
            print(f"  {k:<28} -> {v['checkpoint']} (tuning use {v['tune_use_cm']:+.2f} cm)")


if __name__ == "__main__":
    main()

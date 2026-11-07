"""Shared helpers for R2/R18 fair ablation: pairing keys, path-cond grad slices, bootstrap."""

from __future__ import annotations



import csv

from pathlib import Path



import numpy as np



# NoMaD ViNT encoding + appended goal_pos (see build_e_model global_cond_dim).

ENCODING_SIZE = 256

MU_COLS = slice(ENCODING_SIZE, ENCODING_SIZE + 2)

PATH_COLS = slice(ENCODING_SIZE + 2, ENCODING_SIZE + 18)



PATH_COND_WEIGHT_SUFFIX = ".cond_encoder.1.weight"





def pair_key_from_row(row: dict) -> tuple:

    return (row["traj_name"], str(row["curr_t"]), str(row["goal_t"]))





def load_val_rows(csv_path: str) -> list[dict]:

    with open(csv_path, newline="", encoding="utf-8") as f:

        return list(csv.DictReader(f))





def index_val_by_order(rows: list[dict]) -> dict[int, dict]:

    out = {}

    for r in rows:

        o = int(r.get("order", len(out)))

        if o in out:

            raise ValueError(f"duplicate order {o} in val csv")

        out[o] = r

    return out





def align_paired_ade(csv_r2: str, csv_r18: str) -> tuple[np.ndarray, np.ndarray, list[str]]:

    """Align 500 manifest rows by order then (traj,curr,goal); returns ade_r2, ade_r18, traj_names."""

    r2 = index_val_by_order(load_val_rows(csv_r2))

    r18 = index_val_by_order(load_val_rows(csv_r18))

    if set(r2) != set(r18):

        raise ValueError(f"order mismatch r2={len(r2)} r18={len(r18)}")

    orders = sorted(r2)

    if len(orders) != 500 and len(orders) != len(r2):

        pass

    ade2, ade18, trajs = [], [], []

    for o in orders:

        a, b = r2[o], r18[o]

        ka, kb = pair_key_from_row(a), pair_key_from_row(b)

        if ka != kb:

            raise ValueError(f"order {o} key mismatch {ka} vs {kb}")

        ade2.append(float(a["nav_ade_cm"]))

        ade18.append(float(b["nav_ade_cm"]))

        trajs.append(a["traj_name"])

    return np.array(ade2), np.array(ade18), trajs





def path_cond_grad_and_delta(model_r18, model_r2) -> dict:

    """Grad + weight delta on expanded path input columns only (16 cols per cond_encoder.1.weight)."""

    out = {"matrices": []}

    path_grad_max = 0.0

    path_delta_max = 0.0

    for name, p in model_r18.noise_pred_net.named_parameters():

        if not name.endswith("cond_encoder.1.weight") or p.grad is None:

            continue

        g = p.grad

        if g.shape[1] < PATH_COLS.stop:

            continue

        pg = g[:, PATH_COLS].abs().max().item()

        path_grad_max = max(path_grad_max, pg)

        sd_r18 = p.detach()

        sd_r2 = model_r2.state_dict().get(f"noise_pred_net.{name}")

        if sd_r2 is not None and sd_r2.shape == sd_r18.shape:

            delta = (sd_r18[:, PATH_COLS] - sd_r2[:, PATH_COLS].to(sd_r18.device)).abs().max().item()

            path_delta_max = max(path_delta_max, delta)

        out["matrices"].append(

            {

                "name": f"noise_pred_net.{name}",

                "input_cols_path": f"[{PATH_COLS.start}:{PATH_COLS.stop})",

                "grad_max_path_cols": pg,

            }

        )

    out["path_input_grad_max"] = path_grad_max

    out["path_weight_delta_max_after_one_step"] = path_delta_max

    out["mu_cols"] = f"[{MU_COLS.start}:{MU_COLS.stop})"

    out["path_cols"] = f"[{PATH_COLS.start}:{PATH_COLS.stop})"

    return out





def bootstrap_traj_pooled_pairs(delta_cm: np.ndarray, traj_names: np.ndarray, n_boot=10000, seed=20261107):

    """Resample trajectories; keep all frame-pairs from each drawn trajectory; mean over total pairs."""

    uniq = np.unique(traj_names)

    by_traj = {u: delta_cm[traj_names == u] for u in uniq}

    if len(uniq) < 2:

        m = float(delta_cm.mean()) if len(delta_cm) else float("nan")

        return m, float("nan"), float("nan")

    rng = np.random.default_rng(seed)

    boots = np.empty(n_boot, dtype=np.float64)

    for i in range(n_boot):

        pick = rng.choice(uniq, size=len(uniq), replace=True)

        boots[i] = np.concatenate([by_traj[t] for t in pick]).mean()

    return float(delta_cm.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))





def manifest_units_note(manifest_csv: str) -> dict:

    rows = load_val_rows(manifest_csv)

    return {

        "n_pairs": len(rows),

        "unique_curr_traj_t": len({(r["traj_name"], r["curr_t"]) for r in rows}),

        "unique_triple": len({pair_key_from_row(r) for r in rows}),

        "unit": "one row = one (traj_name, curr_t, goal_t) far-goal pair; metrics averaged over 500 pairs",

    }


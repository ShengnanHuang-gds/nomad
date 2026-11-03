# nomad_e_dino_d2_2026_10_19_09_37_58

## Config

- **YAML:** `shared/nomad_e_dino_mu.yaml` (`goal_pos_dim: 2`)
- **On-disk args.txt:** `pos_dim=2`, DINO e60, B ema_29; **no** `goal_pos_mode`, **no** `init_from`, **no** `true_pos_prob`, **no** `wp_head`

## Training

- **train_log.csv:** epochs **0–29** (30 epochs) — differs from ft_oracle 10-epoch runs.
- **Train command:** 【未确认】not found in repo logs/queues.
- **init_from:** 【未确认】not in args.txt. `revalidate.py` labels this run `"E-mu (from B)"` (naming only).  
  `train_e_dino.py` default if omitted at CLI: `--init-from b` — **not proof this run used default**.

## Pure DINO×B check (train + eval)

| Check | Status |
|-------|--------|
| `pos_dim=2`, no wp_head in args | 【已有实验事实】no 16D path in training config snapshot |
| `goal_pos_mode` | 【未确认】absent from args.txt; train default `goal` only if CLI did not pass blend |
| Eval μ recipe | 【推断】`eval_e_dino.py` with empty run-dir `goal_pos_mode` → default **`goal`** → `dino_dir × b_steps` (no WP blend) |
| `blend_path` / wp_poly | 【已有实验事实】not in args; eval logs show no `E-dino inference: blend_path` line |

## Locked eval artifacts in this pack

| Dir | Checkpoint named in logs | E-dino ADE (all, m) | E-dino cm | Notes |
|-----|---------------------------|---------------------|-----------|--------|
| `eval_ema_29/` | `ema_29.pth` (file **on disk**) | 0.2198 | 21.98 | Older eval: **3 models** only in paired_far (no E-oracle+DINO row); B ADE **≠** pathact8 audit at same index |
| `eval_ema_20/` | `ema_20.pth` (**missing** on disk) | 0.2185 | 21.85 | From `queue_priority.ps1` / `selection.json`; **4 models**; B/oracle rows align with revalidation locked protocol |

## Checkpoint selection (tuning set, not test ADE)

- `shared/tune_e_epochs.csv`: best **tune_use_cm** for `"E-mu (from B)"` at **epoch 20** (+1.276 cm vs +1.228 at 29).
- `shared/selection.json`: `"E-mu (from B)"` → **`ema_20.pth`** for locked re-eval.
- **ema_29** appears in `counterfactual_vs_b_distance80/meta.json` — separate downstream choice; **not** from `selection.json`.

## Files in this folder

`args.txt`, `train_log.csv`, `eval_reval_ema_20.pth.txt`, `eval_ema_29/*`, `eval_ema_20/*` (+ `per_frame_audit.csv` each)

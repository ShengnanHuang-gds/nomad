# nomad_e_dino_ft_oracle_true0

## Config

- **YAML:** `shared/nomad_e_dino_mu.yaml`
- **args.txt (confirmed):**  
  `init_from=e_oracle`, `true_pos_prob=0.0`, `epochs=10`, `lr=3e-05`, `pos_dim=2`, no `goal_pos_mode`, no `wp_head`

## Training / eval commands (executed)

See `shared/train_eval_evidence_queue.txt` — train + `eval_e_dino.py … ema_9.pth` from `logs/queue_c16_then_eft.ps1`.  
Also `eval_stdout.txt` (loads `ema_9.pth`).

## Pure DINO×B check

- Training: `true_pos_prob=0` → batches use DINO μ unless masked (standard `train_e_dino.py`); no blend_path without `wp_head`.
- Eval: queue command has **no** `--goal-pos-mode` → default **`goal`** → pure DINO dir × B for appended μ.

## Locked eval artifacts

| Dir | Checkpoint in log | E-dino ADE all (m) | cm |
|-----|-------------------|-------------------|-----|
| `eval_ema_9/` | ema_9.pth (**file missing**) | 0.2094 | 20.94 |
| `eval_ema_0/` | ema_0.pth (**file missing**) | 0.2094 | 20.94 (same table as revalidate pick) |

**Mismatch:** `selection.json` picks **`ema_0.pth`** by tuning **use**; primary saved queue eval is **`ema_9`**.

## Tuning selection

- `tune_e_epochs.csv`: max tune_use at **epoch 0** (+1.963 cm); epoch 9 = +1.808 cm.

## Files

`args.txt`, `train_log.csv`, `eval_stdout.txt`, `eval_reval_ema_0.pth.txt`, `eval_ema_9/*`, `eval_ema_0/*`

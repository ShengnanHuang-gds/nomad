# nomad_e_dino_ft_oracle_true50

## Config

- **args.txt (confirmed):**  
  `init_from=e_oracle`, `true_pos_prob=0.5`, `epochs=10`, `lr=3e-05`, `pos_dim=2`

## Training / eval commands (executed)

Same queue file as true0 — `--true-pos-prob 0.5`, eval `ema_9.pth`. See `eval_stdout.txt`.

## Pure DINO×B check

- **Train:** half the time GT goal_pos (oracle xy), half DINO μ — still **2D only**, no WP blend in args.
- **Eval (Locked):** still **`goal` mode** default → reported ADE is **pure DINO×B at test time**, not κ-blend.

## Locked eval artifacts

| Dir | E-dino ADE all (m) | cm |
|-----|-------------------|-----|
| `eval_ema_9/` | 0.2074 | 20.74 |
| `eval_ema_0/` | (see paired_far in pack) | ~20.94 |

## Tuning selection

- `selection.json` → **ema_0.pth** (tune_use +1.963 cm at epoch 0, same peak as true0).

## Files

Same layout as true0.

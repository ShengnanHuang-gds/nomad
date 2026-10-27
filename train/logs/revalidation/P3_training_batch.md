# P3 Training Batch (turn-focused, switched 2026-10-24)

## Cancelled
Old queue R1–R7 (`run_p3_batch.ps1`, multi-seed turn winding×2). R1 stopped at ~epoch 0.

## Active: B / C / D (sequential, seed 0, ctx2, init e60 wp)
| ID | Loss (train only) | run-name |
|----|-------------------|----------|
| B | turn_strict 0.30m/45° ×2 | `p3_B_ctx2_turnstrict_x2` |
| C | turn_strict ×3 | `p3_C_ctx2_turnstrict_x3` |
| D | frame-winding tertiles weights 1/1.5/3 | `p3_D_ctx2_curvature_tiers` |

Common: 30 ep, batch 128, `--top-k-checkpoints 3`, init `nomad_dino_wp_e60_.../dino_dir_best.pth`.

## Code
- `train_goal_dino.py`: `--turn-strict-weight`, `--curvature-tiers`
- Queue: `run_p3_turn_batch.ps1` → `logs/queues/p3_turn_*.log`, `p3_turn_manifest.jsonl`
- Morning Val table: `analyze_p3_morning_table.py` (compare SeedA ctx2 vs B/C/D; **no locked** for selection)

## After Val winner
Run E/F (extra seeds) on winning recipe only; locked 1000 for report only.

## ETA
~3×30 ep ctx2 ≈ 3–4 h sequential GPU.

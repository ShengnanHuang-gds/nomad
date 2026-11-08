# 暂停快照（2026-11-07T14:18:40.764984+00:00）

## 进度
| run | 状态 |
|-----|------|
| nomad_e_r2_fair_20261107_seed1 | complete — log 8 / val json 8 |
| nomad_e_r18_fair_20261107_seed1 | partial — log 7 / val json 7 |
| nomad_e_r2_fair_20261107_seed2 | not_started — log 0 / val json 0 |
| nomad_e_r18_fair_20261107_seed2 | not_started — log 0 / val json 0 |

## 已固化参数
- `seed_repeat_train_params.json`
- `SEED_REPEAT_TRAIN_PARAMS.md`

## 续跑注意
1. **R2 seed1**：已完成，会自动跳过。
2. **R18 seed1**：停在 **7/8 epoch**（日志末行 epoch=6）。**不要**直接再跑 `run_r2_r18_seed_repeat.py` 整条 R18（launcher 会拒绝 partial log）。
3. **R18 补最后 1 epoch**（权重续上，LR/optimizer 仍从头，属你方接受的非严格续训）示例：

```text
cd visualnav-transformer/train
C:\Users\61078\anaconda3\envs\nomad_train\python.exe -u train_e_dino.py \
  --config config/nomad_e_dino_r18.yaml \
  --init-ckpt logs/nomad/nomad_e_r18_fair_20261107_seed1/ema_latest.pth \
  --start-epoch 7 \
  --init-from e_oracle --checkpoint-e-oracle logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth \
  --goal-pos-mode goal_path --pos-dim 18 --true-pos-prob 0 \
  --epochs 8 --batch-size 32 --lr 3e-5 --warmup-epochs 1 --lr-schedule per_step \
  --reset-train-rng-after-init --seed 1 --num-workers 2 \
  --run-name nomad_e_r18_fair_20261107_seed1 \
  --dino-head logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth \
  --wp-path-head logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth \
  --path-source wp_poly --path-units dataset \
  --exclude-val-list logs/revalidation/r2_r18_fair_2026-11-07/exclude_val_trajs.txt \
  --val-manifest-csv logs/revalidation/r2_r18_fair_2026-11-07/val_far_manifest_seed20261107.csv
```

4. **seed2**：R18 seed1 满 8 epoch 后：`python run_r2_r18_seed_repeat.py --seeds 2`
5. 全部结束后：`python run_r2_r18_seed_repeat.py --report-only --seeds 1 2` 与 `python r2_r18_multiseed_report.py`

**勿删** `train_log.csv` / `ema_*.pth`。

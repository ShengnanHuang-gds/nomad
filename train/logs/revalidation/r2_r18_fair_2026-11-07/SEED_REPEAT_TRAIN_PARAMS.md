# R2/R18 训练种子重复 — 参数备忘（手动固化）

- UTC: 2026-11-08T04:42:07.423517+00:00
- 每 epoch 保存 EMA 权重 ema_k.pth；无 optimizer/scheduler/EMA step/RNG 全状态。选模用各 run 自己的 val_nav_epoch*.json。

## 固定超参
```json
{
  "epochs": 8,
  "batch_size": 32,
  "optimizer": "AdamW",
  "lr": 3e-05,
  "weight_decay": 0.0001,
  "grad_clip_max_norm": 1.0,
  "warmup_epochs": 1,
  "lr_schedule": "per_step",
  "warmup_steps_per_epoch_then_cosine": true,
  "total_optimizer_steps_per_run": 30776,
  "warmup_optimizer_steps": 3847,
  "true_pos_prob": 0.0,
  "reset_train_rng_after_init": true,
  "num_workers": 2,
  "trainable_params": "noise_pred_net only (~3.85M)"
}
```
## 初始化与验证
```json
{
  "init_from": "e_oracle",
  "checkpoint_e_oracle": "logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth",
  "checkpoint_b_frozen": "logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth",
  "dino_dir_head": "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth",
  "pathact8_frozen_R18": "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth",
  "exclude_val_list": "c:\\Users\\61078\\Desktop\\nomad\\visualnav-transformer\\train\\logs\\revalidation\\r2_r18_fair_2026-11-07\\exclude_val_trajs.txt",
  "val_manifest_csv": "c:\\Users\\61078\\Desktop\\nomad\\visualnav-transformer\\train\\logs\\revalidation\\r2_r18_fair_2026-11-07\\val_far_manifest_seed20261107.csv",
  "val_manifest_sha256": "991e87b8a62c64f353e4ecd7e5e774ce063bf85984c3b5d7b5945c29d98b80c8",
  "val_pairs": 500,
  "unique_curr_frames_note": 482,
  "val_diffusion_noise_seed": 0
}
```
## nomad_e_r2_fair_20261107_seed1 (train_seed=1, status=complete)
- cache = `logs/dino_cache/dinov2_vits14_reg`
- checkpoint_b = `logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth`
- checkpoint_e_oracle = `logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth`
- dino_head = `logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth`
- epochs = `8`
- exclude_val_list = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\exclude_val_trajs.txt`
- goal_mask_prob = `0.5`
- goal_pos_mode = `goal`
- init_ckpt = ``
- init_from = `e_oracle`
- lr = `3e-05`
- lr_schedule = `per_step`
- path_gate = `none`
- path_source = `ray`
- pos_dim = `2`
- reset_train_rng_after_init = `True`
- true_pos_prob = `0.0`
- val_manifest_csv = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\val_far_manifest_seed20261107.csv`
- wp_head = `logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth`
- wp_path_head = ``
- wp_scale = `1.0`
- samples/epoch: **123125**, batches: **3847**
- interim best val: epoch **5**, ADE **12.8972** cm → `logs/nomad/nomad_e_r2_fair_20261107_seed1/ema_5.pth`
- EMA files: ema_0.pth, ema_1.pth, ema_2.pth, ema_3.pth, ema_4.pth, ema_5.pth, ema_6.pth, ema_7.pth

## nomad_e_r18_fair_20261107_seed1 (train_seed=1, status=complete)
- cache = `logs/dino_cache/dinov2_vits14_reg`
- checkpoint_b = `logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth`
- checkpoint_e_oracle = `logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth`
- dino_head = `logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth`
- epochs = `8`
- exclude_val_list = `c:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs\revalidation\r2_r18_fair_2026-11-07\exclude_val_trajs.txt`
- goal_mask_prob = `0.5`
- goal_pos_mode = `goal_path`
- init_ckpt = `logs/nomad/nomad_e_r18_fair_20261107_seed1/ema_latest.pth`
- init_from = `e_oracle`
- lr = `3e-05`
- lr_schedule = `per_step`
- path_gate = `none`
- path_source = `wp_poly`
- pos_dim = `18`
- reset_train_rng_after_init = `True`
- true_pos_prob = `0.0`
- val_manifest_csv = `c:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs\revalidation\r2_r18_fair_2026-11-07\val_far_manifest_seed20261107.csv`
- wp_head = `logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth`
- wp_path_head = `logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth`
- wp_scale = `1.0`
- samples/epoch: **123125**, batches: **3847**
- interim best val: epoch **2**, ADE **11.7561** cm → `logs/nomad/nomad_e_r18_fair_20261107_seed1/ema_2.pth`
- EMA files: ema_0.pth, ema_1.pth, ema_2.pth, ema_3.pth, ema_4.pth, ema_5.pth, ema_6.pth, ema_7.pth

## nomad_e_r2_fair_20261107_seed2 (train_seed=2, status=complete)
- cache = `logs/dino_cache/dinov2_vits14_reg`
- checkpoint_b = `logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth`
- checkpoint_e_oracle = `logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth`
- dino_head = `logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth`
- epochs = `8`
- exclude_val_list = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\exclude_val_trajs.txt`
- goal_mask_prob = `0.5`
- goal_pos_mode = `goal`
- init_ckpt = ``
- init_from = `e_oracle`
- lr = `3e-05`
- lr_schedule = `per_step`
- path_gate = `none`
- path_source = `ray`
- pos_dim = `2`
- reset_train_rng_after_init = `True`
- true_pos_prob = `0.0`
- val_manifest_csv = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\val_far_manifest_seed20261107.csv`
- wp_head = `logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth`
- wp_path_head = ``
- wp_scale = `1.0`
- samples/epoch: **123125**, batches: **3847**
- interim best val: epoch **7**, ADE **12.7996** cm → `logs/nomad/nomad_e_r2_fair_20261107_seed2/ema_7.pth`
- EMA files: ema_0.pth, ema_1.pth, ema_2.pth, ema_3.pth, ema_4.pth, ema_5.pth, ema_6.pth, ema_7.pth

## nomad_e_r18_fair_20261107_seed2 (train_seed=2, status=complete)
- cache = `logs/dino_cache/dinov2_vits14_reg`
- checkpoint_b = `logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth`
- checkpoint_e_oracle = `logs/nomad/nomad_e_oracle_2026_10_09_09_20_40/ema_29.pth`
- dino_head = `logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth`
- epochs = `8`
- exclude_val_list = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\exclude_val_trajs.txt`
- goal_mask_prob = `0.5`
- goal_pos_mode = `goal_path`
- init_ckpt = ``
- init_from = `e_oracle`
- lr = `3e-05`
- lr_schedule = `per_step`
- path_gate = `none`
- path_source = `wp_poly`
- pos_dim = `18`
- reset_train_rng_after_init = `True`
- true_pos_prob = `0.0`
- val_manifest_csv = `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/revalidation/r2_r18_fair_2026-11-07\val_far_manifest_seed20261107.csv`
- wp_head = `logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth`
- wp_path_head = `logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth`
- wp_scale = `1.0`
- samples/epoch: **123125**, batches: **3847**
- interim best val: epoch **2**, ADE **11.6987** cm → `logs/nomad/nomad_e_r18_fair_20261107_seed2/ema_2.pth`
- EMA files: ema_0.pth, ema_1.pth, ema_2.pth, ema_3.pth, ema_4.pth, ema_5.pth, ema_6.pth, ema_7.pth

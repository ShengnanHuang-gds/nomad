# Updated 2026-11-08 resume active

Arm A resuming: epoch 5-7 with bundle_epoch4.pth (strict optimizer/scheduler).

## After Arm A summary.json shows 8 epochs done, run Arm B:
cd visualnav-transformer/train
$env:PYTHONPATH="../diffusion_policy"
python -u train_e_joint_path_ab.py --arm b --run-dir logs/revalidation/e_path_joint_ab_2026-11-08/arm_b --init-ckpt logs/nomad/nomad_e_ft_pathact8/ema_latest.pth --epochs 8 --batch-size 32 --seed 0 --reset-train-rng-after-init --true-pos-prob 0 --goal-mask-prob 0 --val-manifest-csv logs/revalidation/r2_r18_fair_2026-11-07/val_far_manifest_seed20261107.csv --dino-head logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth --wp-head logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth --checkpoint-b logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth

python -u run_e_path_joint_ab.py --only-report --skip-train-a --skip-train-b

Log: resume_pipeline.log

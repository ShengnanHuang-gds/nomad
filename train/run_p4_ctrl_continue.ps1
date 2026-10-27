$ErrorActionPreference = "Continue"
Set-Location "c:\Users\61078\Desktop\nomad\visualnav-transformer\train"
$log = "logs\queues\p4_ctrl_continue15.log"
$ctx2 = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
python -u train_goal_dino.py `
  --target endpoint --init $ctx2 `
  --context 2 --epochs 15 --batch-size 128 --num-workers 0 `
  --top-k-checkpoints 3 --seed 0 `
  --run-name p4_ctrl_ctx2_continue_15ep `
  2>&1 | Tee-Object -FilePath $log
Write-Host "Control done $(Get-Date -Format o)"
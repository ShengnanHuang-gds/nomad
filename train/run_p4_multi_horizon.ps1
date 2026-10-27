$ErrorActionPreference = "Continue"
Set-Location "c:\Users\61078\Desktop\nomad\visualnav-transformer\train"
$logDir = "logs\queues"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "p4_multi_horizon.log"
$ctx2 = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
& python -u train_goal_dino.py `
  --target endpoint --init $ctx2 `
  --context 2 --epochs 15 --batch-size 128 --num-workers 0 `
  --multi-horizon 2,4 --multi-horizon-lambda 0.25 `
  --top-k-checkpoints 3 `
  --run-name p4_ctx2_multi_horizon_248 `
  2>&1 | Tee-Object -FilePath $log
Write-Host "P4 done $(Get-Date -Format o)"
$ErrorActionPreference = "Continue"
Set-Location "c:\Users\61078\Desktop\nomad\visualnav-transformer\train"
$logDir = "logs\queues"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$manifest = Join-Path $logDir "p3_turn_manifest.jsonl"
$master = Join-Path $logDir "p3_turn_batch_master.log"
Add-Content $master "===== SWITCHED to B/C/D $(Get-Date -Format o) (cancelled old R1-R7 queue) ====="
function Write-Manifest($id, $outDir) {
  $line = "{`"id`":`"$id`",`"output_dir`":`"$($outDir.Replace('\','/'))`",`"finished`":`"$(Get-Date -Format o)`"}"
  Add-Content -Path $manifest -Value $line -Encoding utf8
}
function Run-Job($id, [string[]]$pyArgs) {
  $msg = "===== $id $(Get-Date -Format o) ====="
  Add-Content $master $msg
  Write-Host $msg
  $logFile = Join-Path $logDir "p3_$id.log"
  $outLines = @()
  & python -u train_goal_dino.py @pyArgs 2>&1 | ForEach-Object {
    $line = "$_"
    $outLines += $line
    Add-Content $logFile $line
    Write-Host $line
  }
  if ($LASTEXITCODE -ne 0) { throw "Job $id failed exit $LASTEXITCODE" }
  $dirLine = ($outLines | Where-Object { $_ -match "^output:" } | Select-Object -Last 1)
  if ($dirLine) { Write-Manifest $id (($dirLine -replace "^output:\s*","").Trim()) }
}
$init = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth"
$common = @("--target","endpoint","--init",$init,"--epochs","30","--top-k-checkpoints","3","--context","2","--seed","0")
# B: strict turn x2 | C: strict turn x3 | D: curvature tiers 1/1.5/3
Run-Job "B_ctx2_turnstrict_x2" ($common + @("--turn-strict-weight","2","--run-name","p3_B_ctx2_turnstrict_x2"))
Run-Job "C_ctx2_turnstrict_x3" ($common + @("--turn-strict-weight","3","--run-name","p3_C_ctx2_turnstrict_x3"))
Run-Job "D_ctx2_curvature_tiers" ($common + @("--curvature-tiers","1,1.5,3","--run-name","p3_D_ctx2_curvature_tiers"))
Write-Host "P3 turn batch complete $(Get-Date -Format o)"
python -u analyze_p3_morning_table.py
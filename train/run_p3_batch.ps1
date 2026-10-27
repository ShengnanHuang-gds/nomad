$ErrorActionPreference = "Continue"
Set-Location "c:\Users\61078\Desktop\nomad\visualnav-transformer\train"
$logDir = "logs\queues"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$manifest = Join-Path $logDir "p3_batch_manifest.jsonl"
$master = Join-Path $logDir "p3_batch_master.log"
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
    $_ | Out-String | ForEach-Object { $outLines += $_; Add-Content $logFile $_ }
    Write-Host $_
  }
  if ($LASTEXITCODE -ne 0) { throw "Job $id failed exit $LASTEXITCODE" }
  $dirLine = ($outLines | Where-Object { $_ -match "^output:" } | Select-Object -Last 1)
  if ($dirLine) { Write-Manifest $id (($dirLine -replace "^output:\s*","").Trim()) }
}
$init = "logs/nomad_d/nomad_dino_wp_e60_2026_10_20_20_29_32/dino_dir_best.pth"
$common = @("--target","endpoint","--init",$init,"--epochs","30","--top-k-checkpoints","3")
Run-Job "R1_ctx2_turn_seedA" ($common + @("--context","2","--seed","0","--turn-winding-deg","90","--turn-weight","2","--run-name","p3_R1_ctx2_turn_seedA"))
Run-Job "R2_ctx2_turn_seedB" ($common + @("--context","2","--seed","1","--turn-winding-deg","90","--turn-weight","2","--run-name","p3_R2_ctx2_turn_seedB"))
Run-Job "R3_ctx2_turn_seedC" ($common + @("--context","2","--seed","2","--turn-winding-deg","90","--turn-weight","2","--run-name","p3_R3_ctx2_turn_seedC"))
Run-Job "R4_ctx0_seedB" ($common + @("--context","0","--seed","1","--run-name","p3_R4_ctx0_seedB"))
Run-Job "R5_ctx2_seedB" ($common + @("--context","2","--seed","1","--run-name","p3_R5_ctx2_seedB"))
Run-Job "R6_ctx0_seedC" ($common + @("--context","0","--seed","2","--run-name","p3_R6_ctx0_seedC"))
Run-Job "R7_ctx2_seedC" ($common + @("--context","2","--seed","2","--run-name","p3_R7_ctx2_seedC"))
Write-Host "P3 batch complete $(Get-Date -Format o)"
python -u analyze_p3_morning_table.py
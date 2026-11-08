# R2/R18 training-seed repeat (seeds 1,2)

## Frozen (unchanged)
- seed0: 
omad_e_r2_fair_20261107, 
omad_e_r18_fair_20261107
- Val manifest: al_far_manifest_seed20261107.csv (500 pairs, val diffusion seed=0)
- No new Locked eval this round

## New runs
| train_seed | R2 run | R18 run |
|---:|---|---|
| 1 | nomad_e_r2_fair_20261107_seed1 | nomad_e_r18_fair_20261107_seed1 |
| 2 | nomad_e_r2_fair_20261107_seed2 | nomad_e_r18_fair_20261107_seed2 |

## Launch
`
cd visualnav-transformer/train
python run_r2_r18_seed_repeat.py --seeds 1 2
`

## After all 8 epochs + val per run
`
python run_r2_r18_seed_repeat.py --report-only --seeds 1 2
python r2_r18_multiseed_report.py
`

Outputs: seed_repeat_audit.json, summary_seed1.json, summary_seed2.json, multiseed_table.csv, multiseed_summary.json.

## Code change
	rain_arm(..., train_seed=0) passes --seed and uses independent --run-name suffix _seed{N}.

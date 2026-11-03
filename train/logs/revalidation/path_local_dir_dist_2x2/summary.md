# Local 8-point path direction × distance (locked far 1000)
- Round PP baseline: **17.70 cm** (do not merge with other noise draws)
- PP vs export nav_pred_samples max |diff|: 1.035e+01 (mean frame ADE Δ≈−0.13 cm vs export; GPU diffusion nondeterminism; **within-round** GP/PG/GG share identical noise with PP)
- GP/PG points kept at pred (undefined dir): GP=0, PG=0 / 8000

## Main table

| 条件 | 路径方向来源 | 路径距离来源 | ADE (cm) | Δ vs 本轮PP (cm) |
|---|---|---|---:|---:|
| PP | 预测路径 | 预测路径 | 17.70 | +0.00 |
| GP | 真实方向 | 预测距离 | 13.30 | -4.39 |
| PG | 预测方向 | 真实距离 | 16.28 | -1.42 |
| GG | 真实方向 | 真实距离 | 11.51 | -6.19 |

## Decomposition (cm)

- dir_only_from_pp_cm: -4.392
- dist_only_from_pp_cm: -1.417
- dir_when_dist_is_gt_cm: -4.771
- dist_when_dir_is_gt_cm: -1.795
- interaction_cm: -0.379
- I = ADE(GG) - ADE(PG) - ADE(GP) + ADE(PP)

## Bootstrap 95% CI (paired frame, cm)

- GP_minus_PP: -4.392 [-4.877, -3.920]
- PG_minus_PP: -1.417 [-1.652, -1.185]
- GG_minus_PG: -4.771 [-5.293, -4.266]
- GG_minus_GP: -1.795 [-2.030, -1.567]
- interaction_frame: -0.379 [-0.616, -0.145]

## Subsets (ADE cm / Δ vs PP cm)

### all

- PP: n=1000 ade=17.70 Δ=+0.00
- GP: n=1000 ade=13.30 Δ=-4.39
- PG: n=1000 ade=16.28 Δ=-1.42
- GG: n=1000 ade=11.51 Δ=-6.19

### strict_turn

- PP: n=593 ade=20.23 Δ=+0.00
- GP: n=593 ade=14.45 Δ=-5.77
- PG: n=593 ade=18.73 Δ=-1.49
- GG: n=593 ade=12.65 Δ=-7.58

### strict_straight

- PP: n=179 ade=13.71 Δ=+0.00
- GP: n=179 ade=11.68 Δ=-2.03
- PG: n=179 ade=11.88 Δ=-1.84
- GG: n=179 ade=9.68 Δ=-4.03

### middle

- PP: n=228 ade=14.24 Δ=+0.00
- GP: n=228 ade=11.59 Δ=-2.65
- PG: n=228 ade=13.35 Δ=-0.89
- GG: n=228 ade=9.97 Δ=-4.27


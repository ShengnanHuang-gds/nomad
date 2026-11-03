# pathact8 full1000 residual diagnosis
Generated UTC: 2026-11-03T08:33:41.953739+00:00
## Verification (independent from checks.json)
- verify_ok: **True**
- [PASS] n_frames: n=1000
- [PASS] horizon: H=8
- [PASS] num_samples: S=8
- [PASS] finite_nav: nav finite
- [PASS] finite_gt: gt finite
- [PASS] finite_path: path_cond finite
- [PASS] ade_recompute: max |recompute - ade_edino_m| = 0.00e+00 m
- [PASS] mean_s_mean_k: mean_s(mean_k dist)=0.178289 mean_k(mean_s dist)=0.178289 saved_mean=0.178289
- [PASS] per_step_then_mean: mean_k(per_step_mean_s)=0.178289
- [PASS] hash_pathact8_ckpt: full=d3b6053c1efb6aac5a59be8ca6e27aecc0a4ec13ecc9dbe7cfe74da9e9b00bf6 smoke=d3b6053c1efb6aac5a59be8ca6e27aecc0a4ec13ecc9dbe7cfe74da9e9b00bf6
- [PASS] hash_wp_head: full=c2197c133d08cd9b84329d73385b183974d9c42a8c3b9fc0b2f4615156b97d4d smoke=c2197c133d08cd9b84329d73385b183974d9c42a8c3b9fc0b2f4615156b97d4d
- [PASS] e_dino_pos_rebuild: mu+path_cond matches e_dino_pos
- [PASS] path_cond_not_copy_gt: mean L2(path_cond, gt) dataset units = 4.8818

## ADE: new export vs audit (code fact)
- Audit `per_frame.npz` E-dino mean: **17.75 cm** (seed/noise from original eval run).
- This export mean ADE: **17.83 cm** (seed=0).
- Export meta seed/num_samples: 0, 8
- Difference does not imply model change; diffusion noise is resampled unless seed and pipeline match exactly.

## A. 20-frame phenomena supported at n=1000?
**Supported (statistical):**
- Path-head full8 vs nav ADE correlation remains positive (Pearson r=0.868).
- Path-head mean error (16.93 cm) same order as nav ADE (17.83 cm).
- Tail concentration: worst 10% frames contribute 26.6% of summed frame ADE.

**Not supported / not testable from smoke alone:**
- Smoke20 Pearson r≈0.918 **attenuates** at n=1000 (r≈0.868); correlation is real but not as extreme as 20-frame subsample suggested.

## B. Not supported
- Claim that resampled export must reproduce 17.75 cm exactly.
- Using nav last-4 vs nav ADE correlation as independent mechanism proof (last-4 is part of ADE).

## C. Best-supported bottleneck (inference)
- **Path-conditioned nav error co-moves with path-head error** across frames; when path is wrong, deploy nav tends to worsen. This fits **path quality on hard frames** and/or **UNet following the given path**, but correlation alone is not causal.

## D. Still uncertain
- Fraction of gap from UNet under-using path vs faithfully tracking bad path (needs fidelity metrics, not in this script).
- Whether step-error growth is geometric accumulation vs radial amplification (radial GT vs err correlation at step 8: Pearson -0.377 — descriptive only).
- Pure 2D far baselines without missing checkpoints.

## E. One change worth validating (no training this round)
- **GT path noise sweep** on frozen checkpoint (eval probe only): map path RMSE → nav ADE without oracle PG numbers.

## Scene strata (mean nav ADE cm)
- strict_turn: n=593, mean=20.38, path_head=18.88
- strict_straight: n=179, mean=13.80, path_head=13.94
- middle: n=228, mean=14.36, path_head=14.20

## Tail dominance (sum of frame ADE cm)
- Worst 1%: 3.8% of total
- Worst 5%: 15.5% of total
- Worst 10%: 26.6% of total
- Worst 20%: 43.5% of total

## Top trajectories by summed frame ADE (not independent samples)
- sim31hF_0_3: sum_ADE=319.4 cm over 12 frames
- sim23hF_1_6: sum_ADE=312.8 cm over 7 frames
- no6vcF_77_0: sum_ADE=289.4 cm over 11 frames
- no2vc_128_0: sum_ADE=282.4 cm over 11 frames
- sim35hF_0_2: sum_ADE=281.9 cm over 10 frames
- sim29hF_1_0: sum_ADE=274.2 cm over 8 frames
- no16vc_29_1: sum_ADE=271.0 cm over 10 frames
- no26vc_4_1: sum_ADE=265.2 cm over 17 frames
- no15vcF_15_0: sum_ADE=251.9 cm over 19 frames
- sim22hF_0_4: sum_ADE=232.7 cm over 8 frames

## Leave-one-trajectory-out correlation (path8 vs nav)
- Trajectories: 263; mean LOO Pearson r=0.868

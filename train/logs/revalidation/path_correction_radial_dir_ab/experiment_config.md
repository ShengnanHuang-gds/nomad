# Path correction A/B (frozen pathact8)

## Hypothesis / prior

Locked Oracle: local **direction** swap ~4.39 cm vs **distance** ~1.42 cm (upper bound only).

## Frozen stack

| Module | Status |
|---|---|
| DINOv2 token cache (inputs) | frozen (precomputed) |
| `PairTokenHead.proj/encoder/norm` | frozen |
| `PairTokenHead.out` (dir/κ) | frozen |
| `PairTokenHead.path_head` (Linear 256→16) | frozen, always `eval()` |
| Correction MLP | **trainable** (only params with grad) |
| Diffusion E / B | not loaded in this train script |

## Feature tap (correction input)

Tensor **`path_in`** = `PairTokenHead._path_feat(x, feat, odom)` immediately before `path_head`.
For pathact8 checkpoint: **256-d CLS** (`feat = norm(encoder CLS)`) — same as `path_head.weight` in_features.
Not endpoint μ, not GT path, not diffusion cond.

## Branches (zero-init ⇒ identity)

| Group | Param | Update |
|---|---|---|
| **A dist** | `s_k = MLP(path_in)_k` | `p_k = exp(s_k) * p_base_k` |
| **B dir** | `θ_k = MLP(path_in)_k` (rad) | `p_k = R(θ_k) p_base_k` |

Shared MLP: Linear(D,128)→GELU→Linear(128,8); **no dropout**; last layer 0-init.

## Training (identical except `--correction-mode`)

- Init: `C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth` sha256=`c2197c133d08cd9b84329d73385b183974d9c42a8c3b9fc0b2f4615156b97d4d`
- Train endpoint frames: **123125**
- Batches/epoch: **962** (= ceil(frames/128))
- Updates/group (8 ep): **7696**
- Trainable params/group: **33928**
- Loss: SmoothL1 on 8 (x,y) vs GT, β=1.0, dataset units; mean over K and xy
- Sample weight: `steps / FAR_STEPS` (same as path term in `train_goal_dino`, no extra turn/tail weights)
- Optim: AdamW lr=1e-4 wd=0.05; grad clip 1.0; warmup 1 epoch linear then cosine
- Select **`dino_dir_best.pth` by lowest val far path ADE** (`far_path_ade_cm`)

### Commands (not auto-run)

```powershell
cd C:\Users\61078\Desktop\nomad\visualnav-transformer\train
$env:PYTHONPATH="../diffusion_policy"
# A — distance correction
C:\Users\61078\anaconda3\envs\nomad_train\python.exe -u train_path_correction_ab.py --init C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth --batch-size 128 --epochs 8 --seed 0 --max-batches 0 --lr 1e-4 --weight-decay 0.05 --context 2 --path-steps 8 --correction-mode dist --run-name nomad_dino_wp_pathcorr_dist
# B — direction correction
C:\Users\61078\anaconda3\envs\nomad_train\python.exe -u train_path_correction_ab.py --init C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth --batch-size 128 --epochs 8 --seed 0 --max-batches 0 --lr 1e-4 --weight-decay 0.05 --context 2 --path-steps 8 --correction-mode dir --run-name nomad_dino_wp_pathcorr_dir
```

## Consistency checks

- Report: `logs\revalidation\path_correction_radial_dir_ab\consistency_checks.json`
- All passed: **True**

## Downstream nav eval (prepare only — two protocols)

Use frozen E checkpoint `logs/nomad/nomad_e_ft_pathact8/ema_latest.pth`, locked CSV `paired_frames_far_20-40.csv`, num_samples=8, batch_size=8, seed=0, **shared noise** across models.

### Protocol 1 — fixed μ, swap 16-d path only

Keep exported **`mu_units`** from baseline; build `e_dino_pos = concat(mu, flat(corrected_path))`. Does not recompute κ-blend from WP/DINO.

```powershell
# After training — placeholder entrypoint (to implement before running locked1000):
python eval_path_correction_locked_nav.py \
  --mode fixed_mu \
  --wp-base logs/nomad_d/.../pathact8/dino_dir_best.pth \
  --wp-corr-a logs/nomad_d/nomad_dino_wp_pathcorr_dist_*/dino_dir_best.pth \
  --wp-corr-b logs/nomad_d/nomad_dino_wp_pathcorr_dir_*/dino_dir_best.pth \
  --e-run logs\nomad\nomad_e_ft_pathact8 \
  --frames logs\revalidation\eval_audit_pathact8_far\paired_frames_far_20-40.csv \
  --seed 0 --num-samples 8 --batch-size 8
```

### Protocol 2 — full deploy (κ from corrected path endpoint dir)

Recompute blend μ via existing `blend()` using **corrected path last-point direction** (κ from frozen dir heads — **not recalibrated**; document κ source in run meta).

```powershell
python eval_path_correction_locked_nav.py \
  --mode deploy_blend \
  --goal-pos-mode blend_path --path-source wp_poly \
  ... (same wp/e/frames/seed/noise flags as protocol 1)
```

## Success criteria (later)

- Val path ADE improves vs frozen base on far + turn buckets
- Locked1000 **path quality and nav ADE** both improve under each protocol
- Do not claim win from train loss alone

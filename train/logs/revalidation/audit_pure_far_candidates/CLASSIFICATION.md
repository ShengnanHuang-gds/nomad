# Classification (pure far baseline definition)

**Definition:** goal image on; append **μ = DINO_far_dir × B_distance_steps** (dataset units); **no** WP κ-blend; **no** 8-step path (`goal_pos_dim=2`).

---

## Satisfies definition (train + locked eval μ)

| Run | Role | Caveats |
|-----|------|---------|
| **nomad_e_dino_d2_2026_10_19_09_37_58** | Primary 2D E-μ candidate | Train `goal_pos_mode` / `init_from` **not in args.txt**; use **eval_ema_20** for same locked protocol as revalidation; **eval_ema_29** is separate snapshot |
| **nomad_e_dino_ft_oracle_true0** | E-oracle-init FT, test-time pure DINO μ | Train uses DINO μ only (`true_pos_prob=0`); checkpoint mismatch ema_0 vs ema_9 |
| **nomad_e_dino_ft_oracle_true50** | Same with 50% GT pos during train | Eval still pure DINO μ; **not** comparable train recipe to d2 without acknowledging true_pos mix |

All three: **【已有实验事实】** `pos_dim=2`, no `wp_head` / no `blend_path` in args; eval queue commands omit `--goal-pos-mode blend*`.

---

## Reference only (do not treat as pure baseline)

| Item | Why |
|------|-----|
| **E-oracle+DINO** row inside some `paired_far.csv` | Same eval run; 2D μ on **E-oracle UNet**, not the trained E-dino checkpoint |
| **counterfactual_vs_b_distance80** e_dino_d2 metrics | Different metric (D_goal), n=80, not Locked 1000 ADE |
| **nomad_e_dino_d2_blend** / pathact8 | κ-blend and/or path — excluded |

---

## Not confirmed / missing

1. **d2 training CLI** (epochs 30 vs ft 10, lr schedule, init_from b vs e_oracle).  
2. **Whether d2 training used `goal_pos_mode=goal`** explicitly (likely if no wp_head, but args incomplete).  
3. **Checkpoint files** for several saved evals (`ema_20`, `ema_9`, `ema_0`) — logs reference them; **.pth absent** on disk snapshot.  
4. **Single official baseline checkpoint** — intentionally **not** chosen here (tune_use vs test ADE disagree).  
5. **Per-step predictions** — not in any `per_frame.npz`; Phase 3 placeholder remains in `audit_supplement/phase3_diagnostics/`.  
6. **Bit-identical cross-model pairing noise** for d2 `eval_ema_29` vs pathact8 — **refuted** by `ade_B` mismatch; use manifest + `FRAME_INDEX_POLICY.md`.

---

## ema_20 / ema_29 / ema_9 / ema_0 (summary)

| Token | Source | Criterion | Used for |
|-------|--------|-----------|----------|
| **ema_20** | d2 | Highest **tune_use_cm** on **600-frame tuning set** (`tune_e_epochs.csv`, `selection.json`) | `eval_ema_20/` locked revalidation |
| **ema_29** | d2 | On disk; **counterfactual** meta; separate eval dir | `eval_ema_29/` (different B baseline vs audit) |
| **ema_9** | ft_oracle | **queue_c16_then_eft.ps1** post-train eval | `eval_ema_9/` (primary saved ft eval) |
| **ema_0** | ft_oracle | Best **tune_use** on tuning set (`selection.json`) | `eval_ema_0/` from revalidate queue |

**None of these selections used Locked 1000 test ADE as the selection objective** (`revalidate.py` docstring: tuning set disjoint from locked frames).

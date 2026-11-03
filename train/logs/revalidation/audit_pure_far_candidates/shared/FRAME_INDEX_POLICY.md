# Frame index policy (Locked Far 20–40, n=1000)

## 【代码事实】

- `eval_e_dino.py` builds  
  `far = [(name, t, goal_time_far) for … in load_paired_frames(PAIRED_FRAMES)]`  
  with bin `"20-40"` (`eval_frame_sets.PAIRED_FRAMES` →  
  `logs/nomad/nomad_b40_2026_09_29_16_35_23/eval_epoch20_paired/paired_frames.csv`).
- Loop order over `far` defines row `i` in `per_frame.npz` (`ade_*[i]`).
- `per_frame.npz` does **not** store `traj_name`, `t`, or `goal_time`.

## 【已有实验事实】

- Byte-for-byte equality check (2026-11-03): the ordered list `far` from `PAIRED_FRAMES` matches  
  `eval_audit_pathact8_far/paired_frames_far_20-40.csv` (1000 rows, same triples).

## Derived manifest

- `shared/paired_frames_far_20-40.csv`: columns `traj_name,t,goal_time`, row `i` ↔ `frame_index=i`.
- `candidates/.../per_frame_audit.csv`: joins manifest columns with ADE fields from each `per_frame.npz`.

## Cross-run pairing with pathact8

- **Same moments:** use identical `traj_name,t,goal_time` via `frame_index`.
- **Same diffusion noise / B baseline row:** **not** guaranteed across all saved evals.
  - Example: `nomad_e_dino_d2` `eval_ema_29` has `ade_B` mean diff ≈ 2.3 cm vs  
    `eval_audit_pathact8_far/per_frame.npz` at the same index.
  - `eval_ema_20` (d2) and `ft_oracle_*` `eval_ema_9` match pathact8 audit `ade_B` on most frames  
    (mean |Δ| ≈ 0.18 cm for ft0), consistent with shared locked eval protocol after `revalidate.py` queue.

**Do not** infer pathact8 pairing from `len=1000` alone; use manifest + noise check when comparing ADE diffs.

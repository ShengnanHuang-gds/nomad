# Pure far baseline — evidence audit pack

**Scope:** export existing artifacts for three 2D μ-only run directories.  
**No training, no re-eval, no changes to `eval_e_dino.py` / `train_e_dino.py`.**

Does **not** duplicate `eval_audit_pathact8_far/` (deploy pathact8).  
Checkpoints (`.pth`) stay on disk only — see `CHECKPOINTS_ON_DISK.txt`.

## Layout

```
audit_pure_far_candidates/
  README.md
  CLASSIFICATION.md          # which candidate satisfies the definition
  CHECKPOINTS_ON_DISK.txt
  shared/
    nomad_e_dino_mu.yaml
    paired_frames_far_20-40.csv   # sample manifest (traj_name,t,goal_time)
    FRAME_INDEX_POLICY.md
    selection.json                # revalidate.py tuning-set checkpoint picks
    tune_e_epochs.csv
    train_eval_evidence_queue.txt # verbatim queue snippets (executed)
  candidates/<run_dir>/
    args.txt, train_log.csv, eval logs…
    eval_ema_*/paired_far.csv, per_frame.npz, per_frame_audit.csv
```

## Sample index

`per_frame.npz` stores **only** scalar ADE arrays (no `traj_name`).  
Join via `frame_index` = row index in `shared/paired_frames_far_20-40.csv` — see `FRAME_INDEX_POLICY.md`.

# val_metrics.csv (v1) — known issues

- Sample index: `np.arange(len(starts))` instead of `draw(val_pairs, rng(1234))`.
- Turn wrong-way: mean cosine, not end-direction error >45/>90 fraction.

Use `path_readout_ab_v2/` for conclusions.

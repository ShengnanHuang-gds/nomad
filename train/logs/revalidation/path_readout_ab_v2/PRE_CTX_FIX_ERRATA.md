# eb7b56e 结果说明（ctx 未传入）

`path_readout_val_core.make_val_loader` 曾写成：

```python
loader(cache_path, val_pairs, chosen, batch_size, False, 0, context)
```

而 `loader(..., flip, seed, workers, context=0)` 将 `context=2` 误绑到 **workers**，实际 **context=0**，两帧历史未进入模型。

该版本 summary 中 A≈17.31 cm、B≈17.70 cm **不能**作为 ctx2 训练条件下的结论。

修复后见 `ctx_check.json`（`context_frames: 2`）及本目录更新后的 `summary.csv`。
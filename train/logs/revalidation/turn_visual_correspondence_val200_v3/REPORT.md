# 转弯视觉匹配 v3（13 例，修正 S[h,c] 与绘图）

## 代码事实

- **约定**：`S[h,c]` = 历史 patch `h` 与当前 patch `c` 的余弦相似度（形状 `n_hist × n_curr`）。
  - 历史→当前：`hist_to_curr_nn = argmax(axis=1)`；
  - 当前→历史：`curr_to_hist_nn = argmax(axis=0)`；
  - 双向一致：`(h,c)` 满足 `c==hist_to_curr[h]` 且 `h==curr_to_hist[c]`，相似度取 **`S[h,c]`**。
- **修正**（相对 v2）：见 [`../turn_visual_correspondence_val200_v2/V2_ERRATA.md`](../turn_visual_correspondence_val200_v2/V2_ERRATA.md)。
- **CSV 数字**：本目录 `case_stats.csv` 与 v2 **数值列一致**（v2 统计循环未触发 draw 中的 `sim_far` 覆盖）；**案例图 t−2 面板以 v3 为准**。
- **Checkpoint**：`logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth`
- **命令**：`PYTHONPATH=../diffusion_policy python run_turn_visual_correspondence_v3.py`
- **单元验证**：`PYTHONPATH=../diffusion_policy:. python tests/test_turn_match_convention.py`（非对角 4×5 矩阵）

## 实验观察

- 13 例修正图：`cases/*_v2.png`；v1 假线：`cases/*_v1_style_DEPRECATED.png`。

## 尚不能回答

- DINO 离线匹配仍不等于模型内部 goal/ctx 利用；见 [`../goal_sensitivity_pathact8_val13/REPORT.md`](../goal_sensitivity_pathact8_val13/REPORT.md)。

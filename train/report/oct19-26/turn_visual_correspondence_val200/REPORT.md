# Turn vs visual correspondence diagnostic (val, N≤200)

## 代码事实

- **历史帧**：ctx2 使用 **t−1** 与 **t−2**（数据集帧索引，一步一格；**未**按 `waypoint_spacing` 乘间隔）。
  见 `train_goal_dino.build_pairs` / `eval_e_dino.head_predict_wp_path`（`curr-j`, j=1..context）。
- **边界**：依赖 pickle 索引与 `context_size=3` 的 ViNT 索引；本脚本要求 `curr≥2` 且 cache 含对应 key，否则跳过。
- **图像预处理**：与 `cache_dino_features.FrameImages` 一致——宽图中心裁 **4:3**，再 **224×168** BICUBIC，ImageNet 归一化后进 DINO；
  本诊断读 **预缓存 tokens**（`logs/dino_cache/dinov2_vits14_reg/train/features.npy`）。
- **八步头**：`PairTokenHead` 将 **curr / goal / 两帧 ctx** 的 DINO token（每帧 1 CLS + 6×8 patch）投影后加 `pos`/`kind`，
  经 **4 层 TransformerEncoder** 自注意力混合；pathact8 的 8 点路径来自 **CLS 特征** 的 `path_head`（非 lcr 空间读出）。
  **保留** patch 级 token 与网格位置；跨帧交互在 transformer 内完成，并非“无时序建模”。
- **Checkpoint**：`logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth`（冻结推理，无训练）。

## 抽样

- seed=20261103, n=200, trajectories=123, groups={'straight': 72, 'moderate_turn': 59, 'sharp_turn': 69}.
- DFT val trajectories only; endpoint-style frames with ctx t-1,t-2; goal token at curr+min(39,max_goal); stratified ~1/3 straight/moderate/sharp by path_winding_deg; max 1 frame per traj per 15 index steps when possible.

## 观察结果（描述性）

- 急转弯子集（winding≥45°）按 path ADE 中位数分好/差：好组 mutual_match_near≈0.842 (n=35), 差组≈0.833 (n=34); 平均 path ADE 8.04 vs 29.30 cm。
- 全体样本：**较近历史 t−1** 的平均 mutual NN cosine ≈ 0.871，**较远 t−2** ≈ 0.821（差 +0.050）。
- 高 path ADE（≥p75）且匹配度不低于全体中位数的样本：24/50。

## 研究推断（弱，非因果）

- 若在相近转弯子集内“差预测”组的 patch NN 相似度系统性更低，则与“参照减少”**一致**，但也可由纹理重复、
  运动模糊、遮挡或 **路径长度/动力学** 混淆；本批未做偏相关控制。
- 若 t−1 一致高于 t−2，则支持“**较近历史**通常保留更多可匹配外观”，但不等于 overlap 率。

## 尚不能判断

- 不能证明视野重叠减少 **导致** 八步失败；样本≤200，未控 path length 的回归。
- 不能推荐具体新结构；证据不足以在“改历史采样”与“加强已有 transformer 交互”之间下定论。

## 问题简答

1. **相近急弯（winding≥45°）内好/差预测**：mutual NN（t−1→curr）好组 0.842 vs 差组 0.833，差仅 ~0.01，**不支持**“失败样本普遍对应更少”。在 **路径长度中段四分位** 子集内，差组匹配反而略高（0.838 vs 0.829，n≈18/17）——**反例**，不能归因于参照减少。
2. 较近帧 t−1 的 mutual NN cosine 平均更高（Δ=+0.050），符合“较近历史更易匹配”的描述趋势。
3. 存在反例：至少 24 个高 ADE 样本仍有不低于中位的匹配度（见 cases/counter_*）。
4. 证据不足，暂不优先二选一；若需工程试探，可先试 **历史采样/间距**（代价低），因 head 内已有 4 层跨 token 交互。
5. 样本有限，仅报告描述性趋势；见 `samples.csv` 与 `cases/`。

## 交付文件
- `samples.csv`, `meta.json`, `cases/*.png`, 本报告。
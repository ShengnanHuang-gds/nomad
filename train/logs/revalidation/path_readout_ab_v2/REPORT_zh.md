# 路径头读出 A/B 验证报告（v2）

## 协议与 Checkpoint（代码事实）

- **固定 ckpt**（见 `checkpoints.json`）：A=`pathreadout_A_cls` epoch 8；B=`pathreadout_B_stepq` epoch 8；参考=`pathact8` 续训前 best（epoch 8）。
- **初始化差异（实验事实）**：A 从 pathact8 续训并**继承** `path_head`；B 加载时跳过原 `path_head`，**重新初始化** `path_queries` / `path_step_head`，dir/κ 仍来自同一 init 且 `--freeze-dir`。
- **验证配对**：`draw(val_pairs, np.random.default_rng(1234))`，与 `train_goal_dino.py` 验证一致；`flip=False`；head `eval()`。
- **far**：`goal_step >= 20`（FAR_STEPS，**索引步数**，非米）。
- **转弯子集**：GT 未来 8 步 **累计绝对 yaw**（`winding`，`path_winding_deg`），**不是** `turn_strict`。
- **末端方向**：第 8 点相对当前机器人原点的方向夹角；`>45°` / `>90°` 为比例（分母为方向可定义样本）。
- **`pred_polyline_turn_deg`**：预测折线相邻段夹角之和，**不是**相对 GT 的误差，仅作形状描述，不作“越低越好”的 GT 对齐指标。

## 清单质量（实验事实）

| 项 | 值 |
|---|---|
| 验证样本数 | 11519 |
| 唯一当前帧 | 11519（= frame_slots） |
| manifest 内轨迹数 | **156**（DFT val 列表 **236** 条；未覆盖的轨迹在本 split 无有效 endpoint 帧） |
| far (step≥20) | 5110 |
| winding≥45° | 5943 |
| winding≥90° | 2313 |
| turn_strict（仅对照，非主子集） | 4355 |
| 末端方向不可定义 | 0 |

固定清单：`val_pair_manifest.csv`。

## 汇总指标（八点位置 ADE，cm，等权平均）

| 子集 | A ade8 | B ade8 | A back4 | B back4 | A front4 | B front4 |
|---|---|---|---|---|---|---|
| 全体 | 17.31 | 17.70 | 27.31 | 27.70 | 7.32 | 7.71 |
| far | 16.93 | 17.27 | 26.71 | 27.03 | 7.15 | 7.52 |
| winding≥45 | 20.13 | 20.48 | 31.97 | 32.32 | 8.28 | 8.64 |
| winding≥90 | 24.53 | 24.79 | 38.95 | 39.29 | 10.11 | 10.28 |

末端方向（全体）：A 中位 18.4° / P90 42.5°；B 18.6° / 42.8°。>90° 比例 A 2.50% vs B 2.65%（+0.15 pp）。

## B−A 配对 bootstrap（轨迹分组，2000 次，代码事实）

| 指标 | 均值差 (B−A) | 95% CI |
|---|---|---|
| 八点 ADE (cm) | **+0.39** | [+0.28, +0.49] |
| 后四步 ADE (cm) | **+0.39** | [+0.21, +0.57] |
| 转弯≥45 八点 ADE | **+0.35** | [+0.21, +0.51] |
| 末端 >90° 比例 (pp) | **+0.15** | [−0.01, +0.30]（paired_bootstrap.json） |

正值表示 **B 更差**。

## 四问（区分事实与推断）

1. **正确完整清单上 B 是否优于 A？**  
   **实验事实：否。** 全体与 far、转弯子集的八点/后四 ADE 均为 B 略高；bootstrap CI 对 ADE 全在正侧。

2. **转弯方向改善是否伴随转弯位置改善？**  
   **实验事实：未观察到方向改善。** winding≥45 上位置 ADE 仍变差（B−A≈+0.35 cm）；末端 >90° 比例略升。  
   **推断：** 不存在“方向好了、弯上也好了”的联动。

3. **前四/后四是否退化？**  
   **实验事实：两段均略退化**（B front4 +0.39 cm、back4 +0.39 cm 量级，与全体一致）。

4. **是否值得做固定 ckpt 的下游 Locked 导航？**  
   **推断：本轮不值得。** 路径头验证无稳定收益且有统计显著的 ADE 变差；**不能**用本报告的路径 ADE 替代导航 ADE 或宣布下游刷新。

## v1 旧结果

`../path_readout_ab/val_metrics.csv` 已标注 `val_metrics.ERRATA.md`（索引与错向率定义问题）。**勿用 v1 做结论。**

## 复现

见 `eval_command.txt`；入口 `eval_path_readout_val_v2.py`。
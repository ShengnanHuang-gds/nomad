# go_stanford 采样密度只读分析

## 1. 训练实际配置（证据）
- 数据路径: `C:/Users/61078/Desktop/nomad/go_stanford`
- train 轨迹数: **2956**（`traj_names.txt`）
- `context_size=3`，`context_type=temporal` → 当前帧 + 过去 3 步，**步长 waypoint_spacing=1** → **4 张相邻索引图**
- `len_traj_pred=8`，`waypoint_spacing=1` → 标签动作为 **连续 8 个索引步**（约 8×0.12 m 名义跨度）
- `metric_waypoint_spacing=0.12 m`（归一化用；来自 `data_config.yaml`）
- pathact8 WP 头 **context=2**（DINO cache 历史帧，与 ViNT 的 4 图 context 不同）
- e_path O/A/B 实测: batch=32, epochs=8（见 `e_path_joint_ab_2026-11-08`）

## 2. 图像 vs 位姿
- 扫描 train 轨迹: **2956**
- 索引不一致: **0**

## 3. 相邻帧转角 |Δyaw|（度，全 train 边）
- n=156245, median=5.18, P90=21.01, P95=25.14
- ≥5°: 50.72%, ≥10°: 33.38%, ≥20°: 11.40%

### 直线边（|Δyaw|<5°）
- n=77001, median=0.24, P90=3.64, P95=4.34

### 转弯边（|Δyaw|≥5°）
- n=79244, median=12.86, P90=25.05, P95=27.05
- ≥10°: 65.82%, ≥20°: 22.48%

### 相邻帧位移（米，欧氏）
- median=0.1457, P90=0.1667, P95=0.1670 m

## 4. 与「转弯误差大」相关的评估证据（O 基线，500-pair val）
- 全样本 nav ADE 11.769 cm；后四步 18.588 cm
- 严格转弯子集 (n=169): nav 15.816 cm；后四步 25.492 cm

## 5. 困难样本过采样（已证实）
- `hard_frame_boost` / `hard-pairs-csv`：**对已有 (traj, curr) 索引加权重采样**，不生成新图像。
- 示例: `run_ab_mainline_hardwp.py`（boost=5，turn-only pairs）。
- **NoMaD E 训练 (`train_e_dino`) 未接该过采样。**

## 6. 缺失项（无法做处理前后对比）
- **go_stanford_raw_ros_bags**: not found under go_stanford/ (*.bag count 0)
- **go_stanford_hdf5_source**: not in repo; process_recon.py applies to 'recon' HDF5, not go_stanford
- **traj_data_timestamp_fields**: traj_data.pkl only has position, yaw (no t/sec) — cannot compute Hz
- **preprocessing_log_for_go_stanford**: no recorded export command in repo for this machine's go_stanford tree

## 7. 结论（证据分级）
**已证实**
- 处理后每条轨迹 **图像数 = 位姿数**（本 split 扫描结果见 JSON）。
- 训练使用 **索引步长 1**：一图一位姿，无插值中间帧。
- 转弯边占比与 |Δyaw| 分布见统计；相当大比例相邻边存在 ≥5° 转角。
- 验证集上 **转弯 / 后四步 ADE 明显高于平均**（同协议 O 基线）。
- 困难过采样 = **重复采样已有帧**，不是补中间视角。

**无法仅凭本仓库断定**
- go_stanford **原始采集频率**及导出时是否抽稀/删原地转（无 bag/无时间戳）。
- 转弯误差是否 **主要由** 缺少中间视角导致（与模型、条件、扩散多因素耦合）。

**建议优先级（基于证据，非最优保证）**
1. 若可获得原始 go_stanford 或同类 **高频轨迹+同步图**：先做 **重抽帧/保留转弯段** 的小规模消融（比继续堆模型改动更可验证）。
2. 在现有数据上，**过采样已有转弯帧** 已尝试过但未解决 E 侧根本瓶颈；单独加 os **不能** 代替新视角。
3. **换更高密度数据集** 仅当有明确更高 Hz/更短间距证据时优先考虑。
4. **继续调模型** 仍合理，但本轮 e_path joint A/B 仅带来 ~0.1 cm 级边际改善，提示数据/视角上限可能是主因之一（待原始数据验证）。

图例: `examples/rank*_*/` + `frames.csv`
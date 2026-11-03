# 目标图像敏感性诊断（13 验证案例）

## 代码事实

- Checkpoint: `logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth` (sha256[:16]=c2197c133d08cd9b)
- Git: `0a0f41a`
- 命令: `C:\Users\61078\anaconda3\python.exe run_goal_sensitivity_val13.py`
- 冻结 pathact8 路径头；固定 curr、t-1、t-2；**仅更换同轨迹合法 goal**
- 合法 goal 索引间隔 k∈[4, min(39, max_goal)]；附加 goal 要求 **k > 8×spacing**
- 同一条轨迹上 GT 八步路径不变；本实验看 goal 距离/外观变化下的输出，**不是分岔意图实验**

## 逐例简答

### counter_high_match_high_ade — no2vc_5_0 t=40
- **【实验观察】** 共 4 个 goal（原 goal Δidx=19）
- **【代码事实】** 原 goal ADE=23.29 cm，dir_err=24.6°；换 goal 后 ADE 极差≈0.83 cm，八点均位移相对原 goal 最大≈1.65 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）

### counter_low_match_high_ade — no2vc_65_0 t=3
- **【实验观察】** 共 4 个 goal（原 goal Δidx=16）
- **【代码事实】** 原 goal ADE=52.17 cm，dir_err=107.4°；换 goal 后 ADE 极差≈2.17 cm，八点均位移相对原 goal 最大≈4.72 cm
- **【实验观察】** 预测有**中等幅度**变化
- **【实验观察】** 原 goal 方向误差已大（107°）；换 goal 后 3/3 个附加 goal 仍 >45°

### sharp_bad — sim39hF_0_9 t=95
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=42.22 cm，dir_err=104.9°；换 goal 后 ADE 极差≈2.74 cm，八点均位移相对原 goal 最大≈4.42 cm
- **【实验观察】** 预测有**中等幅度**变化
- **【实验观察】** 原 goal 方向误差已大（105°）；换 goal 后 3/3 个附加 goal 仍 >45°

### sharp_bad — no27vc_26_0 t=179
- **【实验观察】** 共 3 个 goal（原 goal Δidx=11）
- **【代码事实】** 原 goal ADE=50.11 cm，dir_err=147.0°；换 goal 后 ADE 极差≈0.16 cm，八点均位移相对原 goal 最大≈0.84 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）
- **【实验观察】** 原 goal 方向误差已大（147°）；换 goal 后 2/2 个附加 goal 仍 >45°

### sharp_bad — sim12h_1_5 t=23
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=36.13 cm，dir_err=80.2°；换 goal 后 ADE 极差≈2.99 cm，八点均位移相对原 goal 最大≈3.61 cm
- **【实验观察】** 预测有**中等幅度**变化
- **【实验观察】** 原 goal 方向误差已大（80°）；换 goal 后 3/3 个附加 goal 仍 >45°

### sharp_bad — no29vc_35_0 t=47
- **【实验观察】** 共 4 个 goal（原 goal Δidx=28）
- **【代码事实】** 原 goal ADE=30.01 cm，dir_err=80.8°；换 goal 后 ADE 极差≈13.87 cm，八点均位移相对原 goal 最大≈18.55 cm
- **【实验观察】** 预测对 goal 变化**明显**
- **【实验观察】** 原 goal 方向误差已大（81°）；换 goal 后 2/3 个附加 goal 仍 >45°

### sharp_good — sim12h_1_6 t=21
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=14.36 cm，dir_err=22.8°；换 goal 后 ADE 极差≈0.74 cm，八点均位移相对原 goal 最大≈1.09 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）

### sharp_good — no28vcF_5_0 t=59
- **【实验观察】** 共 4 个 goal（原 goal Δidx=22）
- **【代码事实】** 原 goal ADE=5.93 cm，dir_err=11.2°；换 goal 后 ADE 极差≈2.07 cm，八点均位移相对原 goal 最大≈2.42 cm
- **【实验观察】** 预测有**中等幅度**变化

### sharp_good — sim7hF_0_2 t=19
- **【实验观察】** 共 4 个 goal（原 goal Δidx=37）
- **【代码事实】** 原 goal ADE=10.16 cm，dir_err=5.0°；换 goal 后 ADE 极差≈2.93 cm，八点均位移相对原 goal 最大≈3.44 cm
- **【实验观察】** 预测有**中等幅度**变化

### sharp_good — sim10hF_0_13 t=16
- **【实验观察】** 共 4 个 goal（原 goal Δidx=20）
- **【代码事实】** 原 goal ADE=12.34 cm，dir_err=13.6°；换 goal 后 ADE 极差≈1.83 cm，八点均位移相对原 goal 最大≈1.43 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）

### straight_ref — no6vc_77_0 t=157
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=31.57 cm，dir_err=34.4°；换 goal 后 ADE 极差≈6.74 cm，八点均位移相对原 goal 最大≈4.99 cm
- **【实验观察】** 预测有**中等幅度**变化

### straight_ref — no13vc_4_0 t=87
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=5.41 cm，dir_err=5.4°；换 goal 后 ADE 极差≈1.35 cm，八点均位移相对原 goal 最大≈1.56 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）

### straight_ref — no15vc_45_1 t=47
- **【实验观察】** 共 4 个 goal（原 goal Δidx=39）
- **【代码事实】** 原 goal ADE=13.70 cm，dir_err=15.5°；换 goal 后 ADE 极差≈0.84 cm，八点均位移相对原 goal 最大≈1.61 cm
- **【实验观察】** 预测对 goal 变化**几乎不变**（就本例数值而言）

## 研究推断（弱）

- 输出变化小 **不能** 单独证明模型忽略 goal；变化大 **不能** 单独证明模型理解 goal。

## 尚不能回答

- 13 例无法推断总体因果；单个 goal 低 ADE 不是可部署成绩。

## 总问

## 总问（明确回答）

**是否值得进一步研究 goal 条件利用？**  
【实验观察】13 例中多数换 goal 后八点路径相对原 goal 位移 **<3 cm**（`mostly_insensitive_in_these_13`）；**方向大错的失败例**换合法 goal 后 **dir_err 仍 >45°**。  
【研究推断】可继续查路径头在固定 ctx 下对 goal token 的响应，但本轮 **不能** 证明模型“忽略 goal”。

**错误是否对 goal 变化基本不敏感？**  
【代码事实】**不是全体不敏感**：**no29vc_35_0 t=47** 换 goal 后 `mean_pos_shift_vs_orig` 可达 **≈18.6 cm**，ADE 可从 **≈30 cm** 降到 **≈16 cm**（同一 GT）。  
【尚不能回答】该 ADE 改善 **不能** 当作部署成绩；13 例 **不能** 外推全集。

**本轮结论**：证据 **不足以** 自动启动新训练。


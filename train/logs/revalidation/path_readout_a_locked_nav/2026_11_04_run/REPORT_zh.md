# A组 CLS 续训 — Locked Far 1000 下游导航验证（O/F/D）

## 主表（导航 ADE，cm）

| 条件 | μ 来源 | 路径来源 | 绝对 ADE | 相对 O 改善 (O−cond) | 相对下降比例 |
|------|--------|----------|----------|----------------------|--------------|
| O | deploy blend: dino_dir/kappa + b_dist + wp_dir(pathact8末点) + wp_kappa(pathact8头) | pathact8 WP head 8点 | 17.7715 | +0.0000 | 0.000% |
| F | 与 O 完全相同（逐样本复制 mu_units） | A_cls WP head 8点 | 17.6683 | +0.1032 | 0.581% |
| D | deploy blend: dino_dir/kappa + b_dist + wp_dir(A末点) + wp_kappa(A_cls头前向) | A_cls WP head 8点 | 17.7720 | -0.0005 | -0.003% |

## 严格转弯子集

- **O**: ADE=20.2859 cm, n=593
- **F**: ADE=20.1761 cm, n=593
- **D**: ADE=20.3179 cm, n=593

## 配对差值（均值，cm；正值表示相对 O 导航 ADE 降低）

- F_minus_O_nav_ade: mean=-0.1032, improve_frac=0.535
- D_minus_O_nav_ade: mean=0.0005, improve_frac=0.521
- D_minus_F_nav_ade: mean=0.1037, improve_frac=0.464
- improvement_F_vs_O: mean=0.1032, improve_frac=0.535
- improvement_D_vs_O: mean=-0.0005, improve_frac=0.521
- improvement_D_vs_F: mean=-0.1037, improve_frac=0.464

## Bootstrap（轨迹重采样，10000 次，seed=20261103)

- **improvement_F_vs_O**: mean=0.1032, 95% CI [-0.0501, 0.2565]
- **improvement_D_vs_O**: mean=-0.0005, 95% CI [-0.1660, 0.1632]
- **improvement_D_vs_F**: mean=-0.1037, 95% CI [-0.1519, -0.0600]

## 说明
- 改善量定义：ADE_O − ADE_condition；Bootstrap 对帧级配对差值做轨迹池化重采样。
- 历史参考 ADE（~17.75 cm）未参与本轮相减；O 在本轮同协议重算。
- 历史参考（只读）：~17.75 (prior locked run; not subtracted this round)
- D 的 μ 含远目标 κ 与 WP κ 的 blend；WP κ 来自 **A_cls** 头前向（同路径预测一次 forward），非 pathact8 κ；共享 Transformer 更新后 κ 数值可与 pathact8 不同，D−F 不能全归因于末点方向。
- 正式 1000 帧前已在 8 帧上通过 smoke（ctx=2、F μ=O μ、扩散步噪声可复现、同 cond 双分支一致）；见 `../_smoke` 或 `smoke_check.json`（若单独跑 smoke）。

## 结论（本轮 O/F/D）

1. **A 是否降低全量导航 ADE？** 正常部署 **D** 相对 **O** 均值约 −0.0005 cm（略差），Bootstrap 95% CI **[−0.166, +0.163]** 跨零 → **未确认改善**。仅换路径、固定 μ 的 **F** 均值改善 **+0.103 cm**，但 CI **[−0.050, +0.257]** 仍跨零 → **未确认显著**。
2. **严格转弯子集（n=593）？** **F** 20.18 vs **O** 20.29 cm（约 +0.11 cm 改善）；**D** 20.32 cm（略差于 O）。幅度小，且全量 CI 未显著。
3. **固定 μ 是否已有改善？** **是（点估计）**：F 相对 O 约 **0.10 cm**、**53.5%** 帧导航 ADE 更低；**D−F** 均值 **−0.104 cm**、CI 不含零，说明在 A 路径下重算 deploy μ 会 **抵消** 大部分固定-μ 收益（κ/方向 blend 与 pathact8 部署不一致）。
4. **是否足以替代原 pathact8 部署？** **否**。路径 ADE 在本清单上 A_cls 优于 pathact8（16.65 vs 16.93 cm），但 **下游导航未得到经 Bootstrap 确认的增益**；不能以单次训练种子替代多 seed 验证。

**归因**：有效信号若存在，应归于 **A 组 CLS 续训整体路径质量**（F 条件），而非 8-query 读出头；**不能**写成 8 查询创新带来导航提升。

结果目录：`logs/revalidation/path_readout_a_locked_nav/2026_11_04_run/`（含 `meta.json`、`per_frame_eval.npz`、`per_frame_nav_ade.csv`、`eval_command.txt`、`ctx_check.json`）。


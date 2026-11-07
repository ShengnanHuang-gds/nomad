# R2 vs R18 — Locked Far 1000 固定测试结论

**协议说明**：`paired_frames_far_20-40.csv` 1000 个 `(traj_name, t, goal_time)`；goal 索引间隔 **20–40** 为既有口径（非米制距离）。本集合在前期工作中已用于 Locked / pathact8 审计，本轮为**同一固定协议复核**，非新盲测。

**Checkpoint（严格 SHA256 加载）**
- R2：`nomad_e_r2_fair_20261107/ema_4.pth`（验证集 nav ADE 选模 epoch，**非** ema_latest）
- R18：`nomad_e_r18_fair_20261107/ema_1.pth`

**路径条件列审计（ConditionalUnet1D）**  
`global_feature = [diffusion_t_embed(256) | vision_enc(256) | goal_pos]` → `cond_encoder.1.weight` 输入维 **cond_dim = 256+256+pos_dim**。R18 新增 16 列位于 **[514:530)**（非旧 preflight 误用的 [258:274)）；相对 e_oracle 零扩展参考，训练后路径列 max|Δ|≈**0.043**（仅审计，未做 optimizer.step）。

**小样本检查（8 帧）**：同模型重复扩散一致；μ 逐样本一致（max diff 0）；条件形状 `[B,2]` / `[B,18]`；pathact8 **ctx=2**；共享初始噪声 + 显式 `Generator` 逐步噪声。

---

## 主表（Locked nav ADE，cm）

| 方法 | 条件维 | Checkpoint | 全体 | turn_strict (n=593) | 前四步 | 后四步 |
|------|--------|------------|------|---------------------|--------|--------|
| R2 | 2 | ema_4 | **20.854** | 24.659 | 8.700 | 33.009 |
| R18 | 18 | ema_1 | **18.285** | 21.091 | 7.884 | 28.686 |

改善定义：**ADE_R2 − ADE_R18**（正值 = 路径条件更好）

| 统计量 | 全体 | 前四步 | 后四步 | 配对 bootstrap 95% CI（全体） |
|--------|------|--------|--------|------------------------------|
| 均值 (cm) | **+2.569** | +0.815 | +4.323 | **[+1.981, +3.177]** |
| R18 更优帧占比 | **70.2%** | — | — | 轨迹重抽样 n=10000 seed=20261107 |

**验证集成绩（仅对照，不与 Locked 直接相减）**：R2 12.829 / R18 11.652 cm（500 对 finetune-val manifest）。

---

## 三问（仅离线轨迹 ADE）

1. **验证集上观察的收益是否在 Locked 协议中仍存在？**  
   **是。** Locked 上 R18 仍低于 R2（约 **2.57 cm** 均值差，bootstrap CI 不跨 0）。绝对 ADE 高于验证集是**测试 split / 清单 / 分布不同**所致，不能与 12.8 vs 11.7 做差解释。

2. **转弯和后四步是否也改善？**  
   **是。** turn_strict（eval_frame_sets，n=593）：24.66 → 21.09 cm；后四步配对均值改善 **~4.32 cm**，大于前四步（~0.82 cm）。

3. **证据支持什么，不支持什么？**  
   - **支持**：在固定 Locked 1000 帧、共享扩散噪声、相同 μ + 冻结 pathact8 路径条件下，R18 **离线 nav ADE** 一致优于 R2；子集与配对 bootstrap 同向。  
   - **不支持**：闭环成功率/安全性、文献式“创新”宣称；单训练种子 + 单测试协议不能替代多种子重复；不能把 finetune-val 与 Locked 数值混算。

交付目录：`train/logs/revalidation/r2_r18_locked_2026-11-07/`（`per_frame.csv` 1000 行、`path_cond_audit.json`、`smoke_check.json`、`per_step_mean_err.npz` 等）。

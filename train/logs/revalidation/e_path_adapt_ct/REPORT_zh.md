# 导航模型适配更新路径 — C/T 对照

## Checkpoint（固定）
- pathact8 WP: `logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth` sha256 `c2197c133d08cd9b84329d73385b183974d9c42a8c3b9fc0b2f4615156b97d4d`
- A_cls WP: `logs/nomad_d/nomad_dino_wp_ctx2_pathreadout_A_cls_2026_11_03_23_38_31/dino_dir_best.pth` sha256 `20bc6350c7af7c4cae830a7f05d24836dacae1c8b3f1d2601c3bcc908b535d90`
- E init: `logs/nomad/nomad_e_ft_pathact8/ema_latest.pth` sha256 `d3b6053c1efb6aac5a59be8ca6e27aecc0a4ec13ecc9dbe7cfe74da9e9b00bf6`

## 验证清单
- seed=20261104, n=500, goal_step>=20

## 导航 ADE（cm，val manifest，true_pos_prob=0）
| 模型 | ADE |
|------|-----|
| 原 E init（未再训） | 12.2951 |
| C 继续训练 | 12.2413 |
| T 路径适配 | 12.3701 |

- C−T（正值= T 更好）: **-0.1289 cm**

## 说明
- 训练排除 DFT val 轨迹；验证仅用 manifest 上 far 样本（步数≥20，非米）。
- **共同 init E** 曾在全 train 索引上微调，可能见过 val 轨迹 → 本轮为**微调验证**，非严格未见域泛化。
- T 的 μ 始终来自 pathact8 部署分支；仅 16 维路径来自 A_cls。

smoke_check passed=True

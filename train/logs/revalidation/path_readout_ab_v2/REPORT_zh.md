# 路径头读出 A/B 验证报告（v2，ctx2 修正后）

## 代码修正（事实）

- **loader 参数**：改为 `flip=False, seed=0, workers=2, context=2`（见 `path_readout_val_core.val_loader`）。
- **ctx 检查**：`ctx_check.json` 记录首 batch `ctx.shape[1]==2`。
- **清单**：复用原 `val_pair_manifest.csv`（11519 对），未重 draw、未重训。
- **eb7b56e 数字**：在 ctx=0 下得到，见 `PRE_CTX_FIX_ERRATA.md`，勿作 ctx2 结论。

## 协议摘要

- 固定配对清单；`flip=False`；冻结 path 头前向。
- far：`goal_step>=20`；转弯子集：GT `winding` 累计绝对 yaw（非 turn_strict）。

## 全体 ade8（cm，等权）

| 模型 | ade8 | front4 | back4 |
|------|------|--------|-------|
| A CLS | **16.03** | 6.79 | 25.27 |
| B step_query | 16.09 | 6.91 | 25.26 |
| ref pathact8 init | （见 summary.csv ref 行） | | |

**B−A（bootstrap）**：ade8 **+0.058** cm，95% CI **[−0.059, +0.162]**（跨零，无显著优劣）。

## 四问（ctx2 条件下）

1. **B 是否优于 A？** 全体均值 B 略高 0.06 cm，**CI 含 0**，不能认定 B 更好或更差。
2. **转弯方向 ↔ 位置？** winding≥45 上 ade8 B−A ≈ +0.14 cm，CI 仍跨零；>90° 比例差 ≈ +0.06 pp，可忽略。
3. **前四/后四？** front4 B 略差（+0.13 cm），back4 几乎相同（B−A −0.01 cm）。
4. **Locked 导航？** 路径头 **无稳定增益**；8 步查询 **未显示明确优于 CLS**，仍不建议为 A/B 结论单独开 Locked。

## 区分

- **实验事实**：上表为 ctx2 正确输入下的冻结验证。
- **推断**：8 查询是否在弯折上更有潜力 → **本实验未给出支持**；与 eb7b56e「B 明显失败」结论不同（该次为 ctx0  artifact）。

复现：`eval_command.txt`（需 `--manifest val_pair_manifest.csv`）。
# 干净视觉微调阶段复核

输入提交 `920d7b7`、`ebc8143`。此复核读取本地 GPU 已产生的日志和指标，
没有在云端重新训练或推理。

## 执行完整性

- 30 个训练 epoch，960 行更新，update 序号 1–960 连续，每 epoch 恰好 32 个更新。
- 初始验证 epoch=-1，加上训练 epoch 0–29，共 31 行验证记录。
- 所有训练 loss 有限；每批有效动作样本均大于 0，平均约 10.62/16。
- 每批学习率与 `5e-5 * (1+cos(pi*epoch/30))/2` 匹配。
- 调度器最终 last_epoch=30、lr=0，符合每个 epoch 一次推进。
- 数据报告为 00–04 的 161 个训练观测、05 的 27 个验证观测，不使用旧缓存。
- 初始化哈希与已核验 b40 一致，optimizer/scheduler 均全新。

## 最佳权重确实改善了 05 验证结果

重新按代码的 eligible 条件和综合 score 检索 CSV，结果与 best.json 一致：
**epoch 6，224 次更新**。这里 epoch 从 0 编号。

| 05 验证指标 | 初始化 b40 | epoch 6 | 变化 |
| --- | ---: | ---: | --- |
| 全路点平均误差 | 0.3326 m | 0.3117 m | 降低 6.3% |
| 转弯平均误差 | 0.4868 m | 0.3486 m | 降低 28.4% |
| 转弯方向正确率 | 64.6% | 75.0% | 提高 10.4 个百分点 |
| 距离 RMSE | 10.5847 | 6.2375 | 降低 41.1% |
| 综合 score | 0.9252 | 0.7227 | 降低 21.9% |

距离 RMSE 是距离类别/帧步单位，不是米。
动作误差按训练标签的 metric_waypoint_spacing=0.12m 恢复单位，
不是机器人实测行驶误差。

05 中只有 6 个转弯观测点（4 左、2 右），每个点采样 8 条轨迹，
方向正确率相当于 48 条采样中的统计：约 31/48 提高到 36/48。
这 48 条采样不是 48 条独立路线；75% 不能表述为闭环成功率。

## 后期训练并非持续改善

训练 loss 总体下降，但转弯验证误差在早期下降后又上升。
最终 epoch 29 的方向正确率为 52.1%，转弯误差约 0.4451 m。
存在后期过拟合/训练与验证行为不一致的迹象；不能因 loss 更小就选最后一轮。
现有选模逻辑保留 epoch 6，避免使用这个更差的最终结果。
曲线见 `training_review.svg`。

## 接下来固定 epoch 6 测试

本机 best.pth 的 README 记录：76,439,885 字节，SHA256
`48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56`。
权重未推到云端，云端不能重新计算该文件哈希；下一步本机检查应核实它。

这批结果还没有 house_06 的新模型离线测试，不能判断四个目标转弯是否正确，
更不能宣称已能视觉导航到终点。
固定此份 best，不依据 06 结果更换 epoch 或继续调参，只进行独立测试报告。

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --config gazebo_sim/visual_stage_clean/model.yaml \
  --checkpoint gazebo_sim/visual_stage_clean/best.pth \
  --out gazebo_sim/visual_audit_clean_gpu
```

读取根目录 `CURSOR_VISUAL_BEST_AUDIT_PROMPT.md` 可让 Cursor 完成核验、GPU 离线检查和结果推送。
本次不修改导航或训练参数，也不让车辆运行。

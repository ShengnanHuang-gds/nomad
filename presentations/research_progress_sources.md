# 中文组会汇报来源（当前完成第 1–2 页）

研究材料核对基准：main 提交 c1b3750。

## 第 1 页：封面
- 用户提供的研究主题、汇报周期与方法描述。
- 路径为概念示意，并非实际轨迹或实验结果。

## 第 2 页：研究问题与方法框架
- 用户提供的研究框架与指标定义。
- `train/logs/revalidation/kappa_fusion_summary.txt`：冻结 B + Goal Head + ctx2 WP + E-oracle，κ 方向融合和距离缩放。
- `train/logs/revalidation/P2_protocol.md`：本轮历史感知 WP Head 优化。
- `train/train_goal_dino.py`：`--context` 为额外加入的历史帧数。
- 本页不报告数值性能；use_cm 是相对 masked 条件的 ADE 改善，不等同于导航成功率。
- Goal/WP 为方向预测模块，绿色标识本轮 WP 优化重点；没有声称两个方向头在本轮联合训练。
- E-oracle 是策略名称，本页推理输入是预测位置，不表示在线使用真实未来轨迹。

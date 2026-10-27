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

## 第 3 页：P0 Oracle 方向替换（独立单页文件）
- 文件：`slide03_oracle_factorial_cn.pptx`，仅包含第 3 页；不修改此前 PPT。
- 原始来源：`train/logs/revalidation/oracle_factorial/factorial_use.csv`，`subset=all`，`n=1000`。
- 行为 Goal、列为 WP；预测/预测 2.6199888861，预测/真实 4.6559387669，真实/预测 2.9856801264，真实/真实 5.0267800394 cm。
- 从原始精度计算相对预测/预测的单因素收益：仅真实 Goal +0.3656912403 cm；仅真实 WP +2.0359498808 cm。
- B 预测距离与 E-oracle 固定；真实 WP 方向使用未来 8 步轨迹终点，仅用于离线 Oracle 分析。
- 本页未声称统计显著性，也未与其他批次评估基线比较。

## 第 4 页：P1 航点误差与收益归因（独立单页文件）
- 文件：`slide04_wp_error_attribution_cn.pptx`，仅包含第 4 页。
- `train/logs/revalidation/wp_oracle_attribution/by_wp_err_quintile.csv`：五等分组，每组200帧；平均Δuse为0.02546、0.12261、0.37347、1.86057、7.79763 cm；Q5占全部净收益76.599%。
- 同目录 `summary.txt`：Pearson r=0.623；收益最高的100帧占全部正收益68.9%。
- 同目录 `turn_vs_straight.csv`：严格转弯593帧，占净收益88.058%。
- 区分正收益总和与带符号净收益总和；严格转弯和直行不是互补分组。本页不绘制未经逐帧数据支持的完整集中曲线。
- 与第3页同一Oracle归因：预测WP→真实WP，其余保持不变；不等同于部署效果。

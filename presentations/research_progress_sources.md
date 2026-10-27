# 中文组会汇报来源

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

## 第 5 页：P1b Hard120 难例分析（独立单页文件）
- 文件：`slide05_hard120_analysis_cn.pptx`，仅包含第 5 页。
- `train/logs/revalidation/wp_hard120/summary.txt`：WP误差≥45°的120帧；严格转弯占93.3%。
- 同目录 `enrichment_H_vs_control.csv`，采用 `C_match` 中位数：未来8步累计转角108.485/69.431°；历史平均步间转角14.101/7.349°；Goal误差50.400/15.228°；WP κ 8.906/35.795（困难/对照）。
- `train/analyze_wp_hard120.py:path_kinematics`：past_yaw_rate实际为过去最多3步绝对yaw变化的均值，不能标成deg/s。
- κ低表示分布更分散；组间差异不证明因果；每个指标独立刻度。
- 数据限制：CSV中n_C字段与设计及当前脚本不一致，未报告对照样本数，也未据此计算新统计量；中位数与summary.txt一致，当前没有原始NPZ可复算。详见幻灯片备注。

### 第5页修订
- 移除18.3%卡片，改为120帧与93.3%两个信息块。
- 补充严格转弯GT判定：绝对横向位移≥0.30m或绝对航向变化≥45°（eval_frame_sets.py）。
- κ说明：Head输出的方向集中度，同时用于标准κ融合加权；不是角误差，也不是另一条独立预测权重。

## 第 6 页：P2 历史感知 WP（独立单页文件）
- 文件：`slide06_history_aware_wp_cn.pptx`，仅包含第 6 页。
- `train/logs/revalidation/P2_protocol.md`：ctx0/ctx2相同初始化和预算；ctx2额外使用2帧历史。
- `p2_val_bearing/summary.txt`（同目录）：Val n=5110，e60/ctx0/ctx2的全量中位角误差8.58/8.50/7.97°；严格转弯n=2751的P90为57.84/59.80/53.12°，>45°占比14.5/14.9/12.6%。
- `P2_conclusions_revised.md`：locked use_cm为2.56/2.68/2.80cm；locked配对Delta-U cluster bootstrap仍为TODO。
- Val误差与locked收益分开展示，不与P0的2.62基线混比，不声称下游收益统计显著。

## 第 7 页：P3 早期转弯加权（独立单页文件）
- 文件：`slide07_turn_weighting_cn.pptx`，仅包含第7页。
- `train/logs/revalidation/P3_training_batch.md`：B严格转弯×2、C×3、D累计转角三分位1/1.5/3；30ep、ctx2、e60初始化。
- 同目录 `p3_morning_metrics.csv`、`p3_morning_table.txt`：与ctx2参考比较Val全量中位误差、转弯中位误差、转弯P90、全量>45°比例。
- `train/analyze_p3_morning_table.py`确认val_gt45_pct分母是全部far帧，不是转弯帧。
- B/C/D的转弯中位数改善，但P90与全量>45°占比未优于ctx2；并未宣称所有尾部指标都恶化（C的P95有改善）。
- CSV参考标SeedA、B/C/D标Seed0；未提供多种子统计或这些模型的locked收益。本页不与后续turnhard混用。

## 第 8 页：P4 多时域方向监督（独立单页文件）
- 文件：`slide08_multi_horizon_cn.pptx`，仅包含第8页。
- `train/logs/revalidation/P4_multi_horizon.md`：ctx2初始化，15ep；2/4步辅助监督lambda=.25，8步主目标，推理不变。
- 同目录 `p4_ablation_val.txt`：mh_2721筛选子集内ctx2/P4中位误差7.11/6.30°，转弯P90为34.88/33.19°；full_5110中位误差7.97/7.97°，转弯P90为53.12/58.87°。
- 同目录 `P4_ablation_status.md`：locked use ctx2=2.80、P4=2.40cm；无辅助续训15ep对照2.80cm。
- masked P4b在full Val中位误差7.76°、转弯P90为54.41°；未报告未经核对的P4b locked结果。
- 区分筛选子集、完整Val与locked；箭头均为同集合ctx2→原始P4；后续mh46是不同设置，未混用。

## 第 9 页：P5 置信度融合与门控（独立单页文件）
- 文件：`slide09_confidence_gating_cn.pptx`，仅包含第9页。
- `train/logs/revalidation/p5ab_summary.txt`：P5a相对份额Cohen d≈-0.04，P5c平均抑制强度约0.027。
- `p5b_harmful_predictor/summary.json`：OOF AUC=0.520051；ADE反事实κ/策略/真实害益择优=2.619989/2.619989/3.803194cm。
- `p5c_trust/summary.json`：rollout κ/trust OOF/代理最优抑制=2.694341/2.691593/3.591327cm。
- `kappa_fusion_summary.txt`：同批rollout κ/固定分歧门控/GT误差门控=2.80/2.24/3.16cm。
- 不跨行排名，不混用2.62/2.69/2.80基线；离线参考定义不同且不可直接部署。
- 检查`train/run_p5b_harmful_predictor.py`等脚本后确认部分输入来自GT未来运动派生特征；本页明确其为离线探索，未声称全部特征在线可用。
- 约束fallback的2.73相对同批2.62有改善，但属于locked扫参结果，未混入本页在线验证结论；详见幻灯片备注。

### 第9页通俗表达修订
- 页面改为四项“尝试—结果”，移除AUC、OOF、rollout、反事实、Oracle等术语与跨批次大表；技术来源与原始数值保留于备注。
- 仅展示固定方向分歧门控同批次的2.80→2.24cm；保留部分模型使用未来轨迹信息的离线分析限制。

## 第 10 页：最新航点训练优化（独立单页文件）
- 文件：`slide10_latest_optimisation_cn.pptx`，仅包含第10页；正文以中文解释各方案。
- `train/logs/revalidation/wp_input_sweep/summary.json`：ctx2全量/转弯2.80/3.61；turnhard2.93/3.91；hist3plain2.84/3.73；hist3turnhard2.93/3.92（均四舍五入）。
- `wp_mh46/summary_cn.txt`：从turnhard初始化的4/6步辅助监督2.85/3.79cm。
- `wp_hard_oversample/summary_cn.txt`：困难采样权重×3方案2.94/3.98cm；全量WP误差>45°占比约11%，turnhard约10%；未单独重评Hard120。
- `train/run_wp_ctx2_turnhard_train.py`、`run_hard_oversample_train.py`：核对组合加权配方与相对采样权重。hard_os3同时从turnhard续训，不能将差异纯归因于采样而忽略续训。
- 0.01cm为汇总精度下差异，未证明统计显著。未报告存在摘要/JSON冲突的B-spread参考值。

## 第 11 页：整体结果回顾（独立单页文件）
- 文件：`slide11_overall_results_cn.pptx`，仅包含第11页；使用可编辑的原生PowerPoint柱状图，纵轴从0开始。
- `train/logs/revalidation/P2_conclusions_revised.md`：e60/ctx0/ctx2的locked κ融合收益为2.56/2.68/2.80cm。
- `README_report_index.md`、`wp_input_sweep/summary.json`、`wp_hard_oversample/summary_cn.txt`：turnhard/hard_os3报告值2.93/2.94cm。
- 按报告精度计算绝对增加0.38cm、相对增长14.84375%；仅指条件收益指标，不是导航成功率或绝对ADE相对改善。
- 只作仓库汇总的阶段回顾；尚缺所有阶段原始逐帧配对与重复种子结果，不宣称严格同批随机采样或统计显著，也不混用P0/P5的其他基线。


## 第 12 页：核心发现与局限（独立单页文件）
- 用户已删除原“实验分析与复现流程”页；本页由原计划第13页前移，后续收尾计划页为第13页。未合并文件。
- 文件：`slide12_key_findings_cn.pptx`，仅包含新第12页。
- `train/logs/revalidation/oracle_factorial/factorial_use.csv`：当前栈中WP方向的离线恢复空间大于Goal方向；真实未来信息不可作为部署条件。
- `wp_oracle_attribution/summary.txt`、`wp_hard120/summary.txt`：严重错误、转弯与集中收益；相关证据不代表因果。
- `P2_conclusions_revised.md`、`wp_input_sweep/summary.json`、`P4_ablation_status.md`、`p5ab_summary.txt`：历史与针对性训练取得进展；额外复杂方案未稳定超过参考。
- `wp_hard_oversample/summary_cn.txt`：2.94与2.93的微小差异尚无可靠重复验证。条件收益不等同于导航成功率，仍需独立测试、跨域与实机验证。

## UniNav 介绍第 1 页：整体架构（独立单页，暂未编入总页码）
- 文件：`uninav01_architecture_cn.pptx`；中文架构图为可编辑简化重绘，不与已有页合并。
- 原文：Zhou等，UniNav: A Unified World-Action Diffusion Model for Visual Navigation，arXiv:2608.03244v1，用户上传PDF。
- PDF第3–4页§3.1–3.3、图2：历史与目标为条件；未来视频、完整轨迹(Δx,Δy,Δψ)与相机几何tokens联合去噪。VAE与DA3冻结，Wan2.1主Transformer及新增模块微调。
- 已知输入与加噪预测目标分开表示；推理不使用真实未来图像；轨迹不是只预测yaw后等长积分。
- 图省略register tokens、位置编码与分支输出头；相机几何分支主要表达训练监督。Fast的独立训练与非对称注意力留后页讲解。

## UniNav 精读第 1 页：输入输出与格式（独立单页）
- 文件：`uninav_io01_inputs_outputs_cn.pptx`；保留此前`uninav01_architecture_cn.pptx`，不合并，不确定最终插入页码。
- 原文：用户上传UniNav arXiv:2608.03244v1，§3.1、§3.2、§4.1。
- Full默认C=3历史（含当前）+1目标；K=6未来RGB帧和6×3轨迹，航点(Δx,Δy,Δψ)，图像默认256×192。
- 目标图像与第6未来帧不预设为同一张；时间索引不代表已确认的FPS/秒数，正文未充分说明坐标基准、归一化或yaw单位，页面不补造。
- 图框与矩阵仅作格式示意，未使用伪造实验图片或数值。训练未来数据为监督，推理只给历史和目标。架构、几何与加噪细节留后页。

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

## 第 5 页：运动特征对比（重写后的独立单页）
- 文件：`slide05_hard120_analysis_cn.pptx`；合并版同步替换第5页。
- 问题：转弯比例相近时，困难帧还有哪些运动特征；说明困难组120帧与从非困难帧中抽取的C_match转弯比例均93.3%。
- 来源：`train/logs/revalidation/wp_hard120/summary.txt`、`enrichment_H_vs_control.csv`（C_match），以及`train/analyze_wp_hard120.py`。
- 未来8步累计绝对转角中位数108.485/69.431°；历史平均步间转角14.101/7.349°（困难/对照）。后者不是deg/s。
- 主页面聚焦两个运动特征，移除Goal误差与κ对比，18.3%不显示。结论只提出“视觉历史是否有帮助”的待检验假设，不作因果解释。
- CSV对照数与设计存在不一致，未报告对照数量或计算新显著性；采用与summary一致的中位数。详细限制见备注。

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

## 第 9 页：航点降权的计算细节（重写后的独立单页）
- 文件：`slide09_confidence_gating_cn.pptx`；按用户最新要求只更新单页，不同步合并版。
- `train/eval_by_distance.py:ade_fde`、`eval_position_noise.py:mean_ade_fde`、`eval_testtime.py:rollout`：预测与真实未来8点统一米制，逐点欧氏距离平均，再对采样轨迹平均；各条件分别评估得到e_b/e_g。
- `run_p5b_harmful_predictor.py`：有害标签y=1[e_b>e_g]；按轨迹5组轮换，逻辑回归预测有害概率；该批选择阈值.60，未切换样本，AUC.520。
- `p5ab_summary.txt`：P5a中r_w中位数有害.701、有益.719，作为组间统计，不代表完整置信度校准结论。
- `run_p5c_trust.py:optimal_s_surrogate`：s在0..1的21点上只计算两端ADE线性插值，不是21次真实策略评估；最优通常为0/1。后续岭回归预测抑制并重跑策略。
- 核查发现P5c回归输入中心化但无截距，也没有给标签中心化后恢复均值；训练样本未截断预测均值固定为0。旧“模型学会不抑制/门控失败”的结论撤回，需修正后重评。这里未修改训练代码或重新运行实验。
- `adaptive_blend.py`及`kappa_fusion_summary.txt`：theta=预测两方向夹角；s=clip((theta-35)/20,0,1)，45度时减半、55度起只用Goal；κ'_wp=(1-s)κ_wp，归一化融合后乘B距离。同批use2.80→2.24cm。阈值来自GT误差扫参，不保证适用于预测分歧。
- 02/03部分输入含真实未来轨迹派生特征，属离线分析；阈值选择与批次差异、具体公式等详见幻灯片备注。不能据此宣称实机有效或所有门控无效。

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

## UniNav 精读第 2 页：编码与共享计算（独立单页）
- 文件：`uninav_io02_encoding_architecture_cn.pptx`；保留原架构页与输入输出页，不合并。
- 用户上传UniNav arXiv:2608.03244v1.pdf，§3.2–3.3、式1–7、图2及§4.1。
- 历史/目标：冻结VAE→压缩特征→切块嵌入；已知条件不作加噪预测目标。
- 未来视觉：冻结VAE编码后在latent空间加噪并切块嵌入。航点：K×3加噪，每点经MLP映射为1个token，K=6。
- 几何：冻结DA3读取历史+真实未来图像，取未来6视角特征并Norm，再加噪经MLP映射；不把它冒称为明确的深度图或位姿矩阵。
- 模态序列与寄存向量共享Transformer；分支头预测与各目标空间匹配的flow更新量，不是一次得到最终干净图像/轨迹。迭代后视频经VAE解码，轨迹直接为连续数值。
- 主网络和新增模块训练，VAE与DA3冻结；视觉沿用时空位置编码，非视觉采用原文所述identity位置编码，未自行补造实现。
- 正文未披露视觉token数量、隐藏维度和camera-token维度；图不填未经证实的数字。公式与损失留后页，完整口径见备注。

### UniNav精读第2页补充：模块来源与术语小字
- 视频VAE及视频主干来源：Wang,A.等（2025），*Wan: Open and Advanced Large-Scale Video Generative Models*，arXiv:2503.20314，https://arxiv.org/abs/2503.20314 。来源依据为UniNav §3.2、§4.1与其参考文献，未将Wan默认尺寸冒充UniNav配置。
- 几何教师来源：Lin,H.等（2025），*Depth Anything 3: Recovering the Visual Space from Any Views*，arXiv:2511.10647，https://arxiv.org/abs/2511.10647 。
- 页内补充VAE中文含义与压缩/重建作用、冻结状态、切块/嵌入含义、D为每token的数字个数、轨迹3维→D维映射、DA3全称和作者年份；完整题名与链接保留在备注及本文档。

### 第7页修订：原损失与转弯加权公式
- 原：L=sum(b_i*l_i)/sum(b_i)；新：L=sum(b_i*alpha_i*l_i)/sum(b_i*alpha_i)。b_i为steps_dev/FAR_STEPS，alpha_i为训练时额外转弯权重。
- `train/train_goal_dir.py:direction_loss`确认加权和除以权重和；预热l_i=1-cos(theta_i)，后续l_i=-kappa_i*cos(theta_i)+log I0(kappa_i)，省略常数项。
- B/C严格转弯alpha=2/3、其余1；D按训练帧累计转角三分位alpha=1/1.5/3。页面将“曲率分档”更正为“累计转角分档”。
- 保留原Val表与结论，只训练时增加alpha；原生可编辑分式、变量定义和单样本损失均加入页面。单页与合并版第7页同步。

### 第7页补充：累计转角分档直接写入页面
- 页内新增S=|Δψ1|+…+|Δψ8|，未来8步各步转角wrap后取绝对值再相加，左右转均累计。
- 按训练帧累计转角S的33.333/66.667分位点划分低、中、高，alpha分别1/1.5/3；不是固定角度阈值。
- 对应`train_goal_dino.py`中的train_pairs winding、np.percentile和curvature tier加权。保留此前原/新总损失公式、单样本损失及全部Val表。

## UniNav 单页论文启发（uninav_research_inspiration_cn）
- 新增独立一页，不替换旧架构页，不更新合并稿；按尚未开展相关实验的口吻介绍。
- 依据用户上传 arXiv:2608.03244v1 图2、表1、表4、§3.4与§5。
- 表1的四基准最佳ATE是Full/Fast变体合看，不声称Full全部最佳或RPE全部最佳。RECON Full .314 对 NWM .326，降低3.68%。
- 表4 RTX4090、RECON、两步采样：Full .389秒，Fast .212秒，速度比约1.835；Fast经非对称注意力专门训练后移除未来视频生成。此处不声称它比所有基线更快。
- 研究启发为尝试未来运动辅助监督，不声称已经实现UniNav或验证转角辅助有效。转角监督与积分推理需要分别验证。
- 限定主要证据为离线局部轨迹评估；详细口径与来源置于PPT备注。

### UniNav 成果表更新
- 将单页成果区替换为四数据集可编辑 ATE 对比表，保留方法特点与研究启发，未更新合并稿。
- 表1：RECON .326→.314（3.7%），SaCSoN .616→.464（24.7%），GO Stanford .840→.687（18.2%），SCAND .497→.463（6.8%）。最强对照分别为NWM、ViNT、NavDP、NWM。
- GO Stanford最好值来自Fast，其余来自Full；各数据集分别选择表中最强对照，并非所有列使用同一基线。
- 为给四行结果留出空间，移除成果区延迟比较数字；ATE定义和最好变体说明直接放在页面。


## 启发口径修订与未来工作独立页
- UniNav页明确：论文验证整体方法，不能把ATE提升归因于转角监督；仅借鉴联合监督思路，转角辅助是待验证假设。保留四数据集ATE表。
- 新增 future_work_yaw_supervision_cn：同turnhard初始化、数据与预算拟12轮；A原方法继续训练，B仅转角辅助（必须关闭积分损失），C额外积分方向损失。
- B原方向对A检查辅助监督；C原方向对B检查积分损失；同C checkpoint双方向对比检查积分推理。两方向分别按各自验证误差选模型并记录选择规则。
- 监督为GT逐步yaw差（SmoothL1，弧度）及GT8步弦向（余弦损失）。先方向误差分布，再固定协议融合收益；配对比较并报告不确定性。
- 两页均为独立文件，未更新合并稿。未修改训练代码或启动训练；未来页为计划而非结论。

### 未来工作页符号解释修订
- 三组公式改为中文损失名称；直接在页面增加L损失、λ辅助权重（0.3示例）和θ积分方向夹角的定义，并展示积分损失1−cosθ。明确0.3为示例，不是已选最优参数。保留监督标签和验证方案，仅更新独立页。

## κ融合调整机制独立页（kappa_fusion_mechanisms_cn）
- 根据kappa_fusion_summary、kappa_gate_sweep、P5b摘要与代码制作，未更新合并稿。
- ① turnhard上κw乘1.3，原方向与κg不变，约2.93→2.93，仅有摘要精度，不泛化为所有缩放无效。
- ② s=clip((目标-WP夹角−35)/20,0,1)，κw乘(1−s)；35不改/45减半/55仅goal。ctx2同组2.80→2.24。阈值原按GT误差选择，不能认为可直接迁移至分歧角。
- ③ 标签1[ADEblend>ADEgoal]，标准化逻辑回归按轨迹5折，阈值.60；没有样本切goal，2.62→2.62，AUC .52。特征含GT未来，仅离线分析；阈值在同一折外结果上选，非独立测试。
- 页内解释κ/单位化/θ/s/p/AUC/ADE及收益，三行不同基线仅组内比较。普通κ相对goal的ctx2同组1.95→2.80说明融合仍有价值，不隔离证明κ权重形式独立增益。
- P5c因回归实现问题不作负结果依据；其他约束fallback有局部改善，结论仅限本页展示三项。

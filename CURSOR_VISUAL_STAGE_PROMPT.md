# 给 Cursor：执行干净的本地 GPU 视觉微调阶段

用户目标是视觉导航，不是示教坐标辅助驾驶。请读取
`gazebo_sim/training_handoff/AUDIT_AND_STAGE.md`，按下面流程执行并同步结果。
本任务允许准备数据、GPU 冒烟、完成指定微调阶段和推送小体积结果；不启动 Gazebo、不驱动车辆。

## 背景与约束

- 资料已收齐，不要再次要求用户收集 00–05。
- 原 train 的文本列表只有 00–05，但旧索引含 06、07；新阶段不能使用旧索引或 LMDB。
- 旧训练恢复与双次调度的问题有保存状态佐证；本阶段使用独立入口、全新 optimizer/scheduler。
- 不使用之前的 nomad_gazebo 权重初始化，不使用示教坐标/yaw 控制，不重录 06。
- 00–04 固定训练、05 固定验证；06–07 不用于梯度、调参或 checkpoint 选择。
- 不修改原始数据、归档源码、原 train/test 文件和旧 checkpoint。

## 环境

在本地 WSL 仓库根目录工作，保留用户未提交修改。
先正常拉取最新 main；不要 reset --hard 或强推。
source `gazebo_sim/nomad_wsl_env.sh`，只用 `$NOMAD_PY`，确认 CUDA 可用。
Python 写入 UTF-8。不要用 Windows Python、不要切换 CPU 训练。

本次用仓库根目录 `gazebo_sim/train_visual_stage.py`，它会复用实际运行环境的 NoMaD 网络和预处理，
但不调用旧 train.py、旧调度循环或旧数据缓存。

## 执行顺序

1. 使用新的输出目录运行 `--prepare-only`，检查 data_report：
   - train 161 个观测点（00–04）；validation 27 个（05）；无 06–07。
   - cache_used=false；旧索引审计能看到 264 个旧观测与其中 76 个来自 06–07。
2. 使用另一个新目录运行 GPU 冒烟：`--epochs 1 --steps-per-epoch 2`。
   检查两次更新完成、损失有限、调度器 last_epoch=1、metrics 与 best.json 已生成。
   如失败，保留完整报错并停止，不擅自改成 CPU、减少模型或取消严格加载。
3. 冒烟通过后，使用新的正式目录，例如 `gazebo_sim/visual_stage_clean`，运行：

   ```bash
   "$NOMAD_PY" gazebo_sim/train_visual_stage.py \
     --out gazebo_sim/visual_stage_clean --epochs 30 --steps-per-epoch 32
   ```

   保持默认 batch 16、lr 5e-5、seed 42，不从 smoke/旧微调阶段续训。
   这是 960 次 GPU 更新。保存终端日志到训练目录外或单独文件，避免事先创建日志使输出目录非空。
   如果目录已有结果，使用新的带后缀目录并记录实际路径，不能覆盖。
4. 检查正式 best.json、metrics.csv、steps.csv、scheduler_state.json：
   - 记录初始化基线、实际更新数、是否完成全部 epoch、是否出现 NaN。
   - 记录 best epoch、转弯误差/正确率、距离 RMSE 相对基线是否改善。
   - 如果 best epoch=-1，意味着训练没有选出优于基线的模型；不能当作修复成功。
5. 只有 best epoch>=0 时，使用正式阶段的 model.yaml 和 best.pth 做离线视觉检查：

   ```bash
   "$NOMAD_PY" gazebo_sim/audit_visual_model.py \
     --config gazebo_sim/visual_stage_clean/model.yaml \
     --checkpoint gazebo_sim/visual_stage_clean/best.pth \
     --out gazebo_sim/visual_audit_clean_gpu
   ```

   如果实际目录不同，替换路径。检查默认 CUDA 是否生效。
   不因这份 06 离线结果重选 checkpoint 或继续针对 06 调参；它只是测试报告。

## 同步结果

在正式训练目录新增中文 README，说明实际路径、运行命令、开始/结束状态、
best epoch、相对初始化基线的验证变化、遇到的问题及可用离线测试结果。

只提交以下小文件和测试输出，不要 `git add .`：

- 预检的 data_report.json。
- 冒烟的 stage_config.json、data_report.json、metrics.csv、steps.csv、best.json、scheduler_state.json。
- 正式的同类 JSON/CSV、model.yaml、README 及保存的终端日志。
- 若执行离线检查，其 manifest.json、image_match.csv、distance_matrix.csv、action_summary.csv；
  sampled_actions.npz 体积很小时也可提交。

不要把解包的 handoff/ 副本、模型/optimizer 权重、旧 LMDB、缓存或无关改动混入此次提交。
best.pth 留在本机，记录 SHA256 和大小即可，后续纯视觉闭环会用到。

正常提交并推送 origin/main，不强推。返回提交号和上述结果摘要。
即使训练失败或验证没有改善，也推送已经产生的诊断记录，准确报告；
不要通过开启 TEACH_ROUTE、修改停止规则或把 06–07 加进训练来宣称走通。

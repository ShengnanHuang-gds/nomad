# 给 Cursor：训练与检查图像预测朝向输出

用户已明确允许增加视觉朝向输出，目标仍是视觉导航。
请读取 `gazebo_sim/visual_audit_clean_gpu/ANALYSIS_AND_YAW_PLAN.md`，按本提示执行。
本轮只做本地 GPU 训练与离线检查，不启动车辆，不跑 Gazebo 闭环。

## 约束

- 不再重跑 XY 干净微调，不换其 epoch；固定 visual_stage_clean/best.pth（epoch 6）。
- 新模块只输入当前图像和目标图像。训练可用 00–04 的 yaw 差作标签，05 验证选模；
  不把示教 yaw/坐标接到运行时控制，不读 06–07 作梯度或选模。
- 不改原始数据、旧源码、划分、已有权重或筛选标准；不启用 TEACH_ROUTE。
- 在 WSL 根仓库拉取最新 main，保留其他未提交修改；source 环境，只用 `$NOMAD_PY` 和 CUDA。

## 执行

1. 检查固定 XY 权重仍为 76,439,885 字节、SHA256：
   `48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56`。
2. 用新的目录做两次更新的 GPU 冒烟：

   ```bash
   source gazebo_sim/nomad_wsl_env.sh
   "$NOMAD_PY" gazebo_sim/train_visual_yaw.py \
     --out gazebo_sim/visual_yaw_smoke --epochs 1 --steps-per-epoch 2
   ```

   确认没有报错/NaN、2 次更新及 05 验证完成；smoke 不需要达标。
   若接口失败，保留报错并停止，不改 CPU、不跳过严格加载。
3. 通过后从固定 XY 编码器重新初始化完整朝向阶段，不从 smoke 恢复：

   ```bash
   "$NOMAD_PY" gazebo_sim/train_visual_yaw.py \
     --out gazebo_sim/visual_yaw_stage --epochs 30 --steps-per-epoch 32
   ```

   保持默认 batch16/lr5e-5/seed42，共 960 次 GPU 更新。
   目录已存在就选新后缀，不覆盖；终端日志先写目录外，完成后再收进去。
4. 检查 best.json 的 epoch、MAE、p90、方向正确率、validation_gate_passed。
   若未通过，准确记录失败，不降低阈值、不看 06 选其他 epoch，也不启动车辆。
5. 仅当正式阶段 best 的 epoch>=0 且 validation_gate_passed=true 时，固定该权重运行：

   ```bash
   "$NOMAD_PY" gazebo_sim/audit_visual_yaw.py \
     --head-dir gazebo_sim/visual_yaw_stage \
     --out gazebo_sim/visual_yaw_audit_06
   ```

   如实际目录带后缀，相应替换；不覆盖旧输出。
   06 的真值只用于结果报告，不能反过来影响模型选择或训练。

## 同步结果

给正式阶段写中文 README：实际命令/目录、是否完成、初始化与最佳 05 结果、
是否达到预先规定的标准、最佳朝向权重 SHA256/大小、XY 权重哈希前后是否一致。
说明这是新增视觉朝向模块，不是原 NoMaD baseline，也不是示教朝向控制。

只提交 smoke/正式阶段的 head_config.json、best.json、metrics.csv、steps.csv、
scheduler_state.json、README 和终端日志；如完成 06 检查，同步其 CSV/JSON 和日志。
best_yaw.pth 和原 XY 权重保留本机，不把 handoff 副本、缓存或其他改动混入提交。
本轮即使失败也推送实际记录，不伪造通过，不强推、不 reset --hard。

正常提交推送 main，返回提交号与 05/06 结果摘要。
用户回来只需说“视觉朝向结果推好了”。

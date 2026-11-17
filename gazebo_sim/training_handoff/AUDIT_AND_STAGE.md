# 训练资料核验与新的视觉微调阶段

输入提交 `4c387f2`。254 张图片解码正常，275 个包内文件 SHA256 均匹配；
原始资料与归档源码未修改。

## 发现了实际训练索引与划分文本不一致

`splits/train/traj_names.txt` 只有 00–05，但同目录已存在的索引 PKL 中：

| 路线 | 缓存观测点数 |
| --- | ---: |
| 00 | 37 |
| 01 | 26 |
| 02 | 35 |
| 03 | 30 |
| 04 | 33 |
| 05 | 27 |
| **06** | **35** |
| **07** | **41** |
| 合计 | **264** |

旧 goals_index 也包含全部八条路线，共 352 个目标。
按当前 00–05 的真实轨迹重建应为 188 个观测点、254 个目标。
实际源码 `_load_index` 直接加载旧 PKL，不核验路线列表或数据版本；
LMDB 也只按固定文件名打开，缺少内容有效性核验。
因此当前旧训练入口会读取与文本划分不一致的缓存，存在留出路线混入训练的实质问题。

没有原始训练 stdout，也没有 LMDB 内容，不能确定每次历史 checkpoint 的准确输入版本；
不能把此前所谓“06–07 留出”的旧模型结果当作已证明无污染的严格留出评估。
现存缓存本身的错误已确认，不仅是超参数猜测。

## 调度问题由实际源码和保存状态共同确认

归档实际源码中每个训练 epoch 两次 step，指定 load_epoch 恢复按两倍推进。
原 scheduler_latest.pth 的实际状态（直接读取，不是 README 的类型占位）：

```json
{"T_max": 4, "base_lrs": [0.00005], "last_epoch": 67,
 "_step_count": 68, "_last_lr": [0.000007322330470336381]}
```

目录有 31、32、33 三个 epoch 的 checkpoint，上一目录为 epoch 30。
保存状态与源码的恢复/双步进逻辑吻合，但完整历史学习率仍没有日志证明。

## 新训练入口如何避免这些问题

`gazebo_sim/train_visual_stage.py` 是独立阶段，不调用旧 train.py/训练循环：

- 验证资料包及逐文件 SHA256，直接读 00–05 原图和轨迹，不用旧索引或 LMDB。
- 固定 00–04 训练：161 个观测点；05 验证：27 个。06–07 的图像/轨迹不读取。
- 从 SHA256 已核实的 b40 初始化相同 NoMaD 网络，严格加载；不从已混入疑似污染链路的微调权重恢复。
- 全新 AdamW、全新余弦调度，epoch 从 0 开始，每 epoch 只 step 一次；
  不恢复旧 optimizer/scheduler，不把预训练 epoch 30 当新阶段时间。
- 对左转、右转、直行观测点平衡采样；保持原 XY 动作标签的坐标/单位定义。
- 本阶段目标始终可见（goal mask=0），聚焦图像目标条件学习。
  同一路线随机目标 0–20 步，另有 10% 训练路线内部负样本；
  仍只对合法正样本动作计算扩散损失。
- 距离监督使用 MSE(pred/20,label/20)，与扩散噪声损失相加，避免照搬旧阶段极小 alpha。
  这是明确的新阶段配方，不应将改善单独归因于某一个参数。
- 使用 EMA 权重验证并输出相同结构的 state_dict；策略运行时不输入坐标/yaw。

原始 XY 标签在所有 188 个当前 00–05 观测点上，与归档实际 `_compute_actions`
逐一比较一致。训练中的真实位置仅是常规监督标签，不用于导航驾驶。

## 验证、选模与失败处理

每个 epoch 验证 05，记录全路点误差、转弯误差、转弯方向正确率与距离 RMSE。
先记录初始化基线（epoch=-1），再训练。
新 checkpoint 只有在转弯误差、方向正确率、距离 RMSE 均不劣于基线，
且综合 score 更低时才替换 best；如果训练没改善，best.json 会保留 epoch=-1。

综合 score 为 `all_ADE + turn_ADE + 0.01 * distance_RMSE`，只用于 05 选模。
动作误差比较时恢复到训练标签的 0.12m 单位；部署仍沿用原 NoMaD 的动作尺度转换。
本阶段不支持旧状态续训。中断时已写出的 metrics/steps 和此前 best 会保留，
但再次完整训练需新目录；不声称完整恢复 optimizer。

每步学习率、训练损失和有效动作样本数写入 steps.csv；每 epoch 写 metrics.csv，
调度状态保存于 scheduler_state.json。输出 model.yaml 仅用于推理，实际训练配方在 stage_config.json。

## 本地 GPU 使用

数据预检（不需要 Torch/GPU，也不训练）：

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/train_visual_stage.py \
  --out gazebo_sim/visual_stage_preflight --prepare-only
```

先做 2 个更新的 GPU 接口冒烟检查：

```bash
"$NOMAD_PY" gazebo_sim/train_visual_stage.py \
  --out gazebo_sim/visual_stage_smoke --epochs 1 --steps-per-epoch 2
```

通过后，从 b40 重新开始完整阶段；不从 smoke 恢复：

```bash
"$NOMAD_PY" gazebo_sim/train_visual_stage.py \
  --out gazebo_sim/visual_stage_clean --epochs 30 --steps-per-epoch 32
```

默认 batch 16、lr 5e-5，总共 960 次 GPU 更新。目录须新建，防止覆盖旧结果。
没有 CUDA 时训练会退出，不会自动退回云端或本地 CPU 训练。

仅当 05 验证改善（best.json 的 epoch >=0）时，对新模型做同一份离线检查：

```bash
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --config gazebo_sim/visual_stage_clean/model.yaml \
  --checkpoint gazebo_sim/visual_stage_clean/best.pth \
  --out gazebo_sim/visual_audit_clean_gpu
```

此时 06 只用于报告离线测试结果，不再据此更新或选择本阶段 checkpoint。
不得看到 06 结果不好就把 06 放入训练或重选权重。
离线转向仍不正确时，先分析训练/验证记录，不启动闭环碰碰运气。

可让 Cursor 执行根目录 `CURSOR_VISUAL_STAGE_PROMPT.md` 完成预检、冒烟、训练和结果同步。

## 已完成的检查和限制

35 项不同的离线检查均通过：无 Torch 的环境运行其余检查，Torch 专用的 2 项在
独立 CPU 环境以极小测试模型验证真实梯度/EMA和每 epoch 一次调度。
这些不是用 b40 在云端训练；没有进行新的完整模型 GPU 训练或闭环。
数据预检已在云端实跑，标签已与归档源码逐样本核对。
本地实际 NoMaD GPU 训练仍需冒烟确认，且 254 张图像的数据量有限，
即便修复训练流程，也不能保证新权重就能走通。

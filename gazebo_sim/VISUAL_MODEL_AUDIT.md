# 用本地 GPU 检查真实视觉模型

已收到提交 `7a43410` 的 `nomad_b40` 权重和 models.yaml。
云端只做了严格权重加载核验，没有跑批量预测或 Gazebo：

- 权重文件 `train/logs/nomad/nomad_b40_2026_09_30_07_52_31/ema_29.pth`，76,473,631 字节。
- 645 个 state_dict 项与配置构建的模型全部匹配，`strict=True` 通过。
- 19,049,675 个参数，未发现漏载键或多余键。

这一结果只排除了本次提供文件在该结构上的键/形状不匹配，不证明模型学会了 Gazebo 的转弯。
云端使用 CPU PyTorch 2.15.0、diffusers 0.11.1、efficientnet-pytorch 0.7.1；
diffusion_policy 源码版本为 `5ba07ac6661db573af695b419a7947ecb704690f`。
用户认为本地 GPU 更适合推理，因此不在云端运行大批量 CPU 预测。

## 本地运行，不需要 Gazebo 或驱动车辆

先拉取代码，在原 WSL 仓库目录执行：

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --model nomad_b40 --topomap house_06 --run house_run_06 \
  --out gazebo_sim/visual_audit_b40_gpu
```

脚本默认要求 CUDA；如果当前 Python 没有 GPU 支持，直接退出，
不会自动退回 CPU 跑很久。只有明确加 `--cpu` 才允许 CPU 推理。
使用已记录的 63 张图像，不创建 ROS 节点，不发布命令，不重录示教。
导入真实导航运行模块以复用部署模型加载、图像预处理、DDPM 和 action decoder；
所以仍需要原 WSL 的 Python 依赖环境，但不需要 T1 仿真运行。

## 一次检查输出什么

- `manifest.json`：本机实际配置、权重 SHA256、Torch 版本、device、样本数/随机种子和严格加载结果。
- `image_match.csv`：示教图与实际部署拓扑图逐张解码像素 MSE；检查是否使用旧拓扑图或图片对应错位。
- `distance_matrix.csv`：多个关键观测位置对全部 63 张目标图的距离预测，包含全局最低距离目标编号。
- `action_summary.csv`：四处转弯前后若干固定观测/目标组合的采样分布；
  给出 waypoint 2 和最后一点的朝向中位数/10–90 分位、左右转和前进比例。
- `sampled_actions.npz`：完整采样轨迹，供后续绘图，CSV 汇总不依赖上传此文件。

比较两种上下文：前三张示教历史+当前图，以及当前图重复四次；
后者只是检查上下文敏感性的对照，不等于真实运行相机上下文。
每个组合 32 个样本、相同随机序列，同时比较目标条件开启（mask 0）和关闭（mask 1）。
坐标仅用于给结果标注实际目标方向，模型输入没有示教坐标或 yaw。

这不是再试 radius、lead、PD 参数，也不是为了重复确认“第 12 张转不过去”。
重点是定位矩阵是否失真、目标条件是否改变输出、问题是否横跨所有转弯，
以及历史图像是否影响模型行为，为实际视觉模块修改提供依据。

结果目录已存在 manifest 时请换一个 --out，避免覆盖旧检查。
如果需要减少首次检查时间，可用 `--samples 8`；默认 32 便于查看采样分布。
请优先保留/推送上述 JSON 和 CSV，体积很小。

## 当前验证边界

云端没有执行此脚本的本地 GPU 推理，也没有视觉闭环成功结果。
已完成语法、CLI help 及上下文/统计函数检查；全项目此处共有 29 项离线检查通过。
脚本结果只衡量示教图上的离线视觉推理，不能替代真实相机输入或闭环评估。

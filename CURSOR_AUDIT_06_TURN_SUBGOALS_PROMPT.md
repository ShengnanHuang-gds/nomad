# 给 Cursor：用已有图像检查 NoMaD 弯中子目标

拉取最新 `main`，打开 `gazebo_sim/visual_reference_06_candidate_recovery/ANALYSIS.md`。这次直接使用已有 36 帧，只做一次冻结的 b40 GPU 离线推理。无需启动 Gazebo、重录、训练或更换权重。保持本机 `visualnav-transformer` 源码和原 b40 配置。若 `nomad_b40` 没有注册，使用原闭环相同的本地配置和 EMA 文件，通过 `--config` 与 `--checkpoint` 显式指定。

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --model nomad_b40 \
  --reference-dir gazebo_sim/visual_reference_06_candidate_recovery \
  --samples 8 \
  --out gazebo_sim/visual_audit_b40_reference_turns
```

每个当前帧对比下一张中间图和该弯最后一张图。用 `action_summary.csv` 中 `goal_mask=0`、`waypoint_index=2` 的 `sample0_cmd_v/w` 检查当前部署所用路点经原 PD 后会给出的命令，另报扩散样本的中位方位和左右比例，注明每种目标与屏蔽目标对照相比改变了多少。`dist_pred` 统一取目标开启时的距离预测。各组使用相同观测和扩散随机序列。第一弯左转，第二弯右转。`goal_relative_yaw_deg` 来自同步 Gazebo 姿态，只用于核对方向，XY 路点方位、PD 角速度与相机朝向的大小分开记录。第二弯最后一张图仍在原地转向，报告不要写已验证驶入弯后直道。

将 `manifest.json`、`action_summary.csv`、`distance_matrix.csv` 和一份短 `RESULTS.md` 放在输出目录并推送。`RESULTS.md` 写清中间图有没有稳定改变第二弯的路点方向，以及是否改善部署所用的 sample 0。保留旧图、原权重和既有闭环记录。

# 给 Cursor：先修复 Gazebo 02 速度命令无响应

先拉取最新 main，保留现有本地修改，读 `gazebo_sim/visual_yaw_sweep/README.md`。已知 00、01 的出生点净空不足，02 的净空充足但是车轮 odom 和模型几乎都没变化。先解决 02 的命令通路，暂停 90° 扫转和训练。不在 00/01 试发指令，不改净空条件，不切到 05/06/07。

在实际 WSL 仓库中 source `gazebo_sim/nomad_wsl_env.sh`，用 `$NOMAD_PY`。只用确认隔离的 02 Gazebo 仿真。保留现有运行环境；如果需要重新启动，使用 02 原生 spawn 和现有镜头。核对当次 world、burger_cam 模型 ID、ROS 发布/订阅、Gazebo 原生 `/cmd_vel` 的消息类型及发布/订阅端点。核对实际 bridge 映射和 DiffDrive 订阅的 topic，比较 launch、bridge 和观察进程的 `GZ_PARTITION`、`GZ_IP`、`GZ_RELAY` 和 ROS domain。只报告环境网络配置，别提交环境变量全量或凭据。不要接管已有控制器。

在确认没有其他控制发布者、扫描净空仍大于 0.3 m 后，用新脚本发一次小幅旋转，并保存输出。目标 8°，若 1 s 仿真时间没有响应，脚本会停车并给出故障层级。实体 ID 必须来自当前仿真：

```bash
"$NOMAD_PY" gazebo_sim/align_spin_once.py 0.12 \
  --world default --model burger_cam --entity-id "$BURGER_ID" --target-deg 8
```

- ROS 发布者没有 QoS 匹配：检查 `ros2 topic info /cmd_vel --verbose` 中 bridge 的实际话题、类型、命名空间和 QoS。修复已证实的映射或 QoS 不一致。
- ROS 已匹配、Gazebo 观察不到非零命令：检查同一仿真两端的 topic 名、类型、方向、传输域和 bridge 日志。只修证据指向的 bridge 配置或启动环境。
- 原生 Gazebo 收到非零命令、车轮未响应：先只读核对实际 SDF 的 DiffDrive、轮关节和 `/joint_states`，确认实际插件订阅者、安装版本、启用状态及仿真状态。车轮转而车身未转时检查地面接触、轮和出生位姿，不修改朝向或跳过障碍。缺证据时保存已定位的层，停止重复发命令。
- 如果做了明确的配置修复，就用相同的短动作复验一次。记录 Gazebo 模型实际 yaw 变化，成功标准是命令经过预期通路、模型按预期方向响应并停稳。仍不要跑大扫转、训练或导航闭环。

把诊断及有证据的修复推到 main，并记录失败层级、改变了什么和实测结果。可以将记录追加到新的 `gazebo_sim/visual_yaw_sweep/motion_fix/`，原始归档保留。

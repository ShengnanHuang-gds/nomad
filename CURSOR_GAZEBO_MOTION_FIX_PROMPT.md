# 给 Cursor：定位 burger_cam 左右轮目标与实际响应

拉取最新 main，保留现有本地修改。先读 `gazebo_sim/visual_yaw_sweep/motion_fix/README.md`。提交 `3a25cd6` 已确认 02 的 Gazebo 原生 `/cmd_vel` 收到 +0.120 rad/s，轮式 yaw 只变化 +0.004°，车身 yaw 几乎为零。停车后读到的关节状态没有覆盖发命令时段。现在直接读取 Gazebo ECS 中的左右轮目标与实测值。

仅使用条件已经确认的隔离 02 仿真。复用本轮仿真，若已关停则用相同配置原生启动。继续要求扫描净空 >0.3 m、时钟和姿态持续更新、无其他 ROS 或 Gazebo 速度发布者、目标模型和 world 已核实。不要运行导航、训练、90° 扫转，或改镜头、净空、速度与现有轨迹。

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" -c 'from gz.msgs10.serialized_map_pb2 import SerializedStepMap; from gz.msgs10.double_v_pb2 import Double_V; from gz.transport13 import Node'
gz service -i -s /world/default/state
```

用当前 `gz model -m burger_cam -p` 查询真实模型 ID 并赋给 `BURGER_ID`。只做下面一次短动作，记录输出：

```bash
out="$(mktemp -d)"
"$NOMAD_PY" gazebo_sim/align_spin_once.py 0.12 \
  --world default --model burger_cam --entity-id "$BURGER_ID" --target-deg 8 \
  --wheel-state-log "$out/wheel_state.csv" >"$out/spin.log" 2>&1
```

程序先等只读状态服务有有效回包，再发速度。它会记录同一对轮关节在 motion 窗口内的 `JointVelocityCmd`、`JointVelocity` 和 `JointPosition`。当前轮距 0.160 m、轮半径 0.033 m，因此正转预期左轮约 −0.291 rad/s，右轮约 +0.291 rad/s。按以下证据处理：

- Gazebo 原生话题看到 +0.120，但发令期间 ECS 两轮目标一直为零或同号：故障在设定轮目标一侧。核对实际加载的 DiffDrive、是否有其它关节控制插件覆盖、插件是否禁用及其实际配置。保存插件日志和证据，再修已确认的问题。
- ECS 持续给到预期反向目标，但关节速度和角度都几乎不动：检查实际物理引擎、轮关节限制和碰撞接触。根据实测修改仿真配置，并保留原配置可恢复。
- 两轮实际反向转动但车身不跟随：检查车轮接触和滑移，分别记录 odom 与真实车身 yaw。
- 状态服务不可用或有效样本不足：保留输出和实际 Gazebo 版本，不从空数据推断故障层，也不反复重发。

如果证据说明具体可修的配置错误，由 Cursor 修正并用同一个短动作复验。把日志、CSV、结论，以及实际改动推到 main 的 `gazebo_sim/visual_yaw_sweep/wheel_response/`，保留原始 motion_fix 记录。此处的 Gazebo 姿态只用于离线诊断。

# 给 Cursor：安全重录一份可核对姿态的 house_06 参考图

拉取最新 main，读 `gazebo_sim/visual_yaw_rendered_result/NEXT_STEP.md`，保留现有数据和本地修改。用 WSL 的既有 house 和 burger_cam 镜头。这次采的是候选视觉拓扑图参考画面。录制与导航分开，暂不跑 NoMaD、PD、模型训练或闭环。

使用原有 06 仿真场景的新进程。先停止或隔离原导航以及其它速度发布者，确认没有设备控制进程连接。仿真中保持原定起点和参考录制初始化方式。可用现有 `launch_tb3_house_at_run.sh house_run_06` 启动，再在单独的**录图会话**执行 `reset_run_pose.py --run house_run_06 --skip-teleport --verify` 进行初始场景对齐。检查 `gz model -m burger_cam -p` 显示的是实际 06 的 Gazebo 模型，提取其当前实体 ID 到 `BURGER_ID`。这次不碰 02，不跨过障碍或改变物理参数完成录制。

上次在第一段 0.9 m 直线停止。Gazebo 原生激光每 0.2 秒仿真时间发布一次，墙钟间隔最长 2.15 秒，已定位到仿真运行速度不足以稳定满足 2 秒的接收时限。直接做下面这一次录制。若激光仅超过 2 秒未更新，记录器立刻发零速，最多再等 2 秒。仅当更晚的扫描满足原有时效和近障条件，且姿态检查通过时，才继续当前路段。日志会有 `scan_pause` 和 `scan_recovered`。本次由录制结果验证恢复，无需再采集一轮原生激光探针。

```bash
source gazebo_sim/nomad_wsl_env.sh
out="$(mktemp -d)"
"$NOMAD_PY" gazebo_sim/record_house_multi.py --spawn-at-launch \
  --out-root "$out" --reference-model-id "$BURGER_ID" house_run_06
```

新路径为 `$out/house_run_06`。程序会在扫描持续失效、接近障碍或姿态超限时结束录制，并保留已有画面和 `gazebo_reference_pose.json`。报告记录扫描暂停与恢复的次数。若停止，`stop_context` 会记录动作段、ROS 激光和 odom 时间戳、两者有符号时差，以及激光距上次收到的 wall 时间。若完成，检查每帧位姿支撑，并记录 Gazebo 实际首尾位置、图像总数和后两弯的代表原图。把本次结果标为参考图录制。

将实际日志、`gazebo_reference_pose.json`、有代表性的原图，以及完成时的 `traj_data.pkl` 放到新的 `gazebo_sim/visual_reference_06_candidate_recovery/`，正常推送。保留此前两次试录、旧 `house_run_06`、部署中的 `house_06` 和权重。候选图是否可用由下一次云端复核决定。

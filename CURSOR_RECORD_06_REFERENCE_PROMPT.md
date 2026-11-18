# 给 Cursor：安全重录一份可核对姿态的 house_06 参考图

拉取最新 main，读 `gazebo_sim/visual_yaw_rendered_result/NEXT_STEP.md`，保留现有数据和本地修改。用 WSL 的既有 house 和 burger_cam 镜头。这次采的是候选视觉拓扑图参考画面。录制与导航分开，暂不跑 NoMaD、PD、模型训练或闭环。

使用原有 06 仿真场景的新进程。先停止或隔离原导航以及其它速度发布者，确认没有设备控制进程连接。仿真中保持原定起点和参考录制初始化方式。可用现有 `launch_tb3_house_at_run.sh house_run_06` 启动，再在单独的**录图会话**执行 `reset_run_pose.py --run house_run_06 --skip-teleport --verify` 进行初始场景对齐。检查 `gz model -m burger_cam -p` 显示的是实际 06 的 Gazebo 模型，提取其当前实体 ID 到 `BURGER_ID`。这次不碰 02，不跨过障碍或改变物理参数完成录制。

```bash
source gazebo_sim/nomad_wsl_env.sh
out="$(mktemp -d)"
"$NOMAD_PY" gazebo_sim/record_house_multi.py --spawn-at-launch \
  --out-root "$out" --reference-model-id "$BURGER_ID" house_run_06
```

新路径为 `$out/house_run_06`。程序会在姿态或扫描失效、接近障碍或横滚/俯仰超限时停止，并保留已有画面和 `gazebo_reference_pose.json`。若停止，记录发生在哪个动作以及画面，不跳过检查强行走完。若完成，检查报告中的每帧位姿支撑，并记录 Gazebo 实际首尾位置、图像总数和后两弯的代表原图。不要把参考脚本走到终点写成模型导航成功。

将实际日志、`gazebo_reference_pose.json`、有代表性的原图，以及完成时的 `traj_data.pkl` 放到新的 `gazebo_sim/visual_reference_06_candidate/`，正常推送。不要覆盖旧 `house_run_06`、部署中的 `house_06` 或权重。候选图是否可用由下一次云端复核决定。

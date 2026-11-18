# 给 Cursor：验证大转弯中的连续视觉对应

这份扫转流程暂不执行。02 的驱动问题独立记录，现有试验不把它作为推进 house_06 视觉导航的前置条件。[02 诊断更正](gazebo_sim/visual_yaw_sweep/wheel_response/README.md)

先读 `gazebo_sim/YAW_GEOMETRY_REVIEW.md`，拉取最新 main 并保留本地修改。使用 WSL 的现有 ROS Jazzy/Gazebo Harmonic 工作流，仓库通常在 `/mnt/c/Users/61078/Desktop/nomad`。本轮只做独立传感器实验和离线评估，不训练、不重录已有路线、不运行部署导航或 PD，不把诊断图写入训练集。保持镜头、渲染参数和权重现状。

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" -c 'import cv2, rclpy; from gz.transport13 import Node; from gz.msgs10.pose_v_pb2 import Pose_V'
```

选 00–04 区域内两处具有不同纹理且能安全原地转动的位置，一处左转、一处右转。可用该区域原生 spawn 启动隔离的 house 仿真，不传送运行中的机器人、不按示教姿态对齐。用真实 world 名、`gz model -m burger_cam -p` 的当前模型 ID 和实际 SDF 校验。确认时钟前进、摄像机和 odom 发布者唯一、速度话题的目标确属 Gazebo bridge 且无其他控制发布者、扫描净空大于 0.3 m。条件不具备时跳过运动并记录。不要选用 05、06 或 07 的地点代替。

每窗使用新目录，指定实时读到的 `BURGER_ID`。例子为正向 90°，反向将速度改为 `-0.12` 并换目录。

```bash
scratch="$(mktemp -d)"
out="$scratch/sweep"
"$NOMAD_PY" gazebo_sim/capture_sensor_alignment.py \
  --world default --model burger_cam --entity-id "$BURGER_ID" \
  --sim-seconds 18 --wall-seconds 200 --image-period-ms 100 \
  --out "$out" >"$scratch/capture.log" 2>&1 &
capture_pid=$!
```

同一仿真环境中等采集日志出现 `capture ready`，随即运行：

```bash
"$NOMAD_PY" gazebo_sim/align_spin_once.py 0.12 \
  --world default --model burger_cam --entity-id "$BURGER_ID" \
  --target-deg 90 --wall-seconds 175 >"$scratch/spin.log" 2>&1
wait "$capture_pid"
"$NOMAD_PY" gazebo_sim/audit_yaw_geometry.py --sequence "$out" >"$out/geometry.json"
```

如果命令失败，收集退出码和日志，仍等采集退出并核对已产出资料。旋转进程按仿真时钟计时，扫描过近、时钟或模型姿态异常、控制发布者冲突或超时时停车。不得修改安全条件来补足转角或直接跑导航。若时间戳覆盖不足或未达到目标角度，写明实际结果和原因。

- 确认转前、转中、转后有时间锚点。报告实际转角、真值位置变化、两路 yaw 增量差、丢帧、时间间隔、SDF 摘要和停止状态。
- `geometry.json` 只按图像时间选帧。报告实际转过约 10°、20°、40°、60° 和 85° 的最近记录，包括首帧直接估计是否弃权、连续估计首次中断的位置与终点误差。不改诊断条件寻找通过结果，不用 odom 补视觉空档。
- 将两个窗口放进新目录 `gazebo_sim/visual_yaw_sweep/`，包括 `samples.json`、`geometry.json`、采集与运动日志、配置摘要和报告。用 tar.gz 保留本次分析选到的 PNG（`reference_image` 和 `rows` 的帧），在 SHA256 清单里绑定路径和图像戳。完整 PNG 留本地，记录归档省略项。只提交本轮资料和必要的诊断工具修正，正常推送 main。

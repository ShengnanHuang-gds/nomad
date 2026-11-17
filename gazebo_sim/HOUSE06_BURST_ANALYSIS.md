# house_06 第一次转弯后的偏移

分析对象：`episodes_eval_gpu/house_06_nomad_b40_burst.{json,ticks.csv}`，
示教：`house_run_06/traj_data.pkl`。这是旧运行的离线分析，未运行新的 Gazebo 闭环。

## 旧数据能够确认的事

示教位置在 spawn odom 坐标系，`world_anchor=[-2.2,1.2]`。
比较下面的数据时，直接比较两份 odom xy，不能再次加 world_anchor。
第 8–12 帧在同一位置 `(0.767,-0.472)`；yaw 从 -31.6° 转至 12.0°。
第 11 帧只有 4.8°，第 12→13 帧的平移方向为约 12.1°。

时间从 CSV 第一条记录算起，横向偏移相对第 12→13 帧的出口直线，左为正。

| 时间/s | 路程/m | 匹配节点 | dist_min | 出口横偏/m |
| ---: | ---: | ---: | ---: | ---: |
| 55.13 | 0.890 | 11 | 1.189 | +0.030 |
| 82.39 | 1.456 | 11 | 1.996 | -0.035 |
| 95.14 | 1.710 | 11 | 3.890 | -0.063 |
| 127.39 | 2.016 | 9 | 5.227 | -0.104 |

第 230→330 条记录的实际平移方向为 5.47°；第 340→380 条为 6.11°。
这是由 xy 差分得到的移动方向，不能冒充当时测得的车身 yaw。
末次结果：路程 2.216 m，节点最高 14、最终 10，碰撞代理累计 28 次。
因此“全程横偏中位数约 0.05 m”掩盖了转后持续向右偏和后续定位回退。
车辆继续到达第二次示教转弯附近时，视觉定位还在第 9 张附近，无法触发正确的后续转弯。

## 代码里的确定问题

旧 `_teach_spin_waypoint` 每帧根据当前 closest_node 重新计算 yaw 目标，
并不只在原地旋转段生效。匹配第 11 帧时，允许绕第 12 帧目标的 ±8°
容差前进；一旦匹配回退到直行第 7/6 帧，目标又变成 -31.6°。
长时间匹配第 11 帧时，出口子目标还会是原地的第 12 帧。

这能解释为什么“图对上”没有保证按出口方向走；实际移动方向也与这个问题一致。
但旧 CSV 没有 model dx/dy、最终 waypoint、yaw 或 cmd_vel，无法精确归因每一步：
不能据此断言模型预测、控制覆盖或执行延迟各占多少责任。

## 本次修改

- `teach_turn.py` 将每段原地旋转视为一次动作，锁定末帧目标；视觉节点回退不改变该动作。
- 仅在视觉节点落入该转弯段且 odom 距该转弯点不超过 0.18 m 时触发；完成后不重复触发。
- 完成容差默认 3°；直行节点不再单独触发示教 yaw 覆盖。
- 转弯和出口阶段的视觉子目标使用首个发生平移的图片，而非原地旋转图片。
  交还模型后若视觉定位回退，也保留已完成转弯后的首个平移目标作为下限，
  不改 closest_node、不靠跳节点宣告到达。
- 默认在出口的 0.35 m 内，以出口示教线上的 0.25 m 前视点修正横偏，之后交还模型。
  这明确使用了示教位置和 yaw，是诊断辅助，不能作为纯视觉 NoMaD 的性能。
- CSV 新增 `model_dx/model_dy`（缩放后的模型原始路点）、`wp_dx/wp_dy/wp_hx/wp_hy`
  （实际发布的路点）、`odom_yaw`、`control_source`、`teach_turn_end`、
  `window_start/sg_node`。原来的 `sg_idx` 是窗口内索引，`sg_node` 才是全局图片编号。
- episode JSON 记录示教辅助模式与参数，避免误读结果。

未重录示教，未改搜索半径、距离阈值或 PD 限速。纯模型模式不启用这些示教覆盖。

## 在原 WSL 环境复验

保持 T1 使用原有启动方式，启动一个新的仿真实例：

```bash
bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06
```

T2 在原仓库目录运行，脚本内会 source `nomad_wsl_env.sh` 并使用 `$NOMAD_PY`：

```bash
TEACH_YAW_SPIN=1 TEACH_EXIT_M=0.35 \
EPISODE_OUT="$PWD/gazebo_sim/episodes_eval_gpu/house_06_nomad_b40_exit035.json" \
bash gazebo_sim/run_holdout_06_b40.sh
```

`TEACH_EXIT_M=0` 可单独验证锁定转弯和出口图选择的修复，不用位置辅助出口。
`TEACH_YAW_SPIN=0` 明确禁用辅助；旧脚本对非空字符串 `0` 也会启用，现已修正。
每次使用新的仿真实例和独立输出文件，保留 burst 原始数据。

检查第 11/12 帧之后 `control_source` 从 `teach_spin` 到 `teach_exit` 再到 `model`；
检查出口 `sg_node=13`，以及后续 model_dy 是否继续把车带向错误方向。
尤其观察交还模型之后视觉节点是否能跟随实际平移推进、第二次转弯能否匹配到。
若仍偏，已有日志可区分模型输出与覆盖路点，不能只看 closest_node。
成功仍需综合约 4.56 m 的示教路程、低 dist、少碰撞与终点位置；
原有代码的 `success` 布尔值仍然只表示节点到终点，不能单独作为成功标准。

## 已完成的验证与限制

通过 7 项基于现有 63 帧示教的离线回归检查：转弯识别、直道不覆盖、
节点回退仍锁定目标、远距离误匹配不触发、出口横偏纠正与释放、
关闭出口辅助、角度跨 ±π。Python 语法、Bash 语法和 diff 空白检查通过。
云端未安装 ROS/Gazebo，也没有 WSL 的模型运行环境；没有新的闭环成功结果。

```bash
python3 -m unittest discover -s gazebo_sim -p test_teach_turn.py -v
```

## 后续补齐的日志（新运行才有）

`run_holdout_06_b40.sh` 自动产生同名的两份 CSV：

- `<episode>.ticks.csv`：每轮导航的模型路点、发布路点、覆盖来源、yaw/xy、里程计实测速度，
  以及最近收到的 `/cmd_vel`。
- `<episode>.control.csv`：控制器每次发布命令都记一行（正常约 9 Hz），
  包含最终限速后的线速度/角速度、输入路点、收到路点的时间、路点序号/年龄与停车原因。

两份 CSV 均逐行 flush，不再等结束时才一次写出，已经写出的行可在运行中读取。
旧 CSV 无法补回当时没有记录的数据。

| 字段 | 含义及单位 |
| --- | --- |
| `model_dx/model_dy` | 模型采样 0 中所选路点，完成原有缩放后、覆盖前，米 |
| `wp_dx/wp_dy/wp_hx/wp_hy` | 实际发布/控制器收到的路点；hx/hy 仅四维路点存在 |
| `control_source` | `model`、`teach_spin`、`teach_exit` 或 `stop` |
| `odom_x/odom_y/odom_yaw` | 里程计位姿，米/弧度 |
| `odom_v/odom_w` | 里程计实测前向速度（m/s）、角速度（rad/s） |
| `cmd_v/cmd_w` | `/cmd_vel` 命令的前向速度（m/s）、角速度（rad/s），不是实测速度 |
| `t`、`wp_publish_t`、`*_received_t` | 主机 Unix 时间，秒；用于对照两个进程的先后顺序 |
| `ros_time_s`、`*_stamp_ros_s` | 节点 ROS 时钟/消息头时间，秒；不与 Unix 时间相减 |
| `odom_age_s/cmd_age_s/wp_age_s` | 从本进程收到消息起的单调时钟时长，秒；未收到时留空 |
| `step_elapsed_s` | 本轮导航耗时，包含推理与发布，秒 |
| `reason` | 控制器的 `tracking/waiting_waypoint/waypoint_timeout/reached_goal/shutdown` |
| `waypoint_seq` | 控制器本次运行中收到的路点序号；同一路点可对应多条控制命令 |

导航节点单线程推理期间无法处理订阅回调，所以 ticks 中的 cmd 是“最近已收到的命令”，
**不能把同一行的 cmd 当作这一行刚发布路点所产生的响应**。
需要准确追踪命令时，使用 control.csv 的输入路点、`wp_received_t` 与命令时间，
对照 ticks 的 `wp_publish_t`；再结合 odom 的消息时间和年龄查看车辆运动。
`*_age_s` 只表示本地接收后的时长，不代表网络延迟。
未收到消息保留空值，收到零速则记录 0，避免把缺失误读为停车。

独立启动控制器时可这样启用完整控制日志：

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/pd_controller_ros2.py --log-csv /tmp/house06.control.csv
```

新增 3 项日志回归检查：运行中可读/关闭不截断；控制器的正常、旋转限速、
等待、超时、到达与退出日志逐条匹配所发命令；导航回调区分命令速度与实测速度。
使用生产方法和消息替身测试，未依赖 ROS，不等同于 Gazebo 联调。

```bash
python3 -m unittest discover -s gazebo_sim -p 'test_*.py' -v
```

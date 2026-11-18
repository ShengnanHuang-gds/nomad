# 给 Cursor：采一组按仿真时间同步的 burger_cam 图像和姿态

先读 `gazebo_sim/SENSOR_ALIGNMENT_REVIEW.md`。本轮验证图像时间、Gazebo 模型和轮式 odom 的对应关系，采集独立诊断数据。保持现有镜头、模型权重、05 门槛与数据划分。不要运行原来的两个 probe 脚本，它们混用主机时间并复用图像文件名。不要训练、重录路线或运行 NoMaD、PD、示教控制和闭环。

## 在 WSL 检查现有仿真

以 `hsnnb` 在仓库内拉取最新 main，保留本地修改。通常路径是 `/mnt/c/Users/61078/Desktop/nomad`。执行：

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" -c 'import rclpy; from gz.transport13 import Node; from gz.msgs10.pose_v_pb2 import Pose_V; from PIL import Image'
```

此脚本是独立收集工具，不加载 NoMaD，也不依赖本地 `visualnav-transformer` 的模型源码。Harmonic 的 Python 模块应与运行中的 Gazebo 版本一致。若系统 Python 能导入、`$NOMAD_PY` 看不到系统绑定，先核实两者 Python ABI 一致，在这次命令的 `PYTHONPATH` 里纳入安装模块的系统路径后复测。若系统也缺，先检查已配置的 Jazzy/Harmonic 软件源中 `python3-gz-transport13` 与 `python3-gz-msgs10` 的候选包，从现有受信任源获取。无法导入就提交环境和错误信息，不用 `gz topic -e` 文本解析替代。

从当前仿真确认 world 与模型。使用 `gz model --help` 核对本机 CLI，再用 `gz model -m burger_cam` 的模型 ID，不能用任一 link 的 ID。确认实际 `/clock` 前进、`/camera/image_raw` 及 `/odom` 唯一发布者、`/cmd_vel` 订阅者确属 Gazebo bridge。记录环境、实体 ID、topic info、镜头配置文件 SHA256 和当前 Git 提交。优先用一处非 05/06/07 的空旷诊断位置，先确认 scan 清障。没有合适仿真条件时只采静止。禁止使用示教姿态或传送控制来跑这次采集。

## 采集与比较

先收集一个短静止窗口，再用独立新目录采两次转动，正向和负向各一次。脚本默认记录 4 s 仿真时间，主机兜底 45 s。若仿真慢，可把主机时限设到 90 s。每次让采集覆盖转前静止、转动、转后静止，前后各保留约 0.5 s 仿真时间。示例中 `BURGER_ID` 应由上一步核实后赋值：

```bash
capture_root="$(mktemp -d ${TMPDIR:-/tmp}/nomad-sensor-alignment.XXXXXXXX)"
"$NOMAD_PY" gazebo_sim/capture_sensor_alignment.py \
  --world default --model burger_cam --entity-id "$BURGER_ID" \
  --out "$capture_root/stationary"
```

两次转动分别用 `--out "$capture_root/left"` 和 `--out "$capture_root/right"`。由 Cursor 在已确认隔离的模拟器中操作另一个短时仿真诊断进程，采集器本身只订阅。保持线速度为 0，角速度绝对值 ≤0.12 rad/s，目标绝对转角约 8–12°，每次运动仿真上限 2 s、主机上限 30 s。运动计时读 `/clock` 或有效模拟消息头，并用独立单调主机时钟做超时。必须先确认没有其他控制发布者、scan 净空 >0.3 m、真值和时钟持续更新；扫描过近、时钟/姿态停更或异常时立即停车。退出时连续发零并只清理自己启动的进程。不得用旧脚本里的系统时钟充当仿真时间。若条件不具备、命令未生效或转角不足，保留失败证据，跳过后续转动，避免反复试跑。

对每次 capture：

1. 检查 `samples.json` 中的错误、零戳计数、仿真/主机时长、图像总数及两路均对齐的图像数。每张用到的图必须有唯一 PNG 和唯一图像戳，两个姿态来源都必须有同一时刻的样本，或前后各 ≤50 ms 的姿态支撑。报告起转前、转动中、停止后是否各有对齐帧，以及实际偏差范围。不要跨捕获窗口补姿态。
2. 用前后静止期的对齐图像，报告各自的 model yaw 与 odom yaw 的带符号增量，两路增量差、world 位移、roll/pitch 变化。若无前后两端或真实角度达不到约 8°，标记为小角度/不完整记录。
3. 比较 PNG 的图像差异与双向特征匹配。使用灰度 SIFT、最多 1000 特征、ratio 0.7，报静止对、左转对、右转对的匹配数和带符号像素位移，保留匹配点的图像位置供之后核验投影。正向 yaw 应在有共同视野时带来总体向右的场景位移，负向相反。若纹理或配对不足，报告不确定。禁止用 CameraInfo 针孔 K/D 或全图平面旋转直接换算机体 yaw。该实验用来验证同步和方向，不用于选择权重。

## 提交给云端

将结果保存到新的 `gazebo_sim/visual_sensor_alignment`，保留采集参数、运动进程或诊断脚本、结论、原始 `samples.json` 和对应 PNG（统一压缩包并用 SHA256 清单绑定路径与图像戳）。如果图片数量大，保留所有消息元数据和每个窗口最多 12 张代表帧的原始 PNG，显式列出保留的文件及 stamp。记录每个 abort 和缺失项，不覆盖旧传感器探针。只提交本轮资料和独立诊断脚本，正常推送 main 并给出提交号。任何端到端导航实验留待云端复核同步和可观测性后再决定。06 已用于开发诊断，07 保持最终留出。

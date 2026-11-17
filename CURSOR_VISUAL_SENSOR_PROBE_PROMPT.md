# 给 Cursor：核对 Gazebo 相机、真实姿态与消息同步

请读取 `gazebo_sim/visual_yaw_stage/REVIEW_AND_SENSOR_PLAN.md`，完成下面的传感器诊断并推送。
朝向头已确认没过 05，本任务不重训、不跑 NoMaD 导航、不重录示教，不启用 TEACH 控制。

## 目标

确认实际输入图像的光轴/投影、图像与 odom 的发布来源、真实 Gazebo 姿态和时间同步。
目前只知道 loss 降低但验证角误差变差，不能预设“相机一定装错”或“标签一定错误”。

## 一、收集实际生效的静态配置（先做）

在 WSL 仓库目录拉取最新 main，保留本地未提交修改。
source `gazebo_sim/nomad_wsl_env.sh`，Python 使用 `$NOMAD_PY`，UTF-8 写入。

根据当前 launch、`ros2 pkg prefix turtlebot3_gazebo`、GZ_SIM_RESOURCE_PATH 等实际信息定位文件，
不要只找一份同名模板就宣称它生效。复制到单独资料目录，记录原路径、SHA256 和引用链：

- burger_cam 及其被引用的实际 model.sdf、model.config、URDF/Xacro。
- camera sensor 及其 parent link/joint 定义、完整 pose/rpy、lens/FOV/尺寸/帧率/畸变配置。
- DiffDrive/odometry 插件配置、odom 话题与基坐标系；不要假定 odom 就是真值。
- 实际启动文件与 ros_gz_bridge 参数/映射，当前模型实体名和 world 名。

资料缺失就记录，没有证据不要猜路径、插件行为或相机光轴。
区分 Gazebo sensor 的坐标约定与 ROS optical frame 的坐标约定。
不要在此阶段修改相机配置或启动参数。

## 二、静止状态的话题与姿态采集

如果 Gazebo 已运行，不重复启动；如果没运行，可用原命令启动一个新仿真：
`bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06`。
只启动模拟环境，不运行 reset 的朝向对齐、record、navigate 或 PD 控制脚本。

收集并保存：

- `ros2 topic list -t`、image/odom/scan/cmd_vel 的 type 与详细发布者信息、use_sim_time 状态。
- 实际 CameraInfo（K、D、P、distortion_model、frame_id），TF static 与可查询的
  base_footprint/base_link 到 camera/optical/base_scan 变换。
- `gz topic -l`，实际 robot/model 的真实 world pose 数据及消息类型。
  先用工具帮助核对一次读取/超时参数，不要套用不存在的 CLI 选项。
- 短时 image/odom/Gazebo pose 记录：原始消息时间、接收时间、frame_id、
  odom position/quaternion/twist、真实 Gazebo model/link position/quaternion。
- 最多 40 张实际相机 PNG，保存图像 header stamp、encoding、step、尺寸，保持内容不变。

可写一个只订阅的临时 rclpy 收集脚本，并把脚本一并打包供核查。
不要把 Unix 时间和仿真时间混减；所有来源缺失或 stamp=0 都要显式报告。
可以创建专门的临时 ros_gz_bridge 接收真实 pose，但须记录转换类型和实际 entity/frame，
结束时只清理自己启动的进程，不杀用户原有进程。

## 三、只有条件满足才做一次小角度纯仿真旋转探针

这是诊断，不是导航或新的示教采集；不把它放进任何训练集。
必须先确认以下实际条件：

- Gazebo world 和目标机器人实体明确，cmd_vel 确实连接到这个模拟机器人。
- 没有其他导航/遥控器在发布 cmd_vel；否则不接管、不杀用户进程，跳过并记录。
- 能读取带时间的真实 Gazebo 机体姿态，而不是把 /odom 另存一份冒充真值。
- 初始扫描净空大于 0.3m，姿态/扫描/图像正常且更新。

条件不具备时，直接跳过探针，仅推送静态资料与不可用原因。
不要为了做探针降低条件或反复重启系统。

条件满足时，可新增独立诊断脚本，使用实际 cmd_vel 消息类型：

- 线速度始终为 0；角速度最多 0.15rad/s。
- 最多转约 12°；仿真运动时间最多 1.5s，主机运动时间最多 30s。
  达到任意上限就停车；依据真实姿态和/clock或有效模拟消息时间计时。
- 扫描过近、位姿/时钟停更或任何异常，立即发布零速度并退出。
- 无论正常或异常退出都连续发布零速度收尾，不依赖之后某个节点接管。
- 保存起转前、转动中、停止后的同步数据和图像；只做一次，不往返试参数。

记录实际转了多少；不要求恰好 12°，也不要用 odom 的角度替代真实角度来证明成功。
不要调用 gz set_pose 或重新对齐到示教角度。

## 四、输出与检查

新增 `gazebo_sim/visual_sensor_probe/`：

- README.md：实际环境、配置来源、静态采集结果、是否执行探针及原因。
- manifest.json：文件列表/来源/大小/SHA256、话题与 frame、实际命令和采集时间范围。
- 配置快照、话题/TF/CameraInfo、同步 CSV/JSONL、图像与采集脚本，可一起放入 tar.gz。
- 若做了探针，对比开始/结束的 odom yaw、Gazebo 机体 yaw、真实 roll/pitch、
  相机旋转和各消息时间偏差；给出原始值与计算约定，不预设哪一个必然正确。

绝对 yaw 的零点可能不同，比较增量前也要确认坐标轴约定。
如果只能拿到平面 odom 的 roll=pitch=0，不能据此断言真实模型没有倾斜。
当前探针不能事后证明旧 254 张训练图像的时间同步，README 保留这个限制。

原始图片可能被全局规则忽略，可压缩打包，解包路径必须相对、无危险链接。
不收集权重、LMDB、凭据或无关个人文件。
只提交本任务资料和独立诊断脚本，不修改原导航/训练/模型资产。
正常推送 main，不 reset --hard、不强推。

最后给用户：提交号、可用/缺失资料、探针是否执行、主要增量对比。
没有证据时写“尚不能判断”，不要宣称相机问题已经修好。

# house_run_02 发令期间轮目标一直是 0

重新启动的 `house_run_02`，实体 271，发令前位置约 (0.008, 3.837)。Gazebo Sim 8.15.0。只发了一次 `+0.12 rad/s`、目标 8°。状态服务有提供者，单独进程 0.35 秒能取回 298 个实体；同一个进程里只要订着姿态话题，请求就没有回包。轮状态因此改到单独进程里读。没有发第二次速度。

## 发令窗口

原生 `/cmd_vel` 上看到 `angular.z=+0.120`。模型 yaw 增量 `+0.000°`，轮式 odom yaw 增量 `+0.004°`。

正转时左右轮目标应约为 `-0.291` 和 `+0.291 rad/s`。15 个发令中的 ECS 样本里，两轮 `JointVelocityCmd` 全是 `0.0`。实测轮速保持发令前的约 `+0.028 rad/s`，左右同号。轮角在这 0.92 秒仿真时间里每轮大约增加 0.026 rad，和这个同号慢转一致，不是左右反向。

停车后模型位置约 (0.076, 3.836)，yaw 仍约 -0.0087 rad。

## 插件

模型 SDF 里有 `gz-sim-diff-drive-system`，话题 `cmd_vel`，左右关节名和 ECS 里读到的关节一致。世界文件没有第二个关节速度插件。安装的插件是 `libgz-sim8-diff-drive-system.so.8.15.0`。这次 launch 输出里没有 `DiffDrive subscribing` 这一行。`/cmd_vel` 在命令结束后仍有一个 Gazebo 进程内的订阅者。没有因此改 SDF 或桥。
## 解释更正

上述 CSV 是 SceneBroadcaster 的物理步结束后快照。Gazebo Sim 8.15.0 的 Physics 系统在该快照生成前清零 `JointVelocityCmd`。因此轮目标列的零值不能用于判定 DiffDrive 有没有在物理步开始前写入目标，也不能据此归因于桥接、插件或物理引擎。原始数据与日志保留。

能确定的是 Gazebo 话题收到了请求，实际两轮没有出现预期的差速，车身没有转起来。新脚本只用实测轮速差描述这条证据。参见 [Physics 清理运动命令](https://github.com/gazebosim/gz-sim/blob/gz-sim8_8.15.0/src/systems/physics/Physics.cc#L4104-L4141) 和 [SceneBroadcaster 的 PostUpdate 快照](https://github.com/gazebosim/gz-sim/blob/gz-sim8_8.15.0/src/systems/scene_broadcaster/SceneBroadcaster.cc#L391-L423)。

云端用 Gazebo Sim 8.11.0、同一模型的车轮碰撞体和 DiffDrive 配置，在最小平地场景做了对照。原生 +0.120 rad/s 指令下，两轮实测约 −0.2909 与 +0.2909 rad/s，同一快照中的两列命令仍为零。这个对照验证了观测方式的误判。它没有复现 WSL 02 的不转故障。

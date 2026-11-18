# house_run_02 速度命令停在车轮之前

仿真是重新启动的 `house_run_02` 原生出生点，实体 271，位置约 (0.009, 3.837, 0.010)。没有改净空条件，没有再发第二次速度。

## 通路

ROS `/cmd_vel` 是 `geometry_msgs/msg/TwistStamped`。发命令前发布者数量为 0，唯一订阅者是根命名空间的 `ros_gz_bridge`，QoS 为 reliable、volatile。图像只有 `ros_gz_image`，`/odom` 只有 `ros_gz_bridge`。

Gazebo `/cmd_vel` 类型是 `gz.msgs.Twist`。命令发出前已有一个发布者和一个订阅者。没有 `/model/burger_cam/cmd_vel`。仿真进程与观察进程都是 `GZ_IP=127.0.0.1`、`GZ_RELAY=127.0.0.1`、`GZ_PARTITION` 为空。`ROS_DOMAIN_ID` 未设置。

SDF 里的 DiffDrive 订阅 `cmd_vel`，左右关节是 `wheel_left_joint`、`wheel_right_joint`，轮距 0.160 m，半径 0.033 m。只写了 `max_linear_acceleration` 1.0，没有角速度上限。

## 一次 8° 测试

`align_spin_once.py 0.12 --entity-id 271 --target-deg 8`。1 秒仿真时间后的记录：

- Gazebo `/cmd_vel` 上观察到 `angular.z=+0.120`
- 轮式 odom yaw 增量 `+0.004°`
- 模型 yaw 增量 `+0.000°`

脚本因此停车，故障层是：Gazebo 已经收到非零角速度，车轮和车身都没有响应。ROS 的 QoS 和 bridge 映射这一层没有发现不一致。

停车之后读到的 `/joint_states` 不能当作命令生效期间的轮速。当时两轮速度约 `0.028 rad/s` 且同号，位置约 0.46 rad 和 0.42 rad，也不是原地转向应有的左右反向。没有再发命令去补这一段。
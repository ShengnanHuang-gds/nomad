# 相机、里程计和 Gazebo 姿态核对

仿真是这次终端里已经启动的 `turtlebot3_house`，世界名 `default`，实体名 `burger_cam`。没有重训，没有重录示教，没有跑导航。启动时打印的示教 yaw 是 -0.552 rad，但 spawn 只传了 x、y，没有做朝向对齐。

## 实际配置从哪来

`gazebo_sim/launch_tb3_house_at_run.sh` 设置 `TURTLEBOT3_MODEL=burger_cam`，调用 `turtlebot3_house.launch.py`。启动日志打印了 `urdf_file_name : turtlebot3_burger_cam.urdf`，并出现 `Entity creation successful`。Gazebo 进程的 `GZ_SIM_RESOURCE_PATH` 末尾是 `/opt/ros/jazzy/share/turtlebot3_gazebo/models`。

因此这次生效的是：

- `models/turtlebot3_burger_cam/model.sdf`，由 `spawn_turtlebot3.launch.py` 按模型名拼出来。
- `urdf/turtlebot3_burger_cam.urdf`，由 `robot_state_publisher` 读取。
- `params/turtlebot3_burger_cam_bridge.yaml`。日志里的桥接和这个文件一致。
- `worlds/turtlebot3_house.world`。

副本、原路径和 SHA256 在 `config_sources.json`。

SDF 相机是 `camera_link` 上的 `wideanglecamera`，没有单独的 sensor pose。`gz_frame_id` 是 `camera_rgb_frame`。水平视场 3.183 rad，图像 320×240、`R8G8B8`、30 Hz。镜头类型是 `custom`，函数 `tan`，c1=1.05、c2=4、f=1.0。`camera_joint` 相对 `base_link` 是 `0.040 0 0.110`，rpy 全 0。

URDF 另外有 `camera_rgb_optical_joint`，rpy 为 `-1.5707 0 -1.57`。这只出现在 TF 里。SDF 传感器标签没有这个 rpy。实机 CameraInfo 的 `frame_id` 是 `camera_rgb_frame`，图像的 `frame_id` 是 `burger_cam/camera_link/camera`。两个 frame 不一样。CameraInfo 写的是 `plumb_bob`、畸变全 0、fx=fy=277、cx=160、cy=120。SDF 写的是 custom tan 镜头。这次不能据此判断渲染光轴到底跟哪一份描述走，也不能判断相机装错了。

## 静止时的话题

`use_sim_time` 在 `robot_state_publisher` 上是 true。`/odom` 由 `ros_gz_bridge` 发布，类型 `nav_msgs/Odometry`，frame `odom`，child `base_footprint`。桥接注释写它来自 DiffDrive 插件，不是直接的世界位姿。`/cmd_vel` 是 `geometry_msgs/TwistStamped`，当时只有 bridge 在订阅，没有别的发布者。图像由 `ros_gz_image` 发布。

Gazebo 话题要带上该进程的 `GZ_IP=127.0.0.1` 才能看到。真实模型位姿来自 `/world/default/dynamic_pose/info`，类型 `gz.msgs.Pose_V`，消息头有仿真时间。

静止时同一批仿真时间大约在 43.3 到 43.5 秒：

| 来源 | 位置 | yaw | roll | pitch |
| --- | --- | ---: | ---: | ---: |
| `/odom` | 约 (0, 0, 0) | 约 0 | 0 | 0 |
| Gazebo 模型 `burger_cam` | 约 (-2.207, 1.200, 0.010) | 约 0 | 约 0 | 约 -0.0125 rad |

图像、odom、pose 的仿真时间相差几十毫秒。接收用的 Unix 时间没有拿来和仿真时间相减。`/odom` 的 roll、pitch 恒为 0，不能用它说明模型没有倾斜；模型 pitch 大约 -0.7°。同一次 Pose_V 里的 `camera_link` 数值停在 SDF 连杆位姿附近，朝向接近单位四元数，没有跟着机体 yaw 走。这条消息没有给每个 pose 标明坐标系，所以这里只报告原始值。

这次同步不能证明以前那 254 张训练图和当时的 yaw 是按时间对齐的。

## 一次原地转动

转动前重新看过 `/cmd_vel`，发布者数量是 0。线速度保持 0，角速度命令 0.15 rad/s。扫描最近距离约 0.85 m，大于 0.3 m。只转了这一次，结束时连续发了零速度。

探针节点没有打开 `use_sim_time`，循环里的 1.52 s 和主机时间一致，不是仿真时长。仿真时间以消息戳为准：odom 从 55.400 s 到 55.720 s，模型 pose 从 55.401 s 到 55.764 s，图像从 55.375 s 到 55.705 s。

按 ZYX 从四元数算出的 yaw 增量：

- Gazebo 模型 `burger_cam`：+0.02955 rad（约 +1.69°）
- `/odom`：+0.02955 rad

两个增量一致。模型位置仍在出生点附近，odom 位置仍在原点附近，所以增量一致不等于 `/odom` 就是世界位姿。roll 前后都接近 0。模型 pitch 保持约 -0.01246 rad，odom pitch 仍是 0。命令是 0.15 rad/s，实际转角小于 0.15 乘以这段仿真时间；这次记录不能单独说明差在限速、命令是否全程生效，还是时间戳覆盖的区间。没有转到 12°，因为仿真时间这段大约只有 0.32–0.36 s 就结束了这次采样。

相机 TF 是固定关节。URDF 光轴关节没有出现在 SDF 传感器里。尚不能判断旧训练标签或相机安装是否错误。
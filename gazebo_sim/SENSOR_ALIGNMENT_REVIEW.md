# burger_cam 传感器探针复核

复核原始提交 `75b6bd261236bed04e8831e30b71498b1d7715e9`。来源为 [试验说明与原始资料](visual_sensor_probe/README.md)、[启动与配置快照](visual_sensor_probe/config_snapshot/)、`sync.jsonl`、`probe.json`、`images_index.json` 和 `images.tar.gz`。未改原始资料。manifest 中 19 个条目里，12 个逐字节匹配。其余 7 个均为配置文本，把工作区的 LF 还原成 CRLF 后，原始文件长度和 SHA256 全部匹配。

## 实际来源和相机帧

- House 启动链按 `burger_cam` 选择模型，spawn 给 Gazebo 的 `-file` 是 `model.sdf`，给 robot_state_publisher 的是另一个 URDF。该次 spawn 用 x/y 加固定 z=0.01 m，未传示教 yaw。
- SDF 的 `camera_link` 连杆 pose 为 `0.076 0 0.093 0 0 0`，`wideanglecamera` 无独立 pose。SDF 同时有固定关节 pose `0.040 0 0.110 0 0 0`。连杆 pose 与关节 pose 有各自的参考帧。原始 Pose_V 里读到的 camera_link 数值与 SDF 连杆值一致。Gazebo SceneBroadcaster 发送实体的 Pose component，不能把这个 link 条目当世界姿态。机器人是 world 下的模型，应使用其实体 ID 对应的模型 pose。
- ROS 静态 TF 的链为 base_footprint → base_link → camera_link → camera_rgb_frame → camera_rgb_optical_frame。base_footprint 到 camera_link 为 (0.040, 0, 0.120) m，旋转为单位四元数。optical joint 的 rpy 约为 (−π/2, 0, −π/2)，其光学 +z 映射到机体 +x。该 TF 建立 ROS 光学坐标约定，不会转动 Gazebo 的传感器。做几何时要分别确认实际渲染外参和 ROS TF。
- SDF 的 `custom` 镜头使用 `tan`，c1=1.05、c2=4、f=1.0，`scale_to_hfov=true`，水平视场 3.183 rad（约 182.4°）。渲染器按 HFOV 缩放自定义径向投影。图像为 320×240、30 Hz，实收 RGB，frame 是 `burger_cam/camera_link/camera`，发布者是 `ros_gz_image`。
- CameraInfo 由 `ros_gz_bridge` 发布，frame 是 `camera_rgb_frame`，K/P 里 fx=fy=277、cx=160、cy=120，`plumb_bob` 且 D 全零。若按针孔理解，K 隐含水平视场约 60°。现有元数据不足以把 K/D 当作这路广角图像的标定来做 `undistort` 或从像素位移直接求 yaw。现有 NoMaD 图像输入无需据此更换镜头或预处理。
- `/odom` 经 `ros_gz_bridge` 从 Gazebo 的 `odom` 桥接，frame `odom`，child `base_footprint`，对应 SDF 的 DiffDrive。Gazebo Sim 8 实现把左右轮 joint position 传给 odom 积分器。起始 odom 约为 (0, 0, 0)，Gazebo 模型约为 (−2.207, 1.200, 0.010) m。Gazebo 模型 pitch 约 −0.714°，odom 为平面姿态。这个工况的轮式 yaw 增量贴合真值，误差仍需在更大的角度和不同工况下测量。

上游实现可复核 [DiffDrive](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/diff_drive/DiffDrive.cc)、[SceneBroadcaster](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/scene_broadcaster/SceneBroadcaster.cc)、[CameraLens](https://github.com/gazebosim/gz-rendering/blob/gz-rendering8/include/gz/rendering/CameraLens.hh)。

## 旋转探针能证明的范围

原始 158 行是轮询快照，同一消息出现多次。按各自 header stamp 去重后，报告的两路端点 yaw 增量均约 +1.693°. Gazebo pose 端点相隔 0.363 s，odom 相隔 0.320 s，图像从 55.375 s 到 55.705 s。三路覆盖范围各自不同，不能当成完全同步的同一对端点。旧探针节点没有开启 `use_sim_time`，`stop_sim_s=1.519` 实际按系统时钟计算，与主机时长相同。

图像索引写了 27 项，归档只有 14 张。旧脚本两次从 `00.png` 编号，第二次会覆盖第一批；因此按索引末尾 14 项解释归档，旧静止阶段的 PNG 已无法按索引核对。样本 `03→13`（55.375→55.705 s）有可见运动。用 OpenCV 4.11 灰度 SIFT（最多 1000 特征、ratio 0.7、双向互检），得到 51 个匹配，后一张相对前一张的中位位移约为右移 2.42 px、下移 0.17 px。归档里起转前的 `00→03` 灰度像素相同。这符合机体小幅左转时视野向右移的预期，不能用这点运动给镜头定标或判断 90° 大转弯的可观测性。

为了按图像时间比较两路 yaw，只对每侧 ≤50 ms 的相邻姿态样本在线性插值前做角度回绕处理。14 帧中，只有 `04–09` 可同时对齐两个来源（55.407–55.573 s）。这 6 帧中两路插值 yaw 的最大绝对差约 0.0062°；同一对齐区间内，Gazebo yaw 增量约 +1.361°，odom 约 +1.367°。该差值只描述本次短探针，且受原始轮询降采样影响。起转前和停止后缺少足够密的双侧时间锚点。静态 optical TF 和 Pose_V 中的局部连杆值均不等于渲染相机的独立世界姿态测量。

## 对导航和训练的影响

旧记录器 `record_house_multi.py` 独立保存最近一次 Image 和 Odometry 回调值，写入 PKL 时只保留 x、y、yaw。短探针可以检验当前链路，无法补出旧图像对应的真值。现有资料支持正向安装、小角度图像响应及轮式积分的来源；尚不能确定旧模型在 05 失败的主因是旧样本姿态偏移、视野重叠不足还是数据量与泛化。

目前最直接的改动在采集链路。[`capture_sensor_alignment.py`](capture_sensor_alignment.py) 用原生 Gazebo Pose_V 按实体名和 ID 取模型姿态，以 image header stamp 连接两路姿态并报告前后时间差，保留每个原始图像、位置和四元数供复查。它只读。新采集先覆盖诊断场景内的静止与正负小幅旋转，补上起转前和停止后的锚点，再判断是否值得为朝向增强另采同步数据。训练仍只用 00–04，05 仍按原门槛验证，06 只做开发诊断，07 保持最终留出。部署时增强的输入仍限于图像，真值与 odom 仅用于离线诊断和监督标签。

下一次 WSL 执行入口在 [CURSOR_VISUAL_SENSOR_ALIGNMENT_PROMPT.md](../CURSOR_VISUAL_SENSOR_ALIGNMENT_PROMPT.md)。

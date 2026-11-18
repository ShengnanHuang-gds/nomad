# 02 轮关节诊断状态

02 的原生 Gazebo 速度话题收到 +0.120 rad/s；实测左右轮速都约 +0.028 rad/s，车身几乎没有转动。[原始证据和解释更正](gazebo_sim/visual_yaw_sweep/wheel_response/README.md)

停止按本提示词重复做 02 短旋转或 90° 大扫转。已收集的完整 ECS 是物理步结束后状态，`JointVelocityCmd` 会在快照前被清零。重复采同种快照无法定位命令在当步有没有交给轮子。02 的问题独立保留，不作为推进 `house_06` 视觉导航的前置条件。

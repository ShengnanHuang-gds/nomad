# 给 Cursor：生成一组无需驱动车轮的转弯图像

先拉取最新 main，保留本地修改。使用 WSL 的现有 ROS Jazzy、Gazebo Harmonic 和 `$NOMAD_PY`。本轮输出新 RGB 图像和已知相对朝向标签，属于离线渲染数据。它使用安装中的 house 场景与 burger_cam 广角镜头，另起独立 Gazebo 服务器，在同一处训练区域放置一组固定朝向的相机。运行中的 TurtleBot3 和导航环境无需操作。

在仓库根目录：

```bash
source gazebo_sim/nomad_wsl_env.sh
scratch="$(mktemp -d)"
out="$scratch/yaw_views"
"$NOMAD_PY" gazebo_sim/render_yaw_views.py --out "$out"
```

一次 run 应输出 13 张 320×240 PNG，朝向从 −90° 到 +90°、每 15° 一张。程序检测无有效时间戳、空图、重图和未完成的输出。关闭时只清理自己启动的 Gazebo 服务器。若失败，从 `gazebo.log` 修复具体资源路径或渲染环境错误。保留已产生的文件和错误记录，不发布不完整的数据为成功。

成功后把原图、`manifest.json` 和 `camera_only.sdf` 打包至新目录 `gazebo_sim/visual_yaw_render_pilot/`，保留文件的 SHA256。附短说明，说明这批画面能否看到连续变化、是否有墙面遮满画面、场景与镜头来自哪一版，并推送 main。这个点在 02 训练区域，05 仍用于原门槛验证，06 和 07 不参与生成。此处只生成数据，暂不训练或运行闭环。

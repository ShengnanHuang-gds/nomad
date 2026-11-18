# 给 Cursor：用多位置渲染数据增强图像朝向模型

先拉取最新 main，保留本地修改。使用 WSL 的 ROS Jazzy、Gazebo Harmonic 和本机 CUDA，仓库通常在 `/mnt/c/Users/61078/Desktop/nomad`。先读 `gazebo_sim/visual_yaw_render_pilot/ANALYSIS.md`。本轮在独立的相机场景生成训练图，再做一次固定配置的 CUDA 朝向训练。不要跑 TurtleBot3、02 车轮试验或导航闭环。

```bash
source gazebo_sim/nomad_wsl_env.sh
scratch="$(mktemp -d)"
"$NOMAD_PY" gazebo_sim/render_yaw_views.py --training-batch --out "$scratch/turn_views"
"$NOMAD_PY" gazebo_sim/train_visual_yaw.py --rendered-data "$scratch/turn_views" \
  --out "$scratch/visual_yaw_rendered" --epochs 30 --steps-per-epoch 32
```

采集按 00–04 的指定锚点逐组渲染，每个世界只有固定相机。锚点的坐标只用于离线布置相机，训练的角度标签来自渲染 SDF 本身。若某组因场景、纹理或渲染问题不可用，批处理保留组日志。训练入口独立核对每组源文件指纹、PNG、姿态和相邻画面，只有至少 3 条训练路线共有至少 6 个合格且彼此分开的地点时才启动训练。若预检没过，提交报告和失败原因，不放宽条件或反复生成同一个位置。

训练沿用固定 epoch-6 XY 检查点和原 05 验证对。旧样本与渲染样本各占一半采样概率，旧样本保留左右与近零平衡，渲染样本使用不同图像间的左右转角。验证仍用原 05 的 MAE≤10°、p90≤20°、大转向方向正确率≥95%。记录初始化、最佳和最后一轮。06 不参与训练或选权重，07 保持最终留出。新输出属于额外的图像朝向增强。

推送 `gazebo_sim/visual_yaw_rendered_result/` 下的短 README、`batch_status.json`、`render_training_report.json`、`head_config.json`、`metrics.csv`、`steps.csv` 和 `best.json` 中实际产生的文件。另保留各组 `manifest.json`、源场景和相机哈希，必要时打包少量有代表性的原图。完整渲染组及权重留在本机，README 给出路径和最佳权重 SHA256。无论结果如何都如实记录，先不部署。

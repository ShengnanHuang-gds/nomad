# visual_stage_clean

从 nomad_b40 重新训练的干净阶段。没有开 Gazebo，没有用旧的 nomad_gazebo 权重，也没有把 house_run_06、07 放进训练。

命令：

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/train_visual_stage.py \
  --out gazebo_sim/visual_stage_clean --epochs 30 --steps-per-epoch 32
```

30 个 epoch、960 次更新已经跑完，终端回到了提示符。验证集是 house_run_05。

训练前基线：路线误差 0.333 m，转弯误差 0.487 m，转弯方向正确率 64.6%，距离 RMSE 10.58，score 0.925。

选出的 best epoch 是 6，更新数 224。路线误差 0.312 m，转弯误差 0.349 m，转弯方向正确率 75.0%，距离 RMSE 6.24，score 0.723。三项都好于基线。

第 6 个 epoch 之后转弯方向正确率下降，最后一轮只有 52.1%，所以没有用最后一个 epoch。

冒烟目录 visual_stage_smoke 只做了 2 次更新，best epoch 仍是 -1，没有用来初始化正式训练。

best.pth 留在本机：76,439,885 字节，SHA256 48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56。

house_06 的离线检查还没跑。
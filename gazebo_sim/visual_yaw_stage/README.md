# 图像朝向模块训练记录

这是加在固定 epoch-6 XY 权重旁边的图像对朝向模块，不是原来的 NoMaD，也不是示教朝向控制。输入只有当前图和目标图。06、07 没有用来训练或选模。05 没过预先规定的门槛，所以没有跑 house_06 审计，也没有开闭环。

## 命令

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/train_visual_yaw.py \
  --out gazebo_sim/visual_yaw_smoke --epochs 1 --steps-per-epoch 2
"$NOMAD_PY" gazebo_sim/train_visual_yaw.py \
  --out gazebo_sim/visual_yaw_stage --epochs 30 --steps-per-epoch 32
```

冒烟和正式阶段都从固定 XY 编码器重新初始化。正式阶段没有从冒烟权重恢复。CUDA，torch 2.6.0+cu124。batch 16，lr 5e-5，seed 42。960 次更新全部完成，没有 NaN，进程退出码 0。

## 固定 XY 权重

训练前后都是 76,439,885 字节，SHA256 `48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56`。脚本在结束时再次核对，没有改这个文件。

## 05 验证

门槛是 MAE≤10°、90 分位误差≤20°、20–160° 大转向方向正确率≥95%。没有一轮通过。

| | MAE | p90 | 大转向方向正确率 | score | 门槛 |
| --- | ---: | ---: | ---: | ---: | --- |
| 初始化 epoch=-1 | 46.24° | 92.08° | 49.2% | 69.26 | 未过 |
| 最后一轮 epoch 29 | 57.26° | 127.57° | 58.9% | 89.15 | 未过 |

方向正确率最高大约 61%，MAE 和 p90 比初始化更差。按现有规则，未通过时保留 score 最低的诊断权重，所以 best.json 停在 epoch=-1。本机 best_yaw.pth 是这份初始化权重，22,675,733 字节，SHA256 `95c8c97bfeabcf369a64efa6dcddd91e27022da6c71e69535348636e4a645a32`。没有降低门槛，也没有用 06 另选 epoch。
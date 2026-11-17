# house_06 干净视觉最佳权重离线检查

固定权重是 `gazebo_sim/visual_stage_clean/best.pth`，对应 best.json 的 epoch 6、224 次更新。没有重训，也没有按这次结果换 epoch。

## 运行

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --config gazebo_sim/visual_stage_clean/model.yaml \
  --checkpoint gazebo_sim/visual_stage_clean/best.pth \
  --out gazebo_sim/visual_audit_clean_gpu
```

命令在 WSL 里跑完，终端回到提示符，并写出本目录。没有报错，没有切到 CPU。

## 身份

- 运行前哈希核对通过：76,439,885 字节，SHA256 `48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56`。
- manifest：`strict_checkpoint_load=true`，`device=cuda`，torch 2.6.0+cu124，seed 0，32 个样本。
- checkpoint_sha256 与上面的固定值一致。
- 这是示教图像上的离线检查，不是实机相机，也不是闭环。

## 四个目标转弯（temporal，goal mask=0，部署用的 waypoint index 2）

几何目标方位与旧审计相同。正角度是左。

| 观测→目标 | 几何目标 | b40 | 旧 gazebo 微调 | 本次 epoch 6 | 末点 index 7 | 向左比例 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8→13 | +43.69 | +2.30 | +0.46 | +14.56 | +22.94 | 0.91 |
| 22→31 | -88.68 | +19.25 | +17.31 | +34.12 | +49.40 | 1.00 |
| 38→43 | -43.54 | +0.35 | +1.96 | +16.41 | +30.49 | 0.81 |
| 51→57 | +58.79 | -7.47 | -3.90 | -31.59 | -50.42 | 0.00 |

第一弯的符号对了，中位转角从大约 +2° 增加到 +15°，仍然小于几何目标 +44°。后三个弯的中位方向都和几何目标相反，而且比 b40 偏得更远：第二、第三弯整段偏左，第四弯 32 条样本全部偏右。

同一组里 goal mask=1 的 waypoint-2 中位角分别是 +4.72、+35.29、+12.38、-36.83。mask=0 和 mask=1 在第二弯几乎一样。mask 差异不能当成模型已经按目标转弯。

距离头在这些配对上仍给出大约 4.7 到 15.8 的类别值，不能把这些数读成米。

离线检查不等于闭环成功。06、07 没有拿来重选权重。
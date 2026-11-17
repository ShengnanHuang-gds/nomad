# 给 Cursor：固定已选最佳视觉模型，完成 GPU 离线测试并推送

干净视觉阶段已经完成，**不要重新训练**。请先读
`gazebo_sim/visual_stage_clean/REVIEW.md`，执行下面任务。

## 固定待测权重

- `gazebo_sim/visual_stage_clean/best.json` 应为 epoch 6、updates 224。
- 本机 `gazebo_sim/visual_stage_clean/best.pth` 应为 76,439,885 字节，SHA256：
  `48a963373cfb1f49c22bd7129e36122d945b67603949008ef15d0a9d20937d56`。
- 模型配置是同目录 `model.yaml`，实际训练配方是 `stage_config.json`。

先核对文件与哈希。若不匹配，保存事实并停止，不换其他 epoch、
不覆盖权重或通过重新训练补出一个文件。
不能因后续 house_06 结果不好而重新挑权重；06–07 继续不加入训练。

## 本机 GPU 离线检查

在 WSL 仓库根目录，保留用户已有改动，正常拉取最新 main。
source 环境，只用 `$NOMAD_PY`。本任务不需要 Gazebo、也不发布车辆命令。

```bash
source gazebo_sim/nomad_wsl_env.sh
"$NOMAD_PY" gazebo_sim/audit_visual_model.py \
  --config gazebo_sim/visual_stage_clean/model.yaml \
  --checkpoint gazebo_sim/visual_stage_clean/best.pth \
  --out gazebo_sim/visual_audit_clean_gpu
```

脚本默认要求 CUDA，保持默认 32 个样本和 seed 0，以便与两份旧审计一致。
如果输出目录已有 manifest，使用新的带后缀目录并记录实际路径，不覆盖旧结果。
如报错，保留完整报错，不切 CPU、不改模型或几何控制规则。

## 结果核对

- manifest 中 strict_checkpoint_load=true、device=cuda，权重 SHA256 为上述固定值。
- 保留 image_match.csv、distance_matrix.csv、action_summary.csv、sampled_actions.npz 和终端日志。
- 简要比较 8→13、22→31、38→43、51→57 的方向与旧模型结果。
- 模型本阶段只训练了 goal mask=0；mask=1 是额外诊断，
  不能只凭两种 mask 差异变大就宣称模型正确，必须检查实际有目标时的方向/轨迹。
- 预测朝向不要求数值直接等于几何目标方位，但要如实报告方向、分布和整段轨迹。
- 这个任务只报告离线测试，不开启闭环，不启用 TEACH_ROUTE/TEACH_YAW_SPIN，
  不改变阈值或子目标参数，不据 06 结果继续训练或选模。

## 提交与汇报

在离线检查目录新增中文 README，记录运行命令、GPU/严格加载、权重身份、
是否完成、四个目标转弯的主要结果，以及任何报错。
正常提交并推送这份检查的 JSON、CSV、README、终端日志与体积很小的 NPZ。
不提交 best.pth、optimizer、解包数据，不混入其他改动，不 reset --hard，不强推。

完成后向用户返回提交 SHA 与摘要，明确“离线检查不等于闭环成功”。
用户只需回云端说“最佳模型检查推好了”，云端继续分析。

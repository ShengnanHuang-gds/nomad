# R2/R18 公平对照 — 本地进度（日志实读）

审计时间（UTC）：2026-11-07T06:07:57.327088+00:00

## 样本单位
{
  "n_pairs": 500,
  "unique_curr_traj_t": 482,
  "unique_triple": 500,
  "unit": "one row = one (traj_name, curr_t, goal_t) far-goal pair; metrics averaged over 500 pairs"
}

## R2
- 目录：`C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs\nomad\nomad_e_r2_fair_20261107`
- 已连续完成 epoch：**0–7**（共 8/8 条 train_log 记录）
- 进行中：无（或尚未写入下一条 log）
- E-oracle 初始化：`ema_29.pth` sha256 `9d31ac8ac03eaa15…`
- 每 epoch：**3847** batch（train_log），索引样本 **123125**，batch32
- LR：ep0 首轮 `lr_epoch_start=3e-7` → 当轮结束 `lr_epoch_end=3e-5`；**per_step** warmup+cosine
- 恢复：**从头训练**，未使用 ema_latest 伪恢复
- 当前验证最佳（按 nav ADE）：**epoch 4** nav_ade=12.829 cm

## R18
- 目录：`C:\Users\61078\Desktop\nomad\visualnav-transformer\train\logs\nomad\nomad_e_r18_fair_20261107`，存在=True
- 状态：R2 同进程串行结束后自动启动（当前未见目录=尚未开始）

## 实现修复（已入库，不打断当前 R2）
1. 路径输入梯度仅统计 cond_encoder.1.weight 列 [258:274)，并记录一步 AdamW 后该列权重 Δ。
2. 报告配对按 manifest `order` 与完整三元组对齐，保留 500 对；bootstrap 按轨迹抽中后保留该轨迹全部配对。
3. 编排脚本禁止仅凭 train_log+ema_latest 继续训；不完整中断保留产物、不自动清空重训。

## 训练命令（R2，终端日志摘录）
```
python -u run_r2_r18_fair_ablation.py --train-only
→ train_e_dino.py --config config/nomad_e_dino_r2_r18.yaml --init-from e_oracle ...
```
# Gazebo 视觉微调训练资料

这次只打包本机实际训练用过的小文件。没有重训，没有改样本，也没有把 house_run_06、07 放进训练包。

压缩包 `gazebo_visual_training_inputs.tar.gz`：2358837 字节，SHA256 `c66009115b4c7119f185305adb7b0675349a4d38985c9250d43e67b0b6a81eb4`。

## 六条训练路线

| 路线 | 图像 | 编号 | 断号 | 轨迹长度与图像一致 | 尺寸 |
| --- | ---: | --- | --- | --- | --- |
| house_run_00 | 48 | 0–47 | 无 | 是 | 320x240 |
| house_run_01 | 37 | 0–36 | 无 | 是 | 320x240 |
| house_run_02 | 46 | 0–45 | 无 | 是 | 320x240 |
| house_run_03 | 41 | 0–40 | 无 | 是 | 320x240 |
| house_run_04 | 44 | 0–43 | 无 | 是 | 320x240 |
| house_run_05 | 38 | 0–37 | 无 | 是 | 320x240 |

## 划分

train：house_run_00、house_run_01、house_run_02、house_run_03、house_run_04、house_run_05。
test：house_run_06、house_run_07。
两边没有交集。test 里原来就是 06 和 07，本次没有改划分。

## 能确认的训练过程

配置是 `visualnav-transformer/train/config/nomad_gazebo.yaml`。data_folder 指向 `C:/Users/61078/Desktop/nomad/gazebo_sim`。batch_size 16，lr 5e-5，epochs 4，load_run 为 `nomad_gazebo_ft_2026_11_16_14_21_34`，load_epoch 30，stop_epoch 33，eval_freq 999，goal_mask_prob 0.5，context_size 3，len_traj_pred 8，action/distance 上限 20。

GPU 检查实际加载的权重在 `D:\nomad_data\...\nomad_gazebo_ft_2026_11_16_14_22_52\ema_latest.pth`。桌面仓库里有一份同名拷贝。两个目录都只有 .pth，没有 stdout、指标或训练时另存的配置。

训练日志：不可用。`scheduler_latest.pth` 已放入包内；旁边的 JSON 只是这个文件保存时的调度器状态，不是整个训练过程的学习率。

## 没有放进包里的内容

- 两个 split 目录里的 `dataset_go_stanford.lmdb/data.mdb`，各显示约 8 GiB，是 LMDB 映射文件，不是小划分文件。
- 模型权重和 optimizer_latest.pth。
- house_run_06、house_run_07 的图像。

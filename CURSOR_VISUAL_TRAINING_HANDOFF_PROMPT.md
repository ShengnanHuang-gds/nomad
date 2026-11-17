# 给 Cursor：收集真实 Gazebo 训练资料并推送，供修复视觉导航

请直接执行下面的资料收集、核对、打包和 Git 推送任务，完成后汇报提交号及缺失项。
用户已授权将这些项目训练资料同步到当前 GitHub 仓库。

## 最终目标与本次范围

用户要 NoMaD 视觉导航走通 house_06：相机图像和拓扑图决定定位/子目标，模型预测运动路点。
不使用示教坐标、示教 yaw、按里程触发转弯或整段路线跟随代替视觉模型。

当前已做过 b40 和 nomad_gazebo 的同条件 GPU 离线检查，两者都没有可靠按目标方向转弯。
本次任务是把**本机实际训练所用的资料**完整交给云端分析。
本次不重新训练、不跑新的闭环、不重录示教、不改导航/控制/训练代码或模型参数。
也不要为了让检查通过而修改、清洗或重新生成训练样本和 train/test 划分。

house_run_06、house_run_07 继续不加入训练。
如果现有划分已经包含它们，保留并报告原始事实，不能静默移除来隐藏问题。

## 已知本机位置：先核实，不要凭目录名猜测

- Git 仓库通常在 Windows `C:\Users\61078\Desktop\nomad`，
  WSL `/mnt/c/Users/61078/Desktop/nomad`；WSL 用户 `hsnnb`。
- 模型实际运行源码通常在仓库下面的 `visualnav-transformer`。
- 最近 GPU manifest 的微调配置路径：
  `/mnt/c/Users/61078/Desktop/nomad/visualnav-transformer/train/config/nomad_gazebo.yaml`。
- 微调 checkpoint 所在目录：
  `/mnt/d/nomad_data/visualnav-transformer/train/logs/nomad/nomad_gazebo_ft_2026_11_16_14_22_52`。
- 微调配置的 load_run 还引用了 `nomad_gazebo_ft_2026_11_16_14_21_34`；
  如有相关配置/日志，也保留它与后续训练的关系。
- 已推送的 manifest：
  `gazebo_sim/visual_audit_gazebo_gpu/manifest.json`。

在 WSL 中先 source `gazebo_sim/nomad_wsl_env.sh`，Python 工作使用 `$NOMAD_PY`。
确认 `sys.executable`，不要误用 Windows Python。
写出的脚本、JSON、Markdown 一律 UTF-8，避免 PowerShell 默认 UTF-16。

Git 中的 `train/` 与本机实际使用的 `visualnav-transformer/train/` 可能不是同一份源码。
必须记录实际路径和文件 SHA256，不能用 Git 里另一份同名文件充当本机训练源码。

## 需要收集的内容

### 1. 训练图像与对应轨迹：house_run_00–05

找到本机实际使用的六条路线目录，每条收集：

- 全部按数字命名的 JPG/PNG 原图，保持原文件名和内容。
- 与这些图像配套的 `traj_data.pkl`。

逐条检查并记录：

- 实际原目录、图像数量、编号范围、是否有断号/重复编号。
- position、yaw 数组长度和形状，以及是否与图像逐帧对应。
- 图片是否可以解码、尺寸及颜色模式。
- 缺失、无法读取或长度不一致的文件；不要擅自补图、插值、重排或重录。

06–07 不放入训练数据包。本次无需再次同步已上传的 06 图像。

### 2. 实际训练配置与数据划分

收集当前实际模型目录中的：

- `train/config/nomad_gazebo.yaml` 和 `train/config/defaults.yaml`。
- `train/vint_train/data/data_config.yaml`。
- `train/vint_train/data/data_splits/gazebo_house/train/`、`test/` 的实际小文件，
  尤其 `traj_names.txt`；如配置指向别处，以实际指向为准。
- 微调输出目录中保存的配置副本（如果存在）；区分“现在的 YAML”和“训练时保存的 YAML”。

记录 train/test 中的真实路线列表与交集，检查是否有 06–07。
记录训练时使用的 data_folder、context_size、waypoint_spacing、len_traj_pred、
action/distance 范围、goals_per_obs、goal_mask_prob、batch_size、lr、epochs、
load_run、load_epoch、stop_epoch、eval_freq、alpha。
已经在 GPU manifest 中出现的值可作为线索，但不能冒充训练时日志证明。

### 3. 实际训练源码快照

收集本机实际使用的以下文件，放进资料包的 `source/`，不要覆盖仓库中其他同名源码：

- `train/train.py`
- `train/vint_train/training/train_eval_loop.py`
- `train/vint_train/training/train_utils.py`
- `train/vint_train/data/vint_dataset.py`
- `train/vint_train/data/data_utils.py`

记录原始绝对路径、SHA256、所属 Git 提交号和是否有本地未提交修改（能查到才填写）。
本次只做快照，不修复源码。

原因：云端当前源码显示每个 epoch 两次 scheduler.step()，指定 epoch 恢复时也按两倍推进；
需要先确认本机实际执行版本，且后续修复必须同时核对恢复与 checkpoint 保存时刻。
不要在收集阶段只删除一处 step() 后直接重新训练。

### 4. 微调训练日志与调度状态

搜索上述两个微调目录以及已有终端保存记录，收集与该次训练直接相关的小文件：

- stdout/stderr 文本、CSV/JSON 指标、配置记录、训练启动命令（如果有）。
- dataset 长度、batch 数、实际开始/结束 epoch、每个 epoch 的学习率、验证是否执行。
- 小体积 `scheduler_*.pth` / `scheduler_latest.pth` 可放入包中。
  如提取成 JSON，明确这是 checkpoint 保存时刻的状态，不是完整训练期间的学习率轨迹。
- checkpoint 文件清单：名字、大小、修改时间，用于确认实际训练到哪个 epoch。

本次不需要再次打包大模型权重、optimizer 权重或 b40 权重。
不要为了获得日志而重启旧训练。
如果日志没有保存、终端输出已丢失，明确写“不可用”，不要补造 loss、epoch 或学习率序列。

## 打包方式与仓库输出

请在仓库新增：

```text
gazebo_sim/training_handoff/
  README.md
  manifest.json
  gazebo_visual_training_inputs.tar.gz
```

压缩包内部建议布局：

```text
dataset/house_run_00/...
dataset/house_run_01/...
...
dataset/house_run_05/...
config/...
splits/train/...
splits/test/...
source/...
logs/...
```

要求：

- 原始训练数据保持不动，在临时目录中收集副本再打包。
- 压缩包使用相对路径，解包不应包含绝对路径、`..` 跳出目录或指向本机其他位置的软链接。
- manifest 记录每个收集文件的包内路径、原始来源路径、字节数、SHA256、缺失项，
  并记录 Python/Torch 版本及数据检查结果。
- README 用中文简要列出六条路线的图像/轨迹数量、实际划分、能确认的训练过程与缺失证据。
- 记录最终压缩包的字节数和 SHA256；不要把压缩包自身放入它的内容中。
- 全局 `.gitignore` 会忽略 JPG/PNG，所以直接添加目录可能漏图。
  使用上述 tar.gz 可保留图像，不要为了同步这批资料而取消全局图片忽略规则。
- 若压缩包接近 GitHub 单文件限制，改为较小的分卷并在 README 写清重组命令。
  不要把超大 checkpoint 混入包中。
- 只收集项目训练资料；排除凭据、缓存、个人文件、无关数据。

## 推送前核对与执行

1. 对压缩包列目录并解到另一个临时目录，核对文件数、图像解码、轨迹长度与 SHA256。
2. 不要求资料必须“全绿”：真实缺失/不一致是重要分析结果，保留并报告即可。
3. 保留本机已有未提交修改，只暂存此次 `gazebo_sim/training_handoff/` 输出；
   不要混入其他源码改动，不用 reset --hard，不强推，不覆盖远端新提交。
4. 查看 origin/main，正常提交并推送到远端 main。
   如当前工作区无法直接同步，使用独立临时 worktree 完成资料提交，保留原工作区。
5. 推送完成后，返回：提交 SHA、压缩包路径/大小/SHA256、六条路线核对表、
   实际 train/test 划分、可用训练日志列表和所有缺失项。

用户做完这一步，只需回云端说“资料推好了”。后续由云端核查训练链路和动作标签，
再准备本地 GPU 上执行的视觉模型修复方案；本次不要提前宣称模型已修复。

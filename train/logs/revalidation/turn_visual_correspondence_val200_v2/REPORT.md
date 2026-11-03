# 转弯视觉对应诊断 v2（13 案例修正图）

## 代码事实

- **Checkpoint**: `logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth`
- **Git**: `6003399`
- **命令**: `C:\Users\61078\anaconda3\envs\nomad_train\python.exe run_turn_visual_correspondence_v2.py`
- **v1 参考目录**: `logs\revalidation\turn_visual_correspondence_val200`
- ctx2 历史帧：**t-1**、**t-2**（数据集帧索引步长 1，非 spacing×）；goal：**curr + goal_k**（goal_k=min(39,max_goal)）。
- 图像：4:3 中心裁切 → 224×168；DINO cache **6×8 patch**（匹配不含 CLS）。
- **legacy_mutual_mean_max_cos（v1 列名，数值未改）** = hist→curr 与 curr→hist 两个方向 **mean(max cos)** 的算术平均；**不是**双向一致配对率。
- v2 另报 **bidirectional_consistent_count / mean_cos**（h→c 最近邻为 c 且 c→h 最近邻为 h）。
- v1 `draw_case` 固定短线已标注 **DEPRECATED**；v2 使用 patch 中心真实坐标跨图连线。
- **展示连线规则**：Up to 10 curr patches: linspace over 48 grid cells, supplemented by rng seed 20261103+t; not ranked by match score.
- **禁止解读**：相似度/配对数 ≠ 真实视野重叠率；连线 ≠ 模型注意力。

## 运动标签（离线 GT，不可部署）

- hist_abs_yaw：t-2→t 累计 **|Δyaw|**（wrap 后求和）。
- future_winding_8step：未来 8 步累计 **|Δyaw|**；future_net：八步净 yaw。
- motion_class：hist≥12° → **A**；否则 future winding≥45° → **B**；否则 **C**。

## 逐例分析（13）

### counter_high_match_high_ade — no2vc_5_0 t=40

- **【代码事实】** goal_t=59，间隔 19 步；motion=B_future_turn_soon；hist_abs=1.077°；future_wind=60.967°；ADE=23.2909 cm (F4=8.6347, B4=37.9470, dir=24.606°)；legacy_near=0.93471；cons_near n=42。
- **1.共同参照** 【图像观察】门廊/拱门与侧墙在 t-2、t-1、curr 仍可见连续结构；目标帧为同走廊更远处的门洞视角。
- **2.匹配合理性** 【代码事实】legacy mutual_near≈0.935，双向一致配对 n=42。【图像观察】lime 线多沿竖直结构；地面/亮区 NN 可能漂移。【尚不能判断】是否等于真实 overlap。
- **3.历史运动** 【代码事实】t-2→t 累计 |Δyaw|≈1.1°；未来八步 winding≈61° → motion_class=B（历史几乎未转，未来将弯）。
- **4.目标线索** 【图像观察】goal index=59，间隔 19 步；含远端通道/门洞，与 curr 同场景族但更远。【研究推断】目标提供“往哪走”的远景，不等于已对齐局部弯折。
- **5.误差类型** 【代码事实】path ADE≈23.3 cm，F4≈8.6 cm，B4≈37.9 cm，dir_err≈25°。【图像观察】pred 弯折幅度/方向弱于 GT，后段误差更大。
- **6.观察/推测** 【观察】高 DINO 匹配 + 低历史转角。【推测】失败更像未来弯折几何或路径头未跟上，而非历史视野完全丢失。【尚不能判断】模型内部是否用到 goal。

### counter_low_match_high_ade — no2vc_65_0 t=3

- **【代码事实】** goal_t=19，间隔 16 步；motion=A_hist_already_turning；hist_abs=16.740°；future_wind=122.707°；ADE=52.2062 cm (F4=18.9511, B4=85.4614, dir=107.518°)；legacy_near=0.70457；cons_near n=24。
- **1.共同参照** 【图像观察】走廊尽头、左侧沙发/杂物区在 t-2 与 curr 部分共有；curr 更近楼梯口，共同参照变少。
- **2.匹配合理性** 【代码事实】legacy mutual_near≈0.705，双向一致 n=24，mean_cos≈0.62。【图像观察】连线稀疏，重复墙面/地面易误导 NN。
- **3.历史运动** 【代码事实】hist |Δyaw|≈16.7°（≥12° 阈值）→ A；未来 winding≈123°。
- **4.目标线索** 【图像观察】goal index=19，间隔 16；为右侧木柜/门局部特写，与 curr 视角差大。
- **5.误差类型** 【代码事实】ADE≈52.2 cm，dir_err≈107°。【图像观察】pred 与 GT 弯折方向相反级。
- **6.观察/推测** 【观察】低 legacy 匹配 + 大方向错。【推测】目标局部帧 + 历史-当前对齐弱可能共同不利。【尚不能判断】因果权重。

### sharp_bad — sim39hF_0_9 t=95

- **【代码事实】** goal_t=134，间隔 39 步；motion=A_hist_already_turning；hist_abs=54.189°；future_wind=225.465°；ADE=42.2325 cm (F4=13.2611, B4=71.2040, dir=104.865°)；legacy_near=0.84503；cons_near n=26。
- **1.共同参照** 【图像观察】室内转弯场景，t-2 与 curr 墙线/家具布局仍有部分重叠但视角差明显（hist |Δyaw|≈54°）。
- **2.匹配合理性** 【代码事实】legacy≈0.845，双向一致 n=26。【图像观察】t-2|curr 连线较 t-1|curr 更散。
- **3.历史运动** 【代码事实】A 类；未来 winding≈225°。
- **4.目标线索** 【代码事实】goal 间隔 39 步。【图像观察】目标为更远处转弯后视角（需结合 case 图）。
- **5.误差类型** 【代码事实】ADE≈42.2 cm，B4≈71 cm，dir_err≈105°；转弯形状与末端朝向均偏。
- **6.观察/推测** 【观察】历史已大角变化仍保留一定 patch 相似度。【推测】失败不 solely 来自“无共同参照”。

### sharp_bad — no27vc_26_0 t=179

- **【代码事实】** goal_t=190，间隔 11 步；motion=A_hist_already_turning；hist_abs=54.473°；future_wind=212.553°；ADE=50.1187 cm (F4=15.8756, B4=84.3618, dir=147.012°)；legacy_near=0.84370；cons_near n=23。
- **1.共同参照** 【图像观察】走廊/窗口在相邻帧仍部分连续；hist 累计转角≈54°，肉眼可见视角变化。
- **2.匹配合理性** 【代码事实】legacy≈0.844，双向一致 n=23。
- **3.历史运动** 【代码事实】A；future winding≈213°。
- **4.目标线索** 【代码事实】goal 间隔仅 11 步（较近）。【研究推断】近 goal 不一定更易——本例 ADE 仍高。
- **5.误差类型** 【代码事实】ADE≈50.1 cm，dir_err≈147°；以转向/朝向为主。
- **6.观察/推测** 【观察】近 goal + 高 legacy 仍大 dir_err。【反例】“goal 近 ⇒ 一定好”不成立。

### sharp_bad — sim12h_1_5 t=23

- **【代码事实】** goal_t=62，间隔 39 步；motion=A_hist_already_turning；hist_abs=50.770°；future_wind=199.344°；ADE=36.1363 cm (F4=10.7616, B4=61.5110, dir=80.200°)；legacy_near=0.71856；cons_near n=19。
- **1.共同参照** 【图像观察】仿真走廊，历史帧与 curr 共有墙/地面纹理；hist |Δyaw|≈51°。
- **2.匹配合理性** 【代码事实】legacy≈0.719（sharp_bad 中偏低），双向一致 mean≈0.59。
- **3.历史运动** 【代码事实】A；future winding≈199°。
- **4.目标线索** 【代码事实】goal 间隔 39。
- **5.误差类型** 【代码事实】ADE≈36.1 cm，dir_err≈80°。
- **6.观察/推测** 【观察】匹配指标偏低的一组失败。【推测】可能与重复纹理有关，但未证明。

### sharp_bad — no29vc_35_0 t=47

- **【代码事实】** goal_t=75，间隔 28 步；motion=A_hist_already_turning；hist_abs=21.553°；future_wind=192.943°；ADE=30.0618 cm (F4=11.1620, B4=48.9615, dir=80.848°)；legacy_near=0.90395；cons_near n=33。
- **1.共同参照** 【图像观察】t-2/t-1/curr 走廊与左侧大窗连续；goal 为转弯后另一段通道（人物/玻璃隔断），场景已切换。
- **2.匹配合理性** 【代码事实】legacy≈0.904，lime 在窗框/墙缘较密。【图像观察】历史-当前匹配位置大体合理。
- **3.历史运动** 【代码事实】hist |Δyaw|≈21.6° → A；future winding≈193°。
- **4.目标线索** 【图像观察】goal 展示弯后通道，提供转向后景象；与 curr 非同一视角。
- **5.误差类型** 【代码事实】ADE≈30 cm，dir_err≈81°。【图像观察】GT 左弯、pred 右弯，符号级转向错误。
- **6.观察/推测** 【观察】高匹配仍转向反号。【推测】更像路径/goal 条件利用或转弯时机，而非历史无参照。【尚不能判断】goal 左右歧义是否主因。

### sharp_good — sim12h_1_6 t=21

- **【代码事实】** goal_t=60，间隔 39 步；motion=A_hist_already_turning；hist_abs=38.333°；future_wind=229.183°；ADE=14.3614 cm (F4=7.7405, B4=20.9824, dir=22.812°)；legacy_near=0.82372；cons_near n=26。
- **1.共同参照** 【图像观察】门廊/墙线在 t-1 与 curr 重叠较多；t-2 视角差更大。
- **2.匹配合理性** 【代码事实】legacy≈0.824，双向一致 n=26。
- **3.历史运动** 【代码事实】hist |Δyaw|≈38° → A（非 B）；future winding≈229°。
- **4.目标线索** 【代码事实】goal 间隔 39。
- **5.误差类型** 【代码事实】ADE≈14.4 cm（sharp_good）；前后段均有偏差但可接受。
- **6.观察/推测** 【观察】大 future winding + 已发生 hist 旋转仍预测较好。【反例】“必须先靠 B 类才转好”不成立。

### sharp_good — no28vcF_5_0 t=59

- **【代码事实】** goal_t=81，间隔 22 步；motion=A_hist_already_turning；hist_abs=38.103°；future_wind=163.987°；ADE=5.9375 cm (F4=2.6220, B4=9.2530, dir=11.142°)；legacy_near=0.84094；cons_near n=30。
- **1.共同参照** 【图像观察】走廊结构在历史与 curr 间连续（结合 case 图）。
- **2.匹配合理性** 【代码事实】legacy≈0.841，双向一致 n=30。
- **3.历史运动** 【代码事实】A，hist |Δyaw|≈38°。
- **4.目标线索** 【代码事实】goal 间隔 22。
- **5.误差类型** 【代码事实】ADE≈5.9 cm，dir_err≈11°。
- **6.观察/推测** 【观察】成功样本；匹配指标与失败组差异不大。【尚不能判断】成功主因。

### sharp_good — sim7hF_0_2 t=19

- **【代码事实】** goal_t=56，间隔 37 步；motion=A_hist_already_turning；hist_abs=34.915°；future_wind=156.759°；ADE=10.1399 cm (F4=5.9102, B4=14.3696, dir=5.036°)；legacy_near=0.83708；cons_near n=34。
- **1.共同参照** 【图像观察】仿真场景墙/地面在历史与 curr 可对照。
- **2.匹配合理性** 【代码事实】legacy≈0.837，far 双向一致 mean≈0.80。
- **3.历史运动** 【代码事实】A，hist |Δyaw|≈35°。
- **4.目标线索** 【代码事实】goal 间隔 37。
- **5.误差类型** 【代码事实】ADE≈10.1 cm，dir_err≈5°。
- **6.观察/推测** 【观察】转向场景下预测与 GT 较一致。

### sharp_good — sim10hF_0_13 t=16

- **【代码事实】** goal_t=36，间隔 20 步；motion=A_hist_already_turning；hist_abs=19.990°；future_wind=137.382°；ADE=12.3202 cm (F4=1.9429, B4=22.6975, dir=13.568°)；legacy_near=0.80718；cons_near n=29。
- **1.共同参照** 【图像观察】历史与 curr 部分结构连续；hist net 与 abs 差异大（净转≈-91°，累计≈20°）。
- **2.匹配合理性** 【代码事实】legacy≈0.807。
- **3.历史运动** 【代码事实】A；future winding≈137°。
- **4.目标线索** 【代码事实】goal 间隔 20。
- **5.误差类型** 【代码事实】ADE≈12.3 cm，F4 小 B4≈22.7 cm；后段弯折偏差更大。
- **6.观察/推测** 【观察】整体尚可但后四步误差抬升。【推测】弯折后半 timing 仍敏感。

### straight_ref — no6vc_77_0 t=157

- **【代码事实】** goal_t=196，间隔 39 步；motion=A_hist_already_turning；hist_abs=14.147°；future_wind=17.377°；ADE=31.5842 cm (F4=9.8122, B4=53.3561, dir=34.369°)；legacy_near=0.84507；cons_near n=26。
- **1.共同参照** 【图像观察】走廊/门洞在帧间大体连续。
- **2.匹配合理性** 【代码事实】legacy≈0.845；far 双向一致 mean 较低≈0.56。
- **3.历史运动** 【代码事实】hist |Δyaw|≈14° → A，但 future winding 仅≈17°（近直行）。【尚不能判断】标签 A 在此例语义有限。
- **4.目标线索** 【代码事实】goal 间隔 39。
- **5.误差类型** 【代码事实】ADE≈31.6 cm，B4≈53 cm；非 sharp 组却路径误差偏大。
- **6.观察/推测** 【观察】未来弯折不大仍 ADE 高。【推测】可能距离/尺度或局部几何，不单是“急转”。

### straight_ref — no13vc_4_0 t=87

- **【代码事实】** goal_t=126，间隔 39 步；motion=C_other_or_unclear；hist_abs=9.647°；future_wind=16.977°；ADE=5.4079 cm (F4=3.3106, B4=7.5053, dir=5.445°)；legacy_near=0.93967；cons_near n=43。
- **1.共同参照** 【图像观察】场景稳定，历史与 curr 参照连续。
- **2.匹配合理性** 【代码事实】legacy≈0.940，双向一致 n=43（13 例中最高档）。
- **3.历史运动** 【代码事实】C；hist |Δyaw|≈9.6°，future winding≈17°。
- **4.目标线索** 【代码事实】goal 间隔 39。
- **5.误差类型** 【代码事实】ADE≈5.4 cm。
- **6.观察/推测** 【观察】近直行 + 高匹配 + 低 ADE 一致。【不能推广】到急转。

### straight_ref — no15vc_45_1 t=47

- **【代码事实】** goal_t=86，间隔 39 步；motion=C_other_or_unclear；hist_abs=1.657°；future_wind=16.767°；ADE=13.7060 cm (F4=3.9051, B4=23.5069, dir=15.527°)；legacy_near=0.93834；cons_near n=43。
- **1.共同参照** 【图像观察】帧间变化小，共同参照清晰。
- **2.匹配合理性** 【代码事实】legacy≈0.938，双向一致 n=40。
- **3.历史运动** 【代码事实】C；hist |Δyaw|≈1.7°。
- **4.目标线索** 【代码事实】goal 间隔 39。
- **5.误差类型** 【代码事实】ADE≈13.7 cm，B4≈23.5 cm；中等误差。
- **6.观察/推测** 【观察】匹配很高但 ADE 非最低。【反例】“匹配高 ⇒ 路径必好”。

## 研究推断（弱）

- sharp_good vs sharp_bad：**legacy mutual 与双向一致计数均无稳定分离**（例如 no29vc 高匹配仍 dir_err≈81°）。
- **counter_high_match_high_ade**（no2vc_5_0）：hist 几乎未转（B），匹配很高仍 ADE≈23 cm → 不支持“失败=历史无重叠”单一叙事。
- **counter_low_match_high_ade**（no2vc_65_0）：匹配偏低 + 目标帧局部化 + 方向近 180° 错 → 历史与 goal 条件 **可能** 同时不利（因果未证）。
- t-1 相对 t-2 的 NN 相似度在 val200 全体仍偏高（v1 统计）；描述性“近历史更易匹配”≠ overlap 率。

## 尚不能判断

- patch 线是否反映模型使用的表征；需 attention/消融而非 DINO 离线匹配。
- 13 例无法做回归；motion_class 阈值（12°/45°）为分析 conveniences。
- goal 图像“有共同物体”是否足以确定局部路径 — **不能**。

## 总问：更提示历史运动问题，还是未来转向/goal 利用问题？

**结论：目前无法单一区分**；若只凭 13 例，**略倾向未来转向几何 + goal/路径头利用**（含弯折时机、符号），而非单纯“历史视野重叠不足”。

**支持“未来转向/goal/路径”侧的证据**
- no2vc_5_0（B）：hist |Δyaw|≈1° 仍要 future wind≈61°，匹配高但 B4 误差大。
- no29vc_35_0：历史-当前匹配密集，GT 左弯 vs pred 右弯（方向级失败）。
- 多个 sharp_bad：dir_err 80°–147°，远超 hist 已转角度所能单独解释的量级。

**支持“历史运动/参照”侧或反例**
- no2vc_65_0：legacy mutual 低、hist 已有 16.7° 变化，失败最极端。
- sim12h_1_5：legacy 相对更低（≈0.72）且 ADE 高。
- sim12h_1_6 / no28vcF：hist 已转（A）且 future winding 极大，仍 **sharp_good** → 说明“已在转”不必然失败。
- no6vc_77_0：future winding 小但 ADE≈31.6 cm → 误差不总是“急转”故事。

## 产出文件

- `cases/*_v2.png`：修正连线 + goal + 路径（米）
- `cases/*_v1_style_DEPRECATED.png`：保留 v1 假线对照
- `case_stats.csv`、`case_notes.json`、本报告、`meta.json`


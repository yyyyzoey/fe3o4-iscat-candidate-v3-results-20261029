# 生成日志 — 真实执行记录

```
result_class                     = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
through_focus                    = true   (NOT sample-space near field)
full_jones_chain                 = UNVERIFIED
high_na_model_validation         = UNVERIFIED
paper_convention_checks          = UNVERIFIED
absolute_calibration             = false
sample_space_near_field          = false
publisher_typeset_pdf            = NOT_OBTAINED
linear_midpoint_reconstruction   = FAILED_KEPT
```

本文件是**事后按实际日志整理**的执行记录，原始逐条日志在 `logs/*.jsonl`（append-only，含失败与重跑）。

## 1. 环境与基线

| 项 | 值 |
|---|---|
| 工作区 | `C:\Users\PC\Documents\Codex\2026-10-29\fe3o4-iscat-codex-handoff-v3-agents` |
| Git 工作树 | `work/v4/repo` |
| 分支 | `v4-audit-final-candidate` |
| HEAD | `0a58aff466d053bbd3f82fe9fc77fb57511edd2c`（2026-10-30 15:53:08 +0800，"Finalize V4.1 candidate audit and reproducible results"） |
| Python | 3.11.7 |
| numpy / h5py | 1.26.4 / 3.9.0 |
| matplotlib / scipy | 3.8.0 / 1.11.4 |
| pandas / scikit-image | 2.1.4 / 0.22.0 |
| plotly | 5.9.0（HTML 交互） |
| 未安装 | pyvista / vtk、kaleido、GitHub CLI |

基线提交在出图前用 `git rev-parse HEAD` 核对，`git status --porcelain` 为空，主 HDF5 只读打开。

## 2. 数据溯源

| 粒径 | 文件 | 字节 | shape |
|---|---|---|---|
| 30 nm | `work/v4_final_20261030/final_tree/results_v4/data/D030nm/cube.h5` | 424,882,738 | 171×241×241 |
| 100 nm | `…/D100nm/cube.h5` | 424,639,674 | 171×241×241 |
| 200 nm | `…/D200nm/cube.h5` | 424,913,287 | 171×241×241 |

三份文件的 SHA256 记录在 `config/visual_config.json` 与包外 `package_verification.json`。
**本轮没有写入过这三个文件。**

## 3. 执行顺序与耗时

| Step | 脚本 | 做了什么 | 日志/耗时 |
|---|---|---|---|
| 1 | `step1_layers.py` | 选 50 层、写 CSV/JSON、算全网格统计与共用色标 | `logs/step1_layers.jsonl`，0.84 s |
| 2 | `step2_2d.py` | 50 层 10×5 总览、6 页图册、信号分解、三粒径对比 | `logs/step2_2d.jsonl`，两轮 30.79 s + 36.88 s |
| 3 | `step3_3d.py` | 50 层堆叠（真实 / z×3）、体渲染、半剖切、正交切片、等值面 | `logs/step3_3d.jsonl`，见下 |
| 4 | `step4_axis.py` | 中心轴向 171 层曲线与 CSV | `logs/step4_axis.jsonl`，1.50 s（重跑 1.54 s） |
| 5 | `step5_html.py` | 6 个自包含 Plotly 页面 | `logs/step5_html.jsonl`，13.09 s |

逐文件记录：

- `step1_layers.jsonl`：6 条记录，1 次执行，各次耗时 0.84s
- `step2_2d.jsonl`：44 条记录，3 次执行，各次耗时 4.86s / 30.79s / 36.88s
- `step3_3d.jsonl`：53 条记录，7 次执行，各次耗时 206.40s / 19.06s / 0.00s / 0.00s / 11.38s / 0.27s / 105.66s
- `step4_axis.jsonl`：6 条记录，2 次执行，各次耗时 1.50s / 1.54s
- `step5_html.jsonl`：8 条记录，1 次执行，各次耗时 13.09s

## 4. 被否决的第一次三维渲染（保留，不隐藏）

第一次跑 `step3_3d.py`（仅 D100，206.4 s）后目检发现：

> 50 个平面用**统一 alpha = 0.30** 叠加，而每层绝大部分区域 `I_cross ≈ 0`、颜色近白，
> 于是 50 层白底叠加成一块**不透明白板**，只有最上层可见，层次与正负结构全部丢失。

因此这一版**没有交付**，渲染器被重写：

1. 四边形面片改为 numpy 向量化构造（320 000 面从 ~40 s/图降到 ~5 s/图）；
2. alpha 改为**随 |I_cross| 超线性增长**（`0.96·max(0, v−0.02)^1.8`），近零背景全透明；
3. 增加**层梯子**：每 5 层一个浅灰边框、每 10 层加粗、左后墙 50 个刻度，保证 50 层可数；
   加一条虚线标出 zeta = 0 焦面；
4. 增加**深度雾化**（远端向白混合 0.70→1.00，仅显示用，已在图注说明）；
5. PDF 改为 `rasterized=True`，z×3 版 PDF 从 14.8 MB 降到 0.16 MB；
6. 新增**半剖切**补充图（每层 x>0 半边 alpha 置 0）以显示正负翻转。

重写后先只渲 D100 两版（19.1 s）目检，再迭代一次（11.4 s），确认后才跑三粒径全量（105.7 s）。

同期还有两次**空跑**（`step3_3d.jsonl` 中 0.27 s 的 start→done）：原因是 `main()` 里
`only` 选择条件写错导致所有粒径都被 `continue` 跳过，发现后立刻修正并重跑，未产生任何交付物。

## 5. 质量门（写包前逐项检查）

| 检查 | 方法 | 结果 |
|---|---|---|
| 50 层互不相同 | 断言 `len(set(indices)) == 50`，最大吸附误差 0.98 nm | 通过 |
| 三粒径图层完全一致 | `identical_selection_all_cases` 事件 | 通过 |
| PNG/PDF/HTML 存在且非空 | 见 `ACCEPTANCE.md` 与 `package_verification.json` | 通过 |
| 图像目检 | 逐张打开 montage / 3D / 剖切 / 分解 / 曲线 | 通过（common 版 D030 空白属预期，已在图注写明） |
| HTML 自包含 | 无 `<script src=...>`；每份 50 个 surface trace | 通过（结构检查） |
| HTML 像素级复验 | 沙箱浏览器拒绝 `file://`，kaleido 未安装 | **未做**，见 `03_limitations_zh.md` |

## 6. 产物计数

- PNG **39** 个、PDF **45** 个、HTML **6** 个。
- 逐文件 SHA256：`SHA256SUMS.txt`（包内）。
- 两个 ZIP 的体积/成员数/SHA256：包外 `package_verification.json`。

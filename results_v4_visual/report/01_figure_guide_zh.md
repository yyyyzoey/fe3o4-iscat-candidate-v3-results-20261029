# 图件导读 — 每个文件画的是什么量

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

## 0. 三条通用说明

- **坐标**：所有二维图的横纵轴是物方横向坐标 x, y（nm，±400 nm 显示窗口，主网格仍为 ±1200 nm / 241 点，
  未重采样）；三维图的 z 轴是 **离焦坐标 zeta（nm）**，不是样品空间深度。
- **主显示量**：`I_cross = 2 Re(E_ref* · E_scat)`，**有符号**，发散色图 `RdBu_r`
  （负 = 蓝，零 = 白，正 = 红）。`I_total` / `I_ref` / `I_scat` 只用 `viridis` / `magma`。
- **两套色标**：文件名含 `common` 的用三粒径统一色标 ±1.5477；含 `normalized` 的用各自
  `max|I_cross|` 归一化到 ±1。

## 1. 主图 `figures_main/`

| 文件 | 展示量 | 色标 | 用途 |
|---|---|---|---|
| `D030_50slice_montage_common.png/pdf` | `I_cross` × 50 层，10×5 | 共用 ±1.5477 | 与 100/200 nm 比**幅度** |
| `D030_50slice_montage_normalized.png/pdf` | 同上，除以本粒径 max|I| | ±1 归一化 | 看 30 nm 自身**结构**（推荐） |
| `D100_*`, `D200_*` 同规格 | — | — | — |
| `D030_50slice_atlas_common.pdf` | 50 层，每页 9 图 | 共用 | 汇报附录，逐层放大看 |
| `D030_50slice_atlas_normalized.pdf` | 50 层，每页 9 图 | 归一化 | 汇报附录，逐层放大看 |
| `D030_3d_stack_common.png/pdf` | 50 层真实坐标堆叠 | 共用 | 三粒径**幅度对比**（30 nm 几乎空白属正常） |
| `D030_3d_stack_normalized.png/pdf` | 50 层真实坐标堆叠 | 归一化 | 三维形貌（核心图） |
| `D030_orthoview.png/pdf` | x–z、y–z、x–y 三视图 | 本粒径 ±max|I| | 看清 zeta 方向**符号翻转**（最诚实的一张） |
| `D030_signal_decomposition.png/pdf` | zeta≈0 处 `I_cross/I_total/I_ref/I_scat` 四联图 | RdBu_r + viridis + magma | 说明「干涉项」和「总强度」不是一回事 |
| `compare_three_sizes_key_slices.png/pdf` | 9 个关键 zeta 层的三粒径横排 | 归一化 | 直观比较粒径效应 |
| `compare_three_sizes_key_slices_common.png/pdf` | 同上 | 共用 ±1.5477 | 直观比较**绝对幅度** |
| `compare_three_sizes_axis_curves.png/pdf` | x=y=0 处 171 层轴向曲线（线性 / 对数 / 归一化三面板 + D030 内嵌小图） | 线图 | 轴向响应、过零点、动态范围 |

### 关于 30 nm 的 common 图「几乎空白」

`max|I_cross|`：D030 = 0.03256，D100 = 1.548，
比值 **47.5×**。共用色标必须取三者最大值，所以 D030 的数值只落在色标中心极窄的一段，
图像接近白色。**这是被正确呈现的物理幅度差，不是色标 bug，也不会为了好看去改色标范围。**
看 30 nm 的结构请用 `*_normalized`，或用 `supplement/D030_50slice_montage_common_asinh.png`
（asinh 压缩，仅显示变换，不改数据）。

## 2. 补充图 `figures_main/supplement/`

| 文件 | 说明 |
|---|---|
| `D0x0_50slice_montage_common_asinh.png/pdf` | 对共用色标图做 asinh 压缩，让 D030/D200 的弱结构在**同一幅度尺度**下可见。**仅显示变换**，标注了 asinh 参数 |
| `D0x0_3d_stack_common_zexag3.png/pdf` | 同上堆叠图，z 轴**显示上**×3，标题与轴标签均写明 `x3 display` |
| `D0x0_3d_stack_normalized_zexag3.png/pdf` | 归一化 + z×3 |
| `D0x0_3d_stack_cutaway.png/pdf` | **半剖切**：把每层 x>0 的一半设为全透明，露出内部正负翻转。没有修改任何存储数值，只在显示时把一半面片的 alpha 置 0 |
| `D0x0_3d_volume_render.png/pdf` | 体切片渲染（透明度 ∝ |I_cross|，α 指数 1.2，比主图更"厚"） |
| `D0x0_isosurface.png/pdf` | ±25/50/75 % max|I| 六个等值面；不存在的层级在 `exported_data/D0x0_isosurface_levels.json` 中明确记为 `not present` |

**等值面存在性（本轮实测）**

| 粒径 | −75 % | −50 % | −25 % | +25 % | +50 % | +75 % |
|---|---|---|---|---|---|---|
| 30 nm | 不存在 | 不存在 | 不存在 | 存在 (25 372 面) | 存在 (15 820 面) | 存在 (8 028 面) |
| 100 nm | 不存在 | 不存在 | 不存在 | 存在 (33 264 面) | 存在 (20 724 面) | 存在 (9 836 面) |
| 200 nm | 不存在 | 不存在 | 存在 (1 996 面) | 存在 (13 420 面) | 存在 (6 868 面) | 存在 (2 772 面) |

负等值面大面积缺失，是因为 `I_cross` 的负向幅度远小于正向
（D100 min = -0.0337 vs max = 1.548）。
这本身就是一条物理信息：**干涉项不是对称的**，所以没有画对称的伪结构。

## 3. 交互页 `html_3d/`

| 文件 | 内容 | 体积 |
|---|---|---|
| `D030_50slice_stack.html` | 50 个真实 zeta 层面的 Plotly 曲面，α 由 |I_cross| 驱动 | ≈12.7 MB |
| `D100_50slice_stack.html` | 同上 | ≈12.8 MB |
| `D200_50slice_stack.html` | 同上 | ≈12.8 MB |
| `D030_isosurface.html` | marching-cubes 网格（真实存在的层级） | ≈5.2 MB |
| `D100_isosurface.html` | 同上 | ≈5.6 MB |
| `D200_isosurface.html` | 同上 | ≈4.4 MB |

Plotly 已**内嵌**，无 `<script src=...>`，断网可直接打开；鼠标拖拽旋转、滚轮缩放。
色标同样是 RdBu（负蓝正红），alpha 随 |值| 增大，近零区域透明。

## 4. 数据 `exported_data/`

| 文件 | 内容 |
|---|---|
| `selected_50_zeta_layers.csv` | 50 行的 `k, target_zeta_nm, layer_index, actual_zeta_nm, offset_nm` |
| `selected_50_zeta_layers.json` | 同上 + 选择规则 + 三粒径一致性声明 + 源文件路径 |
| `stats_D030.json` / `D100` / `D200` | 全网格（未裁剪）统计：max/min/mean/std、max abs、负值占比、p99、峰位置、中心轴向 171 点 |
| `common_scale.json` | 三粒径共用色标上限与规则 |
| `axis_curves_center.csv` | 3 × 171 行，x=y=0 处的 `I_cross/I_total/I_ref/I_scat` |
| `axis_curves_summary.json` | 三粒径轴向峰值/谷值位置 |
| `D0x0_isosurface_levels.json` | 六级等值面的存在性、面数、层级数值 |

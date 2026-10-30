# `figures_main/` — 主图

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

全部图件由 `code/step2_2d.py`、`code/step3_3d.py`、`code/step4_axis.py` 从三份只读 HDF5 生成，
**没有重算任何光场**。坐标：x, y 为物方横向坐标（显示窗口 ±400 nm），
3D 图的第三根轴是**离焦坐标 zeta（nm）**，不是样品深度。

主显示量：`I_cross = 2 Re(E_ref * conj(E_scat))`，**保留正负号**，发散色图 `RdBu_r`。

## 文件清单

| 文件 | 体积 | 内容 |
|---|---|---|
| `compare_three_sizes_axis_curves.pdf` | 24 KB | x=y=0 处 171 层轴向曲线（线性/对数/归一化） |
| `compare_three_sizes_axis_curves.png` | 321 KB | x=y=0 处 171 层轴向曲线（线性/对数/归一化） |
| `compare_three_sizes_key_slices.pdf` | 77 KB | 9 个关键层三粒径横排，归一化 |
| `compare_three_sizes_key_slices.png` | 589 KB | 9 个关键层三粒径横排，归一化 |
| `compare_three_sizes_key_slices_common.pdf` | 61 KB | 9 个关键层三粒径横排，共用色标 |
| `compare_three_sizes_key_slices_common.png` | 419 KB | 9 个关键层三粒径横排，共用色标 |
| `D030_3d_stack_common.pdf` | 21 KB | 50 层真实坐标三维堆叠，共用色标 |
| `D030_3d_stack_common.png` | 652 KB | 50 层真实坐标三维堆叠，共用色标 |
| `D030_3d_stack_normalized.pdf` | 108 KB | 50 层真实坐标三维堆叠，本粒径归一化（核心图） |
| `D030_3d_stack_normalized.png` | 1.11 MB | 50 层真实坐标三维堆叠，本粒径归一化（核心图） |
| `D030_50slice_atlas_common.pdf` | 90 KB | 50 层逐页图册（每页 9 图，共用色标） |
| `D030_50slice_atlas_normalized.pdf` | 214 KB | 50 层逐页图册（每页 9 图，归一化） |
| `D030_50slice_montage_common.pdf` | 59 KB | 50 层 10x5 总览，三粒径共用色标 |
| `D030_50slice_montage_common.png` | 349 KB | 50 层 10x5 总览，三粒径共用色标 |
| `D030_50slice_montage_normalized.pdf` | 122 KB | 50 层 10x5 总览，本粒径归一化 |
| `D030_50slice_montage_normalized.png` | 880 KB | 50 层 10x5 总览，本粒径归一化 |
| `D030_orthoview.pdf` | 26 KB | x-z / y-z / x-y 三视图正交切片 |
| `D030_orthoview.png` | 192 KB | x-z / y-z / x-y 三视图正交切片 |
| `D030_signal_decomposition.pdf` | 70 KB | zeta 附近 I_cross / I_total / I_ref / I_scat 四联分解 |
| `D030_signal_decomposition.png` | 603 KB | zeta 附近 I_cross / I_total / I_ref / I_scat 四联分解 |
| `D100_3d_stack_common.pdf` | 117 KB | - |
| `D100_3d_stack_common.png` | 1.20 MB | - |
| `D100_3d_stack_normalized.pdf` | 120 KB | - |
| `D100_3d_stack_normalized.png` | 1.20 MB | - |
| `D100_50slice_atlas_common.pdf` | 238 KB | - |
| `D100_50slice_atlas_normalized.pdf` | 238 KB | - |
| `D100_50slice_montage_common.pdf` | 137 KB | - |
| `D100_50slice_montage_common.png` | 919 KB | - |
| `D100_50slice_montage_normalized.pdf` | 137 KB | - |
| `D100_50slice_montage_normalized.png` | 915 KB | - |
| `D100_orthoview.pdf` | 25 KB | - |
| `D100_orthoview.png` | 187 KB | - |
| `D100_signal_decomposition.pdf` | 71 KB | - |
| `D100_signal_decomposition.png` | 609 KB | - |
| `D200_3d_stack_common.pdf` | 75 KB | - |
| `D200_3d_stack_common.png` | 950 KB | - |
| `D200_3d_stack_normalized.pdf` | 92 KB | - |
| `D200_3d_stack_normalized.png` | 1.02 MB | - |
| `D200_50slice_atlas_common.pdf` | 173 KB | - |
| `D200_50slice_atlas_normalized.pdf` | 201 KB | - |
| `D200_50slice_montage_common.pdf` | 102 KB | - |
| `D200_50slice_montage_common.png` | 745 KB | - |
| `D200_50slice_montage_normalized.pdf` | 116 KB | - |
| `D200_50slice_montage_normalized.png` | 898 KB | - |
| `D200_orthoview.pdf` | 24 KB | - |
| `D200_orthoview.png` | 179 KB | - |
| `D200_signal_decomposition.pdf` | 81 KB | - |
| `D200_signal_decomposition.png` | 765 KB | - |
| `README.md` | 6 KB | - |

补充图在 `supplement/`（37 个文件），见该目录 README。

## 命名规则

- `D030 / D100 / D200`：粒径 30 / 100 / 200 nm（球心高度 15 / 50 / 100 nm）。
- `common`：三粒径**共用**对称色标 ±1.5477（= 三者 max|I_cross| 的最大值），用于比较**幅度**。
- `normalized`：按本粒径 `I_cross / max|I_cross|` 归一化到 ±1，用于看**结构**。
- `_zexag3`：z 轴**显示**放大 3 倍（标题与轴标签均标注 `x3`），数据未变。
- `_asinh`：对共用色标图做 asinh 压缩，仅显示变换。
- `cutaway`：半剖切（每层 x>0 半边 alpha 置 0），仅显示处理。

## 建议阅读顺序

1. `D100_50slice_montage_normalized.png` — 先看"标准"粒径的结构随离焦如何演化；
2. `D030_*_normalized` 与 `D200_*_normalized` — 看粒径效应；
3. `compare_three_sizes_key_slices_common.png` — 看清**幅度**差异（D030 近白属正常）；
4. `D0x0_3d_stack_normalized.png` — 三维堆叠（核心图）；
5. `D0x0_orthoview.png` — 最"诚实"的一张：x-z 面上直接看到符号变化；
6. `D0x0_signal_decomposition.png` — 区分干涉项 `I_cross` 与强度量 `I_total`。

## 已知"看起来空"的图

`D030_50slice_montage_common.*`、`D030_3d_stack_common.*`、`compare_three_sizes_key_slices_common.*`
里 30 nm 的近白是**正确的物理幅度差**（max|I_cross| 比 D100 小 47.5 倍），
不是色标 bug。看 30 nm 结构请用 `*_normalized` 或 `supplement/D030_50slice_montage_common_asinh.*`。

## 复现

```powershell
cd code
python step1_layers.py      # 50 层选择 + 统计
python step2_2d.py          # 2D 总览/图册/分解/关键层对比
python step3_3d.py all      # 3D 堆叠/正交/等值面/体渲染
python step4_axis.py        # 轴向曲线
python step5_html.py        # 交互页
```

脚本顶部 `vis_common.py` 中的 `DATA` 指向三份 HDF5 的绝对路径；
换机器时只需改这一处，不需要重算数据。

# `figures_main/supplement/` — 补充图

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

这些图都**只是显示增强**，存储的数据一个字节都没改。任何一张都不能单独作为定量证据。

| 文件 | 体积 | 内容 |
|---|---|---|
| `D030_3d_stack_common_zexag3.pdf` | 21 KB | 50 层真实坐标三维堆叠，共用色标 |
| `D030_3d_stack_common_zexag3.png` | 570 KB | 50 层真实坐标三维堆叠，共用色标 |
| `D030_3d_stack_cutaway.pdf` | 90 KB | 半剖切（x>0 半边透明），露出内部正负结构 |
| `D030_3d_stack_cutaway.png` | 972 KB | 半剖切（x>0 半边透明），露出内部正负结构 |
| `D030_3d_stack_normalized_zexag3.pdf` | 143 KB | 50 层真实坐标三维堆叠，本粒径归一化（核心图） |
| `D030_3d_stack_normalized_zexag3.png` | 1.21 MB | 50 层真实坐标三维堆叠，本粒径归一化（核心图） |
| `D030_3d_volume_render.pdf` | 126 KB | 体切片渲染（alpha 更厚） |
| `D030_3d_volume_render.png` | 1.14 MB | 体切片渲染（alpha 更厚） |
| `D030_50slice_montage_common_asinh.pdf` | 92 KB | 50 层 10x5 总览，三粒径共用色标 |
| `D030_50slice_montage_common_asinh.png` | 650 KB | 50 层 10x5 总览，三粒径共用色标 |
| `D030_isosurface.pdf` | 658 KB | +-25/50/75 % max|I| 等值面（只画真实存在的层级） |
| `D030_isosurface.png` | 503 KB | +-25/50/75 % max|I| 等值面（只画真实存在的层级） |
| `D100_3d_stack_common_zexag3.pdf` | 158 KB | - |
| `D100_3d_stack_common_zexag3.png` | 1.34 MB | - |
| `D100_3d_stack_cutaway.pdf` | 98 KB | - |
| `D100_3d_stack_cutaway.png` | 1.01 MB | - |
| `D100_3d_stack_normalized_zexag3.pdf` | 161 KB | - |
| `D100_3d_stack_normalized_zexag3.png` | 1.34 MB | - |
| `D100_3d_volume_render.pdf` | 126 KB | - |
| `D100_3d_volume_render.png` | 1.16 MB | - |
| `D100_50slice_montage_common_asinh.pdf` | 255 KB | - |
| `D100_50slice_montage_common_asinh.png` | 2.62 MB | - |
| `D100_isosurface.pdf` | 876 KB | - |
| `D100_isosurface.png` | 554 KB | - |
| `D200_3d_stack_common_zexag3.pdf` | 87 KB | - |
| `D200_3d_stack_common_zexag3.png` | 902 KB | - |
| `D200_3d_stack_cutaway.pdf` | 73 KB | - |
| `D200_3d_stack_cutaway.png` | 889 KB | - |
| `D200_3d_stack_normalized_zexag3.pdf` | 112 KB | - |
| `D200_3d_stack_normalized_zexag3.png` | 1.01 MB | - |
| `D200_3d_volume_render.pdf` | 140 KB | - |
| `D200_3d_volume_render.png` | 1.26 MB | - |
| `D200_50slice_montage_common_asinh.pdf` | 227 KB | - |
| `D200_50slice_montage_common_asinh.png` | 2.62 MB | - |
| `D200_isosurface.pdf` | 327 KB | - |
| `D200_isosurface.png` | 419 KB | - |
| `README.md` | 5 KB | - |

## 每个显示处理的边界

| 文件名片段 | 做了什么 | 不能读出什么 |
|---|---|---|
| `_zexag3` | 三维图 z 轴显示范围放大 3 倍（标题写明 `x3`） | 真实长宽比；zeta 层间距仍是 2 nm |
| `_cutaway` | 每层 x>0 半边 alpha=0，露出内部 | 剖切面不是物理截面，也不代表"内部场" |
| `_volume_render` | 50 层按 alpha ∝ \|I\|^1.2 叠加的体切片渲染 | 不是光学体渲染积分，不是吸收/散射密度 |
| `_asinh` | asinh 压缩共用色标 | 颜色不再线性对应数值 |
| `_isosurface` | marching cubes 的 ±25/50/75 % max\|I\| 等值面 | 不是等浓度面、不是颗粒表面、不是近场等值面 |

## 等值面存在性（本轮实测，未伪造对称结构）

| 粒径 | −75 % | −50 % | −25 % | +25 % | +50 % | +75 % |
|---|---|---|---|---|---|---|
| 30 nm | **不存在** | **不存在** | **不存在** | 存在 (25,372 面) | 存在 (15,820 面) | 存在 (8,028 面) |
| 100 nm | **不存在** | **不存在** | **不存在** | 存在 (33,264 面) | 存在 (20,724 面) | 存在 (9,836 面) |
| 200 nm | **不存在** | **不存在** | 存在 (1,996 面) | 存在 (13,420 面) | 存在 (6,868 面) | 存在 (2,772 面) |

负等值面大面积缺失是真实数值性质：`I_cross` 的负向幅度远小于正向
（例如 D100 min = -0.0337 vs max = 1.548）。
所以没有画对称的伪结构。逐层数值见 `exported_data/D0x0_isosurface_levels.json`。

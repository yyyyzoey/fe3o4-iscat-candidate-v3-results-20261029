# `exported_data/` — 图件依赖的全部数值

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

本目录是图件的"底稿"：图里出现的每个数都能在这里找到，或由这里的数据算出。
所有数值直接来自三份只读 HDF5，未做平滑、未做插值放大。

## 文件说明

| 文件 | 内容 | 关键字段 |
|---|---|---|
| `selected_50_zeta_layers.csv` | 50 层选择结果（每行一层） | `k, target_zeta_nm, index, actual_zeta_nm, offset_nm` |
| `selected_50_zeta_layers.json` | 同上 + 选择规则 + 三粒径一致性 + 源文件路径 | `selection_rule, identical_across_diameters, per_diameter.<TAG>.layers` |
| `stats_D030/100/200.json` | 全网格（未裁剪）统计 | `shape, cube_max_abs_I_cross, cube_min_I_cross, cube_max_I_cross, cube_std_I_cross, fraction_negative, p99_abs, argmax_*, axis_*` |
| `common_scale.json` | 三粒径共用色标 | `common_vmax, per_diameter_vmax, rule` |
| `axis_curves_center.csv` | x=y=0 的 171 层轴向曲线，3×171 行 | `tag, diameter_nm, centre_height_nm, zeta_nm, I_cross, I_total, I_ref, I_scat` |
| `axis_curves_summary.json` | 轴向峰值/谷值摘要 | `series.<TAG>.zeta_of_max / zeta_of_min / I_cross_at_zeta_0` |
| `D030/100/200_isosurface_levels.json` | 六级等值面的存在性与面数 | `levels[].level_fraction, level, present, note, n_faces` |

## 约定

- **量**：主显示量 `I_cross = 2 Re(E_ref * conj(E_scat))`，**有符号**；
  `I_total`、`I_ref`、`I_scat` 是强度量（非负）。
- **单位**：无量纲，相对同一 on-axis 参考场；`absolute_calibration = false`。
- **坐标**：`zeta` 为离焦坐标（nm），**不是**样品深度；`x, y` 为物方横向坐标（nm）。
- **数组顺序**：`(zeta, y, x)`，shape = (171, 241, 241)。
- **共用色标**：`common_vmax = 1.547655`（= 三者 max|I_cross| 的最大值，来自 D100）。
- **归一化**：`I_cross / max|I_cross|`（同一体数据内）。

## 复算示例

```python
import h5py, numpy as np
p = r"...\D100nm\cube.h5"
with h5py.File(p, "r") as f:
    j = f["signals/I_cross"][:]            # (171, 241, 241) float32
    z = f["coords/zeta_nm"][:]
    x = f["coords/x_object_nm"][:]
print(np.abs(j).max())                     # = stats_D100.json -> cube_max_abs_I_cross
i = np.argmin(np.abs(x))
print(z[np.argmax(j[:, i, i])])            # = axis_curves_summary.json -> zeta_of_max
```

## 注意

- `stats_*.json` 里的 `axis_I_cross_at_center` 是**未裁剪**的 171 点中心轴曲线；
  图件上的曲线来自 `axis_curves_center.csv`，两者数值一致（见 `ACCEPTANCE.md` A6）。
- `fraction_negative` 是全体素占比；**轴上**曲线是否过零是另一回事，
  例如 D100 轴上全程为正而体数据仍有约 46 % 的负值体素。

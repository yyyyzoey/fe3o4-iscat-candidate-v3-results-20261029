# `code/` — 本轮全部出图脚本

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

## 环境（实际执行）

- Python 3.11.7（Anaconda）
- numpy 1.26.4 / h5py 3.9.0 / matplotlib 3.8.0 / scipy 1.11.4
- pandas 2.1.4 / scikit-image 0.22.0 / plotly 5.9.0
- 未使用：pyvista、vtk、kaleido

## 文件（SHA256 前 16 位，完整值见 `../config/visual_config.json`）

| 文件 | 作用 | SHA256 |
|---|---|---|
| `vis_common.py` | 共享路径、样式、HDF5 只读加载、50 层选择、StepLog | `d7efba80de8ffc03` |
| `step1_layers.py` | 50 层选择 + 全网格统计 + 共用色标 | `4ca09030c54a208b` |
| `step2_2d.py` | 50 层 10x5 总览、逐页图册、信号分解、三粒径关键层对比 | `893c664a7490282e` |
| `step3_3d.py` | 50 层三维堆叠（真实/z×3）、半剖切、体渲染、正交切片、等值面 | `1a52b976b2785624` |
| `step4_axis.py` | 中心轴向 171 层曲线与 CSV | `d9a6298a0109c1c9` |
| `step5_html.py` | 6 个自包含 Plotly 交互页 | `1b5e30629beb1290` |
| `mk_report1.py` | 生成根 README 与 00 一页纸摘要 | `fd4e915b91d50d14` |
| `mk_report2.py` | 生成 01 图件导读 | `89a718fd3df77559` |
| `mk_report3.py` | 生成 02 执行日志 | `e81a659bdbc5a9a9` |
| `mk_report4.py` | 生成 03 边界报告、各子目录 README、config、验收、SHA256 | `d4b725b4d49f3732` |
| `mk_package.py` | 打包 REPORT / FULL 两个 ZIP 与包外校验 JSON | `1da733b3364dfb7f` |

## 运行顺序

```powershell
cd code
python step1_layers.py
python step2_2d.py
python step3_3d.py all
python step4_axis.py
python step5_html.py
python mk_report1.py
python mk_report2.py
python mk_report3.py
python mk_report4.py
python mk_package.py
```

## 约定

- **只读**：所有脚本用 `h5py.File(..., "r")` 打开主数据，没有任何写回路径；
  求解器代码不在本包内，也没有被 import。
- **不裁剪数据**：显示只做切片视图（±400 nm），主网格与统计仍用 ±1200 nm 全量。
- **不取绝对值**：`I_cross` 全程保留符号；`abs()` 只用于色标上限与透明度计算。
- 换机器时改 `vis_common.py` 顶部的 `ROOT/DATA/OUT` 三个路径即可。

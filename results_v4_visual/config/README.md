# `config/` — 固定参数与数据溯源

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

`visual_config.json` 是本轮唯一的配置文件（只读出图的"配方"），字段：

| 字段 | 内容 |
|---|---|
| `schema` / `generated_utc` | 配置版本与生成时间（UTC） |
| `purpose` / `physics_unchanged` / `physics_rerun` | 本轮性质：只读重绘，`physics_rerun = false` |
| `baseline` | 仓库、分支、`rev-parse HEAD`、提交时间、祖先提交、工作树是否干净 |
| `environment` | Python 与 numpy/h5py/matplotlib/scipy/pandas/skimage/plotly 版本 |
| `source_data[]` | 三份 HDF5：绝对路径、相对路径、字节数、mtime、**SHA256**、shape、dtype、坐标范围与步长、HDF5 属性子集 |
| `physical_parameters` | 532 nm、NA 1.45、n_sample/n_glass/n_immersion、三粒径与球心高度、网格、数组顺序、**排除的旧课题条件** |
| `display` | 主显示量、符号约定、色图、共用色标、归一化规则、显示窗口 |
| `layer_selection` | 50 层选择方法、最大吸附误差、目标/实际 zeta、索引 |
| `code.files[]` | 每个脚本的字节数与 SHA256 |
| `boundary` | 8 项边界声明（与所有 README 一致） |

## 怎么用它复现

1. 按 `source_data[].sha256` 校验三份 HDF5 是否与本次一致（不一致就不要直接比较图件）；
2. 按 `code.files[].sha256` 校验脚本未被改动；
3. 用 `physical_parameters` 与 `display` 重建同样的色标与窗口；
4. 用 `layer_selection` 复核 50 层是否一致。

## 注意

- `source_data[].mtime_utc` 早于本轮出图开始时间，可作为"未重写主数据"的旁证
  （主证据是 SHA256 与 `ACCEPTANCE.md` A3 项）。
- 配置里**不含**任何凭据、令牌或绝对输出路径之外的个人信息。

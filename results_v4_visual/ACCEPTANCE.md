# 验收表 — 实际执行的检查

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

**总判定：PASS**（14 项检查，失败 0 项）
生成时间（UTC）：2026-10-30T09:54:15Z

本表由 `code/mk_report4.py` 在打包前实际运行生成，不是手写的。
逐项原始记录见 `logs/step6_accept.jsonl`，机器可读版本见本目录的 `acceptance.json`。

## 1. 检查项

| ID | 检查 | 结果 | 实测 |
|---|---|---|---|
| A1 | Git 基线与工作树 | **PASS** | HEAD=0a58aff466d0 branch=v4-audit-final-candidate clean=True |
| A2 | 三份 HDF5 存在且 shape/坐标正确 | **PASS** | shape=171x241x241; zeta -170:2:170; x,y -1200:10:1200 全部一致 |
| A3 | 主数据未被本轮改写（SHA256 复算一致） | **PASS** | D030 ecbbea68c663246f; D100 ffca89836461eae7; D200 c94e7be2d5550fbe |
| A3b | SHA256 与 V4.1 交付清单逐文件一致 | **PASS** | D030=match; D100=match; D200=match |
| A4 | 主数据 mtime 早于本轮出图开始 | **PASS** | first log 2026-10-30T09:28:21Z |
| A5 | 50 层互不相同、覆盖全量程 | **PASS** | n=50 unique=50 zeta -170..+170 max_offset=0.98 nm |
| A6 | stats/轴向曲线与 HDF5 复读数值一致 | **PASS** | max rel err (cube stats) = 0.00e+00; max rel err (axis curve) = 0.00e+00 |
| A7 | 任务书要求的图件全部存在且非空 | **PASS** | required=84 missing=0 undersized=0 |
| A8 | PNG 可解码且不是空白页 | **PASS** | 39 个 PNG；尺寸/非白像素检查通过；无低方差文件 |
| A9 | PDF 结构有效、图册页数=6 | **PASS** | 45 个 PDF；atlas pages={'D030': 6, 'D100': 6, 'D200': 6} |
| A10 | HTML 自包含且每份含 50 个真实 zeta 面 | **PASS** | D030_50slice_stack.html:50; D030_isosurface.html:isosurface; D100_50slice_stack.html:50; D100_isosurface.html:isosurface; D200_50slice_stack.html:50; D200_isosurface.html:isosurface |
| A11 | 产物计数 | **PASS** | PNG=39 PDF=45 HTML=6 total=92.3 MB |
| A12 | 每份 README/报告都含 8 项边界声明 | **PASS** | checked 10 docs; missing=none |
| A13 | 可视化结果树内不含主数据（FULL 包单独放置） | **PASS** | .h5 files inside OUT = 0 |

## 2. 产物计数

- PNG **39** 个、PDF **45** 个、HTML **6** 个，
  可视化结果树合计 **92.3 MB**（不含主数据）。

## 3. 明确未验证（不写成通过）

| 项目 | 状态 |
|---|---|
| `full_jones_chain` | UNVERIFIED |
| `high_na_model_validation` | UNVERIFIED |
| `paper_convention_checks` | UNVERIFIED |
| `publisher_typeset_pdf` | NOT_OBTAINED |
| HTML 浏览器像素级渲染 | 未做（只做结构检查，见 A10） |
| 与论文原图逐像素比对 | 未做 |
| 与实验数据比对 | 未做（`absolute_calibration = false`） |

## 4. 复现

```powershell
cd code
python mk_report4.py      # 重新生成配置 + 本验收表 + SHA256SUMS.txt
python mk_package.py      # 重新打包两个 ZIP 与包外校验 JSON
```

`mk_report4.py` 会重新计算三份 HDF5 的 SHA256 并与 `config/visual_config.json` 比对，
若主数据被改动，A3 会直接 FAIL。

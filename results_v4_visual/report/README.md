# `report/` — 四份中文报告

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

| 文件 | 读什么 | 多长 |
|---|---|---|
| `00_one_page_summary_zh.md` | 一页纸结论：做了什么、关键数值、验收状态 | 1 页 |
| `01_figure_guide_zh.md` | 图件导读：每个文件画的是什么量、色标、用途 | 2 页 |
| `02_generation_log.md` | 真实执行日志：环境、耗时、被否决的第一次三维渲染、空跑记录 | 2 页 |
| `03_limitations_zh.md` | 边界与未核实项：哪些话不能说、升级为"已认证"还需要什么 | 3 页 |

建议阅读顺序：`00` → `01` → `03`，需要复现时再读 `02` 与 `../code/`、`../logs/`。

## 报告之间的一致性

- 四份报告与 `../README.md` 顶部都有同一段边界声明（8 个字段）；
- 报告里出现的数值都来自 `../exported_data/` 的 JSON/CSV，可在 `../ACCEPTANCE.md` 的
  交叉核对项（A5/A6）中复算；
- 任何"未核实"的项目在 `03` 里都有对应的"升级需要什么"。

## 修订记录

- 2026-10-30：`00` 中"三条轴向曲线都过零"的说法**已改正**——实测 D100 轴上全程为正
  （最小 0.6477 @ zeta = +170 nm），
  只有 D030 与 D200 在轴上过零。错误结论不会留在交付物里。

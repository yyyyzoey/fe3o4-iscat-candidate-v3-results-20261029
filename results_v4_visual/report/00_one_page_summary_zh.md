# 一页纸摘要 — Fe₃O₄ iSCAT V4.1 50 层可视化增强

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

## 1. 做了什么

在固定基线 `0a58aff466d053bbd3f82fe9fc77fb57511edd2c`（分支 `v4-audit-final-candidate`）上，
**只读**三份已验收的 through-focus HDF5（171×241×241，`(zeta, y, x)` 顺序），
从 171 个 zeta 层中选出 **恰好 50 个互不相同的真实层**，重新生成：

- 每粒径 50 层二维总览（10×5，common / normalized 两套）+ 逐页 PDF 图册；
- 每粒径 50 层三维堆叠（真实比例 + z×3 夸张版 + 半剖切 + 体渲染）；
- 每粒径三维正交切片（x–z / y–z / x–y）与 ±25/50/75 % 等值面；
- 三粒径关键层横向对比（9 层）与三粒径中心轴向曲线（171 层全量）；
- 6 个自包含 HTML 交互页；
- 完整执行日志、SHA256 清单与两个 ZIP 包。

**没有**重跑光学求解器，**没有**改动波长 532 nm、目标 NA 1.45、球心高度 15/50/100 nm、
zeta = −170:2:170 nm、x,y = −1200:10:1200 nm 中的任何一项。

## 2. 关键定量结果（来自 `exported_data/stats_*.json`）

| 量 | 30 nm | 100 nm | 200 nm |
|---|---|---|---|
| max `I_cross` | 0.0325565 | 1.54766 | 1.04483 |
| min `I_cross` | -0.00711127 | -0.0337006 | -0.32369 |
| 体数据 max abs | 0.0325565 | 1.54766 | 1.04483 |
| 标准差 | 0.001383 | 0.07511 | 0.02958 |
| 负值体素占比 | 25.8 % | 46.3 % | 57.8 % |
| 全局最大值位置 (zeta, x, y) | (+92, 0, 0) | (-68, 0, 0) | (-170, 0, 0) |

三粒径共用色标上限：**±1.547655**（= 三者 max|I_cross| 的最大值，来自 D100）。

## 3. 三个可以写进汇报的观察（都属于候选模型下的数值事实）

1. **幅度强烈非单调**：100 nm 的峰值（1.548）比 200 nm
   （1.045）更大，30 nm（0.03256）比 100 nm
   小约 47.5 倍。因此三粒径共用色标下 30 nm 图接近空白——这是真实幅度差，不是绘图失误。
2. **正负号必须保留**：轴上 `I_cross` 的过零情况是三组**不相同**的——D030 在 zeta ≈ -137 nm 过零变负，
   D200 在 zeta ≈ +31 nm 过零变负，而 D100 无过零点（轴上曲线全程为正，
   最小值 0.6477，位于 zeta = +170 nm）。
   但整个体数据里负值体素占比 30/100/200 nm 仍分别为 25.8 / 46.3 /
   57.8 %，说明 D100 的相消主要发生在**离轴**区域。
   因此 `I_cross` 不能取绝对值后再谈「干涉强度」，「三条曲线都过零」这种说法是错的。
3. **轴向峰值位置随粒径移动**：D030 在 zeta ≈ +92 nm，D100 在
   -68 nm，D200 在 -170 nm（均为 x = y = 0 处）。

## 4. 验收状态

| 检查项 | 状态 | 证据 |
|---|---|---|
| 50 层互不相同、覆盖 −170…+170 | **通过** | `selected_50_zeta_layers.csv`，最大吸附误差 0.98 nm |
| 三粒径都有 50 层二维总览 | **通过** | `figures_main/D0x0_50slice_montage_*.png/pdf` |
| 三粒径都有 50 层三维堆叠 | **通过** | `figures_main/D0x0_3d_stack_*.png/pdf` |
| 三粒径关键层对比 + 轴向曲线 | **通过** | `compare_three_sizes_key_slices*.png`、`compare_three_sizes_axis_curves.png` |
| HTML 交互（自包含） | **通过（结构）** | 每份 50 个 surface trace、无外链脚本；沙箱内未做浏览器像素级复验 |
| 物理模型未被改动 | **通过** | 脚本只读 HDF5；`config/visual_config.json` 记录源文件 SHA256 |
| 物理认证 | **未完成，且本轮不主张** | 见 `03_limitations_zh.md` |

## 5. 一句话结论

这 50 层图件把已有候选结果呈现得更清楚、更可读、可复现，
但**没有**把候选模型变成已认证模型；`full_jones_chain`、`high_na_model_validation`、
`paper_convention_checks` 仍是 UNVERIFIED，`absolute_calibration = false`。

# Fe₃O₄ iSCAT V4.1 — 50 层可视化增强结果包（CANDIDATE）

**基线**：`yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029` @ `v4-audit-final-candidate`
**提交**：`0a58aff466d053bbd3f82fe9fc77fb57511edd2c`
**本轮性质**：只读重绘。三份主 HDF5 未修改、未重算光场。

## 结果边界（每一份子报告都重复这一块）

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

## 这个包是什么

把已保存的 through-focus 三维修正量 `I_cross = 2 Re(E_ref·conj(E_scat))` 从 171 个 zeta 层中
选出 **50 个真实层**，重新出成论文/汇报级的二维与三维图，并附带可离线打开的交互页面。
**没有**重新求解散射问题，**没有**改动物理模型、波长、NA、球心高度或网格。

## 目录

| 路径 | 内容 |
|---|---|
| `figures_main/` | 主图：3 粒径 × (50 层总览 common/normalized + 3D 堆叠 common/normalized + 正交切片 + 信号分解) + 两张三粒径对比图 |
| `figures_main/supplement/` | 补充图：z 轴 ×3 夸张、半剖切、体渲染、等值面、asinh 高动态范围总览 |
| `html_3d/` | 6 个自包含 HTML（每粒径 50 层交互堆叠 + 等值面），无需联网 |
| `exported_data/` | 50 层选择清单、三粒径统计量、共用色标、中心轴向 171 层曲线 CSV、等值面记录 |
| `report/` | 四份中文报告（一页纸摘要 / 图件导读 / 生成日志 / 边界与未核实项） |
| `logs/` | 逐步执行日志 JSONL（含被否决的中间尝试） |
| `code/` | 本轮全部出图脚本（可直接重跑） |
| `config/` | 固定参数与数据溯源 |
| `data/` | 仅 FULL 包含：三份主 HDF5 的只读副本 |

## 五条必须记住的读图规则

1. **zeta 是离焦坐标，不是样品深度。** 三维图里的 z 轴是 through-focus 的扫描坐标，
   不是把颗粒周围近场画成了一个三维体。
2. **`I_cross` 保留正负号**，负值是物理上有意义的相消，不是伪影，也不取绝对值。
3. **两套色标不可混用**：`*_common` 用三粒径统一 ±1.5477；`*_normalized` 用各自
   `max|I_cross|` 归一化。D030 的共用色标图**本来就几乎全白**（它比 D100 小 47.5 倍），
   看 D030 的结构请看 normalized 版。
4. **三维堆叠的透明度按 |I_cross| 加权**，接近零的背景全透明，因此 50 层叠加不会糊成白板；
   层位置另有每 5 层一个的浅灰边框和 50 个刻度标记，便于数层。
5. **等值面/体渲染是显示对象**，不是等浓度面、不是颗粒表面、不是真实近场等值面。

## 快速查看

- 交互：用浏览器直接打开 `html_3d/D100_50slice_stack.html`（Plotly 已内嵌，离线可用）。
- 一页纸结论：`report/00_one_page_summary_zh.md`
- 图件导读：`report/01_figure_guide_zh.md`
- 未核实项：`report/03_limitations_zh.md`

## 文件规模

- PNG 39 个、PDF 45 个、HTML 6 个；
- SHA256 清单见 `SHA256SUMS.txt`（逐文件）与包外 `package_verification.json`。

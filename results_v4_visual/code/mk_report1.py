# -*- coding: utf-8 -*-
"""Generate the Chinese report set, READMEs and config for the V4.1 visual bundle."""
import json
import shutil
from pathlib import Path

import vis_common as C

OUT = C.OUT
FIG = C.FIG
REP = C.REPORT
REP.mkdir(parents=True, exist_ok=True)
CFG = OUT / "config"
CFG.mkdir(exist_ok=True)
(C.CODE).mkdir(exist_ok=True)

BOUND = """```
result_class                     = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
through_focus                    = true   (NOT sample-space near field)
full_jones_chain                 = UNVERIFIED
high_na_model_validation         = UNVERIFIED
paper_convention_checks          = UNVERIFIED
absolute_calibration             = false
sample_space_near_field          = false
publisher_typeset_pdf            = NOT_OBTAINED
linear_midpoint_reconstruction   = FAILED_KEPT
```"""

S = {t: json.loads((C.EXPORT / f"stats_{t}.json").read_text(encoding="utf-8"))
     for t in ("D030", "D100", "D200")}
CS = json.loads((C.EXPORT / "common_scale.json").read_text(encoding="utf-8"))
AX = json.loads((C.EXPORT / "axis_curves_summary.json").read_text(encoding="utf-8"))["series"]
ISO = {t: json.loads((C.EXPORT / f"{t}_isosurface_levels.json").read_text(encoding="utf-8"))
       for t in ("D030", "D100", "D200")}
VMAX = CS["common_vmax"]
RATIO = VMAX / S["D030"]["cube_max_abs_I_cross"]

import csv as _csv
with (C.EXPORT / "selected_50_zeta_layers.csv").open(encoding="utf-8") as _fh:
    MAXOFF = max(abs(float(r["offset_nm"])) for r in _csv.DictReader(_fh))

def _zc(tag):
    z, v = [], []
    with (C.EXPORT / "axis_curves_center.csv").open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            if row["tag"] == tag:
                z.append(float(row["zeta_nm"]))
                v.append(float(row["I_cross"]))
    for i in range(1, len(z)):
        if v[i - 1] == 0 or v[i] == 0:
            continue
        if (v[i - 1] > 0) != (v[i] > 0):
            return f"{0.5 * (z[i - 1] + z[i]):+.0f} nm"
    return "无过零点"


ZC = {t: _zc(t) for t in ("D030", "D100", "D200")}

n_png = len(list(OUT.rglob("*.png")))
n_pdf = len(list(OUT.rglob("*.pdf")))
n_html = len(list(OUT.rglob("*.html")))

# ---------------------------------------------------------------- root README
readme = f"""# Fe₃O₄ iSCAT V4.1 — 50 层可视化增强结果包（CANDIDATE）

**基线**：`yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029` @ `v4-audit-final-candidate`
**提交**：`0a58aff466d053bbd3f82fe9fc77fb57511edd2c`
**本轮性质**：只读重绘。三份主 HDF5 未修改、未重算光场。

## 结果边界（每一份子报告都重复这一块）

{BOUND}

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
3. **两套色标不可混用**：`*_common` 用三粒径统一 ±{VMAX:.4f}；`*_normalized` 用各自
   `max|I_cross|` 归一化。D030 的共用色标图**本来就几乎全白**（它比 D100 小 {RATIO:.1f} 倍），
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

- PNG {n_png} 个、PDF {n_pdf} 个、HTML {n_html} 个；
- SHA256 清单见 `SHA256SUMS.txt`（逐文件）与包外 `package_verification.json`。
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

# ---------------------------------------------------------------- 00 one page
one = f"""# 一页纸摘要 — Fe₃O₄ iSCAT V4.1 50 层可视化增强

{BOUND}

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
| max `I_cross` | {S['D030']['cube_max_I_cross']:.6g} | {S['D100']['cube_max_I_cross']:.6g} | {S['D200']['cube_max_I_cross']:.6g} |
| min `I_cross` | {S['D030']['cube_min_I_cross']:.6g} | {S['D100']['cube_min_I_cross']:.6g} | {S['D200']['cube_min_I_cross']:.6g} |
| 体数据 max abs | {S['D030']['cube_max_abs_I_cross']:.6g} | {S['D100']['cube_max_abs_I_cross']:.6g} | {S['D200']['cube_max_abs_I_cross']:.6g} |
| 标准差 | {S['D030']['cube_std_I_cross']:.4g} | {S['D100']['cube_std_I_cross']:.4g} | {S['D200']['cube_std_I_cross']:.4g} |
| 负值体素占比 | {S['D030']['fraction_negative']*100:.1f} % | {S['D100']['fraction_negative']*100:.1f} % | {S['D200']['fraction_negative']*100:.1f} % |
| 全局最大值位置 (zeta, x, y) | ({S['D030']['argmax_zeta_nm']:+.0f}, {S['D030']['argmax_x_nm']:.0f}, {S['D030']['argmax_y_nm']:.0f}) | ({S['D100']['argmax_zeta_nm']:+.0f}, {S['D100']['argmax_x_nm']:.0f}, {S['D100']['argmax_y_nm']:.0f}) | ({S['D200']['argmax_zeta_nm']:+.0f}, {S['D200']['argmax_x_nm']:.0f}, {S['D200']['argmax_y_nm']:.0f}) |

三粒径共用色标上限：**±{VMAX:.6f}**（= 三者 max|I_cross| 的最大值，来自 D100）。

## 3. 三个可以写进汇报的观察（都属于候选模型下的数值事实）

1. **幅度强烈非单调**：100 nm 的峰值（{S['D100']['cube_max_abs_I_cross']:.4g}）比 200 nm
   （{S['D200']['cube_max_abs_I_cross']:.4g}）更大，30 nm（{S['D030']['cube_max_abs_I_cross']:.4g}）比 100 nm
   小约 {RATIO:.1f} 倍。因此三粒径共用色标下 30 nm 图接近空白——这是真实幅度差，不是绘图失误。
2. **正负号必须保留**：轴上 `I_cross` 的过零情况是三组**不相同**的——D030 在 zeta ≈ {ZC['D030']} 过零变负，
   D200 在 zeta ≈ {ZC['D200']} 过零变负，而 D100 无过零点（轴上曲线全程为正，
   最小值 {S['D100']['axis_valley_I_cross']:.4g}，位于 zeta = {S['D100']['axis_valley_zeta_nm']:+.0f} nm）。
   但整个体数据里负值体素占比 30/100/200 nm 仍分别为 {S['D030']['fraction_negative']*100:.1f} / {S['D100']['fraction_negative']*100:.1f} /
   {S['D200']['fraction_negative']*100:.1f} %，说明 D100 的相消主要发生在**离轴**区域。
   因此 `I_cross` 不能取绝对值后再谈「干涉强度」，「三条曲线都过零」这种说法是错的。
3. **轴向峰值位置随粒径移动**：D030 在 zeta ≈ {AX['D030']['zeta_of_max']:+.0f} nm，D100 在
   {AX['D100']['zeta_of_max']:+.0f} nm，D200 在 {AX['D200']['zeta_of_max']:+.0f} nm（均为 x = y = 0 处）。

## 4. 验收状态

| 检查项 | 状态 | 证据 |
|---|---|---|
| 50 层互不相同、覆盖 −170…+170 | **通过** | `selected_50_zeta_layers.csv`，最大吸附误差 {MAXOFF:.2f} nm |
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
"""
(REP / "00_one_page_summary_zh.md").write_text(one, encoding="utf-8")
print("wrote README + 00")

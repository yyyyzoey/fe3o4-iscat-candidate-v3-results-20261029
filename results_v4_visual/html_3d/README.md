# `html_3d/` — 交互式三维页面

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

## 怎么打开

双击任意 `.html`，或用浏览器打开本地文件。Plotly.js **已内嵌**在页面里，
断网也能用：拖拽旋转、滚轮缩放、悬停读数。

## 文件

| 文件 | 体积 | 真实 zeta 面数 | 外部依赖 |
|---|---|---|---|
| `D030_50slice_stack.html` | 12.11 MB | 50 | 无外链 |
| `D030_isosurface.html` | 4.92 MB | 0 | 无外链 |
| `D100_50slice_stack.html` | 12.16 MB | 50 | 无外链 |
| `D100_isosurface.html` | 5.38 MB | 0 | 无外链 |
| `D200_50slice_stack.html` | 12.16 MB | 50 | 无外链 |
| `D200_isosurface.html` | 4.22 MB | 0 | 无外链 |

- `*_50slice_stack.html`：50 个真实 zeta 层的 Plotly `Surface`，逐层贴到对应 zeta 平面；
  颜色为 `I_cross / max|I_cross|`，alpha 随 \|值\| 增大，近零背景透明（负蓝 / 零白 / 正红）。
- `*_isosurface.html`：marching-cubes 生成的等值面网格，**只包含真实存在的层级**；
  缺失的层级在 `exported_data/D0x0_isosurface_levels.json` 里记为 `not present`。

## 已验证 / 未验证

- 已验证（结构）：每份 stack 页面含 **50** 个 `name="zeta=..."` 的曲面 trace；
  页面不含 `<script src=...>`、不含 `src="http..."`。
  页面源码中出现的 `cdn.plot.ly` 字符串是 plotly.js 内部 topojson 的默认值，本页不使用地图。
- **未验证**：浏览器渲染的像素级效果。本环境没有可用的无头浏览器（`file://` 被拒绝），
  kaleido 也未安装，因此没有做"打开后截图比对"。请以静态图
  `figures_main/D0x0_3d_stack_normalized.png` 作为已目检的对照。

## 边界

交互页里的 z 轴同样是**离焦坐标 zeta**，不是样品深度；透明度、雾化为显示处理，
不能作为定量依据。

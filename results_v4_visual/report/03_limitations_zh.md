# 边界与未核实项 — 这些结论本轮没有、也不能证明

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

## 0. 一句话

本包把**已经存在的候选结果**画得更清楚、更可复现；它没有、也不可能把候选模型变成已认证模型。
下面每一条都是**明确未完成**的，不能因为图画得好看就被读成"已验证"。

## 1. 物理与模型层面（沿用 V4.1 审计结论，本轮无权重开）

| 项目 | 状态 | 具体含义 | 对图件的影响 | 升级需要什么 |
|---|---|---|---|---|
| full_jones_chain | **UNVERIFIED** | 从入射到探测的完整 Jones 链（后向 Mie 角、返回光 p/s 基、S12/S13 符号、相对复振幅、超临界角处理）在 V4 审计中未逐项核实 | 图件里的 `I_cross` 可能带有未被发现的基/符号/幅度约定误差；符号与相对幅度只在**本模型内部**可比 | 逐项对照论文与 Figshare 52761698，并用独立第二实现交叉验证 |
| high_na_model_validation | **UNVERIFIED** | NA 1.45 > n_sample 1.33，存在大量超临界（k_x > n_sample·k0）分量；当前用均匀球远场 Mie/Fresnel 的解析延拓近似，未做严格球-界面 Maxwell 求解 | 高 NA 下的 PSF 形状、旁瓣、轴向包络都只是近似；不能用本结果反演实验 PSF | 严格近场/多层界面求解，或与已发表高 NA 严格解对比 |
| paper_convention_checks | **UNVERIFIED** | 本轮没有重新下载并逐项核对论文正文与 Figshare 文件的参数、符号、归一化约定 | 与论文原图直接叠图比较不合法 | 取得原文 + 补充材料后逐条对照 |
| publisher_typeset_pdf | **NOT_OBTAINED** | 只有预印本级材料，未取得出版社排版版 PDF | 引用图号/页码需回溯到预印本 | 通过机构订阅下载 |
| linear_midpoint_reconstruction | **FAILED_KEPT** | V4 中"线性中点重建"验证失败，按要求保留失败记录，不隐藏也不修补 | 该重建路径的结果不可用作证据 | 重新设计重建验证 |
| absolute_calibration | **false** | 场量无量纲、相对同一 on-axis reference；没有 V/m、没有 W/m² | 只能比较同一归一化下的**相对**大小；不能与实验对比度数值直接比 | 绝对参考场标定 + 探测端响应 |
| sample_space_near_field | **false** | 数据是像平面 through-focus 响应 (zeta, y, x)，zeta 是**离焦扫描坐标** | 三维图的"z 轴"不是样品深度；不能说"画出了颗粒周围的近场三维分布" | 需要真正的样品空间场求解 |
| 模型缺失项 | 已知设定 | 无界面多次散射、无磁光张量、无相机采样/噪声、无布朗运动、单颗粒 | 与真实实验条件的差异全部未建模 | 逐项加入建模后再谈对比 |

## 2. 数据层面

- **50/171 层是子采样**：展示层从 171 个真实 zeta 层中选出（最大吸附误差
  0.98 nm，最坏缺口 4 nm = 2 层）。层与层之间的结构没有被计算，也没有插值"补出来"。
- **显示窗口 ±400 nm**：主网格仍是 x,y = ±1200 nm / 241 点；图件只裁切显示，不重采样。
- **float32 存储**：`I_cross` 以 float32 保存，相对精度约 1e-7；统计量按 float32 数值计算，未做平滑。
- 本轮**没有写回**任何 HDF5：三份文件的 SHA256 记录在 `config/visual_config.json`，
  与 V4.1 交付值一致，详见 `ACCEPTANCE.md` 的 A3/A3b 项。

## 3. 可视化层面（全部是"显示处理"，不改数据）

| 处理 | 用在哪 | 影响 | 不能据此得出 |
|---|---|---|---|
| alpha 随 \|I_cross\| 超线性加权 | 三维堆叠、体渲染 | 弱信号层视觉上更淡 | "看起来透明" ≠ 数值为零 |
| 深度雾化（远端向白混合 0.70→1.00） | 三维堆叠 | 远端层次对比度下降 | 不能比较远近层的绝对幅度 |
| z 轴 ×3 | `*_zexag3` | zeta 方向被拉伸 | 不能读成真实长宽比 |
| 半剖切（x>0 半边 alpha=0） | `*_cutaway` | 露出内部正负结构 | 剖切面不是物理截面 |
| asinh 压缩 | `*_montage_common_asinh` | 弱结构可见 | 颜色不再线性对应数值 |
| 共用色标 ±1.5477 | `*_common` | D030 近白 | 不是 bug，见下 |
| marching cubes 等值面 | `isosurface` | 细节受网格分辨率限制（z 2 nm / xy 10 nm） | 等值面不是等浓度面、不是颗粒表面 |

**D030 在 common 色标下几乎全白是正确结果**：max|I_cross| 为 D030 = 0.03256、
D100 = 1.548（相差 47.5×）。
共用色标必须取三者最大值，所以 30 nm 的数值挤在色标中心极窄一段。**不调色标去掩盖这个物理幅度差。**

**matplotlib 3D 用画家算法排序，不是体光线追踪**：半透明层之间存在遮挡/排序伪影，
某些视角下远景层会盖住近景层。因此另给了 cutaway / volume / orthoview 三种交叉视图；
但**任何单张 3D 图都不能当定量依据**，定量请用 `exported_data/` 的 CSV/JSON 与 2D 层图。

## 4. 本轮明确没做的验证

1. **HTML 未做浏览器像素级复验**：沙箱浏览器拒绝 `file://`，kaleido 未安装。只做了结构检查
   （每份 50 个真实 `zeta` 面、无 `<script src=...>`、无 `src="http..."`）。
   页内 `cdn.plot.ly` 字符串是 plotly.js 内部 topojson 默认值，本页不使用地图。
2. **未与论文原图逐像素比对**（publisher typeset PDF = NOT_OBTAINED，paper_convention_checks 未完成）。
3. **未与任何实验数据比对**（absolute_calibration = false）。
4. **未做独立第二实现交叉验证**（full_jones_chain = UNVERIFIED）。
5. **未在 50 层之间做插值/超分辨**（禁止把插值结果当数据）。

## 5. 可以写 / 不可以写

可以写：

- "在候选模型下，保存的 through-focus `I_cross` 体数据呈现 …（描述图件可见结构与数值）"；
- "30/100/200 nm 的 max|I_cross| 分别为 0.03256 /
  1.548 / 1.045，共用色标下相差 47.5×"；
- "轴上 `I_cross` 的过零情况：D030 -137 nm、D100 无过零点、D200 +31 nm"。

不可以写：

- "已通过物理验证 / 已认证 / 与实验一致"；
- "近场三维分布"、"颗粒周围电场"；
- "绝对散射截面 / 绝对对比度"、"与论文图完全一致"；
- 把 asinh / zexag / cutaway 图当定量结果。

## 6. 升级为"已认证"所需（清单，本轮范围之外）

1. 完整 Jones 链逐项核对（后向 Mie 角、p/s 基、S12/S13 符号、相对复振幅）；
2. 超临界角的严格处理（球-界面 Maxwell 或文献严格解对比）；
3. 论文 + Figshare 52761698 逐项参数/符号/归一化核对；
4. 绝对标定；
5. 独立第二实现交叉验证 + 收敛性（quadrature、径向采样、网格）；
6. 在明确误差模型下与实验数据对比；
7. 失败项 `linear_midpoint_reconstruction` 修复或给出替代方案。

## 7. 本轮没有做的事

- 没有重跑光学求解器，没有改波长 532 nm / 目标 NA 1.45 / 球心高度 15·50·100 nm / 网格；
- 没有改任何测试或验收条件来"通过"；
- 没有用 pilot、旧图或插值结果代替完整网格；
- 没有把 CANDIDATE 写成已认证。

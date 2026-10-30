# previews 预览说明

这里的图全部直接读取已存盘的 `data/D*/cube.h5`，不重新计算物理、不做插值放大。

| 文件 | 内容 |
|---|---|
| `preview_2d_three_diameters.png` | 3 粒径 × 3 个 zeta（−86 / 0 / +86 nm）的 `I_cross` 切片总览；**每行独立对称色标**（30 nm 比 200 nm 弱约两个数量级） |
| `preview_2d_D030.png` / `D100` / `D200` | 单粒径三联切片 + 色标（PNG + SVG） |
| `preview_3d_D030.png` / `D100` / `D200` | 保存网格的 through-focus 正交切片体视：5 个已保存的 xy 层（zeta = −120 / −60 / 0 / +60 / +120 nm）加 x=0 的 yz 剖面 |
| `preview_3d_three_diameters.png` | 三组体视与阅读说明卡组成的 2×2 汇报总览 |
| `preview_manifest.json` | 源数据、切片索引、显示裁剪、对称色标上限和字节数 |

三维预览的 **x/y 显示窗裁剪至 ±400 nm**，zeta 显示完整主窗口；只取保存的 10 nm 网格采样点，主网格仍为 171×241×241，**没有重采样或插值放大**。彩色切片表示 through-focus 干涉场，**不是颗粒表面**。虚线灰圆只是几何球剖面参考，不表示场分布必须呈球形。

可旋转的交互式三维页面在 `../views3d/D030_signed_interference_3d.html` 等文件中（离线、无外部依赖）；它们是独立的体视/等值面查看器，不用于替代上面的保存网格切片预览。

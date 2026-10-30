# Fe₃O₄ iSCAT 前向仿真 V4.1（候选实现）——先读这一页

**交付类别：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`**

三组主数据已实际生成并逐层复读；物理/公式链条**未**获得认证。凡标 `UNVERIFIED` 的项目都仍是候选状态，不是"通过"。

## 60 秒结论

| 项目 | 结果 |
|---|---|
| 粒径 / 球心高度 | 30 nm / 15 nm、100 nm / 50 nm、200 nm / 100 nm |
| 波长 / 目标 NA | 532 nm / 1.45 |
| 主网格 shape | 三组均 `171 × 241 × 241`，数组顺序 `(zeta, y, x)` |
| 轴 | `zeta = -170:2:170 nm`，`x, y = -1200:10:1200 nm` |
| 实读层数 | 171 + 171 + 171 = **513 层**（逐层流式读取，非抽样） |
| pilot 插值放大 | **未使用** |
| 物理认证 | **未认证**，见 `reports/physical_limitations.md` |

| 粒径 | 球心高度 | shape | 层数 | 字节 | SHA256 |
|---:|---:|---|---:|---:|---|
| 30 nm | 15 nm | 171×241×241 | 171 | 424,882,738 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 nm | 50 nm | 171×241×241 | 171 | 424,639,674 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 nm | 100 nm | 171×241×241 | 171 | 424,913,287 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

HDF5 路径：`data/D030nm/cube.h5`、`data/D100nm/cube.h5`、`data/D200nm/cube.h5`。

## 打开顺序

1. `START_HERE.html` —— 浏览器图形入口（离线可用，无外部网络依赖）。
2. `previews/` —— 三种粒径的清晰二维/三维预览图（本页下方可直达）。
3. `reports/00_汇报摘要_一页.md` —— 可直接向上级汇报的一页纸。
4. `reports/01_方法与参数说明.md` —— 模型、符号约定、参数。
5. `reports/02_验收矩阵.csv` / `acceptance_matrix.csv` —— G00–G15 逐条验收。
6. `reports/03_测试与数值验证.md` —— 98 次测试运行、收敛与独立复算。
7. `reports/06_修复与差异摘要.md` —— 本轮到底改了什么、为什么。
8. `reports/physical_limitations.md` —— **必读**：哪些事没被证实。
9. `reports/04_执行日志索引.md`、`logs/` —— 真实执行日志。
10. `reports/05_复现说明.md` —— 复算命令。

## 预览（相对路径）

- 二维总览：`previews/preview_2d_three_diameters.png`
- 单粒径二维：`previews/preview_2d_D030.png`、`preview_2d_D100.png`、`preview_2d_D200.png`
- 三维正交切片体视：`previews/preview_3d_D030.png`、`preview_3d_D100.png`、`preview_3d_D200.png`（5 个保存的 xy 层 + x=0 yz 剖面；x/y 显示裁剪至 ±400 nm，无插值放大，不是颗粒表面）
- 可旋转三维（离线 HTML）：`views3d/D030_signed_interference_3d.html` 等三份

## 包说明

- **轻量包** `Fe3O4_iSCAT_V4_1_REPORT_CANDIDATE.zip`：`LIGHT_NO_HDF5`，不含三份主 HDF5，只含图件、预览、表格、验证记录、日志、源码、XDMF 与离线网页。用于汇报与审查。
- **完整包** `Fe3O4_iSCAT_V4_1_FULL_CANDIDATE.zip`：`FULL_DATA_AND_HDF5`，在三份主 HDF5 之外包含上述全部内容。
- 两个包的 ZIP SHA256、字节数、成员数与验证结论记录在**包外**的 `package_verification.json`（同时是 Release 资产）。ZIP 不能包含自身摘要，故该文件不入包。

## 一句话边界

球形只描述**颗粒几何**。主三维预览显示保存网格的正交切片，彩色区域不是颗粒表面；显示窗只裁剪 x/y 至 ±400 nm，主网格仍为 171×241×241，没有重采样或插值放大。虚线灰圆仅为几何参考，不表示场分布必须呈球形。

# V4.0.0 — Fe₃O₄ 三粒径前向 through-focus 仿真（候选实现）

**状态：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。**

本版本新增 30/100/200 nm 三组完整主数据体。每组 `shape=(171,241,241)`，数组顺序 `(zeta,y,x)`，171 层全部实际计算并逐层复读。固定参数为 Fe₃O₄、532 nm、NA=1.45、球心高度 D/2、`zeta=-170:2:170 nm`、`x,y=-1200:10:1200 nm`。没有用 pilot 插值放大主网格，也没有引入 520 nm、400 Hz、布朗运动或相机条件。

## 实际修复

- 后向 Mie 角采用 `mu_back=-kz_s/ns`。
- 候选返回光 p 基链采用 `i(S1*t_s-S2*t_p)`，并保留与论文 S6/S13 印刷式的 `S2` 项差异证据。
- `S12/S13` 方位项修正为 `J2 sin(2φ)` 正号，并通过直接方位积分与降维积分对照。
- 保留超临界角解析延拓，但球—界面物理状态仍为 `UNVERIFIED`。
- 修复交付审计的嵌套 HDF5、JSON/NumPy、CSV、HTML 离线引用与隐私扫描问题；最终图件、HTML、XDMF、隐私、HDF5 五项审计全部通过。
- 双线性 0.1% 中点重建检查仍失败（约 0.15%–0.22%），按要求保留失败；三次插值通过。

## 数据

| 粒径 | 球心高度 | shape | 层数 | HDF5 SHA256 |
|---:|---:|---:|---:|---|
| 30 nm | 15 nm | 171×241×241 | 171 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 nm | 50 nm | 171×241×241 | 171 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 nm | 100 nm | 171×241×241 | 171 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

## 包

- `results_v4_light.zip`：轻量包，不含 HDF5。
- `results_v4_full.zip`：完整包。
- `parts/results_v4_full.zip.part001` … `part080`：16 MiB 分片。
- `package_verification.json`：独立解压、嵌入 SHA、HTML、XDMF、HDF5 复读和分片重组验证。
- `SHA256SUMS_v4_packages.txt`：本目录发布资产哈希。

## 仍未认证

完整 S3 QWP/PBS/Fresnel/物镜 Jones 链、超临界角球—界面物理、相对/绝对复振幅标定仍未核实；出版社最终排版 PDF 未取得；交付为像面 through-focus 响应，不是样品空间近场。

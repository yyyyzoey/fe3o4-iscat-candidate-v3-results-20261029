# HDF5 数据文件：见 GitHub Release `v4.1.0-candidate`

本结果树中的 7 个 HDF5 文件不进入 Git（3 个主数据体合计约 1.27 GB，另 4 个长程诊断体约 2.9 MB/个），
仅作为 GitHub Release 资产发布。Git 中保留全部代码、图件、表格、日志、验收记录与 `SHA256SUMS.txt`。

## 下载位置

公开仓库 `yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029`，分支 `v4-audit-final-candidate`，
Release tag `v4.1.0-candidate`：

- `Fe3O4_iSCAT_V4_1_FULL_CANDIDATE.zip` —— 完整科研数据包，含下列全部 HDF5（约 1.35 GB）。
- `Fe3O4_iSCAT_V4_1_REPORT_CANDIDATE.zip` —— 轻量汇报包，不含 HDF5（约 45 MB）。
- `package_verification.json` —— 包外验证记录（ZIP 不能包含自身摘要）。

## 主数据体（through-focus）

| 文件 | 粒径 / 球心高度 | shape | bytes | SHA256 |
|---|---|---|---|---|
| `data/D030nm/cube.h5` | 30 nm / 15 nm | (171, 241, 241) | 424882738 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| `data/D100nm/cube.h5` | 100 nm / 50 nm | (171, 241, 241) | 424639674 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| `data/D200nm/cube.h5` | 200 nm / 100 nm | (171, 241, 241) | 424913287 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

坐标：`zeta = -170:2:170 nm`（171 层），`x = y = -1200:10:1200 nm`（241 × 241），数组顺序 `(zeta, y, x)`。

## 长程诊断体

| 文件 | 组别 | bytes | SHA256 |
|---|---|---:|---|
| `diagnostics/paper_control_NA135/D120_long_xz.h5` | 论文参数控制组（D=120 nm, NA=1.35） | 2928065 | `040aa5f3515c5a6025ae18f82fa7fd77a207b72d258c7a12ca0a6ef6f5ae1662` |
| `diagnostics/target_Fe3O4_NA145/D030_long_xz.h5` | Fe₃O₄ 目标组（D=30 nm） | 2929355 | `e09253bbc42767aec087ae463f3c254dd196f6165e3be0c65c6f6103057bd921` |
| `diagnostics/target_Fe3O4_NA145/D100_long_xz.h5` | Fe₃O₄ 目标组（D=100 nm） | 2927798 | `1da284ad0efdfbae0de75ade8bd125c5e451f89d0a5bf2450e4b0375ad09623a` |
| `diagnostics/target_Fe3O4_NA145/D200_long_xz.h5` | Fe₃O₄ 目标组（D=200 nm） | 2932046 | `090da2ef35c9de5e09dfdcad7dc951d69a6a00ee4eadd0eebfdf45c56d43c94c` |

## 解压后复验

```bash
python code/package_v4/tools/verify_results_bundle.py Fe3O4_iSCAT_V4_1_FULL_CANDIDATE.zip --mode full
```

该工具会重算 ZIP 内 518 条 SHA256 清单、逐层读取全部 513 层主 HDF5，并核对每层场/对比度代数一致性。

## 状态说明

`result_class = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。
工程验收通过不等于物理模型认证；完整 Jones 链、超临界高 NA 物理与绝对标定仍为 UNVERIFIED。

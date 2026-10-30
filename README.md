# Fe₃O₄ 表面附着单球 iSCAT through-focus 候选结果

> **当前结果类别：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。**
>
> 数据生成已完成；完整 QWP/PBS/Fresnel/物镜 Jones 链、超临界高 NA 球—界面物理、相对复振幅和绝对标定仍未认证。

## V4 当前交付

V4 是当前结果，位于 [`v4/`](v4/)；分支为 `v4-paper-forward-results`，Commit 为 `49f7f9ac644b6ac59892c3cb31177a2e2b600e16`，Tag 为 `v4.0.0`。

固定条件：Fe₃O₄，`lambda=532 nm`，`NA=1.45`，30/100/200 nm 单球，球心高度分别为 15/50/100 nm。三组均为 `(171,241,241)`，`zeta=-170:2:170 nm`，`x,y=-1200:10:1200 nm`，数组顺序 `(zeta,y,x)`，实际 171 层直接计算。

### 分支内完整数据

完整 `results_v4_full.zip` 已在 Git 分支中按 16 MiB 切分为 80 个文件：

```text
v4/branch_data/full_package/parts/results_v4_full.zip.part001
...
v4/branch_data/full_package/parts/results_v4_full.zip.part080
```

- ZIP 大小：`1,326,369,547` bytes
- ZIP SHA256：`c61f9a3bf7d6d90f0c1746a1e9de104db669cb2e838c84d3d1234f67b8e62a2a`
- 逐片哈希：`v4/branch_data/full_package/parts/results_v4_full.parts.sha256`
- 说明：`v4/branch_data/full_package/README_ZH.md`

```powershell
python .\v4\branch_data\full_package\reassemble_results_v4.py
python .\v4\branch_data\full_package\verify_results_bundle.py .\v4\branch_data\full_package\results_v4_full.zip
```

### 三个主数据体

| 粒径 | ZIP 内路径 | shape | 层数 | HDF5 SHA256 |
|---:|---|---:|---:|---|
| 30 nm | `results_v4/data/D030nm/cube.h5` | `(171,241,241)` | 171 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 nm | `results_v4/data/D100nm/cube.h5` | `(171,241,241)` | 171 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 nm | `results_v4/data/D200nm/cube.h5` | `(171,241,241)` | 171 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

## 验证状态

- V4 导出/光学/Jones/IO/鲁棒性：40/40 PASS
- legacy 物理：7/7 PASS
- HDF5 shape、完成层数、逐层复读：PASS
- 完整 ZIP CRC、380 条目、内嵌哈希：PASS
- 80 个分片与 Release 匿名下载验证：PASS
- `data_generation=COMPLETE`
- `numerical_validation=PARTIAL`
- `formula_fidelity=UNVERIFIED`
- `high_na_model_validation=UNVERIFIED`
- `absolute_calibration=false`
- 双线性 10→5 nm 中点重建：`FAILED_KEPT`；三次插值通过

## 当前入口

- [`v4/README.md`](v4/README.md)
- [`v4/results_v4/START_HERE.html`](v4/results_v4/START_HERE.html)
- [`v4/results_v4/summary_zh.md`](v4/results_v4/summary_zh.md)
- [`v4/results_v4/status.json`](v4/results_v4/status.json)
- [`v4/results_v4/validation/`](v4/results_v4/validation/)

## 旧 v1 内容

根目录 `release/`、`data/`、`verification/` 和旧 `v1.0.0` Release 为历史保留，不是当前 V4 数据。V4 的当前结果以 `v4/` 和 `v4.0.0` 为准。

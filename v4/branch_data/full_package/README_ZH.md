# V4 完整结果包（分支内分片）

此目录把 `v4.0.0` Release 中约 1.33 GB 的 `results_v4_full.zip` 无损切分为 80 个普通 Git 文件，每个分片不超过 16 MiB。这样无需访问 Release API，也能直接从 `v4-paper-forward-results` 分支取得实际结果内容。

## 分片

- `parts/results_v4_full.zip.part001` … `parts/results_v4_full.zip.part080`
- 分片总字节：`1,326,369,547`
- 逐片 SHA256：`parts/results_v4_full.parts.sha256`
- 重组后 ZIP SHA256：`c61f9a3bf7d6d90f0c1746a1e9de104db669cb2e838c84d3d1234f67b8e62a2a`
- 清单：`results_v4_full_manifest.json`

## 重组与验证

在本目录执行：

```powershell
python .\reassemble_results_v4.py
python .\verify_results_bundle.py .\results_v4_full.zip
```

第一条命令会逐片检查大小与 SHA256、按数字顺序重组，并核对最终 ZIP 的 SHA256。第二条命令会检查 ZIP CRC、380 个条目、内嵌哈希，并逐层复读三个主 HDF5。

无凭据匿名访问、80/80 逐片哈希、重组和包内复读的实测记录见同目录 `BRANCH_ACCESS_VERIFICATION.md` 与 `BRANCH_ACCESS_VERIFICATION.json`。GitHub 网页不会直接渲染 HDF5，必须下载后重组。

也可以直接下载单个分片，例如：

```text
https://raw.githubusercontent.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/v4-paper-forward-results/v4/branch_data/full_package/parts/results_v4_full.zip.part001
```

## ZIP 内三个主数据体

| 粒径 | ZIP 内路径 | shape | 层数 | HDF5 SHA256 |
|---:|---|---:|---:|---|
| 30 nm | `results_v4/data/D030nm/cube.h5` | `(171,241,241)` | 171 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 nm | `results_v4/data/D100nm/cube.h5` | `(171,241,241)` | 171 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 nm | `results_v4/data/D200nm/cube.h5` | `(171,241,241)` | 171 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

网格为 `zeta=-170:2:170 nm`、`x,y=-1200:10:1200 nm`，数组顺序为 `(zeta,y,x)`。三组主网格均为 171 层直接计算，不是 pilot 插值放大。

状态保持为 `CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。


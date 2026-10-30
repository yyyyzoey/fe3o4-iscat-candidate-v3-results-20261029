# V4 分支实测可访问性记录

生成时间（UTC）：`2026-10-30T05:11:02.096572+00:00`

## 结论

`PASS`。不携带 GitHub 凭据，从公开 API 与 `raw.githubusercontent.com` 实际取得并核验了 `v4-paper-forward-results` 分支中的数据分片；80/80 分片的大小和 SHA256 全部匹配，重组完整 ZIP 后哈希一致，包内 380 个条目及三个主 HDF5 复读通过。

- 仓库：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029
- 分支：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/tree/v4-paper-forward-results
- 本次核验的数据提交：`324b4b384ac088b8bba93091fea336a6bfe7597d`
- 分支树中的分片：`80` 个普通 Git 文件
- 分片总字节：`1,326,369,547`
- 重组 ZIP 字节：`1,326,369,547`
- 重组 ZIP SHA256：`c61f9a3bf7d6d90f0c1746a1e9de104db669cb2e838c84d3d1234f67b8e62a2a`
- 包内条目：`380`
- 三个主 HDF5：均 `(171,241,241)`，`completed_slices=171`，全数组有限，哈希与清单一致
- 当前物理分类：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`

## 为什么分支里是 80 个分片

每个 `cube.h5` 约 424 MB，超过 GitHub 单文件 100 MB 限制。因此完整 ZIP 被无损拆成 80 个不超过 16 MiB 的普通 Git 文件。GitHub 网页不会把 HDF5 直接渲染成可读表格；需要下载分支/分片后重组。这不表示分支没有数据。

## 复现命令

```powershell
git clone --branch v4-paper-forward-results --single-branch https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029.git fe3o4-v4
cd .\fe3o4-v4\v4\branch_data\full_package
python .\reassemble_results_v4.py
python .\verify_results_bundle.py .\results_v4_full.zip
```

预期最后输出 `pass=true`、`entries=380`、`hdf5_present=true`、`failures=[]`，并逐片核对 80/80 的 SHA256。

## 直接入口

- 完整包目录：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/tree/v4-paper-forward-results/v4/branch_data/full_package
- 分片目录：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/tree/v4-paper-forward-results/v4/branch_data/full_package/parts
- 中文说明（raw）：https://raw.githubusercontent.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/v4-paper-forward-results/v4/branch_data/full_package/README_ZH.md
- 重组脚本（raw）：https://raw.githubusercontent.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/v4-paper-forward-results/v4/branch_data/full_package/reassemble_results_v4.py
- 验证脚本（raw）：https://raw.githubusercontent.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/v4-paper-forward-results/v4/branch_data/full_package/verify_results_bundle.py

## 边界

本记录只证明公开分支中的实际数据文件可匿名取得且包内数据与技术验收通过；不证明严格论文复现或完整物理认证。完整 S3 QWP/PBS/Fresnel/物镜 Jones 链、超临界球—界面物理、相对/绝对复振幅、出版社最终 PDF 等仍未核实。

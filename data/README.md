# Data

当前 V4 完整数据位于 [`../v4/branch_data/full_package/`](../v4/branch_data/full_package/)。

该目录包含 80 个 `results_v4_full.zip.partNNN` 分片、逐片 SHA256、重组脚本和三个主 cube 的校验说明。根目录其余 `data/` 和 `release/` 文件属于旧 v1 历史，不是当前 V4 结果。

```powershell
python ..\v4\branch_data\full_package\reassemble_results_v4.py
python ..\v4\branch_data\full_package\verify_results_bundle.py ..\v4\branch_data\full_package\results_v4_full.zip
```

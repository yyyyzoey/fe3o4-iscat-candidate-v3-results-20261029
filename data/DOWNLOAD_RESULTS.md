# 完整结果包下载与重组

> 仓库为 **Public**（2026-10-29 起公开）。GitHub Release 中的完整数据被无损切分为 **76 个 16 MiB 分片**，以便并行上传和断点续传。分片不是独立数据文件；必须按名称顺序拼接后，才得到原始 `results_bundle.zip`。

## 数据标识

| 项目 | 值 |
|---|---|
| Release | `v1.0.0` |
| 分片数 | `76`（`results_bundle.zip.part000` 至 `part075`） |
| 分片大小 | `16,777,216` bytes；最后一片较小 |
| 重组后大小 | `1,273,486,344` bytes |
| 重组后 SHA256 | `fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7` |
| 清单文件 | `results_bundle.zip.manifest.json` |
| 清单 SHA256 | `07b8d5a19ce260b4f7e57898e16b7a978c82b94cdf384e628f682a08700188df` |
| 分片校验表 | `results_bundle.zip.parts.sha256` |
| 下载脚本 | `download_results.py` |

ZIP 内含 139 个成员，三个 HDF5 数据体均为完整 `(171,241,241)` 网格。完整包位于 Release，不进入普通 Git 历史。

## 推荐方式：脚本下载并自动校验

需要 Python 3.8+。仓库已公开，脚本默认匿名下载，无需 GitHub token；只有遇到匿名 API 限额时才需要设置只读 token。不要把 token 提交到仓库。

PowerShell：

```powershell
python .\download_results.py --tag v1.0.0 --out .\download
```

脚本会：

1. 读取并保存 `results_bundle.zip.manifest.json`；
2. 并行下载全部分片；
3. 逐片核对 byte 数和 SHA256；
4. 按 `part000`→`part075` 顺序重组；
5. 核对最终大小与 SHA256，只有通过后才删除分片缓存。

成功时最后一行应包含：

```text
FINAL ARCHIVE VERIFICATION PASSED
```

输出文件为 `download/results_bundle.zip`。

## 手工方式

### 1. 下载全部分片

已安装 GitHub CLI 且已登录时：

```powershell
gh release download v1.0.0 --repo yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029 --pattern "results_bundle.zip.part*" --dir .\results_bundle.zip.parts
gh release download v1.0.0 --repo yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029 --pattern "results_bundle.zip.parts.sha256" --dir .\results_bundle.zip.parts
```

也可在仓库的 Release 页面逐个下载分片。

### 2. 校验每个分片

PowerShell：

```powershell
Get-Content .\results_bundle.zip.parts\results_bundle.zip.parts.sha256 | ForEach-Object {
    $hash, $name = $_ -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path '.\results_bundle.zip.parts' $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $hash.ToLowerInvariant()) { throw "Part mismatch: $name" }
}
```

### 3. 按顺序重组并校验

PowerShell：

```powershell
.\scripts\reassemble_results.ps1 -PartsDir .\results_bundle.zip.parts -Output .\results_bundle.zip
```

Linux/macOS：

```sh
sh ./scripts/reassemble_results.sh ./results_bundle.zip.parts ./results_bundle.zip
```

最终必须得到：

```text
SHA256  fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7
```

## 使用数据

ZIP 解压后保持原有目录结构，XDMF 通过相对路径引用 `D030nm/cube.h5`、`D100nm/cube.h5`、`D200nm/cube.h5`。不要重命名 `D0xxnm` 目录。

## 状态限制

`result_class=CANDIDATE`。完整 Jones 链、超临界 NA 物理、相对复振幅与绝对标定仍未核实；不得把数据表述为严格论文复现或实验相机图像。

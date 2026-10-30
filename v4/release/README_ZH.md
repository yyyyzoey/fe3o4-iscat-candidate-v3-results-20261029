# Fe₃O₄ iSCAT V4 结果下载与复核

**状态：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。** 这里是论文启发的候选实现结果，不是严格论文复现、完整 Jones 链认证、高 NA 物理认证或绝对强度标定。

## 内容

- `results_v4_full.zip`：完整结果，含三个主 cube 与四个长程诊断 HDF5。
- `results_v4_light.zip`：轻量包，不含任何 `*.h5`；含代码、图件、表格、HTML、XDMF、验证记录和文档。
- `parts/results_v4_full.zip.part001` … `part080`：完整 ZIP 的 16 MiB 分片，用于下载大文件。
- `results_v4_full_manifest.json`：文件大小、SHA256、分片数量与数据 shape。
- `results_v4_full.zip.sha256`、`results_v4_light.zip.sha256`、`parts/results_v4_full.parts.sha256`：校验值。
- `package_verification.json`：本包的实际独立解压、分片重组、HDF5 复读与哈希验证记录。

## 下载完整结果

优先直接下载 `results_v4_full.zip`。若网络不稳定，下载全部 80 个分片，保持文件名不变并与下载脚本放在同一目录，然后运行：

```powershell
python reassemble_results_v4.py
python verify_results_bundle.py results_v4_full.zip
```

轻量包直接运行：

```powershell
python verify_results_bundle.py results_v4_light.zip
```

## 三个正式数据体

| 粒径 | 球心高度 | shape | 层数 | 数组顺序 |
|---:|---:|---:|---:|---|
| 30 nm | 15 nm | 171×241×241 | 171 | (zeta,y,x) |
| 100 nm | 50 nm | 171×241×241 | 171 | (zeta,y,x) |
| 200 nm | 100 nm | 171×241×241 | 171 | (zeta,y,x) |

共同网格：`zeta=-170:2:170 nm`，`x=y=-1200:10:1200 nm`。波长 532 nm，目标 NA=1.45，Fe₃O₄，球心高度 `D/2`。三种粒径均使用同一参考尺度和同一演示 `gamma=0.5+0i`。

## 未认证边界

完整 S3 QWP/PBS/Fresnel/物镜 Jones 链、超临界角球—界面物理、相对/绝对复振幅标定仍未核实；出版社最终排版 PDF 未取得；交付的是像面 through-focus 响应，不是样品空间近场；双线性 0.1% 显示插值检查保留失败（约 0.15%–0.22%），三次插值通过。

GitHub 分支：`v4-paper-forward-results`；Release：`v4.0.0`。旧 `v1.0.0` Release 保持不变。

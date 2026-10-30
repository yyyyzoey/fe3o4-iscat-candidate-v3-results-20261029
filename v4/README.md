# V4：Fe₃O₄ 三粒径前向 through-focus 仿真（候选实现）

**状态：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。**

本目录发布 V4 的源码、报告、图件、验收记录，并在 Git 分支内提供完整结果包分片。

## 完整数据：分支内可直接取得

完整 `results_v4_full.zip` 已无损切分为 80 个 16 MiB 分片，放在：

- `branch_data/full_package/parts/results_v4_full.zip.part001` … `part080`
- 逐片哈希：`branch_data/full_package/parts/results_v4_full.parts.sha256`
- 重组脚本：`branch_data/full_package/reassemble_results_v4.py`
- 验证脚本：`branch_data/full_package/verify_results_bundle.py`

在本目录运行：

```powershell
python .\branch_data\full_package\reassemble_results_v4.py
python .\branch_data\full_package\verify_results_bundle.py .\branch_data\full_package\results_v4_full.zip
```

完整 ZIP 大小 `1,326,369,547` bytes，SHA256：

```text
c61f9a3bf7d6d90f0c1746a1e9de104db669cb2e838c84d3d1234f67b8e62a2a
```

Release `v4.0.0` 仍作为冗余下载入口保留。分支中的 80 个分片已用无 GitHub 凭据的公开 HTTP 下载逐片复核，并实际重组、复读完整包；证据见 `branch_data/full_package/BRANCH_ACCESS_VERIFICATION.md` 与 `.json`。

GitHub 文件页面不能直接展开或渲染 HDF5 二进制；这不表示分支缺少数据。请按上方命令先重组 ZIP。

- 数据 shape：三组均为 `(171,241,241)`，轴顺序 `(zeta,y,x)`，实际完成 171 层
- 网格：`zeta=-170:2:170 nm`，`x,y=-1200:10:1200 nm`
- 固定参数：Fe₃O₄，532 nm，NA=1.45，球心高度 D/2
- 三个主 HDF5：`results_v4/data/D030nm/cube.h5`、`D100nm/cube.h5`、`D200nm/cube.h5`

## 入口

- `results_v4/START_HERE.html`：图形化入口
- `results_v4/summary_zh.md`：完整中文摘要
- `results_v4/status.json`：机器可读状态
- `results_v4/validation/`：测试、数值、来源、HDF5、HTML、XDMF 和隐私审计
- `results_v4/code/`：求解器、导出器、审计脚本及配置
- `results_v4/SHA256SUMS.txt`：完整 `results_v4` 树逐文件哈希
- `release/README_ZH.md`：Release 下载与验证说明

## 未认证边界

完整 S3 QWP/PBS/Fresnel/物镜 Jones 链、超临界角球—界面物理、相对/绝对复振幅标定仍未核实；出版社最终排版 PDF 未取得；交付的是像面 through-focus 响应，不是样品空间近场；双线性 0.1% 显示插值检查保留失败（约 0.15%–0.22%）。


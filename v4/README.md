# V4：Fe₃O₄ 三粒径前向 through-focus 仿真（候选实现）

**状态：`CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。**

本目录发布 V4 的轻量复现内容。完整 HDF5 位于 Release `v4.0.0`：

- 完整包：`results_v4_full.zip`
- 80 个分片：`results_v4_full.zip.part001` … `part080`
- 轻量包：`results_v4_light.zip`
- 数据 shape：三组均为 `(171,241,241)`，轴顺序 `(zeta,y,x)`，实际完成 171 层
- 网格：`zeta=-170:2:170 nm`，`x,y=-1200:10:1200 nm`
- 固定参数：Fe₃O₄，532 nm，NA=1.45，球心高度 D/2

## 本地入口

- `results_v4/START_HERE.html`：图形化入口
- `results_v4/summary_zh.md`：完整中文摘要
- `results_v4/status.json`：机器可读状态
- `results_v4/validation/`：测试、数值、来源、HDF5、HTML、XDMF 和隐私审计
- `results_v4/code/`：求解器、导出器、审计脚本及配置
- `results_v4/SHA256SUMS.txt`：完整 `results_v4` 树逐文件哈希（含 Release 中的 7 个 HDF5）
- `release/README_ZH.md`：下载、分片重组与验证说明
- `release/package_verification.json`：独立解压与数据复读结果

`results_v4/data/` 中没有 `cube.h5` 是刻意设计；完整数据只通过 Release 资产分发。

## 未认证边界

完整 S3 QWP/PBS/Fresnel/物镜 Jones 链、超临界角球—界面物理、相对/绝对复振幅标定仍未核实；出版社最终排版 PDF 未取得；交付的是像面 through-focus 响应，不是样品空间近场；双线性 0.1% 显示插值检查保留失败（约 0.15%–0.22%）。

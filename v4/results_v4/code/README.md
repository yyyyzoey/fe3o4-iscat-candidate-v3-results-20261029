# V4 交付代码

本目录保存生成 V4 结果与审计的全部可复现源码，不含 HDF5 数据体。

- `solver/`：产生三个 `cube.h5` 的光学求解器与配置（`src/iscat_core.py`、`src/run_dataset.py`）、
  31 项光学/IO 测试（`tests/`）、审计工具（`tools/`）、论文约定审计文档（`docs/`）。
  `src/*.py` 的规范化哈希等于 cube 属性 `implementation_sha256`，见 `../provenance/source_hashes.json`。
- `package_v4/`：用户提供的 V4 执行包原件（12/12 文件哈希校验通过）。
  `tools/export_paper_views.py` 只做了路径处理修改（把绝对路径改为相对标签），
  差异见 `package_v4/docs/export_tool_path_patch.diff`；光学公式未改动。
- `figures/`：由保存的 HDF5 复读生成 F1–F7 图件、CSV、XDMF 的脚本。
- `figures/audits/`：数据体逐层复读、图件完整性、链接、隐私扫描与打包脚本。

所有脚本只读取已保存数据或从配置重新计算，不修改已有 HDF5。

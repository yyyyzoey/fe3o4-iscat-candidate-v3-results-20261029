# Fe₃O₄ 三粒径论文模型仿真——聚焦目标执行包 V4

本包针对用户当前目标：采用论文级近似模型，对30/100/200 nm贴壁单球，在球心参考的名义景深窗口内进行轴向密切片，得到无噪声三维干涉成像响应及清楚的论文式图件。

**不是新的一套光学求解器，不是新生成的正式仿真结果。**
它包含可直接执行的只读图像/三维导出工具，以及交给 Codex 的完整修订与验收指令。光学主体复用指定仓库；其公式约定需要按任务书做有限的内部核验。不要再把绝对实验标定、全波近场认证、追踪或反演作为完成本轮的前提。

## 入口

- `CODEX_PROMPT.md`：直接发送给 Codex。
- `docs/EXECUTION_SPEC.md`：范围、公式、网格、图件、验收及停止条件。
- `docs/CURRENT_RESULT_REVIEW.md`：对现有v1.0.0结果的判断和此前要求的纠正。
- `configs/delivery_contract.json`：交付合同，**不是**旧求解器的运行配置。
- `tools/export_paper_views.py`：读取已有HDF5，复读字段、导出切片/剖面/曲线/3D网页/静态图/CSV。
- `tests/test_exporter.py`：只读工具单元测试，不是光学模型认证。
- `reports/TOOL_TEST_REPORT.md`：本包实际测试范围。

## 已有数据的快速出图

先下载并重组既有仓库的Release，找到包含 `D030nm/cube.h5`、`D100nm/cube.h5`、`D200nm/cube.h5` 的 `release` 根目录。
安装本包依赖后，在本包根目录执行：

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tools/export_paper_views.py --data-root "已有数据/release" --out "v4_views" --mesh-step 2
```

打开 `v4_views/index.html`。三维HTML内嵌Plotly运行代码，下载后无需联网即可查看。
正式出图**不加** `--allow-pilot`；它只用于工具测试，且会把所有输出标为PILOT。
`--skip-3d`只允许调试，输出会明确记录可视化不完整。
默认300 dpi，PNG及SVG并存。三维静态图220 dpi，离线三维网页支持旋转和逐面开关。

## 重要边界

出图工具只执行读取与代数一致性检查，不修改原数据、不改变相位、不重设粒径、不补出不存在的结构。它保留源数据状态，**不能通过一次出图把CANDIDATE升级为VERIFIED**。

本轮允许最终结果标为“论文近似模型下的归一化仿真”，绝对实验单位不必成立。前提是代码中角度、偏振基、传播相位的约定相互一致；内部矛盾不能用归一化掩盖。

主数据第三维是焦点扫描量zeta；球形的是颗粒，不要求等值面为球形。主窗口之外的信号没有计算进主数据体，不允许把窗口边缘当作信号真实终止边界。

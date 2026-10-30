# Fe₃O₄ 表面附着单球 iSCAT 前向仿真 V4：结果摘要

## 结论先行

三组主数据均已实际生成并逐层复读：直径 **30、100、200 nm**，球心高度分别为 **15、50、100 nm**，波长 **532 nm**，目标 **NA=1.45**。每组数据体均为 **171×241×241**，轴为 **zeta=−170:2:170 nm**、**x,y=−1200:10:1200 nm**，数组顺序为 **(zeta, y, x)**。没有用 pilot 插值放大代替主网格。

本轮交付类别是 **CANDIDATE（论文启发、显式候选实现）**，不是“严格复现论文”、不是“完整 Jones 链认证”、不是“高 NA 物理认证”，也不是绝对强度标定。主数据是像面 through-focus 响应 **F(x,y,zeta)**；zeta 是焦点扫描量，不是样品空间近场 z 坐标。

## 三个正式数据体

| 粒径 | 球心高度 | shape | 实际完成层数 | HDF5 字节数 | SHA256 |
|---:|---:|---:|---:|---:|---|
| 30 nm | 15 nm | 171×241×241 | 171 | 424,882,738 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 nm | 50 nm | 171×241×241 | 171 | 424,639,674 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 nm | 100 nm | 171×241×241 | 171 | 424,913,287 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

文件位于：

- `data/D030nm/cube.h5`
- `data/D100nm/cube.h5`
- `data/D200nm/cube.h5`

三组共用轴上参考场尺度 `reference_field_scale=9.422632737507974e-08`，共用演示相对复振幅 `gamma=0.5+0i`。生产路径设 `CR=CS=1`（`cs_over_cr=1.0`），保存的 `E_scat_unit` 不含 `eta`；随后 `E_scat=gamma*E_scat_unit`，`I_scat=|gamma|^2*U=0.25U`，`I_cross=2Re(gamma*Q)`。`eta=0.5` 只是论文符号下的可选收集效率约定，不是 Fe₃O₄ 实验对比度标定。

主信号为

```text
J = I_cross = 2 Re(conj(E_ref) · E_scat)
I_total = I_ref + I_scat + I_cross
```

`J` 可正可负。HDF5 同时保存 `E_ref`、`E_scat`、`I_ref`、`I_scat`、`I_cross`、`I_total`、固定参考归一化信号与局部归一化信号。

## 本轮实际修复与核查

1. **后向 Mie 角**：代码采用 `mu_back=-kz_s/ns`，使沿入射反方向返回的光对应 `theta=pi, mu=-1`；不再使用符号不明确的正向角约定。
2. **返回光 p/s 基与 Fresnel 链**：候选实现采用 `i(S1*t_s-S2*t_p)`。论文补充 S6/S13 印刷形式在可读文本中是 `i(S2*t_p+S1*t_s)`；两者的 `S2` 项符号不同。依据返回光 p 基与标准 Mie 球坐标分量的直接 3D 投影，候选链与 `-S2_Mie` 的 p 系数一致。该证据闭合的是标量代数与基映射，**不等于**对 S3 整条 QWP/PBS/Fresnel/物镜/镜筒透镜 Jones 矩阵链的逐矩阵认证，因此 `paper_convention_checks` 仍为 `UNVERIFIED`。
3. **S12/S13 方位项**：将 `(1-cos(theta_d)) J2 sin(2*phi_d)` 从旧实现的负号修为止号；通过对 `phi` 的直接数值积分与降维 Bessel 结果比较，两者复振幅一致，相关测试通过。
4. **S6 印刷差异留档**：没有把印刷式改写成“自己的答案”后宣称一致；差异、边界和证据均在 `validation/model_conventions.md` 与 `validation/jones_chain_numbers.json` 中留档。
5. **超临界角**：NA=1.45 > ns=1.33，`u∈(1.33,1.45]` 采用 `Im(kz_s)>=0` 的解析延拓。数值上无 NaN/Inf，且求积从 512/256 加密到 1024/512 的相对 L2 误差约 1e-8；但均匀球远场 Mie/Fresnel 延拓能否代表球—界面超临界谱仍未证实，保留 `ANALYTIC_CONTINUATION_UNVALIDATED` 与 `high_na_model_validation=UNVERIFIED`。
6. **来源核对**：已取得并核对 Figshare file **52761698**（2,821,576 字节，SHA256 `62a60e7194230c7ad5ed7635c951dfdab81e6f82e2e0f4772b6b71ef70ffbbfe`）与 arXiv 2209.14508（4,776,448 字节，20 页，SHA256 `1e40105aa5f1fe5ad399185f0ec84c400178c94fbdb1c1ea199496b452114358`）。出版社最终排版 PDF 未取得，因此不声称与 DOI 最终版逐式一致。
7. **交付审计脚本**：修复了嵌套 HDF5 路径检查、NumPy/JSON 转换、CSV 行数下限、HTML 外部加载/inert URL 区分和绝对路径隐私扫描。归档源码的规范化实现哈希已从交付树复算一致。

## 测试与数值检查

- 六组共 **98 次测试运行全部通过**，去重后 **86 个唯一用例**：solver+V4.1 35/35、exporter 9/9、legacy 7/7、handoff 21/21、strict auditor 12/12、verifier 错误注入 14/14。
- 测试原始日志位于 `logs/tests/`，命令、退出码、耗时和哈希见 `validation/tests.json`；没有修改测试以凑通过。
- 完整数值诊断：`numerical_audit_pass=true`。角积分连续加密、径向、Mie 阶数、轴向 2→1 nm 抽检均满足 1e-3 阈值；三粒径各检查了 5 个 zeta、轴上/离轴点。
- **保留失败**：10 nm 主网格使用双线性从 20 nm 中点重建时，误差约 0.15%–0.24%，不满足 0.1%；三次插值误差小于 1e-5。该检查不改阈值、不删除，记录在 `validation/numerical_audit.json`。这不否定主网格坐标点是直接求值的事实。
- 图件完整性、CSV、HTML 本地链接、隐私扫描、XDMF 结构和三组 HDF5 抽层复读均通过。
- 三个离线 3D HTML 均用断网的 Microsoft Edge 实际渲染成功；不是只做 XML/HTML 解析。

## 图件怎么看

- `previews/`：汇报用二维切片和三维正交切片体视。三维图使用 5 个保存的 xy 层与 x=0 yz 剖面，x/y 仅裁剪显示至 ±400 nm；主网格未重采样、未插值放大，彩色切片不是颗粒表面。
- `figures/F1_geometry_method/`：几何、界面和传播约定。
- `figures/F2_xy_slices/`：九层 xy 切片。`common` 使用跨粒径共同色标，用于比较；`shape` 使用单数据体归一化，用于看形态。30 nm 在共同色标下较弱是量级差异，不是缺数据。
- `figures/F3_sections/`：xz/yz 纵剖面；入口为 `figures/F3_sections/index.html`。
- `figures/F4_axial/`：轴上 CSV 对应的轴向曲线与分量。
- `figures/F5_decomposition/`：zeta=0 的 `I_ref`、`I_scat`、`J`、`I_total` 分解；入口为 `figures/F5_decomposition/index.html`。
- `figures/F6_3d_static/`：真实 3D 体素静态概览；入口为 `figures/F6_3d_static/index.html`。可旋转离线视图位于 `views3d/D030|D100|D200_signed_interference_3d.html`。
- `figures/F7_long_range/`：±3 μm 诊断曲线，并标出 ±170 nm 主窗口。它是诊断，不是主三维数据体。
- `tables/axis_D*.csv`、`tables/metrics.csv`：由同一 HDF5 复读生成的曲线与指标。
- `views3d/*.xdmf`：引用 `data/*/cube.h5` 的三维查看文件。

球形只描述颗粒几何。三维汇报图的彩色体视由保存网格的正交切片构成，不是颗粒表面；显示裁剪不改变 171×241×241 主网格，也没有插值放大。`views3d` 中的离线等值面视图同样不要求呈球形。

## 明确的未完成/未认证项

| 项目 | 状态 | 说明 |
|---|---|---|
| 论文整条 S3 Jones 链逐矩阵认证 | UNVERIFIED | 已做基映射和直接 3D 投影代数；未取得论文全部中间矩阵 |
| 超临界角球—界面物理 | UNVERIFIED | 只有均匀球远场 Mie/Fresnel 解析延拓与数值稳定性证据 |
| 相对复振幅/绝对对比度 | UNVERIFIED / false | `gamma` 是演示约定；无实验标定 |
| 出版社最终排版 PDF | NOT OBTAINED | 无机构访问；只核对了 Figshare v3 补充材料与 arXiv 预印本 |
| 样品空间近场 | false | 交付的是像面 through-focus 响应 |
| 双线性 0.1% 显示插值 | FAILED（保留） | 实测约 0.15%–0.24%；三次插值通过 |

## 复算入口

```powershell
python -m unittest discover -s code/package_v4/tests -v
python -m unittest discover -s code/solver/tests -v
python code/solver/tools/numerical_audit.py --config code/solver/configs/target_Fe3O4_NA145.json
python code/package_v4/tools/audit_final_tree.py --results .
python code/package_v4/tools/render_html_final.py --results .
python code/package_v4/tools/verify_results_bundle.py --help
```

审计脚本使用交付树相对路径；完整数据包约 1.3 GB（含三份 HDF5）；轻量包明确标注 `LIGHT_NO_HDF5`，不含主 HDF5，只含图件、代码、表格、验证记录、日志和离线网页。两包的 ZIP/SHA/成员数在包外 `package_verification.json` 记录。

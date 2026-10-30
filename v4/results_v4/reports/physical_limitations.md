# 物理边界与未认证项（必读）

本文件是本次交付的**硬边界**。任何汇报、摘要、图注都不得越过这里列的界线。

```text
result_class=CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
formula_fidelity=UNVERIFIED
full_jones_chain=UNVERIFIED
high_na_model_validation=UNVERIFIED
paper_convention_checks=UNVERIFIED
absolute_calibration=false
sample_space_near_field=false
publisher_typeset_pdf=NOT_OBTAINED
linear_midpoint_reconstruction=FAILED_KEPT
```

## 1 这是什么，不是什么

- **是**：按论文"表面附着单球 iSCAT"建模思路实现的候选前向模型，输出的像面 through-focus 强度响应，三组主网格完整、可复算、逐层核验过。
- **不是**：论文的严格复现；不是完整 Jones 链认证；不是高 NA 物理认证；不是绝对强度标定；不是样品空间近场场分布；不是实验数据拟合。

## 2 逐项说明

| 事项 | 状态 | 为什么 |
|---|---|---|
| 公式保真度 | `UNVERIFIED` | 出版社最终排版 PDF 未取得；只核对了 Figshare v3 补充材料与 arXiv 预印本 |
| 完整 S3 Jones 链 | `UNVERIFIED` | 只闭合了 `S2/S4/S5 → S6` 的标量代数与基映射，未取得论文全部中间矩阵做逐矩阵乘法验证 |
| 高 NA 模型 | `UNVERIFIED` | NA=1.45 > ns=1.33，超临界扇区用 `Im(kz)≥0` 解析延拓；未与球—界面全波解比对 |
| 论文符号约定核对 | `UNVERIFIED` | S6 的 `S2` 项符号与候选实现不同，差异已留档但未获作者/排版版确认 |
| 绝对标定 | `false` | `gamma=0.5+0i` 是演示约定；输出为"相对共享轴上参考"的无量纲场，无 V/m 或 W/m² |
| 样品空间近场 | `false` | 交付的是像面 through-focus 响应；`zeta` 是焦点扫描量 |
| 出版社排版 PDF | `NOT_OBTAINED` | 无机构访问权限（DOI 10.1364/OE.480337） |
| 双线性 0.1% 显示插值 | `FAILED_KEPT` | 实测 0.15%–0.21%，未改门槛、未删除记录；三次插值 1e-5 通过 |

## 3 与论文印刷式的已知差异（唯一结构性偏离）

补充材料 S6/S13 印刷为 `i(S2·t_p + S1·t_s)`。由于后向散射恒有 `S2(π) = -S1(π)`，且正入射 `t_p = t_s`，逐字实现会把**任何**粒子的轴上后向散射场整体消掉（纯电偶极子极限：印刷式和为 0，链式差为 3.0）。

候选实现因此取 `i(S1·t_s − S2·t_p)`，并用返回光 p 基下的直接 3D 投影独立核对（`validation/jones_chain_numbers.json`，5 条光线 `core/chain = 0.5+0j` 恒定）。

**这意味着**：本实现与印刷式**不是逐字一致**，而是"物理自洽的候选修正"。这一条必须在任何对外材料里如实说明。

## 4 超临界角：为什么仍是 UNVERIFIED

`u ∈ (1.33, 1.45]` 共 256 个求积点落在超临界扇区。已核实的是**数值稳定性**：分支取 `Im(kz)≥0` 时场沿传播方向指数衰减（`test_branch_passive_decay`），高 NA 下无 NaN/Inf（`test_pupil_highNA_non_nan_and_branch`），求积 512/256→1024/512 相对 L2 约 `1e-8`。

未核实的是**物理正确性**：均匀球远场 Mie + Fresnel 的复角解析延拓，能否代表球—界面体系的超临界角谱。这需要全波（如球—平面界面的多散射/严格耦合波）解作对照，本轮未做。

## 5 允许与禁止的表述

| 可以说 | 不可以说 |
|---|---|
| "三种粒径的 through-focus 候选仿真数据已完整生成并逐层核验" | "已复现论文结果" |
| "后向角、返回光 p/s 基、γ 单次施加、S12/S13 方位符号已修复并有测试" | "Jones 链已认证" |
| "超临界角解析延拓数值稳定" | "高 NA 物理已验证" |
| "输出为相对共享参考的无量纲场" | "绝对对比度/强度已标定" |
| "双线性显示插值未达 0.1%，已保留失败" | "插值检查全部通过" |

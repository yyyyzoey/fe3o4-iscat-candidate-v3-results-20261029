# 公式与物理约定审计

状态：`formula_fidelity=UNVERIFIED`，`high_na_model_validation=UNVERIFIED`，`absolute_calibration=false`，结果类别 `CANDIDATE`。本文件记录已核对、已修补和仍未闭合的项目，不能把局部测试通过解释成完整物理认证。

## 1. 已核对的后向 Mie 角与返回光基

实现使用从入射 `+Z` 方向定义的 Mie 角：

`mu_back = -kz_s / n_s`

在纯电偶极后向 `theta=pi` 的标准 Mie 角函数满足 `S2=-S1`。返回光 p 基相对标准球坐标 `e_theta` 反向，因此候选实现使用：

`S2_return = -S2_Mie`

`S1` 在 s 基下不变。旧式 `S2*tp + S1*ts` 在 `tp=ts` 的电偶极后向会强制相消；候选 `0.5j*cs*(-S2*tp + S1*ts)` 则保留非零后向响应。

已通过的证据：

- `test_backscatter_returning_p_basis`；
- `test_pupil_candidate_uses_returning_p_basis`；
- `test_backward_spherical_basis_equals_p_s_basis`；
- legacy 相消例子记录：`S1=1.5`、`S2=-1.5`，旧组合实部为 0，返回 p 基组合实部为 3.0。

**边界**：这证明旧组合存在基约定错误并验证候选变换，不证明完整 QWP/PBS/Fresnel/lens 链已闭合。

## 2. Jones 链与 S6 的候选符号

指定 Figshare 补充第 6 页（印刷 Page 5 | 11）的 S2/S4/S5 给出：

- 参考光瞳：`1/2 i (r_p+r_s)` 乘固定空间矢量；
- Mie 散射在返回方向：p 分量 `-S2`，s 分量 `i S1`；
- 由线性 Jones 响应推得散射光瞳应与 `S1*ts - S2*tp` 成比例。

指定 PDF 的 S6 印刷式看起来是 `i(S2*tp + S1*ts)`。两者不是简单整体相位差：对纯电偶极后向，印刷组合会再次相消。

当前实现采用与 S2/S4/S5 链条一致的候选式 `0.5j*cs*(-S2*tp + S1*ts)`，并通过：

- `test_candidate_pupil_matches_chain_result`；
- `test_chain_consistent_s6_sign`；
- `test_literal_printed_S6_requires_contradictory_S2`；
- `test_rayleigh_backscatter_does_not_vanish`。

**未完成**：没有用独立的矩阵实现把 QWP、PBS、Fresnel、物镜和成像透镜的全部 Jones 矩阵逐项乘出并闭合。因此不能声称论文必然印错，也不能声称当前实现是完整出版公式的唯一正确解释。此项仍是正式 blocker `full_Jones_chain`。

## 3. S12/S13 方位项与 `Ex` 符号

指定补充 S12/S13 的第一分量是：

`+(1-\cos\theta_d) J_2(q) \sin(2\phi_d)`（参考/散射各自带相应强度因子）。

旧 `fields_at_slice` 写为负号。直接 φ 积分中，瞳面 `-\sin(2φ)` 与二阶 Bessel 的 `i²=-1` 共同给出正的整体符号。当前实现为：

`Ex = +A2 * sin2phi`，`Ey = A0 - A2 * cos2phi`。

通过的证据包括 `test_azimuthal_direct_integral_sign`、`test_reduced_RW_against_direct_phi`，以及不共享解析 Bessel 公式的方位直接积分。旧代码同时给参考场和散射场的 `Ex` 改号可能使部分标量强度看不出差异，因此不能只用旧强度测试判断该约定正确。

## 4. Mie 截断与独立特殊函数检查

- `mie_coefficients` 支持显式 `nmax`；默认值保持 `max(5, ceil(x+4x^(1/3)+2)+3)`。
- 30/100/200 nm 分别以默认阶数 8/10/12 与增加 10 阶的 18/20/22 比较，最大复振幅变化均为 0。
- 通过高精度 mpmath 半整数柱 Bessel oracle、Legendre 递推、Rayleigh 极限、被动/无损极限等测试。

这验证了当前 Mie 子问题的数值实现，不验证球—界面多次散射或高 NA 超临界物理。

## 5. Fresnel 与超临界高 NA

- 法向 Fresnel、s 偏振低于临界角能量关系已通过测试。
- NA=1.45 大于 `n_s=1.33`；`u=n_s` 两侧用显式积分点，临界扇区积分收敛检查通过。
- `u>n_s` 使用复 `k_z` 与 Mie 角函数解析延拓；这是候选解析延拓，不是经过独立基准验证的有限球—平面界面 Maxwell 解。
- 没有把超临界扇区暗中截断到 1.33，也没有降低 NA。数值收敛不能替代物理验证，因此状态保持 `high_na_model_validation=UNVERIFIED`，blocker 为 `supercritical_high_NA_physical_validation`。

## 6. 相对复振幅与绝对标定

保存的量是单位散射基：

- `E_scat_unit` 对应 `Cs/Cr=1` 的同一模型；
- `U=|Es_unit|²`；
- `Q=Er*·Es_unit` 的实部/虚部；
- 任意复 `gamma` 下 `I_total=I_ref+|gamma|²U+2Re(gamma Q)`。

默认 `gamma=0.5+0i` 只是为了让示例图和标量字段有连续的演示值。论文中的 `C_R`、`C_S` 和 Fresnel/Mie/光瞳量纲没有唯一确定该比值；没有用拟合、最小二乘或挑选最漂亮图形来固定它。因此 `absolute_calibration=false`，blocker 为 `relative_complex_amplitude`。

可做的敏感性分析是把统一 `gamma` 用于三个粒径后重算；不能用不同粒径分别调参后声称粒径趋势被验证。

## 7. 材料与数据语义

Fe₃O₄ 的 `n=2.3456`、`k=0.0926` 是 Querry 块体磁铁矿在 530–540 nm 的插值模型，不是用户颗粒测量值。当前实现是均匀、非磁性、单球的 Mie 远场加界面 Fresnel/高 NA 光瞳的候选模型：

- 没有球—界面多次散射；
- 没有磁光张量；
- 没有相机、背景杂光或布朗运动；
- 没有悬浮高度扫描；球心固定为 `D/2`。

保存数组是 `(zeta,y,x)` 的成像面 through-focus 响应；zeta 是相对焦点扫描量，不是样品空间近场坐标，也不是测得的景深。±170 nm 只是任务规定的固定采样窗口。

## 8. 审计矩阵

| 环节 | 证据 | 状态 |
|---|---|---|
| 后向 Mie 角与返回 p 基 | 基变换、电偶极、候选光瞳测试 | 候选修补通过 |
| S2/S4/S5→候选 S6 符号 | 独立线性代数测试 | 候选一致；完整链未闭合 |
| S12/S13 的 `Ex` 方位项 | 直接 φ 积分、补充页面目视核对 | 通过 |
| Fresnel 法向/低于临界 s | 单元测试 | 通过（范围有限） |
| 高 NA `u>n_s` | 临界积分收敛 | 数值检查通过；物理 `UNVERIFIED` |
| 相对复振幅 | 基底保存、γ 敏感性 | 参数化；绝对标定 false |
| 材料常数 | Querry 文件与配置 | 块体模型，不是样品实测 |
| 完整 QWP/PBS/lens Jones 链 | — | `UNVERIFIED` |

最终 release 的 `status.json` 必须保持 `formula_fidelity=UNVERIFIED`、`high_na_model_validation=UNVERIFIED`、`result_class=CANDIDATE`；不得因 31 项测试全部通过而改成 `VERIFIED` 或“严格论文复现”。

# 论文符号 → 标准 Mie → 代码变量：约定映射与逐项核对状态

本文件是 `status.json` 里 `paper_convention_checks=UNVERIFIED` 的具体展开：
**说清楚哪一步已经有了可复算的证据，哪一步仍然只是候选实现。**

- 交付类别：`CANDIDATE`（候选实现，不是严格复现，也不是物理认证）。
- 数据类别：像面 through-focus 响应 `F(x,y,zeta)`，**不是**样品空间近场电磁场。
- 时谐约定：`exp(-i omega t)`。

---

## 1 本次实际获取与核对的原文

| 来源 | 状态 | 字节 | 页数 | SHA256 |
|---|---|---:|---:|---|
| Figshare article 22047950 / file 52761698（`6288691.pdf`，补充材料 v3） | 已下载，哈希与任务书一致 | 2,821,576 | 12 | `62a60e71…ffbbfe` |
| arXiv 2209.14508（作者预印本，含补充） | 已下载 | 4,776,448 | 20 | `1e40105a…114358` |
| Optica 出版社最终排版 PDF（DOI 10.1364/OE.480337） | **未取得**（无机构访问权限） | — | — | — |

本次用 `pypdf` 抽取全文、`pypdfium2` 以 2.5× 渲染被引用的页面，并逐页目视核对：

- `sources/pages/supplement_idx04.png`（印刷页 4/11）：S3、S4、S5、S6、S7
- `sources/pages/supplement_idx05.png`（印刷页 5/11）：S8–S13
- `sources/pages/supplement_idx06.png`（印刷页 6/11）：后续推导
- `sources/pages/preprint_idx03.png`（预印本第 4 页）：正文 (6)–(11)

机读记录：`sources/source_check.json`；纯文本：`sources/*_text.txt`。

**不能声称**：与出版社排版版逐式一致。补充材料的版本以 Figshare v3 为准。

---

## 2 符号映射表

| 论文符号 | 物理含义 | 标准 Mie 符号 | 本代码变量 |
|---|---|---|---|
| `S1(θ)` | 垂直（s）散射振幅 | `S1(mu)`，`mu=cosθ` | `mie_S1_S2(...)` 第 1 返回值 |
| `S2(θ)` | 平行（p）散射振幅 | `S2(mu)` | `mie_S1_S2(...)` 第 2 返回值 |
| `π_n, τ_n` | 角函数 | `π_n=P_n^1/sinθ`, `τ_n=dP_n^1/dθ` | `mie_S1_S2` 内递推 |
| `a_n, b_n` | Mie 系数 | 电/磁多极 | `mie_coefficients(x, m)` |
| `E_Sθ, E_Sφ` | 球坐标散射场分量 | `S2`、`S1` 组合（S4/S5） | `e_s = e^{iφ_s}(S2 e_θ + i S1 e_φ)` |
| `e_θ, e_φ` | 球坐标单位基 | 由方向 `(θ_s,φ_s)` 定义 | 测试内显式构造 |
| `p̂, ŝ` | 返回光 p/s 基 | `p̂ = ŝ × k_in`，`ŝ = (-sinφ, cosφ, 0)` | 测试内显式构造 |
| `t_p, t_s` | **样品→玻璃（返回光）**透射系数；正入射 `2·1.33/(1.33+1.52)=0.9333333` | Fresnel 振幅 | `fresnel_glass_sample(...)` → `tp, ts` |
| `r_p, r_s` | 玻璃—水界面反射 | Fresnel 振幅 | 同上 → `rp, rs` |
| `u = n_i sinθ` | 瞳面变量 | — | `quadrature_u(...)` |
| `M` | 有效放大率 170 | — | `op['M']` |
| `θ_d, φ_d` | 像面/检测极角、方位角 | — | `cos_td`、`geo['sin2']`、`geo['cos2']` |
| `Λ_OPD`, `Λ_OPD,ref` | 光程差 | 正文 (8)(9)(10) | `axial_opd_nm(...)` |
| `C_R, C_S` | 参考/散射总前因子 | 论文符号含收集效率 `η`（可选模型约定） | 生产路径设 `cs_over_cr=1.0`，即 `cr=cs=1`；`E_scat_unit` 不含 `η`，随后 `E_scat=γ·E_scat_unit`，`γ=0.5+0i` |
| `γ` | 相对复振幅 | 文献未唯一定义 | `gamma_real=0.5, gamma_imag=0.0` |

### 后向散射角

入射沿 `+z` 传播（玻璃→水），收集光沿 `-k_in` 返回。代码取

```
kz_s = sqrt(ns^2 - u^2)，分支 Im(kz_s) >= 0        # _complex_sqrt_positive_imag
mu_back = -kz_s / ns                                # 后向 Mie 角
```

即 `θ=π` 对应 `mu=-1`；`u>ns` 时 `kz_s` 纯虚，`mu` 变为复数（解析延拓）。

---

## 3 印刷式与候选实现的差异

补充材料印刷（已目视确认）：

```
S3 : E_∞ = R_z^{-1}(φ) L(θd) R_z(φ) P(0°) W(90°,45°) R_z^{-1}(φ) F_T E_S
S6 : E_S,∞ = C_S · i ( S2 t_p + S1 t_s ) · [ -(1-cosθd) cosφ sinφ ; cos²φ + sin²φ cosθd ]
S12: E_a,ref  ∝ (1/2) C_R i (r_p + r_s) [ (1-cosθd) J2 sin2φd ; (1+cosθd) J0 - (1-cosθd) J2 cos2φd ]
S13: E_a,scat ∝ (1/2) C_S i ( S2 t_p + S1 t_s ) · 同一空间向量
```

候选实现（`src/iscat_core.py::pupil_precompute`）：

```python
eta = asin(min(NA/n_s, 1.0))/pi            # optional collection convention; 0.5 here
cr, cs = 1.0, op.get('cs_over_cr', eta)    # fallback only
# run_dataset production override before pupil_precompute:
op['cs_over_cr'] = 1.0                      # therefore cr = cs = 1
ref_strength  = 0.5j * cr * (r_p + r_s)
scat_strength = 0.5j * cs * (-S2*tp + S1*ts)   # = 0.5j*(S1*ts - S2*tp)
```

生产路径中 `cs_over_cr=1.0`，所以 `E_scat_unit` 不含 `eta`。差异 **只在 `S2 t_p` 的符号**。这不是"把论文改成自己的答案"，而是把 S6 与 S2/S4/S5
在**返回光 p 基**下的线性链做一致性检查后得到的候选：S6 的括注说明 `t_p, t_s` 是
"glass–water interface" 的透射系数，而 S3 的 `F_T` 作用在返回光上，返回光的 `p̂`
相对入射光的 `p̂` 反向，故 `p` 分量的系数整体多一个负号；`s` 分量不受影响。

---

## 4 直接数值证据（本次实跑，`jones_chain_numbers.json`）

Fe₃O₄、D=100 nm、λ=532 nm、n_s=1.33、NA=1.45，`x=π n_s D/λ=0.785`。
对 5 条显式瞳面光线，把 S4/S5 的三维 Mie 场**投影**到返回光的 `(p̂, ŝ)` 基，
再与两种标量比较（数值单位：无量纲复振幅）：

| θ (deg) | φ (deg) | S1 | S2 | 印刷式 `i(S2 t_p+S1 t_s)` | 链式 `i(S1 t_s-S2 t_p)` | core/chain |
|---:|---:|---|---|---|---|---|
| 0 | 0 | +0.0410−0.1696j | −0.0410+0.1696j | **−2.8e−17 − 6.9e−18j** | +3.1661e−01+7.6545e−02j | 0.5+0j |
| 30 | 0 | +0.0415−0.1737j | −0.0353+0.1477j | +2.3423e−02+5.5851e−03j | +2.9433e−01+7.0374e−02j | 0.5+0j |
| 30 | 65 | 同上 | 同上 | 同上 | 同上 | 0.5+0j |
| 60 | −40 | +0.0430−0.1851j | −0.0196+0.0843j | +7.9755e−02+1.8513e−02j | +2.1748e−01+5.0471e−02j | 0.5+0j |
| 75 | 120 | +0.0439−0.1929j | −0.0090+0.0395j | +9.0198e−02+2.0575e−02j | +1.3943e−01+3.1738e−02j | 0.5+0j |

两点读数：

1. **`core/chain` 在全部 5 条光线上恒为 `0.5+0j`**。这里为隔离标量代数，直接审计脚本
   临时设 `cs_over_cr=1`，所以这个 `0.5` 是 S13 的 `(1/2)·i` 前因子，不是 `η`。
   生产路径 `run_dataset.py` 同样显式设 `op['cs_over_cr']=1.0`，因此保存的
   `E_scat_unit` **不含 `η`**；分解阶段再施加演示相对复振幅 `γ=0.5+0i`：
   `E_scat=γ·E_scat_unit`，`I_scat=|γ|²U=0.25U`，`I_cross=2Re(γQ)`；`γ=0.5+0i` 只在分解阶段施加一次。
   `η=0.5` 只作为论文符号下的可选收集效率约定出现在讨论中，不进入生产 cube。
   方位角从 0° 变到 120°，`S1,S2` 不变（轴对称），符合球对称性。
2. **θ=0（沿光轴返回）时印刷式的值恰好为 0（2.8e−17 为浮点零）**。这是结构性的：
   后向散射恒有 `S2(θ=π) = -S1(θ=π)`，而正入射处 `t_p = t_s`，于是
   `S2 t_p + S1 t_s ≡ 0`。逐字实现的 S6 会把**任何**粒子的正后向散射场整体消掉。

纯电偶极子（`a_1=1, b_1=0`）极限把同一件事放到解析层面：

```
S1 = +1.5,  S2 = -1.5
|印刷式和| = 0.0        （完全相消）
|链式差|   = 3.0        （非零，符合电偶极后向散射不为零）
```

**这条证据的边界**：它闭合的是 `S2/S4/S5 → S6` 的标量代数（假设 Fresnel 透射对 p/s
分量独立作用）。它**不是**对 S3 整条矩阵链的逐矩阵验证。

---

## 5 方位角 `S12/S13` 的 `J2 sin2φ` 符号

印刷式第一分量是 `+(1-cosθd) J2(q) sin(2φd)`。旧代码写成负号。候选改为正号。

验证方式：不走解析 Bessel 恒等式，直接对 `φ` 做数值积分得到瞳面 `Ex`，与降维结果比较——
`tests/test_handoff.py::test_azimuthal_direct_integral_sign` 与
`test_reduced_RW_against_direct_phi` 均通过（直接积分与降维积分的 Er、Es 复振幅分别比较，
不使用强参考场作分母掩盖弱散射场误差）。

---

## 6 超临界角的处理与它为什么仍是 UNVERIFIED

NA=1.45 > n_s=1.33，因此 `u ∈ (1.33, 1.45]` 有 256 个求积点落在超临界扇区
（`critical_quadrature`: below=512, above=256）。该扇区内 `kz_s` 纯虚，`mu_back` 为复数，
Mie 角函数在复角上解析延拓，Fresnel 系数同样延拓。

已核实：分支取 `Im(kz)>=0` 使场沿传播方向指数衰减而非增长
（`test_branch_passive_decay`）；高 NA 下无 NaN/Inf（`test_pupil_highNA_non_nan_and_branch`）；
求积加密 512/256→1024/512 的相对 L2 误差量级 1e−8（见 `numerical_audit.json`）。

未核实：均匀球远场 Mie + Fresnel 解析延拓能否代表**球—界面**体系的超临界角谱。
cube 属性写作 `supercritical_sector=ANALYTIC_CONTINUATION_UNVALIDATED`，
`high_na_model_validation=UNVERIFIED` 保持不动。

---

## 7 相对复振幅与绝对标定

- 所有 cube 共享同一个参考场尺度 `reference_field_scale = 9.422632737507974e-08`
  （轴上 `max|E_ref|`），三组可跨粒径直接比较。
- 生产 cube 设 `C_R=C_S=1`（`run_dataset.py` 中 `op['cs_over_cr']=1.0`），
  保存的 `E_scat_unit` **不含 `η`**；分解阶段再施加演示相对复振幅 `γ = 0.5 + 0i`：
  `E_scat = γ·E_scat_unit`，`I_scat = |γ|²·U`，`I_cross = 2 Re(γ Q)`。
- 论文符号中的收集效率 `η=0.5` 是**可选模型约定**，没有被再乘进 `E_scat_unit`，
  因此不存在 `η·γ=0.25` 的“场幅”乘积；`|γ|²=0.25` 是强度因子，不是场幅因子。
- `γ` 是**演示约定**，不是 Fe₃O₄ 的标定对比度。文献只说明 `C_S` 含 `η`，
  推不出 `C_S/C_R = η`，也定不出全部相对复相位。
- `absolute_calibration=false`；`units` 属性写的是"相对共享轴上参考的无量纲场，无 V/m 或 W/m²"。

---

## 8 对比度定义与正文 (11)

正文 (11)：`I_sim = (|E_R|² + 2|E_R||E_S| cosΦ) / |E_R|²`。

本代码保留复数场，因此 `Φ` 不是独立参数，而是逐体素的相对相位：

```
I_ref   = |E_r|²
I_scat  = |γ|² |E_s,unit|²
I_cross = 2 Re(γ Q),  Q = conj(E_r) · E_s,unit        # 即 2|E_r||γE_s| cosΦ
I_total = |E_r + γE_s,unit|²  ≡  I_ref + I_scat + I_cross
contrast_local            = (I_scat + I_cross) / I_ref     ，仅 I_ref > 1e-12
contrast_fixed_reference  =  I_scat + I_cross              （固定参考归一化）
```

`I_total = I_ref + I_scat + I_cross` 在磁盘复读数据上逐层被重新验证（`test_saved_algebra`
与 `validation/data_hdf5_check.json`）。`I_ref > 1e-12` 与 `I_ref >= 0.005` 是**数值掩膜**，
不是物理遮挡；掩膜比例记录在 cube 的 `masks/` 与 `data_audit.json` 中。

---

## 9 仍未核实（保持原样，不写成 PASSED）

| 项目 | 状态 | 缺什么 |
|---|---|---|
| S3 整条 QWP/PBS/Fresnel/物镜/镜筒透镜 Jones 链逐矩阵 | UNVERIFIED | 论文未给出中间矩阵；本轮只做了标量代数和 3D 投影 |
| 超临界角（u>1.33）的物理正确性 | UNVERIFIED | 需要球—界面全波解或独立近场方法 |
| 相对复振幅 / 绝对对比度 | UNVERIFIED | 需要实验标定或仪器参数 |
| 出版社排版版逐式一致 | UNVERIFIED | 未取得最终排版 PDF |
| 双线性中点插值 0.1% | **FAILED（保留）** | 10 nm 主网格上双线性重建相对误差 ~0.2%；三次插值 <1e−5 |

最后一项是有意保留的失败记录：主网格的 10 nm 坐标值是直接求值，不是插值放大；
但"用双线性从 20 nm 恢复 10 nm 网格"达不到 0.1%，该检查不通过且不改阈值，
详见 `numerical_audit.json` 的 `horizontal_10nm_vs_direct_5nm_midpoint`。

---

## 10 复算方法

```bash
python -m unittest discover -s tests -v                      # 31 项光学/IO 测试
python tools/numerical_audit.py --config configs/target_Fe3O4_NA145.json
python ../../build/audit_deliverables.py                     # 交付树只读审计
python ../../build/render_html_audit.py                      # 断网渲染三张 HTML
```

代码与配置的规范化哈希写在 `provenance/run_identity.json`：
`config_sha256=01e910c0…7815`、`implementation_sha256=1a170ab6…46c6`（已从归档源码复算一致）。

# Fe₃O₄ 表面附着单球 iSCAT 最终执行审查

生成时间：2026-10-29（UTC 执行记录）；结果类别：`CANDIDATE`。

## 1. 结论摘要

- 主数据生成：`COMPLETE`。30、100、200 nm 三组均实际完成 171 层，shape 均为 `[171, 241, 241]`。
- 数值验证：`PARTIAL`。角积分、正式 512/256→1024/512、径向 1601→3201、径向直接求值、轴向 1 nm 中点、Mie 增阶和临界扇区积分均通过；横向 10→5 nm 的双线性中点重建未达到 `1e-3` 门槛。因此不能把本轮写成“全部数值验收通过”。
- 来源版本：`VERIFIED`，仅指用户指定 Figshare 文件 `52761698` 已真实下载、校验并按页面核对；出版社最终排版 PDF 未取得。
- 公式保真度：`UNVERIFIED`。后向 Mie 角、返回光 p/s 基和补充 S12/S13 方位项已做候选修补与一致性测试，但完整 QWP/PBS/Fresnel/lens Jones 链没有独立闭合。
- 高 NA：`UNVERIFIED`。`u>n_s` 扇区使用解析延拓；临界扇区积分收敛不等于有限球—界面 Maxwell 物理已认证。
- 绝对标定：`false`。`gamma=0.5+0i` 是演示约定，不是 Fe₃O₄ 样品实测的相对复振幅。
- 数据语义：保存的是 `(zeta,y,x)` through-focus 成像响应，不是样品空间电磁场。

## 2. 固定任务范围

| 项目 | 实际值 |
|---|---|
| 波长 | 532 nm |
| 目标 NA | 1.45（实际积分上限 1.45） |
| 样品介质 | 水，`n_s=1.33` |
| 粒径 | 30、100、200 nm |
| 单球几何 | 球心高度 `D/2`，即 15、50、100 nm；表面间隙 0 nm |
| through-focus 轴 | `zeta=-170:2:170 nm`，171 层 |
| 横向网格 | `x,y=-1200:10:1200 nm`，每轴 241 点 |
| 数组顺序 | `(zeta,y,x)`；复场最后维为 `(Ex,Ey)` |
| 禁止项 | 未引入 520 nm、400 Hz、布朗运动、相机或悬浮高度扫描 |

三组主数据均由配置规定的完整网格直接求值，不是 pilot 插值放大，也没有降低 NA 或缩减主网格。

## 3. 正式 HDF5 结果

| D (nm) | 文件（相对 `full/`） | shape | 实际读取层数 | 字节数 | SHA256 |
|---:|---|---|---:|---:|---|
| 30 | `D030nm/cube.h5` | `[171,241,241]` | 171 | 424,882,738 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 | `D100nm/cube.h5` | `[171,241,241]` | 171 | 424,639,674 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 | `D200nm/cube.h5` | `[171,241,241]` | 171 | 424,913,287 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

`full/run_summary.json` 的 `dataset_complete=true`；`diameters_nm=[30,100,200]`、`NA_requested=NA_integrated=1.45`。三组共享同一个实正参考场尺度（`9.422632737507974e-08`），没有逐粒径或逐层重新归一化。

## 4. 最终实现中的关键修补

### 4.1 交接候选中的公式修补（本轮通过测试与审计保留）

1. **后向 Mie 的返回光 p 基**：Mie 角仍从入射 `+Z` 方向定义，使用 `mu_back=-kz_s/n_s`；返回光 p 基相对标准 Mie `e_theta` 反向，因此实现采用 `S2_return=-S2_Mie`。旧式 `S2*tp + S1*ts` 在纯电偶极后向会出现非物理相消。当前候选散射强度为 `0.5j*cs*(-S2*tp + S1*ts)`。
2. **Jones 链候选符号**：由补充 S2、S4、S5 的线性响应可推得 `S1*ts - S2*tp`；补充 S6 的印刷式看起来是 `S1*ts + S2*tp`。本实现采用与 S2/S4/S5 链条一致的候选式，但因为没有把未印刷的完整 QWP/PBS/Fresnel/lens 链逐矩阵独立闭合，**不宣称论文公式必然错误，也不宣称完整 Jones 链已认证**。
3. **S12/S13 的 `Ex` 方位项**：直接 φ 积分及补充 S12/S13 都要求 `Ex` 中的 `(1-\cos\theta_d) J_2(q) \sin(2\phi_d)` 为正号；`fields_at_slice` 已由旧负号改为正号。`Ey=A0-A2\cos2phi` 保持原结构。
4. **Mie 截断可控**：`mie_coefficients` 增加可选 `nmax` 参数，便于独立增加阶数做复振幅收敛审计；默认截断策略不变。

### 4.2 本轮实际修复的工具问题

1. `tools/fetch_sources.py`：修正公开 Figshare 下载处理。第一次抓取留下了真实失败日志；修复后通过 `https://ndownloader.figshare.com/files/52761698` 获取 HTTP 200、`application/pdf` 的指定文件。
2. `tools/numerical_audit.py`：修正 Mie 阶数指标的实现错误，使“增加 10 阶后的最大复振幅变化”按实际两个截断计算，而不是误报。
3. `src/run_dataset.py`：移除仅允许 `material_name='Fe3O4'` 的硬编码拒绝，使论文参数控制组能够运行；目标组仍由配置与测试锁定为 Fe₃O₄、532 nm、NA 1.45 和固定主网格。

交接 manifest 共 72 项：70 项哈希不变，本轮发生哈希变化的文件仅为 `tools/fetch_sources.py` 与 `tools/numerical_audit.py`；`legacy/` 全部未改。

## 5. 测试与环境

- 现行测试：31/31 `OK`，重复复跑 `EXIT=0`。日志：`results/execution_20261029/logs/final_recheck_tests.stdout.txt`。
- Legacy 测试：7/7 `OK`，重复复跑 `EXIT=0`。日志：`results/execution_20261029/logs/final_recheck_legacy.stdout.txt`。
- Python 3.11.7；numpy 2.3.5、scipy 1.17.0、h5py 3.15.1、matplotlib 3.10.8、mpmath 1.3.0。
- 离线 preflight 通过，manifest 72 项校验通过。
- 没有删除、跳过或修改测试来掩盖失败；`validate_cube` 容差未放宽。

## 6. 数值收敛与独立检查

### 6.1 通过的检查

| 检查 | 30 nm (L2 / L∞) | 100 nm (L2 / L∞) | 200 nm (L2 / L∞) | 状态 |
|---|---:|---:|---:|---|
| 正式角积分 512/256→1024/512 | 2.946e-8 / 1.456e-8 | 1.856e-8 / 9.408e-9 | 3.040e-8 / 1.673e-8 | PASS |
| 径向 1601→3201 | 1.476e-5 / 1.001e-5 | 1.165e-5 / 7.980e-6 | 1.590e-5 / 1.125e-5 | PASS |
| 轴向 2 nm 中点 vs 1 nm 直接值 | 6.442e-4 / 6.445e-4 | 5.574e-4 / 4.920e-4 | 5.271e-4 / 6.172e-4 | PASS |

另通过：128/64→256/128→512/256 连续角加密；径向插值 vs 直接求值；Mie 额外增加 10 阶后复振幅变化为 0；`u=n_s` 两侧显式积分点检查。上述均是对当前候选模型数值实现的收敛检查，不是物理认证。

### 6.2 未通过的附加检查

横向 10 nm 采样与 5 nm 直接求值中点比较，双线性重建超过 `1e-3`：

| D (nm) | 双线性 L2 | 双线性 L∞ | 三次重建 L2 / L∞ |
|---:|---:|---:|---:|
| 30 | 1.955e-3 | 2.133e-3 | 6.494e-6 / 1.043e-5 |
| 100 | 1.543e-3 | 1.699e-3 | 4.742e-6 / 7.597e-6 |
| 200 | 2.159e-3 | 2.399e-3 | 7.505e-6 / 1.260e-5 |

三次重建通过说明结构可由当前采样表达，但这不能撤销双线性失败。该失败限制“用双线性插值重建更细横向结构”的声明；保存的 10 nm 体素本身就是直接求值结果，主数据没有用插值替代。综合状态因此是 `numerical_validation=PARTIAL`，`strict_all_including_linear_reconstruction=false`。

## 7. 保存后 HDF5 逐层复读验收

`diagnostics/full_validation.json` 与 `diagnostics/saved_cube_audit.json` 均为 `data_checks_pass=true`。以 `audit_saved_cubes.py` 对三个 cube 逐层读取，结果：

- 三组均为 171 层、每层 `241×241`，`completed_slices_attr=171`；
- `zeta=0` 层存在，坐标精确；
- 定义区域外没有非预期 NaN/Inf；
- `I_ref`、`I_scat`、`I_total` 无非负强度负值；
- `contrast_local` 仅在数学未定义处为 NaN；
- 掩膜与保存阈值一致；共享参考尺度为真；
- 最大保存强度恒等式归一化残差约 `1.192e-7`，低于 `1e-5`；
- 13 项 manifest 逐项校验通过；三组文件 SHA256 与 manifest 一致。

逐层读取和复验使用的完整日志位于 `results/execution_20261029/logs/`，最终报告后还会对 release 副本再做一次同样的复读。

## 8. 长程诊断、图与 XDMF

- 目标组长程诊断：`diagnostics/target_long/`，D030/D100/D200，zeta 范围 `±3000 nm`、步长 10 nm，横向 `±1200 nm`、步长 20 nm。
- 论文参数控制组：`diagnostics/paper_control_long/`，D120、NA=1.35，同一长程 zeta/横向诊断范围。
- 两组都明确标注 `kind=diagnostic_sections_not_final_3d` 和 `status=CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`；它们不是主 3D 数据。
- `figures/` 中共 16 个 PNG（每粒径 xz、yz、zeta=-170/0/+170 的 xy 截面，以及三粒径轴向曲线），`diagnostics/figure_audit.json` 为 PASS，所有图从保存的 HDF5 读取。
- 三个 XDMF 为 `full/D030_focus_stack.xdmf`、`D100_focus_stack.xdmf`、`D200_focus_stack.xdmf`；结构审计 `diagnostics/xdmf_audit.json` 为 PASS，维度为 `171 241 241`，第三轴明确是 zeta 离焦量，HDF5 相对路径可解析。
- **没有用 ParaView 打开过这些 XDMF**；本报告只声明 XML/HDF5 结构审计通过，不声明 GUI 可视化验收。

## 9. 数据能做什么、不能做什么

可以做：在明确候选模型下比较 30/100/200 nm 的 through-focus 强度、干涉项、复场基和固定参考归一化图；读取任意层做截面；用保存的 `U`、`Q_real`、`Q_imag` 重新计算任意假设 `gamma` 下的信号；做进一步数值和模型敏感性研究。

不能做：不能把这些文件称为严格论文复现、实验绝对对比度、样品空间三维近场、已认证的球—界面全波解，或用它们直接反演真实 Fe₃O₄ 粒径。`gamma` 未标定；Fe₃O₄ 的块体折射率只是材料模型，不是用户样品实测。

## 10. 历史状态说明

`full/run_summary.json` 的 `open_gates` 里保留了 `published_supplement_version`，`full/config_used.json` 的 `source.version_difference_audit` 也保留了交接时的旧文字。这些是冻结的历史运行记录，不应回写；本轮的 `source_audit.md` 和 `diagnostics/sources_retrieval/retrieval_report.json` 才是指定 Figshare 文件的真实获取证据。`docs/SOURCES.md` 和 `docs/FORMULA_AUDIT.md` 中“下载失败”的描述同样是交接时状态，不是本轮最终状态。

## 11. 证据索引

- `diagnostics/tests.json`、`diagnostics/convergence.json`、`diagnostics/numerical_audit.json`
- `diagnostics/full_validation.json`、`diagnostics/saved_cube_audit.json`
- `diagnostics/sources_retrieval/retrieval_report.json`
- `diagnostics/figure_audit.json`、`diagnostics/xdmf_audit.json`
- `diagnostics/target_long/`、`diagnostics/paper_control_long/`
- `results/execution_20261029/logs/`

# 验收条件与诚实状态

## A. 必须满足的任务条件

三种直径均为30/100/200 nm；球心高度D/2；NA实际积分上限1.45；波长532 nm；无多球/运动/背景/相机。每组主结果必须171层、每层241×241，zeta±170、步长2，横向±1200、步长10。粒径顺序不影响任何结果。

## B. 数值验收

| 检查 | 建议门槛/要求 | 交接时状态 |
|---|---|---|
| 全部21项现行测试 | 不跳过、不删除、通过 | 已实跑通过 |
| 原版已知问题回归 | 记录原版抵消及Ex差异，不把旧版当金标准 | 已分析；证据脚本可复现 |
| Mie独立高精度 | 对应项rtol1e-8/atol1e-14 | 已通过 |
| Mie额外截断阶数 | 加阶后非零复振幅变化<1e-6 | Codex补做 |
| 被动/无损极限 | Qext-Qsca非负；无损近0；只适用于均匀介质Mie子问题 | 已通过 |
| 全Jones链 | 独立未降维实现与简化表达式逐点一致 | 未完成 |
| 直接φ积分 vs Bessel降维 | 复场一致，非只强度 | 已通过 |
| 角积分128/64→256/128→512/256 | 每次L2和L∞≤1e-3 | 已通过 |
| 正式512/256→1024/512 | 含临界、轴上及离轴 | Codex补做 |
| 径向1601→3201与直接求值 | L2和L∞≤1e-3 | 801/1601已检；3201待补 |
| 轴向2nm中点 vs 1nm直接求值 | L2和L∞≤1e-3；不只比较重合网格点 | 已通过指定抽样 |
| 横向10nm中点 vs 5nm直接求值 | 两分量、多个zeta，L2和L∞≤1e-3 | Codex补做 |
| 高NA独立物理基准 | 给出来源、复场比较、适用近似；不是“没有NaN” | 未完成 |
| 保存后强度复算 | 稳定归一化误差≤1e-5；局部contrast≤1e-4 | 新pilot已通过 |
| float32对float64量化 | 误差明确记录，不把float32内恒等当双精度证明 | pilot已检查；full待运行 |
| 空粒子/折射率匹配 | 散射与干涉项为零 | 已通过子函数检查 |
| 复γ/相位翻转 | 只有相应交叉项变化，纯散射按|γ|²变化 | 已通过 |
| 全数据finite/非负/掩膜 | 只允许定义外contrast为NaN；其他不得NaN/Inf | 新pilot已通过 |
| 复现/续跑 | 输入/代码hash一致，换配置拒绝续跑 | 小网格已通过 |
| 半文件/损坏/单位错 | 不进入最终结果；错误退出非0 | 已有保护，Codex补破坏性测试 |
| 粒径顺序不变性 | D排序变化不改变共享尺度和单组结果 | Codex补做 |

以上容差是工程/数值阈值，不是论文宣称的精度，也不等于材料参数精度。

### 误差定义

对独立参考解B，`e2=||A-B||₂/max(||B||₂,eps)`，`e∞=max|A-B|/max(max|B|,eps)`。不在接近零的单像素使用无意义相对误差；同时报告绝对误差。不能任意对齐相位、逐层归一化、移动zeta再计算误差。零场限值使用绝对误差。

## C. 来源与物理认证不能由数值测试替代

- SOURCE：指定Figshare版本PDF已获取并检查，正文版本明确。
- FORMULA：Mie/p/s/Jones/OPD/RW约定一致且有独立证据。
- HIGH_NA：>ns部分得到与所声明近似相匹配的验证。
- AMPLITUDE：缺失的相对复振幅若尚未确定，保持参数化/未绝对标定；不能把γ默认值写成测量值。
- MATERIAL：块体Fe₃O₄常数只是材料模型，不能宣称是用户颗粒实测。

## D. 推荐status.json

```
{
  "task": "Fe3O4_surface_bound_three_diameter_through_focus",
  "data_generation": "COMPLETE | PARTIAL | FAILED",
  "numerical_validation": "PASS | FAIL | PARTIAL",
  "source_version_audit": "VERIFIED | UNVERIFIED",
  "formula_fidelity": "VERIFIED_WITH_DOCUMENTED_CONVENTIONS | UNVERIFIED",
  "high_na_model_validation": "VALIDATED_WITHIN_STATED_APPROXIMATION | UNVERIFIED",
  "absolute_calibration": false,
  "result_class": "CANDIDATE | NUMERICALLY_VALIDATED_MODEL_DATA",
  "target_shapes": {"30": [171,241,241], "100": [171,241,241], "200": [171,241,241]},
  "actual_shapes": {},
  "blockers": [],
  "evidence_paths": {}
}
```

这是结构示意，不是可以直接复制成最终状态的模板数据。最终不得保留含“|”的枚举说明；必须填真实单值。`NUMERICALLY_VALIDATED_MODEL_DATA`只表示所声明模型内验证，不代表实验定量标定、真实样品全波解或与原论文完全同参数。

## E. 不通过时

不要无限重复原命令。定位到源公式、模型近似、数值收敛、I/O或环境哪一类；保留失败输入和最小复现。无法解决时输出有明确限制的候选完整数据；无法生成某组则报告PARTIAL和实际完成层数。禁止为了“完成”降低精度、裁剪难点、用插值扩成主shape或用旧结果补数。

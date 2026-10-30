# 数据合同：HDF5 V3

## 每个文件

`D030nm/cube.h5`、`D100nm/cube.h5`、`D200nm/cube.h5`，分别只有一个粒子。

主结果数组顺序固定 `(Nz,Ny,Nx)=(171,241,241)`；向量复场分量放最后一维 `(Nz,Ny,Nx,2)`，顺序Ex,Ey。单位是统一参考场尺度下的无量纲值，**不标成V/m、W/m²或实验计数**。

## 坐标

- `coords/x_object_nm`：物方等效横向x，241点。
- `coords/y_object_nm`：物方等效横向y，241点。
- `coords/zeta_nm`：相对球心约定零点的焦点扫描，171点。
- `coords/oil_thickness_nm`：对应各层的实际油层厚度。

所有坐标float64，长度nm；零点和顺序明确。zeta既不是球心距玻璃的高度，也不是样品空间切片Z。

## 复场基底（float32分开存实部/虚部）

- `fields/E_ref_real`, `fields/E_ref_imag`
- `fields/E_scat_unit_real`, `fields/E_scat_unit_imag`

单位散射基由Cs/Cr=1的同一模型给出；实际示例场为 `E_scat=gamma*E_scat_unit`。gamma由文件属性中的real/imag共同给出。这样当相对振幅/相位进一步确定时，不必重新做三维积分。

参考归一化采用相同光学参数下参考场轴上幅值，三种粒径共享一个实正尺度；不能每粒径、每切片重新归一化。尺度写入文件属性。

## 标量信号

`signals/I_ref=Er*·Er`

`signals/I_scat=|gamma|² |Es_unit|²`

`signals/I_cross=2 Re[gamma (Er*·Es_unit)]`

`signals/I_total=|Er+gamma Es_unit|²`

`signals/contrast_local=(I_scat+I_cross)/I_ref`，仅在defined_contrast为真处定义，其余NaN。

`signals/contrast_fixed_reference=(I_scat+I_cross)/I_ref,0`；归一化后I_ref,0=1，因此代码直接存分子。**这不是逐像素论文对比度的另一个名字**，用于全图稳定显示、共用尺度比较。

所有量保留符号，尤其I_cross和两种contrast；仅I_ref/I_scat/I_total非负。

## 幅相参数化基底

- `basis/I_scat_unit=U`
- `basis/Q_real=Re(Er*·Es_unit)`
- `basis/Q_imag=Im(Er*·Es_unit)`

任意复γ=gr+i gi：

`I_cross=2(gr Q_real - gi Q_imag)`；`I_scat=(gr²+gi²)U`。

不得只保存实Q而丢掉相位。这个参数化不是绝对标定；主结果metadata必须说明γ是假设。

## 掩膜

- `masks/defined_contrast`：I_ref>1e-12，数值上可定义局部对比度。
- `masks/stable_reference`：I_ref>=0.005，显示/统计稳定区域。

uint8。显示屏蔽不改变原始强度/复场。局部contrast只在数学未定义处NaN，稳定区域以外仍保留可定义值，不任意裁剪。

## 元数据

至少包括：schema、status、diameter/radius/center_height/surface_gap、NA、wavelength、material、gamma实虚部、reference_field_scale、配置原文与SHA256、源码SHA256、时谐约定、轴/分量顺序、completed_slices、absolute_calibration=false、is_sample_space_field=false、超临界模型标记。

最终总status还必须把“数值数据完成”和“论文/物理验证完成”分开，不能依赖文件存在就输出PASS。

## 可重现与完整性

结果文件要能脱离作图程序，用本合同公式重新构造所有保存信号。浮点误差按ACCEPTANCE验收。图像必须从这些文件读取，而不是调用另外一个生成图的物理模型。任何HDF5字段改名/维度变更须提升schema版本并更新所有读者/测试。

XDMF只引用已有标量，不复制数据；它将zeta显示为第三轴，必须带“focus scan, not sample-space field”的说明。输出迁移时保证相对HDF5路径有效。

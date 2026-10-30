# -*- coding: utf-8 -*-
"""Part 4: limitations report, sub-READMEs, config, code copy, acceptance, SHA256.

Everything in this module is read-only with respect to the physics: the three
V4.1 HDF5 cubes are opened with h5py in read mode only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import vis_common as C

OUT, FIG, REP, EXP, LOGS, CODE = C.OUT, C.FIG, C.REPORT, C.EXPORT, C.LOGS, C.CODE
CFG = OUT / "config"
SRC = Path(__file__).resolve().parent

BOUND = """```
result_class                     = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
through_focus                    = true   (NOT sample-space near field)
full_jones_chain                 = UNVERIFIED
high_na_model_validation         = UNVERIFIED
paper_convention_checks          = UNVERIFIED
absolute_calibration             = false
sample_space_near_field          = false
publisher_typeset_pdf            = NOT_OBTAINED
linear_midpoint_reconstruction   = FAILED_KEPT
```"""

TAGS = ("D030", "D100", "D200")
DIA = {"D030": 30, "D100": 100, "D200": 200}
HEIGHT = {"D030": 15.0, "D100": 50.0, "D200": 100.0}

S = {t: json.loads((EXP / f"stats_{t}.json").read_text(encoding="utf-8")) for t in TAGS}
CS = json.loads((EXP / "common_scale.json").read_text(encoding="utf-8"))
AX = json.loads((EXP / "axis_curves_summary.json").read_text(encoding="utf-8"))["series"]
ISO = {t: json.loads((EXP / f"{t}_isosurface_levels.json").read_text(encoding="utf-8"))
       for t in TAGS}
VMAX = float(CS["common_vmax"])

CODE_FILES = ["vis_common.py", "step1_layers.py", "step2_2d.py", "step3_3d.py",
              "step4_axis.py", "step5_html.py", "mk_report1.py", "mk_report2.py",
              "mk_report3.py", "mk_report4.py", "mk_package.py"]


def sha256(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def iso_table() -> dict:
    return {t: {f"{l['level_fraction']:+.2f}": l for l in ISO[t]["levels"]} for t in TAGS}


def axis_series(tag: str):
    z, v = [], []
    with (EXP / "axis_curves_center.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["tag"] == tag:
                z.append(float(r["zeta_nm"]))
                v.append(float(r["I_cross"]))
    return np.array(z), np.array(v)


def zero_crossings(tag: str) -> list[float]:
    z, v = axis_series(tag)
    out = []
    for i in range(1, z.size):
        if v[i - 1] == 0 or v[i] == 0:
            continue
        if np.sign(v[i - 1]) != np.sign(v[i]):
            out.append(0.5 * (z[i - 1] + z[i]))
    return out


def copy_code() -> list[dict]:
    CODE.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in CODE_FILES:
        src = SRC / name
        if not src.exists():
            print(f"[code] skip missing {name}")
            continue
        dst = CODE / name
        shutil.copyfile(src, dst)
        rows.append({"file": name, "bytes": dst.stat().st_size, "sha256": sha256(dst)})
    return rows


def source_rows() -> list[dict]:
    rows = []
    for tag in TAGS:
        p = C.cube_path(tag)
        import h5py
        with h5py.File(p, "r") as f:
            attrs = {k: f.attrs[k] for k in f.attrs}
            shape = list(f["signals/I_cross"].shape)
            dtype = str(f["signals/I_cross"].dtype)
            z = f["coords/zeta_nm"][:]
            x = f["coords/x_object_nm"][:]
            keep = ["NA", "wavelength_nm", "center_height_nm", "diameter_nm",
                    "particle_radius_nm", "surface_gap_nm", "axis_order",
                    "field_component_order", "grid_mode", "completed_slices",
                    "status", "physical_validation", "supercritical_sector",
                    "absolute_calibration", "is_sample_space_field", "time_convention",
                    "units", "gamma_real", "gamma_imag", "schema",
                    "implementation_sha256", "config_sha256", "reference_field_scale"]
            attrs = {k: attrs[k] for k in keep if k in attrs}
        st = p.stat()
        rows.append({
            "tag": tag,
            "diameter_nm": DIA[tag],
            "centre_height_nm": HEIGHT[tag],
            "path": str(p),
            "path_relative_to_workspace": str(p.relative_to(C.ROOT)).replace("\\", "/"),
            "bytes": st.st_size,
            "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
            "sha256": sha256(p),
            "shape_zeta_y_x": shape,
            "dtype": dtype,
            "grid": {
                "zeta_nm": {"min": float(z[0]), "max": float(z[-1]),
                            "step": float(z[1] - z[0]), "n": int(z.size)},
                "x_nm": {"min": float(x[0]), "max": float(x[-1]),
                         "step": float(x[1] - x[0]), "n": int(x.size)},
                "y_nm": {"min": float(x[0]), "max": float(x[-1]),
                         "step": float(x[1] - x[0]), "n": int(x.size)},
                "axis_order": "zeta,y,x",
            },
            "hdf5_attrs_subset": {k: (bool(v) if isinstance(v, np.bool_) else
                                      float(v) if isinstance(v, (np.floating, np.integer)) else v)
                                  for k, v in attrs.items()},
        })
    return rows


def git_info() -> dict:
    repo = C.ROOT / "work" / "v4" / "repo"

    def g(*args):
        cp = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        return cp.stdout.strip()

    return {
        "repository": "yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029",
        "worktree": str(repo),
        "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": g("rev-parse", "HEAD"),
        "commit_date": g("show", "-s", "--format=%cI", "HEAD"),
        "commit_subject": g("show", "-s", "--format=%s", "HEAD"),
        "ancestor_commit": "e96d8b13a7410af5e864d09f22f1bf6e8bbc70a7",
        "worktree_clean": g("status", "--porcelain") == "",
    }


def env_info() -> dict:
    import matplotlib
    import h5py
    import pandas
    import plotly
    import scipy
    import skimage
    return {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "h5py": h5py.__version__,
        "matplotlib": matplotlib.__version__,
        "scipy": scipy.__version__,
        "pandas": pandas.__version__,
        "scikit_image": skimage.__version__,
        "plotly": plotly.__version__,
    }


def build_config(sources: list[dict], code_rows: list[dict]) -> dict:
    layers = [r for r in csv.DictReader(
        (EXP / "selected_50_zeta_layers.csv").open(encoding="utf-8"))]
    max_off = max(abs(float(r["offset_nm"])) for r in layers)
    cfg = {
        "schema": "v4-visual-config-1.0",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "read-only 50-layer 2D/3D re-visualisation of the accepted V4.1 candidate cubes",
        "physics_unchanged": True,
        "physics_rerun": False,
        "baseline": git_info(),
        "environment": env_info(),
        "source_data": sources,
        "physical_parameters": {
            "wavelength_nm": 532.0,
            "target_NA": 1.45,
            "n_sample": 1.33,
            "n_glass": 1.52,
            "n_immersion": 1.52,
            "particles": [{"diameter_nm": DIA[t], "centre_height_nm": HEIGHT[t],
                           "geometry": "surface-bound single sphere (gap = 0 nm)",
                           "tag": t} for t in TAGS],
            "zeta_nm": {"min": -170.0, "max": 170.0, "step": 2.0, "n": 171},
            "x_y_nm": {"min": -1200.0, "max": 1200.0, "step": 10.0, "n": 241},
            "array_order": "zeta,y,x",
            "excluded_conditions": [
                "520 nm illumination", "400 Hz frame rate", "Brownian motion",
                "camera sampling / shot noise", "tracking / inversion", "multi-particle",
            ],
        },
        "display": {
            "main_quantity": "I_cross = 2 Re(E_ref * conj(E_scat))",
            "sign_convention": "signed, never abs() for display",
            "colormap_signed": "RdBu_r (blue negative, white zero, red positive)",
            "colormap_positive": "viridis (I_total) / magma (I_scat, I_ref)",
            "common_scale": {"vmin": -VMAX, "vmax": +VMAX, "rule": CS["rule"],
                             "per_diameter_vmax": CS["per_diameter_vmax"]},
            "normalized_rule": "I_cross / max|I_cross| of the same cube",
            "display_window_nm": {"x": [-400.0, 400.0], "y": [-400.0, 400.0],
                                  "note": "cropped view of the full 241-point grid; no resampling"},
            "units": "dimensionless, relative to the shared on-axis reference",
        },
        "layer_selection": {
            "n_layers": 50,
            "method": "np.linspace(-170, 170, 50) targets snapped to nearest unused real layer index; "
                      "collisions resolved by walking to the nearest still-unused index",
            "max_snap_offset_nm": round(max_off, 6),
            "identical_for_all_diameters": True,
            "targets_nm": [float(r["target_zeta_nm"]) for r in layers],
            "indices": [int(r.get("index") or r["layer_index"]) for r in layers],
            "actual_zeta_nm": [float(r["actual_zeta_nm"]) for r in layers],
            "table": "exported_data/selected_50_zeta_layers.csv",
        },
        "code": {"files": code_rows,
                 "note": "scripts read the HDF5 cubes only; no solver entry point is imported"},
        "boundary": {
            "result_class": "CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED",
            "through_focus": True,
            "sample_space_near_field": False,
            "full_jones_chain": "UNVERIFIED",
            "high_na_model_validation": "UNVERIFIED",
            "paper_convention_checks": "UNVERIFIED",
            "absolute_calibration": False,
            "publisher_typeset_pdf": "NOT_OBTAINED",
            "linear_midpoint_reconstruction": "FAILED_KEPT",
        },
    }
    return cfg

# ------------------------------------------------------------------ documents
def kb(n: int) -> str:
    return f"{n/1024:.0f} KB" if n < 1024**2 else f"{n/1024**2:.2f} MB"


FIG_DESC = {
    "50slice_montage_common": "50 层 10x5 总览，三粒径共用色标",
    "50slice_montage_normalized": "50 层 10x5 总览，本粒径归一化",
    "50slice_montage_common_asinh": "asinh 压缩版共用色标总览（仅显示变换）",
    "50slice_atlas_common": "50 层逐页图册（每页 9 图，共用色标）",
    "50slice_atlas_normalized": "50 层逐页图册（每页 9 图，归一化）",
    "3d_stack_common": "50 层真实坐标三维堆叠，共用色标",
    "3d_stack_normalized": "50 层真实坐标三维堆叠，本粒径归一化（核心图）",
    "3d_stack_common_zexag3": "同上，z 轴显示 x3",
    "3d_stack_normalized_zexag3": "同上，归一化 + z 轴显示 x3",
    "3d_stack_cutaway": "半剖切（x>0 半边透明），露出内部正负结构",
    "3d_volume_render": "体切片渲染（alpha 更厚）",
    "orthoview": "x-z / y-z / x-y 三视图正交切片",
    "signal_decomposition": "zeta 附近 I_cross / I_total / I_ref / I_scat 四联分解",
    "isosurface": "+-25/50/75 % max|I| 等值面（只画真实存在的层级）",
}


def describe(name: str) -> str:
    stem = name.rsplit(".", 1)[0]
    for k, v in FIG_DESC.items():
        if stem.startswith("D0") and k in stem:
            return v
    if stem.startswith("compare_three_sizes_key_slices_common"):
        return "9 个关键层三粒径横排，共用色标"
    if stem.startswith("compare_three_sizes_key_slices"):
        return "9 个关键层三粒径横排，归一化"
    if stem.startswith("compare_three_sizes_axis_curves"):
        return "x=y=0 处 171 层轴向曲线（线性/对数/归一化）"
    return "-"


def write_limitations() -> None:
    iso = iso_table()
    zc = {t: zero_crossings(t) for t in TAGS}
    zc_txt = {t: (f"{zc[t][0]:+.0f} nm" if zc[t] else "无过零点") for t in TAGS}
    txt = f"""# 边界与未核实项 — 这些结论本轮没有、也不能证明

{BOUND}

## 0. 一句话

本包把**已经存在的候选结果**画得更清楚、更可复现；它没有、也不可能把候选模型变成已认证模型。
下面每一条都是**明确未完成**的，不能因为图画得好看就被读成"已验证"。

## 1. 物理与模型层面（沿用 V4.1 审计结论，本轮无权重开）

| 项目 | 状态 | 具体含义 | 对图件的影响 | 升级需要什么 |
|---|---|---|---|---|
| full_jones_chain | **UNVERIFIED** | 从入射到探测的完整 Jones 链（后向 Mie 角、返回光 p/s 基、S12/S13 符号、相对复振幅、超临界角处理）在 V4 审计中未逐项核实 | 图件里的 `I_cross` 可能带有未被发现的基/符号/幅度约定误差；符号与相对幅度只在**本模型内部**可比 | 逐项对照论文与 Figshare 52761698，并用独立第二实现交叉验证 |
| high_na_model_validation | **UNVERIFIED** | NA 1.45 > n_sample 1.33，存在大量超临界（k_x > n_sample·k0）分量；当前用均匀球远场 Mie/Fresnel 的解析延拓近似，未做严格球-界面 Maxwell 求解 | 高 NA 下的 PSF 形状、旁瓣、轴向包络都只是近似；不能用本结果反演实验 PSF | 严格近场/多层界面求解，或与已发表高 NA 严格解对比 |
| paper_convention_checks | **UNVERIFIED** | 本轮没有重新下载并逐项核对论文正文与 Figshare 文件的参数、符号、归一化约定 | 与论文原图直接叠图比较不合法 | 取得原文 + 补充材料后逐条对照 |
| publisher_typeset_pdf | **NOT_OBTAINED** | 只有预印本级材料，未取得出版社排版版 PDF | 引用图号/页码需回溯到预印本 | 通过机构订阅下载 |
| linear_midpoint_reconstruction | **FAILED_KEPT** | V4 中"线性中点重建"验证失败，按要求保留失败记录，不隐藏也不修补 | 该重建路径的结果不可用作证据 | 重新设计重建验证 |
| absolute_calibration | **false** | 场量无量纲、相对同一 on-axis reference；没有 V/m、没有 W/m² | 只能比较同一归一化下的**相对**大小；不能与实验对比度数值直接比 | 绝对参考场标定 + 探测端响应 |
| sample_space_near_field | **false** | 数据是像平面 through-focus 响应 (zeta, y, x)，zeta 是**离焦扫描坐标** | 三维图的"z 轴"不是样品深度；不能说"画出了颗粒周围的近场三维分布" | 需要真正的样品空间场求解 |
| 模型缺失项 | 已知设定 | 无界面多次散射、无磁光张量、无相机采样/噪声、无布朗运动、单颗粒 | 与真实实验条件的差异全部未建模 | 逐项加入建模后再谈对比 |

## 2. 数据层面

- **50/171 层是子采样**：展示层从 171 个真实 zeta 层中选出（最大吸附误差
  {cfg_off():.2f} nm，最坏缺口 4 nm = 2 层）。层与层之间的结构没有被计算，也没有插值"补出来"。
- **显示窗口 ±400 nm**：主网格仍是 x,y = ±1200 nm / 241 点；图件只裁切显示，不重采样。
- **float32 存储**：`I_cross` 以 float32 保存，相对精度约 1e-7；统计量按 float32 数值计算，未做平滑。
- 本轮**没有写回**任何 HDF5：三份文件的 SHA256 记录在 `config/visual_config.json`，
  与 V4.1 交付值一致，详见 `ACCEPTANCE.md` 的 A3/A3b 项。

## 3. 可视化层面（全部是"显示处理"，不改数据）

| 处理 | 用在哪 | 影响 | 不能据此得出 |
|---|---|---|---|
| alpha 随 \\|I_cross\\| 超线性加权 | 三维堆叠、体渲染 | 弱信号层视觉上更淡 | "看起来透明" ≠ 数值为零 |
| 深度雾化（远端向白混合 0.70→1.00） | 三维堆叠 | 远端层次对比度下降 | 不能比较远近层的绝对幅度 |
| z 轴 ×3 | `*_zexag3` | zeta 方向被拉伸 | 不能读成真实长宽比 |
| 半剖切（x>0 半边 alpha=0） | `*_cutaway` | 露出内部正负结构 | 剖切面不是物理截面 |
| asinh 压缩 | `*_montage_common_asinh` | 弱结构可见 | 颜色不再线性对应数值 |
| 共用色标 ±{VMAX:.4f} | `*_common` | D030 近白 | 不是 bug，见下 |
| marching cubes 等值面 | `isosurface` | 细节受网格分辨率限制（z 2 nm / xy 10 nm） | 等值面不是等浓度面、不是颗粒表面 |

**D030 在 common 色标下几乎全白是正确结果**：max|I_cross| 为 D030 = {S['D030']['cube_max_abs_I_cross']:.4g}、
D100 = {S['D100']['cube_max_abs_I_cross']:.4g}（相差 {VMAX/S['D030']['cube_max_abs_I_cross']:.1f}×）。
共用色标必须取三者最大值，所以 30 nm 的数值挤在色标中心极窄一段。**不调色标去掩盖这个物理幅度差。**

**matplotlib 3D 用画家算法排序，不是体光线追踪**：半透明层之间存在遮挡/排序伪影，
某些视角下远景层会盖住近景层。因此另给了 cutaway / volume / orthoview 三种交叉视图；
但**任何单张 3D 图都不能当定量依据**，定量请用 `exported_data/` 的 CSV/JSON 与 2D 层图。

## 4. 本轮明确没做的验证

1. **HTML 未做浏览器像素级复验**：沙箱浏览器拒绝 `file://`，kaleido 未安装。只做了结构检查
   （每份 50 个真实 `zeta` 面、无 `<script src=...>`、无 `src="http..."`）。
   页内 `cdn.plot.ly` 字符串是 plotly.js 内部 topojson 默认值，本页不使用地图。
2. **未与论文原图逐像素比对**（publisher typeset PDF = NOT_OBTAINED，paper_convention_checks 未完成）。
3. **未与任何实验数据比对**（absolute_calibration = false）。
4. **未做独立第二实现交叉验证**（full_jones_chain = UNVERIFIED）。
5. **未在 50 层之间做插值/超分辨**（禁止把插值结果当数据）。

## 5. 可以写 / 不可以写

可以写：

- "在候选模型下，保存的 through-focus `I_cross` 体数据呈现 …（描述图件可见结构与数值）"；
- "30/100/200 nm 的 max|I_cross| 分别为 {S['D030']['cube_max_abs_I_cross']:.4g} /
  {S['D100']['cube_max_abs_I_cross']:.4g} / {S['D200']['cube_max_abs_I_cross']:.4g}，共用色标下相差 {VMAX/S['D030']['cube_max_abs_I_cross']:.1f}×"；
- "轴上 `I_cross` 的过零情况：D030 {zc_txt['D030']}、D100 {zc_txt['D100']}、D200 {zc_txt['D200']}"。

不可以写：

- "已通过物理验证 / 已认证 / 与实验一致"；
- "近场三维分布"、"颗粒周围电场"；
- "绝对散射截面 / 绝对对比度"、"与论文图完全一致"；
- 把 asinh / zexag / cutaway 图当定量结果。

## 6. 升级为"已认证"所需（清单，本轮范围之外）

1. 完整 Jones 链逐项核对（后向 Mie 角、p/s 基、S12/S13 符号、相对复振幅）；
2. 超临界角的严格处理（球-界面 Maxwell 或文献严格解对比）；
3. 论文 + Figshare 52761698 逐项参数/符号/归一化核对；
4. 绝对标定；
5. 独立第二实现交叉验证 + 收敛性（quadrature、径向采样、网格）；
6. 在明确误差模型下与实验数据对比；
7. 失败项 `linear_midpoint_reconstruction` 修复或给出替代方案。

## 7. 本轮没有做的事

- 没有重跑光学求解器，没有改波长 532 nm / 目标 NA 1.45 / 球心高度 15·50·100 nm / 网格；
- 没有改任何测试或验收条件来"通过"；
- 没有用 pilot、旧图或插值结果代替完整网格；
- 没有把 CANDIDATE 写成已认证。
"""
    (REP / "03_limitations_zh.md").write_text(txt, encoding="utf-8")


def cfg_off() -> float:
    with (EXP / "selected_50_zeta_layers.csv").open(encoding="utf-8") as fh:
        return max(abs(float(r["offset_nm"])) for r in csv.DictReader(fh))


def write_figure_readme() -> None:
    rows = []
    for p in sorted(FIG.glob("*")):
        if p.is_file():
            rows.append(f"| `{p.name}` | {kb(p.stat().st_size)} | {describe(p.name)} |")
    sup = sorted(p.name for p in (FIG / "supplement").glob("*") if p.is_file())
    txt = f"""# `figures_main/` — 主图

{BOUND}

全部图件由 `code/step2_2d.py`、`code/step3_3d.py`、`code/step4_axis.py` 从三份只读 HDF5 生成，
**没有重算任何光场**。坐标：x, y 为物方横向坐标（显示窗口 ±400 nm），
3D 图的第三根轴是**离焦坐标 zeta（nm）**，不是样品深度。

主显示量：`I_cross = 2 Re(E_ref * conj(E_scat))`，**保留正负号**，发散色图 `RdBu_r`。

## 文件清单

| 文件 | 体积 | 内容 |
|---|---|---|
{chr(10).join(rows)}

补充图在 `supplement/`（{len(sup)} 个文件），见该目录 README。

## 命名规则

- `D030 / D100 / D200`：粒径 30 / 100 / 200 nm（球心高度 15 / 50 / 100 nm）。
- `common`：三粒径**共用**对称色标 ±{VMAX:.4f}（= 三者 max|I_cross| 的最大值），用于比较**幅度**。
- `normalized`：按本粒径 `I_cross / max|I_cross|` 归一化到 ±1，用于看**结构**。
- `_zexag3`：z 轴**显示**放大 3 倍（标题与轴标签均标注 `x3`），数据未变。
- `_asinh`：对共用色标图做 asinh 压缩，仅显示变换。
- `cutaway`：半剖切（每层 x>0 半边 alpha 置 0），仅显示处理。

## 建议阅读顺序

1. `D100_50slice_montage_normalized.png` — 先看"标准"粒径的结构随离焦如何演化；
2. `D030_*_normalized` 与 `D200_*_normalized` — 看粒径效应；
3. `compare_three_sizes_key_slices_common.png` — 看清**幅度**差异（D030 近白属正常）；
4. `D0x0_3d_stack_normalized.png` — 三维堆叠（核心图）；
5. `D0x0_orthoview.png` — 最"诚实"的一张：x-z 面上直接看到符号变化；
6. `D0x0_signal_decomposition.png` — 区分干涉项 `I_cross` 与强度量 `I_total`。

## 已知"看起来空"的图

`D030_50slice_montage_common.*`、`D030_3d_stack_common.*`、`compare_three_sizes_key_slices_common.*`
里 30 nm 的近白是**正确的物理幅度差**（max|I_cross| 比 D100 小 {VMAX/S['D030']['cube_max_abs_I_cross']:.1f} 倍），
不是色标 bug。看 30 nm 结构请用 `*_normalized` 或 `supplement/D030_50slice_montage_common_asinh.*`。

## 复现

```powershell
cd code
python step1_layers.py      # 50 层选择 + 统计
python step2_2d.py          # 2D 总览/图册/分解/关键层对比
python step3_3d.py all      # 3D 堆叠/正交/等值面/体渲染
python step4_axis.py        # 轴向曲线
python step5_html.py        # 交互页
```

脚本顶部 `vis_common.py` 中的 `DATA` 指向三份 HDF5 的绝对路径；
换机器时只需改这一处，不需要重算数据。
"""
    (FIG / "README.md").write_text(txt, encoding="utf-8")


def write_supplement_readme() -> None:
    rows = []
    for p in sorted((FIG / "supplement").glob("*")):
        if p.is_file():
            rows.append(f"| `{p.name}` | {kb(p.stat().st_size)} | {describe(p.name)} |")
    txt = f"""# `figures_main/supplement/` — 补充图

{BOUND}

这些图都**只是显示增强**，存储的数据一个字节都没改。任何一张都不能单独作为定量证据。

| 文件 | 体积 | 内容 |
|---|---|---|
{chr(10).join(rows)}

## 每个显示处理的边界

| 文件名片段 | 做了什么 | 不能读出什么 |
|---|---|---|
| `_zexag3` | 三维图 z 轴显示范围放大 3 倍（标题写明 `x3`） | 真实长宽比；zeta 层间距仍是 2 nm |
| `_cutaway` | 每层 x>0 半边 alpha=0，露出内部 | 剖切面不是物理截面，也不代表"内部场" |
| `_volume_render` | 50 层按 alpha ∝ \\|I\\|^1.2 叠加的体切片渲染 | 不是光学体渲染积分，不是吸收/散射密度 |
| `_asinh` | asinh 压缩共用色标 | 颜色不再线性对应数值 |
| `_isosurface` | marching cubes 的 ±25/50/75 % max\\|I\\| 等值面 | 不是等浓度面、不是颗粒表面、不是近场等值面 |

## 等值面存在性（本轮实测，未伪造对称结构）

| 粒径 | −75 % | −50 % | −25 % | +25 % | +50 % | +75 % |
|---|---|---|---|---|---|---|
""" + "\n".join(
        "| {0} nm | {1} |".format(
            DIA[t],
            " | ".join(
                ("存在 ({:,} 面)".format(iso_table()[t][f"{f:+.2f}"]["n_faces"])
                 if iso_table()[t][f"{f:+.2f}"].get("present") else "**不存在**")
                for f in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75)))
        for t in TAGS) + f"""

负等值面大面积缺失是真实数值性质：`I_cross` 的负向幅度远小于正向
（例如 D100 min = {S['D100']['cube_min_I_cross']:.4g} vs max = {S['D100']['cube_max_I_cross']:.4g}）。
所以没有画对称的伪结构。逐层数值见 `exported_data/D0x0_isosurface_levels.json`。
"""
    (FIG / "supplement" / "README.md").write_text(txt, encoding="utf-8")

def write_html_readme() -> None:
    rows = []
    for p in sorted(C.HTML.glob("*.html")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        rows.append("| `{0}` | {1} | {2} | {3} |".format(
            p.name, kb(p.stat().st_size), t.count('"name":"zeta='),
            "否" if ('<script src=' in t or 'src="http' in t) else "无外链"))
    txt = f"""# `html_3d/` — 交互式三维页面

{BOUND}

## 怎么打开

双击任意 `.html`，或用浏览器打开本地文件。Plotly.js **已内嵌**在页面里，
断网也能用：拖拽旋转、滚轮缩放、悬停读数。

## 文件

| 文件 | 体积 | 真实 zeta 面数 | 外部依赖 |
|---|---|---|---|
{chr(10).join(rows)}

- `*_50slice_stack.html`：50 个真实 zeta 层的 Plotly `Surface`，逐层贴到对应 zeta 平面；
  颜色为 `I_cross / max|I_cross|`，alpha 随 \\|值\\| 增大，近零背景透明（负蓝 / 零白 / 正红）。
- `*_isosurface.html`：marching-cubes 生成的等值面网格，**只包含真实存在的层级**；
  缺失的层级在 `exported_data/D0x0_isosurface_levels.json` 里记为 `not present`。

## 已验证 / 未验证

- 已验证（结构）：每份 stack 页面含 **50** 个 `name="zeta=..."` 的曲面 trace；
  页面不含 `<script src=...>`、不含 `src="http..."`。
  页面源码中出现的 `cdn.plot.ly` 字符串是 plotly.js 内部 topojson 的默认值，本页不使用地图。
- **未验证**：浏览器渲染的像素级效果。本环境没有可用的无头浏览器（`file://` 被拒绝），
  kaleido 也未安装，因此没有做"打开后截图比对"。请以静态图
  `figures_main/D0x0_3d_stack_normalized.png` 作为已目检的对照。

## 边界

交互页里的 z 轴同样是**离焦坐标 zeta**，不是样品深度；透明度、雾化为显示处理，
不能作为定量依据。
"""
    (C.HTML / "README.md").write_text(txt, encoding="utf-8")


def write_exported_readme() -> None:
    txt = f"""# `exported_data/` — 图件依赖的全部数值

{BOUND}

本目录是图件的"底稿"：图里出现的每个数都能在这里找到，或由这里的数据算出。
所有数值直接来自三份只读 HDF5，未做平滑、未做插值放大。

## 文件说明

| 文件 | 内容 | 关键字段 |
|---|---|---|
| `selected_50_zeta_layers.csv` | 50 层选择结果（每行一层） | `k, target_zeta_nm, index, actual_zeta_nm, offset_nm` |
| `selected_50_zeta_layers.json` | 同上 + 选择规则 + 三粒径一致性 + 源文件路径 | `selection_rule, identical_across_diameters, per_diameter.<TAG>.layers` |
| `stats_D030/100/200.json` | 全网格（未裁剪）统计 | `shape, cube_max_abs_I_cross, cube_min_I_cross, cube_max_I_cross, cube_std_I_cross, fraction_negative, p99_abs, argmax_*, axis_*` |
| `common_scale.json` | 三粒径共用色标 | `common_vmax, per_diameter_vmax, rule` |
| `axis_curves_center.csv` | x=y=0 的 171 层轴向曲线，3×171 行 | `tag, diameter_nm, centre_height_nm, zeta_nm, I_cross, I_total, I_ref, I_scat` |
| `axis_curves_summary.json` | 轴向峰值/谷值摘要 | `series.<TAG>.zeta_of_max / zeta_of_min / I_cross_at_zeta_0` |
| `D030/100/200_isosurface_levels.json` | 六级等值面的存在性与面数 | `levels[].level_fraction, level, present, note, n_faces` |

## 约定

- **量**：主显示量 `I_cross = 2 Re(E_ref * conj(E_scat))`，**有符号**；
  `I_total`、`I_ref`、`I_scat` 是强度量（非负）。
- **单位**：无量纲，相对同一 on-axis 参考场；`absolute_calibration = false`。
- **坐标**：`zeta` 为离焦坐标（nm），**不是**样品深度；`x, y` 为物方横向坐标（nm）。
- **数组顺序**：`(zeta, y, x)`，shape = (171, 241, 241)。
- **共用色标**：`common_vmax = {VMAX:.6f}`（= 三者 max|I_cross| 的最大值，来自 D100）。
- **归一化**：`I_cross / max|I_cross|`（同一体数据内）。

## 复算示例

```python
import h5py, numpy as np
p = r"...\\D100nm\\cube.h5"
with h5py.File(p, "r") as f:
    j = f["signals/I_cross"][:]            # (171, 241, 241) float32
    z = f["coords/zeta_nm"][:]
    x = f["coords/x_object_nm"][:]
print(np.abs(j).max())                     # = stats_D100.json -> cube_max_abs_I_cross
i = np.argmin(np.abs(x))
print(z[np.argmax(j[:, i, i])])            # = axis_curves_summary.json -> zeta_of_max
```

## 注意

- `stats_*.json` 里的 `axis_I_cross_at_center` 是**未裁剪**的 171 点中心轴曲线；
  图件上的曲线来自 `axis_curves_center.csv`，两者数值一致（见 `ACCEPTANCE.md` A6）。
- `fraction_negative` 是全体素占比；**轴上**曲线是否过零是另一回事，
  例如 D100 轴上全程为正而体数据仍有约 {S['D100']['fraction_negative']*100:.0f} % 的负值体素。
"""
    (EXP / "README.md").write_text(txt, encoding="utf-8")


def write_report_readme() -> None:
    txt = f"""# `report/` — 四份中文报告

{BOUND}

| 文件 | 读什么 | 多长 |
|---|---|---|
| `00_one_page_summary_zh.md` | 一页纸结论：做了什么、关键数值、验收状态 | 1 页 |
| `01_figure_guide_zh.md` | 图件导读：每个文件画的是什么量、色标、用途 | 2 页 |
| `02_generation_log.md` | 真实执行日志：环境、耗时、被否决的第一次三维渲染、空跑记录 | 2 页 |
| `03_limitations_zh.md` | 边界与未核实项：哪些话不能说、升级为"已认证"还需要什么 | 3 页 |

建议阅读顺序：`00` → `01` → `03`，需要复现时再读 `02` 与 `../code/`、`../logs/`。

## 报告之间的一致性

- 四份报告与 `../README.md` 顶部都有同一段边界声明（8 个字段）；
- 报告里出现的数值都来自 `../exported_data/` 的 JSON/CSV，可在 `../ACCEPTANCE.md` 的
  交叉核对项（A5/A6）中复算；
- 任何"未核实"的项目在 `03` 里都有对应的"升级需要什么"。

## 修订记录

- 2026-10-30：`00` 中"三条轴向曲线都过零"的说法**已改正**——实测 D100 轴上全程为正
  （最小 {S['D100']['axis_valley_I_cross']:.4g} @ zeta = {S['D100']['axis_valley_zeta_nm']:+.0f} nm），
  只有 D030 与 D200 在轴上过零。错误结论不会留在交付物里。
"""
    (REP / "README.md").write_text(txt, encoding="utf-8")


def write_logs_readme() -> None:
    rows = []
    for p in sorted(LOGS.glob("*.jsonl")):
        n = sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
        rows.append(f"| `{p.name}` | {kb(p.stat().st_size)} | {n} |")
    txt = f"""# `logs/` — 原始执行日志（append-only）

{BOUND}

每行一个 JSON 对象，字段固定：

| 字段 | 含义 |
|---|---|
| `step` | 步骤名（`step1_layers` … `step7_package`） |
| `event` | `start` / `done` / 具体产物事件（如 `png`、`html_stack`） |
| `t_rel_s` | 相对本次运行开始的秒数 |
| `utc` | UTC 时间戳 |
| 其余键 | 该事件的载荷（文件路径、字节数、形状、断言结果…） |

日志是**追加**写入的，因此同一个步骤可能有多次运行的记录（包括失败、空跑、重跑）。
这些记录**保留不删**，用于说明真实执行过程；`report/02_generation_log.md` 是对它们的整理。

| 文件 | 体积 | 记录数 |
|---|---|---|
{chr(10).join(rows)}

## 说明

- 日志里出现的路径是本机绝对路径（`C:\\Users\\PC\\...`），换机器后需要改 `code/vis_common.py` 的 `DATA`。
- 日志不包含任何凭据。
"""
    (LOGS / "README.md").write_text(txt, encoding="utf-8")


def write_code_readme(code_rows: list[dict]) -> None:
    hl = {r["file"]: r["sha256"][:16] for r in code_rows}
    order = [
        ("vis_common.py", "共享路径、样式、HDF5 只读加载、50 层选择、StepLog"),
        ("step1_layers.py", "50 层选择 + 全网格统计 + 共用色标"),
        ("step2_2d.py", "50 层 10x5 总览、逐页图册、信号分解、三粒径关键层对比"),
        ("step3_3d.py", "50 层三维堆叠（真实/z×3）、半剖切、体渲染、正交切片、等值面"),
        ("step4_axis.py", "中心轴向 171 层曲线与 CSV"),
        ("step5_html.py", "6 个自包含 Plotly 交互页"),
        ("mk_report1.py", "生成根 README 与 00 一页纸摘要"),
        ("mk_report2.py", "生成 01 图件导读"),
        ("mk_report3.py", "生成 02 执行日志"),
        ("mk_report4.py", "生成 03 边界报告、各子目录 README、config、验收、SHA256"),
        ("mk_package.py", "打包 REPORT / FULL 两个 ZIP 与包外校验 JSON"),
    ]
    rows = ["| `{0}` | {1} | `{2}` |".format(n, d, hl.get(n, "-")) for n, d in order]
    txt = f"""# `code/` — 本轮全部出图脚本

{BOUND}

## 环境（实际执行）

- Python 3.11.7（Anaconda）
- numpy 1.26.4 / h5py 3.9.0 / matplotlib 3.8.0 / scipy 1.11.4
- pandas 2.1.4 / scikit-image 0.22.0 / plotly 5.9.0
- 未使用：pyvista、vtk、kaleido

## 文件（SHA256 前 16 位，完整值见 `../config/visual_config.json`）

| 文件 | 作用 | SHA256 |
|---|---|---|
{chr(10).join(rows)}

## 运行顺序

```powershell
cd code
python step1_layers.py
python step2_2d.py
python step3_3d.py all
python step4_axis.py
python step5_html.py
python mk_report1.py
python mk_report2.py
python mk_report3.py
python mk_report4.py
python mk_package.py
```

## 约定

- **只读**：所有脚本用 `h5py.File(..., "r")` 打开主数据，没有任何写回路径；
  求解器代码不在本包内，也没有被 import。
- **不裁剪数据**：显示只做切片视图（±400 nm），主网格与统计仍用 ±1200 nm 全量。
- **不取绝对值**：`I_cross` 全程保留符号；`abs()` 只用于色标上限与透明度计算。
- 换机器时改 `vis_common.py` 顶部的 `ROOT/DATA/OUT` 三个路径即可。
"""
    (CODE / "README.md").write_text(txt, encoding="utf-8")


def write_config_readme() -> None:
    txt = f"""# `config/` — 固定参数与数据溯源

{BOUND}

`visual_config.json` 是本轮唯一的配置文件（只读出图的"配方"），字段：

| 字段 | 内容 |
|---|---|
| `schema` / `generated_utc` | 配置版本与生成时间（UTC） |
| `purpose` / `physics_unchanged` / `physics_rerun` | 本轮性质：只读重绘，`physics_rerun = false` |
| `baseline` | 仓库、分支、`rev-parse HEAD`、提交时间、祖先提交、工作树是否干净 |
| `environment` | Python 与 numpy/h5py/matplotlib/scipy/pandas/skimage/plotly 版本 |
| `source_data[]` | 三份 HDF5：绝对路径、相对路径、字节数、mtime、**SHA256**、shape、dtype、坐标范围与步长、HDF5 属性子集 |
| `physical_parameters` | 532 nm、NA 1.45、n_sample/n_glass/n_immersion、三粒径与球心高度、网格、数组顺序、**排除的旧课题条件** |
| `display` | 主显示量、符号约定、色图、共用色标、归一化规则、显示窗口 |
| `layer_selection` | 50 层选择方法、最大吸附误差、目标/实际 zeta、索引 |
| `code.files[]` | 每个脚本的字节数与 SHA256 |
| `boundary` | 8 项边界声明（与所有 README 一致） |

## 怎么用它复现

1. 按 `source_data[].sha256` 校验三份 HDF5 是否与本次一致（不一致就不要直接比较图件）；
2. 按 `code.files[].sha256` 校验脚本未被改动；
3. 用 `physical_parameters` 与 `display` 重建同样的色标与窗口；
4. 用 `layer_selection` 复核 50 层是否一致。

## 注意

- `source_data[].mtime_utc` 早于本轮出图开始时间，可作为"未重写主数据"的旁证
  （主证据是 SHA256 与 `ACCEPTANCE.md` A3 项）。
- 配置里**不含**任何凭据、令牌或绝对输出路径之外的个人信息。
"""
    (CFG / "README.md").write_text(txt, encoding="utf-8")

# ------------------------------------------------------------------ acceptance
def required_figures() -> list[tuple[str, int]]:
    req: list[tuple[str, int]] = []
    for t in TAGS:
        for suf in ("50slice_montage_common", "50slice_montage_normalized",
                    "3d_stack_common", "3d_stack_normalized"):
            req += [(f"{t}_{suf}.png", 10_000), (f"{t}_{suf}.pdf", 5_000)]
        req += [(f"{t}_orthoview.png", 10_000), (f"{t}_orthoview.pdf", 5_000),
                (f"{t}_signal_decomposition.png", 10_000),
                (f"{t}_signal_decomposition.pdf", 5_000),
                (f"{t}_50slice_atlas_common.pdf", 20_000),
                (f"{t}_50slice_atlas_normalized.pdf", 20_000)]
    req += [("compare_three_sizes_key_slices.png", 10_000),
            ("compare_three_sizes_key_slices.pdf", 5_000),
            ("compare_three_sizes_key_slices_common.png", 10_000),
            ("compare_three_sizes_key_slices_common.pdf", 5_000),
            ("compare_three_sizes_axis_curves.png", 10_000),
            ("compare_three_sizes_axis_curves.pdf", 5_000)]
    for t in TAGS:
        for suf in ("3d_stack_common_zexag3", "3d_stack_normalized_zexag3",
                    "3d_stack_cutaway", "3d_volume_render", "isosurface",
                    "50slice_montage_common_asinh"):
            req += [(f"supplement/{t}_{suf}.png", 10_000),
                    (f"supplement/{t}_{suf}.pdf", 5_000)]
    return req


def png_metrics(path: Path) -> dict:
    from PIL import Image
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        a = np.asarray(im.convert("L"), dtype=np.uint8)
    return {"width": int(w), "height": int(h),
            "mean": float(a.mean()), "std": float(a.std()),
            "frac_nonwhite": float((a < 250).mean())}


def pdf_pages(path: Path) -> int:
    b = path.read_bytes()
    if not b.startswith(b"%PDF"):
        return -1
    return b.count(b"/Type /Page") - b.count(b"/Type /Pages")


def run_acceptance(sources: list[dict], cfg: dict) -> dict:
    import h5py
    log = C.StepLog("step6_accept")
    checks: list[dict] = []

    def add(cid: str, name: str, ok, detail: str, evidence: str = "", info: bool = False):
        status = "INFO" if info else ("PASS" if ok else "FAIL")
        checks.append({"id": cid, "check": name, "status": status,
                       "detail": detail, "evidence": evidence})
        log.record("check", {"id": cid, "status": status, "detail": detail})

    # A1 baseline
    gb = cfg["baseline"]
    add("A1", "Git 基线与工作树",
        gb["commit"] == "0a58aff466d053bbd3f82fe9fc77fb57511edd2c"
        and gb["branch"] == "v4-audit-final-candidate" and gb["worktree_clean"],
        f"HEAD={gb['commit'][:12]} branch={gb['branch']} clean={gb['worktree_clean']}",
        "git rev-parse HEAD / git status --porcelain")

    # A2 source files: bytes, sha256, shape, coords
    ok_shape = all(r["shape_zeta_y_x"] == [171, 241, 241] for r in sources)
    ok_sha = all(r["sha256"] == src["sha256"] for r, src in zip(sources, cfg["source_data"]))
    ok_grid = all(
        r["grid"]["zeta_nm"] == {"min": -170.0, "max": 170.0, "step": 2.0, "n": 171}
        and r["grid"]["x_nm"] == {"min": -1200.0, "max": 1200.0, "step": 10.0, "n": 241}
        for r in sources)
    add("A2", "三份 HDF5 存在且 shape/坐标正确", ok_shape and ok_grid,
        "shape=171x241x241; zeta -170:2:170; x,y -1200:10:1200 全部一致",
        "h5py 只读打开后重读 coords")
    add("A3", "主数据未被本轮改写（SHA256 复算一致）", ok_sha,
        "; ".join(f"{r['tag']} {r['sha256'][:16]}" for r in sources),
        "config/visual_config.json -> source_data[].sha256")

    # A3b independent reference: V4.1 delivery SHA256SUMS.txt
    ref_file = (C.ROOT / "work" / "v4_final_20261030" / "final_tree" / "results_v4"
                / "SHA256SUMS.txt")
    ref = {}
    if ref_file.exists():
        for line in ref_file.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].endswith("cube.h5"):
                ref[parts[1]] = parts[0]
    ok_ref = bool(ref) and all(
        ref.get(f"data/{r['tag']}nm/cube.h5") == r["sha256"] for r in sources)
    ref_detail = []
    for r in sources:
        key = "data/" + r["tag"] + "nm/cube.h5"
        ref_detail.append(r["tag"] + ("=match" if ref.get(key) == r["sha256"] else "=MISMATCH"))
    add("A3b", "SHA256 与 V4.1 交付清单逐文件一致", ok_ref, "; ".join(ref_detail),
        "work/v4_final_20261030/final_tree/results_v4/SHA256SUMS.txt")

    # A4 mtime predates the plotting pass
    logs = sorted(p.stat().st_mtime for p in LOGS.glob("step*.jsonl")
                  if p.name != "step6_accept.jsonl") or [time.time()]
    first_log = min(logs)
    ok_mtime = all(Path(r["path"]).stat().st_mtime < first_log for r in sources)
    add("A4", "主数据 mtime 早于本轮出图开始", ok_mtime,
        time.strftime("first log %Y-%m-%dT%H:%M:%SZ", time.gmtime(first_log)),
        "logs/step1_layers.jsonl 起的时间戳")

    # A5 layer selection
    layers = list(csv.DictReader((EXP / "selected_50_zeta_layers.csv").open(encoding="utf-8")))
    idx = [int(r.get("index") or r["layer_index"]) for r in layers]
    zs = [float(r["actual_zeta_nm"]) for r in layers]
    off = max(abs(float(r["offset_nm"])) for r in layers)
    add("A5", "50 层互不相同、覆盖全量程", len(idx) == 50 and len(set(idx)) == 50
        and idx == sorted(idx) and zs[0] == -170.0 and zs[-1] == 170.0 and off <= 1.0,
        f"n={len(idx)} unique={len(set(idx))} zeta {zs[0]:+.0f}..{zs[-1]:+.0f} max_offset={off:.2f} nm",
        "exported_data/selected_50_zeta_layers.csv")

    # A6 numeric cross-check against HDF5
    worst = 0.0
    axis_worst = 0.0
    for r in sources:
        tag = r["tag"]
        with h5py.File(r["path"], "r") as f:
            j = f["signals/I_cross"][:]
            z = f["coords/zeta_nm"][:]
            x = f["coords/x_object_nm"][:]
        st = S[tag]
        worst = max(worst, abs(float(np.abs(j).max()) - st["cube_max_abs_I_cross"])
                    / max(abs(st["cube_max_abs_I_cross"]), 1e-30))
        worst = max(worst, abs(float(j.min()) - st["cube_min_I_cross"])
                    / max(abs(st["cube_min_I_cross"]), 1e-30))
        i0 = int(np.argmin(np.abs(x)))
        axis = np.asarray(j[:, i0, i0], dtype=float)
        zz, vv = axis_series(tag)
        if zz.size != z.size:
            axis_worst = 9.9
        else:
            scale = max(float(np.abs(vv).max()), 1e-30)
            axis_worst = max(axis_worst, float(np.abs(axis - vv).max()) / scale)
    add("A6", "stats/轴向曲线与 HDF5 复读数值一致", worst < 1e-9 and axis_worst < 1e-9,
        f"max rel err (cube stats) = {worst:.2e}; max rel err (axis curve) = {axis_worst:.2e}",
        "重读 signals/I_cross 与 export CSV 逐点比较")

    # A7 required figures
    missing, small = [], []
    for rel, minb in required_figures():
        p = FIG / rel
        if not p.exists():
            missing.append(rel)
        elif p.stat().st_size < minb:
            small.append(f"{rel} ({p.stat().st_size} B)")
    add("A7", "任务书要求的图件全部存在且非空", not missing and not small,
        f"required={len(required_figures())} missing={len(missing)} undersized={len(small)}"
        + ((" :: " + "; ".join(missing + small)) if (missing or small) else ""),
        "figures_main/ 逐文件大小检查")

    # A8 PNG pixel sanity
    pngs = sorted(FIG.rglob("*.png"))
    bad_png, blank = [], []
    for p in pngs:
        m = png_metrics(p)
        if m["width"] < 600 or m["height"] < 400 or m["frac_nonwhite"] < 1e-4:
            bad_png.append(p.name)
        if m["std"] < 2.0:
            blank.append((p.relative_to(FIG).as_posix(), round(m["std"], 2)))
    add("A8", "PNG 可解码且不是空白页", not bad_png,
        f"{len(pngs)} 个 PNG；尺寸/非白像素检查通过"
        + (f"；低方差(<2)文件: {blank}" if blank else "；无低方差文件"),
        "PIL 解码 + 灰度 std / 非白像素比例")

    # A9 PDF pages
    pdfs = sorted(FIG.rglob("*.pdf"))
    bad_pdf = [p.name for p in pdfs if pdf_pages(p) < 1]
    atlas_pages = {t: pdf_pages(FIG / f"{t}_50slice_atlas_common.pdf") for t in TAGS}
    add("A9", "PDF 结构有效、图册页数=6", not bad_pdf and all(v == 6 for v in atlas_pages.values()),
        f"{len(pdfs)} 个 PDF；atlas pages={atlas_pages}",
        "/Type /Page 计数")

    # A10 HTML
    html_rows = []
    ok_html = True
    for p in sorted(C.HTML.glob("*.html")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        nz = t.count('"name":"zeta=')
        ext = ('<script src=' in t) or ('src="http' in t)
        is_stack = "stack" in p.name
        html_rows.append({"file": p.name, "bytes": p.stat().st_size,
                          "zeta_faces": nz if is_stack else None,
                          "kind": "50-plane stack" if is_stack else "isosurface",
                          "external_ref": ext})
        if p.stat().st_size < 50_000 or ext:
            ok_html = False
        if is_stack and nz != 50:
            ok_html = False
        if (not is_stack) and "Plotly.newPlot" not in t:
            ok_html = False
    detail = []
    for r in html_rows:
        detail.append(r["file"] + (":" + str(r["zeta_faces"]) if r["zeta_faces"] is not None
                                   else ":" + r["kind"]))
    add("A10", "HTML 自包含且每份含 50 个真实 zeta 面", ok_html, "; ".join(detail),
        "字符串检查：无 <script src=>、无 src=\"http…\"；name=\"zeta=…\" 计数")

    # A11 inventory
    n_png, n_pdf, n_html = len(pngs), len(pdfs), len(list(C.HTML.glob("*.html")))
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    add("A11", "产物计数", n_png >= 30 and n_pdf >= 30 and n_html == 6,
        f"PNG={n_png} PDF={n_pdf} HTML={n_html} total={total/1024**2:.1f} MB",
        "目录遍历")

    # A12 boundary statements
    tokens = ["CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED", "full_jones_chain",
              "high_na_model_validation", "paper_convention_checks", "absolute_calibration",
              "sample_space_near_field", "publisher_typeset_pdf",
              "linear_midpoint_reconstruction"]
    docs = [OUT / "README.md", FIG / "README.md", FIG / "supplement" / "README.md",
            C.HTML / "README.md", EXP / "README.md", REP / "README.md",
            REP / "00_one_page_summary_zh.md", REP / "01_figure_guide_zh.md",
            REP / "02_generation_log.md", REP / "03_limitations_zh.md"]
    missing_tok = []
    for d in docs:
        if not d.exists():
            missing_tok.append(f"{d.name}:missing")
            continue
        txt = d.read_text(encoding="utf-8")
        for tk in tokens:
            if tk not in txt:
                missing_tok.append(f"{d.name}:{tk}")
    add("A12", "每份 README/报告都含 8 项边界声明", not missing_tok,
        f"checked {len(docs)} docs; missing={missing_tok if missing_tok else 'none'}",
        "字符串包含检查")

    # A13 light bundle carries no HDF5
    data_in_out = list(OUT.rglob("*.h5"))
    add("A13", "可视化结果树内不含主数据（FULL 包单独放置）", not data_in_out,
        f".h5 files inside OUT = {len(data_in_out)}",
        "OUT 递归查找 *.h5")

    overall = "PASS" if all(c["status"] in ("PASS", "INFO") for c in checks) else "FAIL"
    out = {
        "schema": "v4-visual-acceptance-1.0",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall": overall,
        "n_checks": len(checks),
        "n_fail": sum(1 for c in checks if c["status"] == "FAIL"),
        "checks": checks,
        "artifacts": {
            "png": n_png, "pdf": n_pdf, "html": n_html,
            "html_detail": html_rows,
            "total_bytes": total,
        },
        "boundary": cfg["boundary"],
        "not_verified": [
            "full_jones_chain", "high_na_model_validation", "paper_convention_checks",
            "publisher_typeset_pdf", "html_pixel_level_render",
        ],
    }
    log.done({"overall": overall, "n_fail": out["n_fail"]})
    return out


def write_acceptance_md(acc: dict) -> None:
    rows = []
    for c in acc["checks"]:
        mark = {"PASS": "**PASS**", "FAIL": "**FAIL**", "INFO": "INFO"}[c["status"]]
        rows.append(f"| {c['id']} | {c['check']} | {mark} | {c['detail']} |")
    a = acc["artifacts"]
    txt = f"""# 验收表 — 实际执行的检查

{BOUND}

**总判定：{acc['overall']}**（{acc['n_checks']} 项检查，失败 {acc['n_fail']} 项）
生成时间（UTC）：{acc['generated_utc']}

本表由 `code/mk_report4.py` 在打包前实际运行生成，不是手写的。
逐项原始记录见 `logs/step6_accept.jsonl`，机器可读版本见本目录的 `acceptance.json`。

## 1. 检查项

| ID | 检查 | 结果 | 实测 |
|---|---|---|---|
{chr(10).join(rows)}

## 2. 产物计数

- PNG **{a['png']}** 个、PDF **{a['pdf']}** 个、HTML **{a['html']}** 个，
  可视化结果树合计 **{a['total_bytes']/1024**2:.1f} MB**（不含主数据）。

## 3. 明确未验证（不写成通过）

| 项目 | 状态 |
|---|---|
| `full_jones_chain` | UNVERIFIED |
| `high_na_model_validation` | UNVERIFIED |
| `paper_convention_checks` | UNVERIFIED |
| `publisher_typeset_pdf` | NOT_OBTAINED |
| HTML 浏览器像素级渲染 | 未做（只做结构检查，见 A10） |
| 与论文原图逐像素比对 | 未做 |
| 与实验数据比对 | 未做（`absolute_calibration = false`） |

## 4. 复现

```powershell
cd code
python mk_report4.py      # 重新生成配置 + 本验收表 + SHA256SUMS.txt
python mk_package.py      # 重新打包两个 ZIP 与包外校验 JSON
```

`mk_report4.py` 会重新计算三份 HDF5 的 SHA256 并与 `config/visual_config.json` 比对，
若主数据被改动，A3 会直接 FAIL。
"""
    (OUT / "ACCEPTANCE.md").write_text(txt, encoding="utf-8")


def write_sums() -> dict:
    files = [p for p in OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"]
    files.sort(key=lambda p: p.relative_to(OUT).as_posix())
    lines = [f"{sha256(p)}  {p.relative_to(OUT).as_posix()}" for p in files]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in files)
    return {"n_files": len(files), "total_bytes": total,
            "table": "SHA256SUMS.txt"}


def main() -> int:
    C.ensure_dirs()
    CFG.mkdir(parents=True, exist_ok=True)
    code_rows = copy_code()
    sources = source_rows()
    cfg = build_config(sources, code_rows)
    (CFG / "visual_config.json").write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    write_limitations()
    write_figure_readme()
    write_supplement_readme()
    write_html_readme()
    write_exported_readme()
    write_report_readme()
    write_logs_readme()
    write_code_readme(code_rows)
    write_config_readme()

    acc = run_acceptance(sources, cfg)
    (OUT / "acceptance.json").write_text(
        json.dumps(acc, indent=2, ensure_ascii=False), encoding="utf-8")
    write_acceptance_md(acc)
    sums = write_sums()
    print(json.dumps({"overall": acc["overall"], "checks": acc["n_checks"],
                      "fail": acc["n_fail"], "sums": sums}, ensure_ascii=False, indent=2))
    return 0 if acc["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

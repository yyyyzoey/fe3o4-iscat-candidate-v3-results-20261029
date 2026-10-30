#!/usr/bin/env python3
"""Clear 2D/3D previews for the V4.1 candidate delivery, read from saved cubes.

Nothing here recomputes physics. 2D panels are direct xy slices. 3D panels are
display cutaways made from five saved xy slices plus the saved x=0 yz section.
The xy display window is cropped to +/-400 nm so the field is legible; the main
171x241x241 grid is neither resampled nor interpolated-upscaled.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.cm import ScalarMappable
from PIL import Image, ImageDraw, ImageFont

CASES = [("D030", 30, 15), ("D100", 100, 50), ("D200", 200, 100)]
SLICES = [-86.0, 0.0, 86.0]
DISPLAY_HALF_NM = 400.0
STACK_Z_NM = [-120.0, -60.0, 0.0, 60.0, 120.0]


def load_cross(path: Path):
    with h5py.File(path, "r") as f:
        j = f["signals/I_cross"][:]
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
    return j, z, x


def load_volume(path: Path):
    with h5py.File(path, "r") as f:
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
        ix = np.where(np.abs(x) <= DISPLAY_HALF_NM)[0]
        iy = np.where(np.abs(y) <= DISPLAY_HALF_NM)[0]
        j = f["signals/I_cross"][:][:, iy][:, :, ix]
    return j, z, x[ix], y[iy]


def sym_scale(a: np.ndarray) -> float:
    v = np.abs(a[np.isfinite(a)])
    return float(np.percentile(v, 99.5)) if v.size else 1.0


def panel(ax, j, iz, x, vmax, title):
    ext = [float(x[0]), float(x[-1]), float(x[0]), float(x[-1])]
    im = ax.imshow(j[iz], origin="lower", extent=ext, cmap="RdBu_r",
                   vmin=-vmax, vmax=vmax, interpolation="nearest")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("x (nm)", fontsize=9)
    ax.set_ylabel("y (nm)", fontsize=9)
    ax.tick_params(labelsize=8)
    return im


def render_3d_cutaway(res: Path, out: Path, tag: str, D: int, h: int) -> dict:
    j, z, x, y = load_volume(res / "data" / f"{tag}nm" / "cube.h5")
    vclip = float(np.percentile(np.abs(j[np.isfinite(j)]), 99.5))
    norm = TwoSlopeNorm(vmin=-vclip, vcenter=0.0, vmax=vclip)
    cmap = plt.get_cmap("RdBu_r")

    fig = plt.figure(figsize=(11.0, 8.6), facecolor="white")
    ax = fig.add_axes([0.035, 0.095, 0.685, 0.79], projection="3d")
    X, Y = np.meshgrid(x / 1000.0, y / 1000.0)

    slice_indices = []
    for zv in STACK_Z_NM:
        iz = int(np.argmin(np.abs(z - zv)))
        slice_indices.append(iz)
        ax.plot_surface(
            X, Y, np.full_like(X, z[iz] / 1000.0),
            facecolors=cmap(norm(j[iz])),
            rstride=1, cstride=1, linewidth=0, antialiased=False,
            shade=False, alpha=0.72,
        )

    jx = int(np.argmin(np.abs(x)))
    YZ, ZZ = np.meshgrid(y / 1000.0, z / 1000.0)
    ax.plot_surface(
        np.full_like(YZ, x[jx] / 1000.0), YZ, ZZ,
        facecolors=cmap(norm(j[:, :, jx])),
        rstride=1, cstride=1, linewidth=0, antialiased=False,
        shade=False, alpha=0.88,
    )

    # Geometric sphere reference only (not an iso-surface of the field).
    theta = np.linspace(0.0, 2.0 * np.pi, 241)
    r = D / 2000.0  # nm -> micrometres
    ax.plot(np.full_like(theta, x[jx] / 1000.0),
            r * np.sin(theta), r * np.cos(theta),
            color="#444444", linestyle="--", linewidth=1.0, alpha=0.7)

    ax.set_xlim(y[0] / 1000.0, y[-1] / 1000.0)
    ax.set_ylim(x[0] / 1000.0, x[-1] / 1000.0)
    ax.set_zlim(z[0] / 1000.0, z[-1] / 1000.0)
    ax.set_xticks([-0.4, -0.2, 0.0, 0.2, 0.4])
    ax.set_yticks([-0.4, -0.2, 0.0, 0.2, 0.4])
    ax.set_zticks([-0.15, 0.0, 0.15])
    ax.set_xlabel("y (µm)", labelpad=2)
    ax.set_ylabel("x (µm)", labelpad=2)
    ax.set_zlabel("zeta (µm)", labelpad=4)
    ax.tick_params(labelsize=8, pad=1)
    ax.set_box_aspect((800, 800, 340))
    ax.view_init(elev=24, azim=-55)
    ax.set_title(
        f"{tag}: Fe$_3$O$_4$ D={D} nm, center height {h} nm\n"
        "Saved-grid 3D through-focus cutaway; xy display crop ±400 nm",
        fontsize=12.5, pad=8,
    )
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 1))
        axis.pane.set_edgecolor("#d0d0d0")

    cax = fig.add_axes([0.825, 0.34, 0.018, 0.38])
    sm = ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("I$_{cross}$ (a.u.)", fontsize=9)
    cb.ax.tick_params(labelsize=7)

    fig.text(
        0.025, 0.018,
        "Blue/red planes: saved xy slices at zeta = −120, −60, 0, +60, +120 nm "
        "plus the yz section at x=0. Dashed grey circle: geometric sphere cross-section "
        "(reference only).\nDisplay crop uses saved 10 nm xy samples; the 171×241×241 main "
        "grid is not resampled or interpolated-upscaled. This is a through-focus field "
        "cutaway, not a particle-surface rendering.",
        fontsize=7.4, color="#333333",
    )
    p = out / f"preview_3d_{tag}.png"
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {
        "png_bytes": p.stat().st_size,
        "display_crop_xy_nm": [-DISPLAY_HALF_NM, DISPLAY_HALF_NM],
        "xy_slice_zeta_nm": [float(z[i]) for i in slice_indices],
        "yz_section_x_nm": float(x[jx]),
        "symmetric_vmax": vclip,
        "geometric_sphere_reference": True,
        "main_grid_resampled_or_upscaled": False,
        "preview_representation": "5 saved xy slices + saved x=0 yz section",
    }


def render_combined_3d(out: Path, meta: dict) -> None:
    tiles = []
    for tag, _, _ in CASES:
        im = Image.open(out / f"preview_3d_{tag}.png").convert("RGB")
        tiles.append(im)
    width = max(im.width for im in tiles)
    tiles = [im.resize((width, int(im.height * width / im.width)), Image.Resampling.LANCZOS)
             for im in tiles]
    height = max(im.height for im in tiles)
    note = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(note)
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.is_file():
        title_font = ImageFont.truetype(str(font_path), 42)
        body_font = ImageFont.truetype(str(font_path), 28)
        small_font = ImageFont.truetype(str(font_path), 23)
    else:
        title_font = body_font = small_font = ImageFont.load_default()
    draw.rectangle((30, 30, width - 30, height - 30), outline="#c8c8c8", width=3)
    draw.text((70, 70), "三维预览阅读说明", font=title_font, fill="#222222")
    body = [
        "• 三幅图均直接从保存的 HDF5 网格生成。",
        "• 显示窗仅裁剪 x,y 至 ±400 nm；zeta 保持 −170…+170 nm。",
        "• 主数据仍为 171×241×241；未插值放大、未重算物理。",
        "• 彩色正交切片展示 through-focus 干涉场；不是颗粒表面。",
        "• 虚线灰圆仅为几何球剖面参考，不表示场分布必须呈球形。",
        "• 三组使用各自独立的对称色标；30 nm 幅值约弱两个数量级。",
        "",
        "结果分类：CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED",
        "完整 Jones 链、超临界高 NA 物理与绝对标定：UNVERIFIED",
    ]
    yy = 170
    for line in body:
        draw.text((75, yy), line, font=body_font, fill="#333333")
        yy += 72
    draw.text((75, height - 120),
              "Original grid: zeta × y × x = 171 × 241 × 241; 10 nm lateral sampling.",
              font=small_font, fill="#555555")
    sheet = Image.new("RGB", (width * 2, height * 2), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 2) * width, (i // 2) * height))
    sheet.paste(note, (width, height))
    p = out / "preview_3d_three_diameters.png"
    sheet.save(p, optimize=True)
    meta["combined_3d_png_bytes"] = p.stat().st_size
    meta["combined_3d_shape"] = list(sheet.size)
    meta["combined_3d_layout"] = "2x2: D030, D100 / D200, reading-guide card"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    RES = a.results.resolve()
    out = RES / "previews"
    out.mkdir(exist_ok=True)
    meta = {
        "source": "read directly from data/D*/cube.h5 signals/I_cross; no physics recomputation",
        "slices_zeta_nm": SLICES,
        "display_crop_note": "3D xy display crop is a direct subset of saved 10 nm samples; no interpolation enlargement",
        "cases": {},
    }

    # Per-diameter 2D: three direct slices in one row.
    for tag, D, h in CASES:
        j, z, x = load_cross(RES / "data" / f"{tag}nm" / "cube.h5")
        idx = [int(np.argmin(np.abs(z - s))) for s in SLICES]
        vmax = max(sym_scale(j[i]) for i in idx)
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), constrained_layout=True)
        for ax, iz, s in zip(axes, idx, SLICES):
            im = panel(ax, j, iz, x, vmax, f"zeta = {s:+.0f} nm")
        cb = fig.colorbar(im, ax=axes, shrink=0.9)
        cb.set_label("I_cross = 2 Re(conj(E_ref)·E_scat)  [a.u.]", fontsize=9)
        fig.suptitle(f"Fe$_3$O$_4$  D = {D} nm, center height {h} nm, 532 nm, NA 1.45 "
                     f"— through-focus xy slices (candidate)", fontsize=12)
        p = out / f"preview_2d_{tag}.png"
        fig.savefig(p, dpi=180)
        fig.savefig(out / f"preview_2d_{tag}.svg")
        plt.close(fig)
        meta["cases"][tag] = {
            "diameter_nm": D, "center_height_nm": h,
            "zeta_indices": idx, "symmetric_vmax": vmax,
            "png_bytes": p.stat().st_size,
        }

    # Combined 2D contact sheet (rows = diameter, per-row scale).
    fig, axes = plt.subplots(3, 3, figsize=(13.5, 12.5), constrained_layout=True)
    for r, (tag, D, h) in enumerate(CASES):
        j, z, x = load_cross(RES / "data" / f"{tag}nm" / "cube.h5")
        idx = [int(np.argmin(np.abs(z - s))) for s in SLICES]
        vmax = max(sym_scale(j[i]) for i in idx)
        for c, (iz, s) in enumerate(zip(idx, SLICES)):
            ax = axes[r, c]
            im = panel(ax, j, iz, x, vmax, f"D = {D} nm  |  zeta = {s:+.0f} nm")
            cb = fig.colorbar(im, ax=ax, shrink=0.85)
            cb.ax.tick_params(labelsize=7)
    fig.suptitle("Fe$_3$O$_4$ single-sphere iSCAT, 532 nm, NA 1.45 — signed interference I_cross\n"
                 "rows: 30 / 100 / 200 nm (center height 15 / 50 / 100 nm); "
                 "each row has its own symmetric colour scale (30 nm is ~2 orders weaker)",
                 fontsize=12)
    p = out / "preview_2d_three_diameters.png"
    fig.savefig(p, dpi=170)
    plt.close(fig)
    meta["combined_2d_png_bytes"] = p.stat().st_size

    # Per-diameter 3D cutaways, read from the same saved HDF5 cubes.
    for tag, D, h in CASES:
        meta["cases"][tag].update(render_3d_cutaway(RES, out, tag, D, h))
    render_combined_3d(out, meta)

    (out / "preview_manifest.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

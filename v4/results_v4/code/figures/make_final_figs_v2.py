"""V4 figure completion: F2 full-range common montages + F4 full-component axial curves.

Reads saved HDF5 only. No optical recomputation, no data modification.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import h5py

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results_v4"
FIG = RES / "figures"
DATA = RES / "data"
CASES = (("D030", 30.0), ("D100", 100.0), ("D200", 200.0))
ZETA = [-170.0, -128.0, -86.0, -42.0, 0.0, 42.0, 86.0, 128.0, 170.0]
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.unicode_minus": True})


def load(d):
    with h5py.File(DATA / f"{d}nm" / "cube.h5", "r") as f:
        return dict(J=f["signals/I_cross"][:], Iref=f["signals/I_ref"][:],
                    Iscat=f["signals/I_scat"][:], Itot=f["signals/I_total"][:],
                    S=f["signals/contrast_fixed_reference"][:],
                    x=f["coords/x_object_nm"][:], y=f["coords/y_object_nm"][:],
                    z=f["coords/zeta_nm"][:], D=float(f.attrs["diameter_nm"]))


def grid9(d, mode, jmax_common, vmax, cblabel, title, outbase):
    fig, axes = plt.subplots(3, 3, figsize=(9.6, 9.0), layout="constrained")
    jmax = float(np.max(np.abs(d["J"])))
    denom = jmax if mode == "shape" else jmax_common
    for ax, zv in zip(axes.ravel(), ZETA):
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        a = d["J"][iz] / denom
        im = ax.imshow(a, origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                       extent=[d["x"][0], d["x"][-1], d["y"][0], d["y"][-1]],
                       interpolation="nearest")
        ax.set_title(f"zeta = {d['z'][iz]:+.0f} nm", pad=3)
        ax.axhline(0, color="0.65", lw=0.35); ax.axvline(0, color="0.65", lw=0.35)
    for ax in axes[-1]:
        ax.set_xlabel("x (nm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("y (nm)")
    cb = fig.colorbar(im, ax=axes, shrink=0.72, pad=0.015, aspect=40)
    cb.set_label(cblabel)
    fig.suptitle(title, fontsize=9.6)
    fig.savefig(outbase.with_suffix(".png"), dpi=200)
    fig.savefig(outbase.with_suffix(".svg"))
    plt.close(fig)


def axial_components(d):
    z = d["z"]
    j = d["J"][:, 120, 120]
    jmax = float(np.max(np.abs(d["J"])))
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9), layout="constrained")
    ax = axes[0]
    ax.plot(z, j, lw=1.3, color="#b2182b", label="J = I_cross (common units)")
    ax.plot(z, j / jmax, lw=1.1, ls="--", color="#2166ac", label="J / max_cube|J| (shape)")
    ax.axhline(0, color="0.4", lw=0.6)
    ax.axvline(0, color="0.75", lw=0.6, ls=":")
    ax.set_xlabel("zeta (nm, focus scan)"); ax.set_ylabel("J")
    ax.set_title("(a) interference cross term, common vs shape")
    ax.legend(fontsize=7.5); ax.grid(alpha=0.25)
    ax = axes[1]
    ax.plot(z, d["Iref"][:, 120, 120], lw=1.2, color="0.35", label="I_ref")
    ax.plot(z, d["Iscat"][:, 120, 120], lw=1.2, color="#1b7837", label="I_scat")
    ax.plot(z, d["Itot"][:, 120, 120], lw=1.2, color="#762a83", label="I_total")
    ax.plot(z, d["S"][:, 120, 120], lw=1.2, color="#e08214", label="S_fixed")
    ax.axvline(0, color="0.75", lw=0.6, ls=":")
    ax.set_xlabel("zeta (nm, focus scan)"); ax.set_ylabel("shared model units")
    ax.set_title("(b) I_ref, I_scat, I_total, S_fixed at x=y=0")
    ax.legend(fontsize=7.5); ax.grid(alpha=0.25)
    fig.suptitle(f"Fe3O4 D={d['D']:.0f} nm, NA=1.45, lambda=532 nm | axial (on-axis) components\n"
                 "no recentering; window-limited extrema only", fontsize=9.4)
    out = FIG / "F4_axial"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{d['D']:03.0f}nm_axial_full_components.png", dpi=200)
    fig.savefig(out / f"{d['D']:03.0f}nm_axial_full_components.svg")
    plt.close(fig)


def main():
    cubes = {k: load(k) for k, _ in CASES}
    jmax_common = max(float(np.max(np.abs(c["J"]))) for c in cubes.values())
    mo = FIG / "F2_xy_slices" / "montage"
    mo.mkdir(parents=True, exist_ok=True)
    for dname, _ in CASES:
        d = cubes[dname]
        grid9(d, "shape", jmax_common, 1.0,
              "J / max_cube|J| (one constant for this cube)",
              f"D={d['D']:.0f} nm | I_cross = J | 9 xy slices | shape normalization (whole cube)",
              mo / f"{dname}_shape_montage")
        grid9(d, "common", jmax_common, jmax_common,
              f"J (model units) | full shared range +-{jmax_common:.3g}",
              f"D={d['D']:.0f} nm | 9 xy slices | COMMON FULL RANGE (vmax = max over all 3 cubes)",
              mo / f"{dname}_common_full_montage")
        grid9(d, "common", jmax_common, 0.25,
              "J (model units) | EMPHASIZED +-0.25, not full range",
              f"D={d['D']:.0f} nm | 9 xy slices | common units, emphasized +-0.25 display window",
              mo / f"{dname}_common_emphasized_montage")
        old = mo / f"{dname}_common_montage.png"
        old_svg = mo / f"{dname}_common_montage.svg"
        if old.is_file():
            old.unlink()
        if old_svg.is_file():
            old_svg.unlink()
        axial_components(d)
        print(dname, "ok")
    print("jmax_common", jmax_common)


if __name__ == "__main__":
    main()

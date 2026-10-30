"""Regenerate F2 montages and raw-pixel zooms with a clean layout."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import h5py

import argparse

_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[2],
                 help="results_v4 package root containing data/, figures/, tables/")
_ap.add_argument("--out", type=Path, default=None,
                 help="figure output root (default: <data-root>/figures)")
_ap.add_argument("--diagnostics-root", type=Path, default=None,
                 help="folder holding target_long/ and paper_control_long/ (default: <data-root>/diagnostics)")
_a, _unknown = _ap.parse_known_args()
RES = _a.data_root.resolve()
FIG = (_a.out or RES / "figures").resolve()
DATA = RES / "data"
TAB = RES / "tables"
DIAG = (_a.diagnostics_root or RES / "diagnostics").resolve()
CASES = (("D030", 30.0), ("D100", 100.0), ("D200", 200.0))
ZETA = [-170.0, -128.0, -86.0, -42.0, 0.0, 42.0, 86.0, 128.0, 170.0]
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.unicode_minus": True})


def load(d):
    with h5py.File(DATA / f"{d}nm" / "cube.h5", "r") as f:
        return dict(J=f["signals/I_cross"][:], x=f["coords/x_object_nm"][:],
                    y=f["coords/y_object_nm"][:], z=f["coords/zeta_nm"][:],
                    D=float(f.attrs["diameter_nm"]))


def grid9(d, mode, jmax_common, ix, iy, vmax, cblabel, title, outbase):
    fig, axes = plt.subplots(3, 3, figsize=(9.8, 9.2), layout="constrained")
    jmax = float(np.max(np.abs(d["J"])))
    denom = jmax if mode == "shape" else jmax_common
    xs, ys = d["x"][ix], d["y"][iy]
    for ax, zv in zip(axes.ravel(), ZETA):
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        a = d["J"][iz][np.ix_(iy, ix)] / denom
        im = ax.imshow(a, origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                       extent=[xs[0], xs[-1], ys[0], ys[-1]], interpolation="nearest")
        ax.set_title(f"zeta = {d['z'][iz]:+.0f} nm", pad=3)
        ax.axhline(0, color="0.65", lw=0.35); ax.axvline(0, color="0.65", lw=0.35)
    for ax in axes[-1]: ax.set_xlabel("x (nm)")
    for ax in axes[:, 0]: ax.set_ylabel("y (nm)")
    cb = fig.colorbar(im, ax=axes, shrink=0.72, pad=0.015, aspect=40)
    cb.set_label(cblabel)
    fig.suptitle(title, fontsize=9.8)
    fig.savefig(outbase.with_suffix(".png"), dpi=200)
    fig.savefig(outbase.with_suffix(".svg"))
    plt.close(fig)


def single_zoom(d, mode, jmax_common, ix, iy, vmax, cblabel, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    jmax = float(np.max(np.abs(d["J"])))
    denom = jmax if mode == "shape" else jmax_common
    xs, ys = d["x"][ix], d["y"][iy]
    for zv in ZETA:
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        fig, ax = plt.subplots(figsize=(4.4, 3.9), layout="constrained")
        im = ax.imshow(d["J"][iz][np.ix_(iy, ix)] / denom, origin="lower", cmap="RdBu_r",
                       vmin=-vmax, vmax=vmax, extent=[xs[0], xs[-1], ys[0], ys[-1]],
                       interpolation="nearest")
        ax.set_title(f"D={d['D']:.0f} nm, zeta={d['z'][iz]:+.0f} nm ({mode})")
        ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
        fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02).set_label(cblabel)
        fig.savefig(outdir / f"zoom_{mode}_xy_{d['z'][iz]:+.1f}.png", dpi=150)
        plt.close(fig)


def main():
    cubes = {k: load(k) for k, _ in CASES}
    jmax_common = max(float(np.max(np.abs(c["J"]))) for c in cubes.values())
    for dname, _ in CASES:
        d = cubes[dname]
        ix_full = np.arange(len(d["x"])); iy_full = np.arange(len(d["y"]))
        ix_z = np.where((d["x"] >= -300) & (d["x"] <= 300))[0]
        iy_z = np.where((d["y"] >= -300) & (d["y"] <= 300))[0]
        mo = FIG / "F2_xy_slices" / "montage"; mo.mkdir(parents=True, exist_ok=True)
        grid9(d, "shape", jmax_common, ix_full, iy_full, 1.0,
              "J / max_cube|J| (one constant for this cube)",
              f"D={d['D']:.0f} nm | I_cross = J | 9 xy layers | shape normalization (whole cube)",
              mo / f"{dname}_shape_montage")
        grid9(d, "common", jmax_common, ix_full, iy_full, 0.25,
              "J (model units, shared scale across D)",
              f"D={d['D']:.0f} nm | I_cross = J | 9 xy layers | common scale (max over all 3 cubes)",
              mo / f"{dname}_common_montage")
        zo = FIG / "F2_xy_slices" / "zoom" / dname
        grid9(d, "shape", jmax_common, ix_z, iy_z, 1.0,
              "J / max_cube|J| (one constant for this cube)",
              f"D={d['D']:.0f} nm | raw 10 nm pixels, zoom +-300 nm | 9 xy layers | shape normalization",
              zo / "zoom_shape_montage")
        grid9(d, "common", jmax_common, ix_z, iy_z, 0.25,
              "J (model units, shared scale across D)",
              f"D={d['D']:.0f} nm | raw 10 nm pixels, zoom +-300 nm | 9 xy layers | common scale",
              zo / "zoom_common_montage")
        single_zoom(d, "shape", jmax_common, ix_z, iy_z, 1.0,
                    "J / max_cube|J|", zo)
        single_zoom(d, "common", jmax_common, ix_z, iy_z, 0.25, "J (model units, shared)", zo)
        print(dname, "ok")
    print("jmax_common", jmax_common)


if __name__ == "__main__":
    main()

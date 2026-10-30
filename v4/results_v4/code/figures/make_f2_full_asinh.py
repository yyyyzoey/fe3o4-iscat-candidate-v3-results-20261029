"""Patch: regenerate F2 common FULL-RANGE montages with a shared asinh display scale."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import AsinhNorm
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

cubes = {k: load(k) for k, _ in CASES}
jmax = max(float(np.max(np.abs(c["J"]))) for c in cubes.values())
norm = AsinhNorm(linear_width=0.02, vmin=-jmax, vmax=jmax)
mo = FIG / "F2_xy_slices" / "montage"
for dname, _ in CASES:
    d = cubes[dname]
    fig, axes = plt.subplots(3, 3, figsize=(9.6, 9.0), layout="constrained")
    for ax, zv in zip(axes.ravel(), ZETA):
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        im = ax.imshow(d["J"][iz], origin="lower", cmap="RdBu_r", norm=norm,
                       extent=[d["x"][0], d["x"][-1], d["y"][0], d["y"][-1]],
                       interpolation="nearest")
        ax.set_title(f"zeta = {d['z'][iz]:+.0f} nm", pad=3)
        ax.axhline(0, color="0.65", lw=0.35); ax.axvline(0, color="0.65", lw=0.35)
    for ax in axes[-1]:
        ax.set_xlabel("x (nm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("y (nm)")
    cb = fig.colorbar(im, ax=axes, shrink=0.72, pad=0.015, aspect=40)
    cb.set_label(f"J (shared model units, full range +-{jmax:.3g}, asinh)")
    fig.suptitle(f"D={d['D']:.0f} nm | 9 xy slices | COMMON FULL RANGE across all 3 diameters "
                 f"(vmin/vmax = +-{jmax:.4g}, asinh linear width +-0.02)", fontsize=9.0)
    fig.savefig(mo / f"{dname}_common_full_montage.png", dpi=200)
    fig.savefig(mo / f"{dname}_common_full_montage.svg")
    plt.close(fig)
    print(dname, "ok")
print("jmax", jmax)

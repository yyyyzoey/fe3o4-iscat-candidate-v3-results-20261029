"""Build V4 final auxiliary figures (F1, F7), montages, raw-pixel zooms, tables, metrics.

Reads the saved HDF5 only; never modifies the data or the optical model.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import h5py

ROOT = Path(__file__).resolve().parents[1]          # work/v4
RES = ROOT / "results_v4"
FIG = RES / "figures"
DATA = RES / "data"
TAB = RES / "tables"
RELEASE = ROOT.parents[1] / "outputs" / "release"

CASES = (("D030", 30.0), ("D100", 100.0), ("D200", 200.0))
ZETA = [-170.0, -128.0, -86.0, -42.0, 0.0, 42.0, 86.0, 128.0, 170.0]
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 110,
                     "savefig.dpi": 200, "axes.unicode_minus": True})


def load(d):
    with h5py.File(DATA / f"{d}nm" / "cube.h5", "r") as f:
        J = f["signals/I_cross"][:]
        Ire = f["signals/I_ref"][:]
        Isc = f["signals/I_scat"][:]
        Itot = f["signals/I_total"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
        z = f["coords/zeta_nm"][:]
        oil = f["coords/oil_thickness_nm"][:]
        attrs = dict(f.attrs)
    return dict(J=J, Iref=Ire, Iscat=Isc, Itot=Itot, x=x, y=y, z=z, oil=oil, attrs=attrs)


def montage(d, mode, jmax_common, out_png, out_svg):
    cube_j = d["J"]
    jmax = float(np.max(np.abs(cube_j)))
    fig, axes = plt.subplots(3, 3, figsize=(10.2, 9.6), sharex=True, sharey=True)
    for ax, zv in zip(axes.ravel(), ZETA):
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        a = cube_j[iz] / (jmax if mode == "shape" else jmax_common)
        lim = 1.0 if mode == "shape" else 0.25
        im = ax.imshow(a, origin="lower", cmap="RdBu_r", vmin=-lim, vmax=lim,
                       extent=[d["x"][0], d["x"][-1], d["y"][0], d["y"][-1]])
        ax.set_title(f"zeta = {d['z'][iz]:+.0f} nm")
        ax.axhline(0, color="0.7", lw=0.3); ax.axvline(0, color="0.7", lw=0.3)
    for ax in axes[-1]:
        ax.set_xlabel("x (nm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("y (nm)")
    cb = fig.colorbar(im, ax=axes, shrink=0.75, pad=0.02)
    cb.set_label("J / max_cube|J|" if mode == "shape" else "J (model units, shared scale)")
    norm = ("one constant = max_cube|J| for this diameter" if mode == "shape"
            else f"shared model-unit scale, D=30 cube max|J| = {jmax_common:.6g}")
    fig.suptitle(f"D={d['attrs']['diameter_nm']:.0f} nm | I_cross=J | 9 xy slices ({mode})\n"
                 f"normalization: {norm}", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_png); fig.savefig(out_svg); plt.close(fig)


def zoom_slices(d, mode, jmax_common, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    lo, hi = -300.0, 300.0
    ix = np.where((d["x"] >= lo) & (d["x"] <= hi))[0]
    iy = np.where((d["y"] >= lo) & (d["y"] <= hi))[0]
    jmax = float(np.max(np.abs(d["J"])))
    xs, ys = d["x"][ix], d["y"][iy]
    files = []
    for zv in ZETA:
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        raw = d["J"][iz][np.ix_(iy, ix)]
        a = raw / (jmax if mode == "shape" else jmax_common)
        vmax = 1.0 if mode == "shape" else 0.25
        fig, ax = plt.subplots(figsize=(4.6, 4.0))
        im = ax.imshow(a, origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                       extent=[xs[0], xs[-1], ys[0], ys[-1]], interpolation="nearest")
        ax.set_title(f"D={d['attrs']['diameter_nm']:.0f} nm, zeta={d['z'][iz]:+.0f} nm ({mode})")
        ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
        cb = fig.colorbar(im, ax=ax, shrink=0.85)
        cb.set_label("J / max_cube|J|" if mode == "shape" else "J (model units, shared)")
        fig.tight_layout()
        name = f"zoom_{mode}_xy_{d['z'][iz]:+.1f}.png"
        fig.savefig(outdir / name, dpi=150); plt.close(fig)
        files.append(name)
    # montage of the 9 zooms
    fig, axes = plt.subplots(3, 3, figsize=(9.0, 8.6), sharex=True, sharey=True)
    for ax, zv in zip(axes.ravel(), ZETA):
        iz = int(np.argmin(np.abs(d["z"] - zv)))
        a = d["J"][iz][np.ix_(iy, ix)] / (jmax if mode == "shape" else jmax_common)
        vmax = 1.0 if mode == "shape" else 0.25
        im = ax.imshow(a, origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                       extent=[xs[0], xs[-1], ys[0], ys[-1]], interpolation="nearest")
        ax.set_title(f"zeta={d['z'][iz]:+.0f} nm")
    for ax in axes[-1]: ax.set_xlabel("x (nm)")
    for ax in axes[:, 0]: ax.set_ylabel("y (nm)")
    cb = fig.colorbar(im, ax=axes, shrink=0.75, pad=0.02)
    cb.set_label("J / max_cube|J|" if mode == "shape" else "J (model units, shared)")
    fig.suptitle(f"D={d['attrs']['diameter_nm']:.0f} nm | zoom +-300 nm, raw 10 nm grid pixels (no interpolation) | {mode}", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(outdir / f"zoom_{mode}_montage.png")
    fig.savefig(outdir / f"zoom_{mode}_montage.svg")
    plt.close(fig)
    return files


def f1_geometry():
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.axhspan(-2.2, 0, color="#dce9f5", zorder=0)
    ax.axhline(0, color="0.35", lw=1.4)
    ax.text(-1.55, -1.9, "glass  n_g=1.52  (t_g=170 um)", fontsize=8.5)
    ax.text(-1.55, -1.55, "design oil  t_i*=100 um, n_i=1.52", fontsize=8.5)
    ax.text(-1.55, -1.2, "water  n_s=1.33", fontsize=8.5)
    D = 200.0
    a = D / 2
    zp = a
    cx, cy = 0.0, 0.0
    th = np.linspace(0, np.pi, 200)
    ax.fill_between(cx + a*np.cos(th)/100, cy, cy + a*np.sin(th)/100,
                    color="#6b4b2a", alpha=0.85, zorder=3)
    ax.text(cx, zp/100 + 0.16, "Fe$_3$O$_4$ sphere\nD=30/100/200 nm\nn=2.3456+0.0926i",
            ha="center", fontsize=8.2)
    ax.annotate("", xy=(0, zp/100), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", lw=0.9, color="0.2"))
    ax.text(0.06, zp/200, "z_p = D/2\n(surface gap = 0)", fontsize=8)
    ax.plot([0], [0], marker="o", ms=3.5, color="k")
    zeta = 170.0
    ax.annotate("", xy=(0, (zp+zeta)/100), xytext=(0, zp/100),
                arrowprops=dict(arrowstyle="<->", lw=1.1, color="#b2182b"))
    ax.text(0.08, (zp+zeta*0.55)/100, "zeta = focus offset\n(sampled -170:2:170 nm)",
            color="#b2182b", fontsize=8)
    ax.plot([-1.3, 1.3], [(zp-zeta)/100]*2, color="#b2182b", ls=":", lw=0.9)
    ax.plot([-1.3, 1.3], [(zp+zeta)/100]*2, color="#b2182b", ls=":", lw=0.9)
    ax.text(1.0, (zp-zeta)/100-0.09, "zeta=-170 nm", fontsize=7.5, color="#b2182b")
    ax.text(1.0, (zp+zeta)/100+0.04, "zeta=+170 nm", fontsize=7.5, color="#b2182b")
    ax.text(-1.55, 1.55, "Schematic, not a solution. The particle is fixed at z_p=D/2;\n"
                         "only the focus is scanned. The x,y plane is the image-plane coordinate.",
            fontsize=8)
    ax.text(-1.55, 1.25, "Per layer: t_i = 100000 - zeta - (1.52/1.33) z_p  nm  [paper Eq. (7)]",
            fontsize=8, color="#2166ac")
    ax.set_xlim(-1.6, 1.6); ax.set_ylim(-2.3, 1.9)
    ax.set_xlabel("x (um)"); ax.set_ylabel("z (um)")
    ax.set_title("F1 | geometry and through-focus scan definition")
    fig.tight_layout()
    (FIG / "F1_geometry_method").mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "F1_geometry_method" / "F1_geometry_method.png")
    fig.savefig(FIG / "F1_geometry_method" / "F1_geometry_method.svg")
    plt.close(fig)


def f7_long():
    target = RELEASE / "diagnostics/target_long"
    control = RELEASE / "diagnostics/paper_control_long"
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    for name, lab in (("D030_axis.csv", "D=30 nm"), ("D100_axis.csv", "D=100 nm"),
                      ("D200_axis.csv", "D=200 nm")):
        a = np.loadtxt(target / name, delimiter=",", skiprows=1)
        ax.plot(a[:, 0], a[:, 6], lw=1.0, label=lab)
    ax.axvspan(-170, 170, color="#fddbc7", alpha=0.7, zorder=0)
    ax.axvline(-170, color="#b2182b", lw=0.8, ls="--"); ax.axvline(170, color="#b2182b", lw=0.8, ls="--")
    ax.set_xlabel("zeta (nm)"); ax.set_ylabel("contrast_fixed_reference")
    ax.set_title("F7 | long-range axial diagnostic (target Fe3O4, NA=1.45)\n"
                 "shaded: +-170 nm window of the delivered 3D cubes", fontsize=9.5)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    ax = axes[1]
    a = np.loadtxt(control / "D120_axis.csv", delimiter=",", skiprows=1)
    ax.plot(a[:, 0], a[:, 6], lw=1.1, color="#2166ac")
    ax.axvspan(-170, 170, color="#fddbc7", alpha=0.7, zorder=0)
    ax.set_xlabel("zeta (nm)"); ax.set_ylabel("contrast_fixed_reference")
    ax.set_title("paper-parameter control: D=120 nm PS, NA=1.35\n(diagnostic only; not the main target)", fontsize=9.5)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    (FIG / "F7_long_range").mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "F7_long_range" / "F7_long_range_diagnostic.png")
    fig.savefig(FIG / "F7_long_range" / "F7_long_range_diagnostic.svg")
    plt.close(fig)


def tables_and_metrics():
    rows = []
    for dname, D in CASES:
        d = load(dname)
        J = d["J"]; z = d["z"]
        ax_j = J[:, 120, 120]
        ipk = int(np.argmax(ax_j)); ivl = int(np.argmin(ax_j))
        rows.append(dict(
            diameter_nm=D, shape="171x241x241", zeta_layers=len(z),
            cube_max_abs_J=float(np.max(np.abs(J))),
            cube_min_J=float(J.min()), cube_max_J=float(J.max()),
            axis_peak_zeta_nm=float(z[ipk]), axis_peak_J=float(ax_j[ipk]),
            axis_valley_zeta_nm=float(z[ivl]), axis_valley_J=float(ax_j[ivl]),
            center_zeta0_J=float(ax_j[85]),
            I_ref_min=float(d["Iref"].min()), I_scat_max=float(d["Iscat"].max()),
            I_total_max=float(d["Itot"].max()),
            oil_t_first_nm=float(d["oil"][0]), oil_t_last_nm=float(d["oil"][-1]),
        ))
        # tables
        with (TAB / f"axis_{dname}.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["zeta_nm", "J_I_cross", "J_div_max_cube_absJ", "I_ref", "I_scat",
                        "I_total", "contrast_fixed_reference"])
            jmax = float(np.max(np.abs(J)))
            for iz, zv in enumerate(z):
                w.writerow([f"{zv:.1f}", repr(float(ax_j[iz])), repr(float(ax_j[iz]/jmax)),
                            repr(float(d["Iref"][iz, 120, 120])), repr(float(d["Iscat"][iz, 120, 120])),
                            repr(float(d["Itot"][iz, 120, 120])),
                            repr(float((d["Iscat"][iz,120,120]+ax_j[iz])/d["Iref"][iz,120,120]))])
    with (TAB / "metrics.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    # long-range table (copy)
    import shutil
    shutil.copy2(RELEASE / "diagnostics/axis_profiles.csv", TAB / "axis_profiles_long_range.csv")
    return rows


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    f1_geometry()
    f7_long()
    rows = tables_and_metrics()
    cubes = {k: load(k) for k, _ in CASES}
    jmax_common = max(float(np.max(np.abs(c["J"]))) for c in cubes.values())
    summary = {"jmax_common": jmax_common, "cases": {}}
    for dname, D in CASES:
        d = cubes[dname]
        out = FIG / "F2_xy_slices" / "montage"
        out.mkdir(parents=True, exist_ok=True)
        montage(d, "shape", jmax_common, out / f"{dname}_shape_montage.png", out / f"{dname}_shape_montage.svg")
        montage(d, "common", jmax_common, out / f"{dname}_common_montage.png", out / f"{dname}_common_montage.svg")
        fz_shape = zoom_slices(d, "shape", jmax_common, FIG / "F2_xy_slices" / "zoom" / dname)
        fz_common = zoom_slices(d, "common", jmax_common, FIG / "F2_xy_slices" / "zoom" / dname)
        summary["cases"][dname] = {"zoom_shape": fz_shape, "zoom_common": fz_common}
    (ROOT / "build" / "figure_generation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"jmax_common": jmax_common, "metrics": rows}, indent=2))


if __name__ == "__main__":
    main()




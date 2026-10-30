"""Step 4 - centre-axis (x = y = 0) through-focus curves for the three sizes.

Read-only: values come straight from the saved cubes, all 171 zeta layers.
"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np
import matplotlib.pyplot as plt

import vis_common as C


def centre_series(tag):
    import h5py
    with h5py.File(C.cube_path(tag), "r") as f:
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
        i0 = int(np.argmin(np.abs(x)))
        i1 = int(np.argmin(np.abs(y)))
        out = {"zeta_nm": z}
        for name in ("I_cross", "I_total", "I_ref", "I_scat"):
            out[name] = f[f"signals/{name}"][:, i1, i0]
        out["ix0"] = int(i0)
        out["iy0"] = int(i1)
        out["x0_nm"] = float(x[i0])
        out["y0_nm"] = float(y[i1])
    return out


def main():
    C.apply_style()
    C.ensure_dirs()
    log = C.StepLog("step4_axis")

    series = {tag: centre_series(tag) for tag, _, _ in C.CASES}
    z = series["D030"]["zeta_nm"]

    rows = []
    for tag, D, h in C.CASES:
        s = series[tag]
        for k, zz in enumerate(z):
            rows.append({
                "diameter_nm": D,
                "tag": tag,
                "centre_height_nm": h,
                "zeta_nm": float(zz),
                "I_cross": float(s["I_cross"][k]),
                "I_total": float(s["I_total"][k]),
                "I_ref": float(s["I_ref"][k]),
                "I_scat": float(s["I_scat"][k]),
            })
    fields = list(rows[0])
    with (C.EXPORT / "axis_curves_center.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    peaks = {}
    for tag, D, h in C.CASES:
        s = series[tag]
        v = s["I_cross"]
        pm = float(np.abs(v).max())
        peaks[tag] = {
            "diameter_nm": D,
            "centre_point_nm": [s["x0_nm"], s["y0_nm"]],
            "max_abs_I_cross_on_axis": pm,
            "zeta_of_max": float(z[int(np.argmax(v))]),
            "zeta_of_min": float(z[int(np.argmin(v))]),
            "I_cross_at_zeta_0": float(v[int(np.argmin(np.abs(z)))]),
        }
    (C.EXPORT / "axis_curves_summary.json").write_text(
        json.dumps({"note": "x = y = 0 nm axis of the saved through-focus cubes; "
                            "zeta is defocus, not sample depth",
                    "n_layers": int(z.size), "series": peaks}, indent=2),
        encoding="utf-8")

    colours = {"D030": "#1b7837", "D100": "#c51b7d", "D200": "#2166ac"}
    fig = plt.figure(figsize=(10.6, 3.5))
    gs = fig.add_gridspec(1, 3, left=0.055, right=0.985, top=0.80, bottom=0.17, wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    for tag, D, h in C.CASES:
        s = series[tag]
        ax.plot(z, s["I_cross"], color=colours[tag], lw=1.1, label=f"{D} nm")
    ax.axhline(0, color="0.4", lw=0.5, ls=(0, (3, 2)))
    ax.set_xlabel(r"zeta (nm)")
    ax.set_ylabel(r"$I_\mathrm{cross}$ at $x=y=0$")
    ax.set_title("(a) signed $I_\\mathrm{cross}$ - linear scale", fontsize=8.6)
    ax.legend(fontsize=6.8, frameon=False, loc="upper left")
    # D030 is ~48x weaker than D100, so give it its own scale in an inset rather
    # than inflating the main axis or silently rescaling the data
    ins = ax.inset_axes([0.56, 0.10, 0.40, 0.34])
    s30 = series["D030"]
    ins.plot(z, s30["I_cross"], color=colours["D030"], lw=0.9)
    ins.axhline(0, color="0.45", lw=0.4, ls=(0, (3, 2)))
    ins.set_title("D030, own y-scale", fontsize=6.2, pad=2)
    ins.tick_params(labelsize=5.4, length=1.5, width=0.4)
    ins.set_xlabel("zeta (nm)", fontsize=5.6, labelpad=1)
    ins.set_facecolor("white")
    for sp in ins.spines.values():
        sp.set_linewidth(0.5)
        sp.set_color("0.55")

    ax = fig.add_subplot(gs[0, 1])
    for tag, D, h in C.CASES:
        s = series[tag]
        ax.semilogy(z, np.abs(s["I_cross"]) + 1e-12, color=colours[tag], lw=1.1,
                    label=f"{D} nm")
    ax.set_xlabel(r"zeta (nm)")
    ax.set_ylabel(r"$|I_\mathrm{cross}|$ (log)")
    ax.set_title("(b) magnitude - log scale (dynamic range)", fontsize=8.6)
    ax.grid(alpha=0.25, lw=0.4)

    ax = fig.add_subplot(gs[0, 2])
    for tag, D, h in C.CASES:
        s = series[tag]
        v = s["I_cross"] / np.abs(s["I_cross"]).max()
        ax.plot(z, v, color=colours[tag], lw=1.1, label=f"{D} nm")
    ax.axhline(0, color="0.4", lw=0.5, ls=(0, (3, 2)))
    ax.set_xlabel(r"zeta (nm)")
    ax.set_ylabel(r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$")
    ax.set_title("(c) shape only - per-particle normalisation", fontsize=8.6)
    for a in (ax,):
        pass
    for a in fig.axes:
        a.tick_params(labelsize=7.0, length=2, width=0.5)
        for sp in a.spines.values():
            sp.set_linewidth(0.6)
            sp.set_color("0.45")
        a.set_xlim(z[0], z[-1])

    fig.suptitle(r"Fe$_3$O$_4$ single sphere on a surface - centre-axis through-focus response "
                 r"($\lambda$ = 532 nm, target NA = 1.45; $z_\mathrm{centre}$ = "
                 r"15 / 50 / 100 nm)", fontsize=9.4, y=0.965)
    fig.text(0.5, 0.905, r"all 171 saved zeta layers; zeta is the defocus coordinate of the "
             r"through-focus stack, not a sample-space depth",
             ha="center", va="top", fontsize=7.2, color="0.3")
    png = C.FIG / "compare_three_sizes_axis_curves.png"
    fig.savefig(png, dpi=330, facecolor="white")
    fig.savefig(png.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    log.record("axis_curves", {"file": png.name, "bytes": png.stat().st_size,
                               "n_rows": len(rows)})
    log.done({"csv": str(C.EXPORT / "axis_curves_center.csv")})
    print(json.dumps({"ok": True, "peaks": peaks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

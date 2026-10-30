"""Step 2 - 50-layer 2D slice montages, per-diameter atlases, decompositions
and the three-diameter comparison sheets. Read-only w.r.t. the physics."""
from __future__ import annotations

import json

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

import vis_common as C

CMAP_SIGNED = "RdBu_r"
CMAP_POS = "viridis"
CMAP_POS2 = "magma"


def fmt_z(z: float, unit: bool = True) -> str:
    s = "0" if abs(z) < 0.5 else f"{z:+.0f}"
    return s + (" nm" if unit else "")


def imshow_slice(ax, data, vmin, vmax, cmap=CMAP_SIGNED):
    ext = [-C.HALF_NM, C.HALF_NM, -C.HALF_NM, C.HALF_NM]
    return ax.imshow(data, origin="lower", extent=ext, cmap=cmap,
                     vmin=vmin, vmax=vmax, interpolation="bilinear",
                     aspect="equal", rasterized=True)


def tidy(ax, row, col, nrow, ncol):
    ax.set_xticks([-400, -200, 0, 200, 400])
    ax.set_yticks([-400, -200, 0, 200, 400])
    ax.set_xticklabels(["-400", "-200", "0", "200", "400"] if row == nrow - 1 else [])
    ax.set_yticklabels(["-400", "-200", "0", "200", "400"] if col == 0 else [])
    if row == nrow - 1:
        ax.set_xlabel("x (nm)", labelpad=1.5)
    if col == 0:
        ax.set_ylabel("y (nm)", labelpad=1.5)
    for s in ax.spines.values():
        s.set_linewidth(0.4)
        s.set_color("0.65")
    ax.tick_params(length=2, width=0.4, pad=1.0)


def montage(tag, D, h, layers, vlim, mode, out_stem, log, asinh_thresh=None):
    """mode: 'common' | 'normalized'; asinh_thresh enables the HDR variant."""
    cube = C.load_cube(tag)
    V = cube["I_cross"]
    pmax = float(np.abs(V).max())
    fig = plt.figure(figsize=(15.6, 9.0))
    gs = fig.add_gridspec(5, 10, left=0.055, right=0.985, top=0.875,
                          bottom=0.135, wspace=0.07, hspace=0.20)

    def tr(a):
        if asinh_thresh is None:
            return a
        return np.arcsinh(a / asinh_thresh)

    if asinh_thresh is None:
        lim = vlim if mode == "common" else pmax
        data_lim = (-lim, lim) if mode == "common" else (-1.0, 1.0)
    else:
        lim = float(tr(np.array([vlim]))[0])
        data_lim = (-lim, lim)

    for k, r in enumerate(layers):
        ax = fig.add_subplot(gs[k // 10, k % 10])
        d = V[r["index"]]
        if mode == "normalized":
            d = d / pmax
        d = tr(d)
        imshow_slice(ax, d, data_lim[0], data_lim[1])
        ax.set_title(fmt_z(r["actual_zeta_nm"]), pad=2.0, fontsize=7.2)
        tidy(ax, k // 10, k % 10, 5, 10)

    if asinh_thresh is not None:
        sub = (r"asinh stretch, shared linear threshold $I_0$ = "
               f"{asinh_thresh:g}, symmetric to $\\pm${vlim:.4g} (common scale)")
        cbl = "I_cross (dimensionless, common scale, asinh)"
    elif mode == "common":
        sub = ("common scale shared by all three diameters, "
               f"$\\pm${vlim:.4g}")
        cbl = "I_cross (dimensionless, common scale)"
    else:
        sub = (r"$I_\mathrm{cross}\,/\,\max|I_\mathrm{cross}|$ for this particle "
               f"(per-particle normalisation, max = {pmax:.4g})")
        cbl = r"$I_\mathrm{cross}\,/\,\max|I_\mathrm{cross}|$"

    fig.suptitle(
        f"Fe$_3$O$_4$  D = {D} nm, centre height {h:.0f} nm  -  50 selected zeta planes "
        f"({fmt_z(layers[0]['actual_zeta_nm'])} to {fmt_z(layers[-1]['actual_zeta_nm'])})\n"
        f"$I_\\mathrm{{cross}} = 2\\,\\mathrm{{Re}}(E_\\mathrm{{ref}}^*\\cdot E_\\mathrm{{scat}})$, signed, " + sub,
        fontsize=10.0, y=0.972, linespacing=1.4)

    cax = fig.add_axes([0.325, 0.055, 0.35, 0.011])
    m = ScalarMappable(norm=Normalize(data_lim[0], data_lim[1]),
                       cmap=plt.get_cmap(CMAP_SIGNED))
    cb = fig.colorbar(m, cax=cax, orientation="horizontal")
    cb.set_label(cbl, fontsize=7.5, labelpad=3)
    cb.ax.tick_params(labelsize=6.5, length=2, width=0.4)
    cb.outline.set_linewidth(0.4)
    if asinh_thresh is not None:
        ticks = [vlim * f for f in (-1, -0.3, -0.1, -0.03, 0, 0.03, 0.1, 0.3, 1)]
        cb.set_ticks([float(tr(np.array([t]))[0]) for t in ticks])
        cb.set_ticklabels([f"{t:+.3g}" if t else "0" for t in ticks])

    png = C.FIG / f"{out_stem}.png"
    fig.savefig(png, dpi=320, facecolor="white")
    fig.savefig(C.FIG / f"{out_stem}.pdf", facecolor="white")
    plt.close(fig)
    log.record("montage", {"file": png.name, "bytes": png.stat().st_size,
                           "layers": len(layers), "vlim": float(vlim),
                           "mode": mode, "asinh": asinh_thresh is not None})
    return png


def atlas(tag, D, h, layers, vlim, mode, out_pdf, log):
    cube = C.load_cube(tag)
    V = cube["I_cross"]
    pmax = float(np.abs(V).max())
    per_page = 9
    with PdfPages(out_pdf) as pdf:
        for pg in range(0, len(layers), per_page):
            chunk = layers[pg:pg + per_page]
            fig = plt.figure(figsize=(11.69, 8.27))
            gs = fig.add_gridspec(3, 3, left=0.06, right=0.90, top=0.90,
                                  bottom=0.07, wspace=0.12, hspace=0.24)
            im = None
            for k, r in enumerate(chunk):
                ax = fig.add_subplot(gs[k // 3, k % 3])
                if mode == "normalized":
                    d, lim = V[r["index"]] / pmax, 1.0
                else:
                    d, lim = V[r["index"]], vlim
                im = imshow_slice(ax, d, -lim, lim)
                ax.set_title(f"zeta = {fmt_z(r['actual_zeta_nm'])}   (layer {r['index']})",
                             fontsize=9, pad=3)
                tidy(ax, k // 3, k % 3, 3, 3)
            fig.suptitle(f"Fe$_3$O$_4$  D = {D} nm  -  I_cross atlas, page {pg // per_page + 1}"
                         f"  ({mode} scale)", fontsize=12, y=0.962)
            cax = fig.add_axes([0.925, 0.12, 0.014, 0.70])
            cb = fig.colorbar(im, cax=cax)
            cb.set_label(r"$I_\mathrm{cross}$ (dimensionless)" if mode == "common"
                         else r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$", fontsize=9)
            cb.ax.tick_params(labelsize=7.5, length=2, width=0.4)
            cb.outline.set_linewidth(0.4)
            pdf.savefig(fig, facecolor="white")
            plt.close(fig)
        d = pdf.infodict()
        d["Title"] = f"Fe3O4 iSCAT V4.1 - 50-layer I_cross atlas, D = {D} nm ({mode})"
        d["Subject"] = "through-focus xy slices read from results_v4/data; no recomputation"
    log.record("atlas", {"file": out_pdf.name, "bytes": out_pdf.stat().st_size,
                         "pages": int(np.ceil(len(layers) / per_page))})


def decomposition(tag, D, h, log):
    cube = C.load_cube(tag)
    z = cube["zeta"]
    i0 = int(np.argmin(np.abs(z)))
    panels = [
        ("I_cross", CMAP_SIGNED, "signed"),
        ("I_total", CMAP_POS, "pos"),
        ("I_ref", CMAP_POS, "pos"),
        ("I_scat", CMAP_POS2, "pos"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 8.2))
    for ax, (key, cmap, kind) in zip(axes.ravel(), panels):
        d = cube[key][i0]
        if kind == "signed":
            v = float(np.abs(d).max())
            im = imshow_slice(ax, d, -v, v, cmap)
            lbl = r"$I_\mathrm{cross}$ (dimensionless)"
        else:
            v = float(np.percentile(d, 99.9))
            im = imshow_slice(ax, d, 0.0, v, cmap)
            lbl = {"I_total": r"$I_\mathrm{total}$", "I_ref": r"$I_\mathrm{ref}$",
                   "I_scat": r"$I_\mathrm{scat}$"}[key] + " (dimensionless)"
        ax.set_title(f"${key.replace('_', chr(92) + '_')}$   zeta = {fmt_z(z[i0])}", fontsize=9.5)
        ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
        for s in ax.spines.values():
            s.set_linewidth(0.5)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label(lbl, fontsize=7.0)
        cb.ax.tick_params(labelsize=6.5, length=2, width=0.4)
        cb.outline.set_linewidth(0.4)
    fig.suptitle(
        f"Fe$_3$O$_4$  D = {D} nm (centre height {h:.0f} nm)  -  signal decomposition at zeta = 0\n"
        r"$I_\mathrm{total}=I_\mathrm{ref}+I_\mathrm{cross}+I_\mathrm{scat}$,   "
        r"$I_\mathrm{cross}=2\,\mathrm{Re}(E_\mathrm{ref}^*\cdot E_\mathrm{scat})$",
        fontsize=9.5, y=0.985, linespacing=1.45)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.90, bottom=0.06,
                        wspace=0.28, hspace=0.22)
    png = C.FIG / f"{tag}_signal_decomposition.png"
    fig.savefig(png, dpi=320, facecolor="white")
    fig.savefig(C.FIG / f"{tag}_signal_decomposition.pdf", facecolor="white")
    plt.close(fig)
    log.record("decomposition", {"file": png.name, "bytes": png.stat().st_size})


def compare_slices(layers_all, vlim, log):
    key_pos = [0, 6, 12, 18, 24, 30, 36, 42, 49]
    cubes = {t: C.load_cube(t) for t, _, _ in C.CASES}
    for mode in ("normalized", "common"):
        fig, axes = plt.subplots(3, len(key_pos), figsize=(15.0, 5.6))
        for row, (tag, D, h) in enumerate(C.CASES):
            cube = cubes[tag]
            layers = layers_all[tag]
            pmax = float(np.abs(cube["I_cross"]).max())
            for col, kp in enumerate(key_pos):
                r = layers[kp]
                ax = axes[row, col]
                if mode == "normalized":
                    im = imshow_slice(ax, cube["I_cross"][r["index"]] / pmax, -1, 1)
                else:
                    im = imshow_slice(ax, cube["I_cross"][r["index"]], -vlim, vlim)
                if row == 0:
                    ax.set_title(fmt_z(r["actual_zeta_nm"]), fontsize=8, pad=3)
                ax.set_xticks([-400, 0, 400]); ax.set_yticks([-400, 0, 400])
                ax.set_xticklabels(["-400", "0", "400"] if row == 2 else [], fontsize=6)
                ax.set_yticklabels(["-400", "0", "400"] if col == 0 else [], fontsize=6)
                ax.tick_params(length=2, width=0.4, pad=1)
                for s in ax.spines.values():
                    s.set_linewidth(0.4); s.set_color("0.65")
            fig.text(0.012, 0.80 - row * 0.283, f"D = {D} nm\nh = {h:.0f} nm",
                     fontsize=7.8, va="center", ha="left", linespacing=1.4)
        cax = fig.add_axes([0.27, 0.075, 0.46, 0.017])
        lim = 1.0 if mode == "normalized" else vlim
        cb = fig.colorbar(ScalarMappable(norm=Normalize(-lim, lim),
                                         cmap=plt.get_cmap(CMAP_SIGNED)),
                          cax=cax, orientation="horizontal")
        cb.set_label(r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$ (per particle)" if mode == "normalized"
                     else r"$I_\mathrm{cross}$ (common scale across diameters)", fontsize=7.8)
        cb.ax.tick_params(labelsize=6.8, length=2, width=0.4)
        cb.outline.set_linewidth(0.4)
        ttl = ("per-particle normalised (shape comparison)" if mode == "normalized"
               else "common colour scale (amplitude comparison)")
        fig.suptitle("Three-diameter comparison at nine key zeta planes  -  " + ttl,
                     fontsize=10.5, y=0.975)
        fig.subplots_adjust(left=0.075, right=0.99, top=0.87, bottom=0.19,
                            wspace=0.05, hspace=0.06)
        name = "compare_three_sizes_key_slices" + ("" if mode == "normalized" else "_common")
        fig.savefig(C.FIG / f"{name}.png", dpi=320, facecolor="white")
        fig.savefig(C.FIG / f"{name}.pdf", facecolor="white")
        plt.close(fig)
        log.record("compare_slices", {"file": name, "mode": mode})


def main() -> int:
    C.apply_style()
    C.ensure_dirs()
    log = C.StepLog("step2_2d")
    vlim = C.common_scale()
    layers_all = {t: C.layer_index(t) for t, _, _ in C.CASES}

    for tag, D, h in C.CASES:
        layers = layers_all[tag]
        montage(tag, D, h, layers, vlim, "common", f"{tag}_50slice_montage_common", log)
        montage(tag, D, h, layers, vlim, "normalized", f"{tag}_50slice_montage_normalized", log)
        montage(tag, D, h, layers, vlim, "common", f"supplement/{tag}_50slice_montage_common_asinh",
                log, asinh_thresh=0.01)
        atlas(tag, D, h, layers, vlim, "common", C.FIG / f"{tag}_50slice_atlas_common.pdf", log)
        atlas(tag, D, h, layers, vlim, "normalized",
              C.FIG / f"{tag}_50slice_atlas_normalized.pdf", log)
        decomposition(tag, D, h, log)

    compare_slices(layers_all, vlim, log)
    n = len(list(C.FIG.rglob("*.png"))) + len(list(C.FIG.rglob("*.pdf")))
    log.done({"files": n})
    print(json.dumps({"ok": True, "vlim": vlim, "files": n, "dir": str(C.FIG)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Step 3 - 3D renderings from the saved cubes.

The z axis of every 3D object is the *defocus* zeta, not physical depth: these
objects are displays of the through-focus stack, not a reconstruction of the
sample-space near field.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import vis_common as C


def fmt_z(z):
    return "0" if abs(z) < 0.5 else f"{z:+.0f}"


def build_quads(X, Z, kz):
    """One quad per (layer, cell), C order: layer major, then row, then column."""
    xi, yi = np.meshgrid(X, X)
    px = np.stack([xi[:-1, :-1], xi[:-1, 1:], xi[1:, 1:], xi[1:, :-1]], axis=-1)
    py = np.stack([yi[:-1, :-1], yi[:-1, 1:], yi[1:, 1:], yi[1:, :-1]], axis=-1)
    nz = len(Z)
    quads = np.empty((nz,) + px.shape[:2] + (4, 3))
    quads[..., 0] = px[None]
    quads[..., 1] = py[None]
    quads[..., 2] = (np.asarray(Z, dtype=float) * kz)[:, None, None, None]
    return quads.reshape(-1, 4, 3)


def face_colors(V, vmin, vmax, cmap, alpha_mode, alpha_gamma=1.8):
    """Per-quad RGBA for the (nz, ny, nx) stack of the 50 selected planes.

    ``alpha_mode='value'`` makes the transparency follow |I_cross| so that the
    near-zero background of every plane stays transparent instead of building
    up into an opaque white slab.  ``'uniform'`` is kept for reference only.

    The colour fade along zeta ("depth fog") is a *display* device that helps
    the eye separate 50 stacked planes; it is not applied to any saved number.
    """
    vf = 0.25 * (V[:, :-1, :-1] + V[:, :-1, 1:] + V[:, 1:, :-1] + V[:, 1:, 1:])
    norm = Normalize(vmin, vmax)
    rgba = plt.get_cmap(cmap)(norm(vf))
    if alpha_mode == "uniform":
        a = np.full(vf.shape, 0.28)
    else:
        vn = np.abs(vf) / max(abs(vmin), abs(vmax), 1e-30)
        # super-linear ramp: the near-zero background of a plane becomes fully
        # transparent, so 50 stacked planes no longer add up to an opaque slab
        a = np.clip(0.96 * np.clip(vn - 0.02, 0.0, None) ** alpha_gamma, 0.0, 0.94)
    rgba[..., 3] = a
    nz = vf.shape[0]
    fade = np.linspace(0.70, 1.00, nz)[:, None, None, None]
    rgba[..., :3] = 1.0 - (1.0 - rgba[..., :3]) * fade
    return rgba.reshape(-1, 4)


def render_3d(V, X, Z, vmin, vmax, kz, out_png, title, sub, cbl, log,
              alpha_mode="value", elev=26.0, azim=-58.0, note=None,
              alpha_gamma=1.8, cut_x=None):
    quads = build_quads(X, Z, kz)
    cols = face_colors(V, vmin, vmax, "RdBu_r", alpha_mode, alpha_gamma)
    if cut_x is not None:
        cx = quads[:, :, 0].mean(axis=1)
        cols[cx > cut_x, 3] = 0.0

    fig = plt.figure(figsize=(9.4, 7.1))
    ax = fig.add_axes([0.005, 0.015, 0.865, 0.925], projection="3d")
    pc = Poly3DCollection(quads, facecolors=cols, edgecolors="none",
                          linewidths=0.0, rasterized=True)
    pc.set_zsort("average")
    ax.add_collection3d(pc)

    lim = float(X[-1])
    zl = 170.0 * kz
    # ladder of plane outlines: keeps the 50-layer geometry readable even when
    # the data on a plane is nearly zero (e.g. D030 on the three-size scale)
    sq = np.array([[-lim, -lim], [lim, -lim], [lim, lim], [-lim, lim], [-lim, -lim]])
    Zz = np.asarray(Z, dtype=float) * kz
    for k, zz in enumerate(Zz):
        # one full outline every five layers: enough to read the 50-plane ladder
        # without the 50 grey squares swamping the data
        if k % 5 != 0 and k != len(Zz) - 1:
            continue
        emph = (k % 10 == 0)
        ax.plot(sq[:, 0], sq[:, 1], np.full(5, zz),
                color="0.55" if emph else "0.80",
                lw=0.9 if emph else 0.45, zorder=1, solid_capstyle="butt")
    # a 50-tick ruler on the back wall so every single plane is countable
    tk = 0.035 * (2 * lim)
    for zz in Zz:
        ax.plot([-lim, -lim + tk], [-lim, -lim], [zz, zz], color="0.74", lw=0.45, zorder=1)
    # focal plane marker
    ax.plot(sq[:, 0], sq[:, 1], np.zeros(5), color="0.35", lw=0.8,
            ls=(0, (4, 3)), zorder=1)

    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-zl, zl)
    ax.set_box_aspect((2 * lim, 2 * lim, 2 * zl))
    ax.set_proj_type("ortho")
    ax.view_init(elev=elev, azim=azim)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 0))
        axis.pane.set_edgecolor((0.72, 0.72, 0.72, 1))
        axis._axinfo["grid"]["color"] = (0.90, 0.90, 0.90, 1)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax.set_xlabel("x (nm)", labelpad=1, fontsize=9)
    ax.set_ylabel("y (nm)", labelpad=1, fontsize=9)
    ax.set_zlabel("zeta (nm)" + ("" if kz == 1 else f"  (x{kz:g} display)"), labelpad=2, fontsize=9)
    ax.set_xticks([-300, 0, 300]); ax.set_yticks([-300, 0, 300])
    ax.set_zticks([-170, 0, 170])
    ax.tick_params(labelsize=7.5, pad=-1)
    fig.suptitle(title, fontsize=10.0, y=0.975, linespacing=1.4)
    fig.text(0.5, 0.945, sub, ha="center", va="top", fontsize=7.6, color="0.25")
    if note:
        fig.text(0.5, 0.055, note, ha="center", va="top", fontsize=7.4, color="0.30")

    cax = fig.add_axes([0.878, 0.30, 0.016, 0.40])
    cb = fig.colorbar(ScalarMappable(norm=Normalize(vmin, vmax),
                                     cmap=plt.get_cmap("RdBu_r")), cax=cax)
    cb.set_label(cbl, fontsize=7.6)
    cb.ax.tick_params(labelsize=6.8, length=2, width=0.4)
    cb.outline.set_linewidth(0.4)
    fig.savefig(out_png, dpi=300, facecolor="white")
    fig.savefig(out_png.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    log.record("render3d", {"file": out_png.name, "bytes": out_png.stat().st_size,
                            "kz": kz, "alpha": alpha_mode,
                            "elev": elev, "azim": azim})
    return out_png


def orthoview(tag, D, h, cube, log):
    V = cube["I_cross"]
    z = cube["zeta"]; x = cube["x"]
    i0 = int(np.argmin(np.abs(z)))
    pmax = float(np.abs(V).max())
    fig = plt.figure(figsize=(11.4, 4.6))
    gs = fig.add_gridspec(1, 3, left=0.06, right=0.90, top=0.80, bottom=0.16, wspace=0.28)

    ax = fig.add_subplot(gs[0, 0])
    ext = [x[0], x[-1], z[0], z[-1]]
    im = ax.imshow(V[:, 0, :].T, origin="lower", extent=ext, cmap="RdBu_r",
                   vmin=-pmax, vmax=pmax, aspect="auto", interpolation="bilinear",
                   rasterized=True)
    ax.set_xlabel("x (nm)"); ax.set_ylabel("zeta (nm)")

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(V[:, :, 0], origin="lower", extent=[x[0], x[-1], z[0], z[-1]],
               cmap="RdBu_r", vmin=-pmax, vmax=pmax, aspect="auto",
               interpolation="bilinear", rasterized=True)
    ax2.set_xlabel("y (nm)"); ax2.set_ylabel("zeta (nm)")

    ax3 = fig.add_subplot(gs[0, 2])
    ax3.imshow(V[i0], origin="lower", extent=[x[0], x[-1], x[0], x[-1]],
               cmap="RdBu_r", vmin=-pmax, vmax=pmax, aspect="equal",
               interpolation="bilinear", rasterized=True)
    ax3.set_xlabel("x (nm)"); ax3.set_ylabel("y (nm)")
    ax3.add_patch(Circle((0, 0), D / 2.0, fill=False, ls=(0, (3, 2)), lw=0.7,
                         ec="0.45", zorder=5))
    for a_ in (ax, ax2, ax3):
        a_.set_xticks([-400, 0, 400]); a_.tick_params(labelsize=6.8, length=2, width=0.4)
        for s in a_.spines.values():
            s.set_linewidth(0.5); s.set_color("0.55")
    ax3.set_yticks([-400, 0, 400])

    cax = fig.add_axes([0.92, 0.20, 0.013, 0.58])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label(r"$I_\mathrm{cross}$ (dimensionless)", fontsize=7.6)
    cb.ax.tick_params(labelsize=6.8, length=2, width=0.4)
    cb.outline.set_linewidth(0.4)
    fig.suptitle(f"Fe$_3$O$_4$  D = {D} nm  (centre height {h:.0f} nm)  -  orthogonal sections of "
                 f"$I_\\mathrm{{cross}}$\n"
                 r"x-z at y = 0 (left), y-z at x = 0 (middle), x-y at zeta = 0 (right; "
                 r"dashed circle = particle outline)", fontsize=9.2, y=0.975, linespacing=1.4)
    png = C.FIG / f"{tag}_orthoview.png"
    fig.savefig(png, dpi=320, facecolor="white")
    fig.savefig(png.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    log.record("orthoview", {"file": png.name, "bytes": png.stat().st_size})


def isosurface(tag, D, h, log):
    from skimage import measure
    V = C.load_cube(tag)["I_cross"]
    z = C.load_cube(tag)["zeta"]
    x = C.load_cube(tag)["x"]
    pmax = float(np.abs(V).max())
    levels = [-0.75, -0.5, -0.25, 0.25, 0.5, 0.75]
    spacing = (float(z[1] - z[0]), float(x[1] - x[0]), float(x[1] - x[0]))
    present, meshes = [], []
    for f in levels:
        lv = f * pmax
        if lv <= V.min() or lv >= V.max():
            present.append({"level_fraction": f, "level": float(lv), "present": False})
            continue
        verts, faces, _, _ = measure.marching_cubes(V, level=lv, spacing=spacing)
        verts[:, 0] -= 0.0
        meshes.append((f, lv, verts, faces))
        present.append({"level_fraction": f, "level": float(lv), "present": True,
                        "n_vertices": int(len(verts)), "n_faces": int(len(faces))})
    for rec in present:
        if not rec["present"]:
            rec["note"] = "not present (level outside data range)"

    fig = plt.figure(figsize=(8.8, 7.4))
    ax = fig.add_axes([0.0, 0.02, 0.88, 0.92], projection="3d")
    cm = plt.get_cmap("RdBu_r")
    norm = Normalize(-pmax, pmax)
    for f, lv, verts, faces in meshes:
        col = cm(norm(lv))
        poly = Poly3DCollection(verts[faces], facecolors=[(col[0], col[1], col[2], 0.42)],
                                edgecolors="none", linewidths=0)
        ax.add_collection3d(poly)
    lim = float(x[-1])
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(z[0], z[-1])
    ax.set_box_aspect((2 * lim, 2 * lim, z[-1] - z[0]))
    ax.set_proj_type("ortho")
    ax.view_init(elev=16, azim=-64)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 0))
        axis.pane.set_edgecolor((0.72, 0.72, 0.72, 1))
        axis._axinfo["grid"]["color"] = (0.90, 0.90, 0.90, 1)
    ax.set_xlabel("x (nm)", fontsize=9, labelpad=1)
    ax.set_ylabel("y (nm)", fontsize=9, labelpad=1)
    ax.set_zlabel("zeta (nm)", fontsize=9, labelpad=2)
    ax.set_xticks([-400, 0, 400]); ax.set_yticks([-400, 0, 400]); ax.set_zticks([-170, 0, 170])
    ax.tick_params(labelsize=7.5, pad=-1)
    n_present = sum(1 for r in present if r["present"])
    fig.suptitle(f"Fe$_3$O$_4$  D = {D} nm  -  iso-surfaces of $I_\\mathrm{{cross}}$ at "
                 f"$\\pm$25/50/75 % of max|$I_\\mathrm{{cross}}$| = {pmax:.4g}",
                 fontsize=9.6, y=0.965)
    fig.text(0.5, 0.935, f"{n_present} of 6 requested levels exist in this cube "
             f"(see {tag}_isosurface_levels.json); z axis = defocus zeta, display object only",
             ha="center", va="top", fontsize=7.4, color="0.25")
    cax = fig.add_axes([0.885, 0.30, 0.016, 0.40])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cm), cax=cax)
    cb.set_label(r"$I_\mathrm{cross}$ level (dimensionless)", fontsize=7.6)
    cb.ax.tick_params(labelsize=6.8, length=2, width=0.4)
    cb.outline.set_linewidth(0.4)
    png = C.FIG / "supplement" / f"{tag}_isosurface.png"
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(png.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    (C.EXPORT / f"{tag}_isosurface_levels.json").write_text(json.dumps(
        {"tag": tag, "diameter_nm": D, "max_abs_I_cross": pmax,
         "levels": present,
         "note": "iso-surfaces of the defocus stack; a display object, not a physical surface"},
        indent=2), encoding="utf-8")
    log.record("isosurface", {"file": png.name, "n_present": n_present})


def main(argv):
    C.apply_style()
    C.ensure_dirs()
    log = C.StepLog("step3_3d")
    vlim = C.common_scale()
    only = argv[1] if len(argv) > 1 else None
    quick = "quick" in argv[2:]

    for tag, D, h in C.CASES:
        if only and only != "all" and tag != only:
            continue
        cube = C.load_cube(tag, half_nm=300.0)
        layers = C.layer_index(tag)
        idx = [r["index"] for r in layers]
        V = cube["I_cross"][idx]
        X = cube["x"]; Z = np.array([r["actual_zeta_nm"] for r in layers])
        pmax = float(np.abs(V).max())

        variants = [1.0] if quick else [1.0, 3.0]
        for kz in variants:
            suffix = "" if kz == 1 else "_zexag3"
            base = "" if kz == 1 else "supplement/"
            common_out = C.FIG / f"{base}{tag}_3d_stack_common{suffix}.png"
            norm_out = C.FIG / f"{base}{tag}_3d_stack_normalized{suffix}.png"
            ztxt = ("; zeta exaggerated x3 for visibility" if kz != 1
                    else "; true physical proportions")
            sub_common = (f"50 zeta planes, all {len(Z)} selected layers, common colour scale "
                          f"$\\pm${vlim:.4g} shared by the three diameters" + ztxt)
            note_common = None
            if tag == "D030":
                note_common = (r"common scale reminder: max$|I_\mathrm{cross}|$ of D030 is "
                               f"{pmax:.4g}, i.e. ~{vlim / pmax:.0f}x smaller than D100, so this "
                               "panel is deliberately almost blank; see the normalised version")
            render_3d(V, X, Z, -vlim, vlim, kz, common_out,
                      f"Fe$_3$O$_4$  D = {D} nm  -  50-plane through-focus stack  (common scale)",
                      sub_common, "I_cross (common scale)", log, "value",
                      elev=26.0 if kz == 1 else 22.0, note=note_common)
            sub_norm = (r"50 zeta planes, per-particle normalisation "
                        r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$ "
                        f"(max = {pmax:.4g})" + ztxt)
            render_3d(V / pmax, X, Z, -1.0, 1.0, kz, norm_out,
                      f"Fe$_3$O$_4$  D = {D} nm  -  50-plane through-focus stack  (normalised)",
                      sub_norm, r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$", log, "value",
                      elev=26.0 if kz == 1 else 22.0)

        if not quick:
            vol_out = C.FIG / "supplement" / f"{tag}_3d_volume_render.png"
            render_3d(V / pmax, X, Z, -1.0, 1.0, 1.0, vol_out,
                      f"Fe$_3$O$_4$  D = {D} nm  -  volume-slice render of the 50-plane stack",
                      "opacity proportional to |I_cross|; value-weighted alpha blending of all 50 "
                      "saved planes (display object, zeta = defocus)",
                      r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$", log, "value",
                      elev=20.0, note=None, alpha_gamma=1.2)
            cut_out = C.FIG / "supplement" / f"{tag}_3d_stack_cutaway.png"
            render_3d(V / pmax, X, Z, -1.0, 1.0, 1.0, cut_out,
                      f"Fe$_3$O$_4$  D = {D} nm  -  cut-away of the 50-plane stack",
                      "the x > 0 half of every plane is set transparent so the sign change "
                      "of I_cross through focus becomes visible; no stored value is modified",
                      r"$I_\mathrm{cross}/\max|I_\mathrm{cross}|$", log, "value",
                      elev=22.0, cut_x=0.0)
            orthoview(tag, D, h, cube, log)
            isosurface(tag, D, h, log)
        log.record("case_done", {"tag": tag, "kz_list": variants})

    log.done({})
    print(json.dumps({"ok": True, "dir": str(C.FIG)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

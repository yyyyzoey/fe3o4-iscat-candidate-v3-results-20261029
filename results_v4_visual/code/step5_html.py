"""Step 5 - self-contained interactive 3D HTML for the 50-plane stacks.

The alpha channel of the custom RdBu colorscale is driven by |I_cross| so that
near-zero background is transparent (same idea as the static renderer).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import plotly.graph_objects as go

import vis_common as C

# value -> colour, alpha grows with |value|; blue negative, white zero, red positive
RDBU_ALPHA = [
    [0.00, "rgba(5,10,172,0.92)"],
    [0.10, "rgba(24,60,180,0.55)"],
    [0.22, "rgba(80,130,215,0.30)"],
    [0.40, "rgba(160,200,235,0.12)"],
    [0.50, "rgba(248,248,248,0.00)"],
    [0.60, "rgba(248,190,165,0.12)"],
    [0.78, "rgba(215,90,75,0.30)"],
    [0.90, "rgba(178,24,43,0.55)"],
    [1.00, "rgba(103,0,31,0.92)"],
]

BOUNDARY = ("CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED | through-focus response, "
            "not sample-space near field | zeta = defocus | full_jones_chain = UNVERIFIED | "
            "high_na_model_validation = UNVERIFIED | absolute_calibration = false")


def stack_figure(tag, D, h):
    cube = C.load_cube(tag, half_nm=400.0)
    layers = C.layer_index(tag)
    idx = [r["index"] for r in layers]
    V = cube["I_cross"][idx]
    X = cube["x"]
    Z = np.array([r["actual_zeta_nm"] for r in layers])
    pmax = float(np.abs(V).max())
    Vn = V / pmax

    fig = go.Figure()
    for k in range(len(Z)):
        fig.add_trace(go.Surface(
            x=X, y=X, z=np.full((X.size, X.size), Z[k]),
            surfacecolor=Vn[k],
            cmin=-1.0, cmax=1.0, colorscale=RDBU_ALPHA,
            showscale=False, opacity=1.0, hoverinfo="skip",
            lighting=dict(ambient=1.0, diffuse=0.0, specular=0.0, roughness=1.0),
            name=f"zeta={Z[k]:+.0f}",
        ))
    # one invisible trace that only carries the colour bar
    fig.add_trace(go.Scatter3d(x=[None], y=[None], z=[None], mode="markers",
                               marker=dict(opacity=0, colorscale=RDBU_ALPHA,
                                           cmin=-1, cmax=1, color=[0],
                                           colorbar=dict(title="I_cross / max|I_cross|",
                                                         thickness=14, len=0.62)),
                               showlegend=False, hoverinfo="skip"))
    fig.update_layout(
        title=dict(
            text=(f"Fe<sub>3</sub>O<sub>4</sub> D = {D} nm (centre height {h:.0f} nm) - "
                  f"50-plane through-focus stack, per-particle normalised<br>"
                  f"<span style='font-size:11px'>max|I_cross| = {pmax:.4g}; "
                  f"50 real zeta layers; x,y = -400..400 nm; {BOUNDARY}</span>"),
            x=0.02, xanchor="left", y=0.97),
        scene=dict(
            xaxis=dict(title="x (nm)", range=[-400, 400], nticks=5),
            yaxis=dict(title="y (nm)", range=[-400, 400], nticks=5),
            zaxis=dict(title="zeta (nm)", range=[-175, 175], nticks=5),
            aspectmode="manual",
            aspectratio=dict(x=1.0, y=1.0, z=0.57),
            camera=dict(eye=dict(x=1.55, y=-1.35, z=0.95)),
        ),
        template="plotly_white",
        margin=dict(l=0, r=0, t=88, b=0),
        width=1180, height=880,
        paper_bgcolor="white",
    )
    return fig


def isosurface_figure(tag, D, h):
    from skimage import measure
    cube = C.load_cube(tag, half_nm=400.0)
    V = cube["I_cross"]
    z = cube["zeta"]; x = cube["x"]
    pmax = float(np.abs(V).max())
    spacing = (float(z[1] - z[0]), float(x[1] - x[0]), float(x[1] - x[0]))
    fig = go.Figure()
    used = []
    for f, col in ((-0.5, "rgb(33,102,172)"), (-0.25, "rgb(103,169,207)"),
                   (0.25, "rgb(253,174,97)"), (0.5, "rgb(215,48,39)"),
                   (0.75, "rgb(165,15,21)")):
        lv = f * pmax
        if lv <= float(V.min()) or lv >= float(V.max()):
            continue
        verts, faces, _, _ = measure.marching_cubes(V, level=lv, spacing=spacing)
        verts[:, 0] += float(z[0])
        verts[:, 1] += float(x[0])
        verts[:, 2] += float(x[0])
        fig.add_trace(go.Mesh3d(
            x=verts[:, 2], y=verts[:, 1], z=verts[:, 0],
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            color=col, opacity=0.42, flatshading=False,
            name=f"{f:+.2f} x max|I| = {lv:+.4g}",
            lighting=dict(ambient=0.9, diffuse=0.2, specular=0.05),
        ))
        used.append({"level_fraction": f, "level": float(lv),
                     "n_faces": int(faces.shape[0])})
    fig.update_layout(
        title=dict(text=(f"Fe<sub>3</sub>O<sub>4</sub> D = {D} nm - iso-surfaces of signed "
                         f"I_cross (max|I| = {pmax:.4g})<br>"
                         f"<span style='font-size:11px'>levels present: "
                         + ", ".join(f"{u['level_fraction']:+.2f}" for u in used)
                         + f" | {BOUNDARY}</span>"), x=0.02, xanchor="left"),
        scene=dict(xaxis=dict(title="x (nm)"), yaxis=dict(title="y (nm)"),
                   zaxis=dict(title="zeta (nm)"),
                   aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.57),
                   camera=dict(eye=dict(x=1.5, y=-1.3, z=0.9))),
        template="plotly_white", margin=dict(l=0, r=0, t=88, b=0),
        width=1180, height=880, paper_bgcolor="white",
    )
    return fig, used


def main():
    C.ensure_dirs()
    log = C.StepLog("step5_html")
    out = []
    for tag, D, h in C.CASES:
        p = C.HTML / f"{tag}_50slice_stack.html"
        stack_figure(tag, D, h).write_html(str(p), include_plotlyjs=True,
                                           full_html=True,
                                           config={"displaylogo": False})
        log.record("html_stack", {"file": p.name, "bytes": p.stat().st_size})
        out.append(p)

        p2 = C.HTML / f"{tag}_isosurface.html"
        fig, used = isosurface_figure(tag, D, h)
        fig.write_html(str(p2), include_plotlyjs=True, full_html=True,
                       config={"displaylogo": False})
        log.record("html_isosurface", {"file": p2.name, "bytes": p2.stat().st_size,
                                       "levels": used})
        out.append(p2)
    log.done({})
    print(json.dumps({"ok": True, "files": [{"f": str(p), "bytes": p.stat().st_size}
                                            for p in out]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

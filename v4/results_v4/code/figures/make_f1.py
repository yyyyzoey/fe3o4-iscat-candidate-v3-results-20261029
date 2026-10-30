"""Redraw F1: clean not-to-scale schematic, separate annotation zones."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG = Path(__file__).resolve().parents[1] / "results_v4" / "figures" / "F1_geometry_method"
FIG.mkdir(parents=True, exist_ok=True)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.35, 1]})

# ---------- panel A: layer stack, not to scale ----------
ax.set_xlim(-3.0, 3.0); ax.set_ylim(-2.6, 3.4)
ax.axhspan(-2.0, 0, color="#dbe8f6", zorder=0)
ax.axhline(0, color="0.3", lw=1.6, zorder=2)
for y, txt in ((-1.85, "glass   n_g = 1.52   t_g = 170 um"),
               (-1.45, "immersion oil (design)  t_i* = 100 um, n_i = 1.52"),
               (-1.05, "water   n_s = 1.33")):
    ax.text(-2.85, y, txt, fontsize=8.6, va="center")
ax.text(2.85, -0.35, "Z = 0\ninterface", fontsize=8.2, ha="right", va="top", color="0.25")
th = np.linspace(0, np.pi, 300)
ax.fill(np.cos(th), np.sin(th), color="#7a5330", alpha=0.9, zorder=3)
ax.plot([0], [0], "o", ms=3, color="k", zorder=4)
ax.annotate("", xy=(1.06, 0.0), xytext=(0, 0),
            arrowprops=dict(arrowstyle="<->", lw=1.0, color="0.15"))
ax.text(1.14, 0.28, "a = D/2\nz_p = D/2\nsurface gap = 0", fontsize=8.4, va="center")
ax.text(0, 1.55, "Fe3O4 sphere, D = 30 / 100 / 200 nm\nn_p = 2.3456 + 0.0926 i",
        ha="center", fontsize=8.8, color="#3b2a17")
ax.annotate("", xy=(0, 2.55), xytext=(0, 0),
            arrowprops=dict(arrowstyle="<->", lw=1.0, color="0.15"))
ax.text(0.12, 2.62, "z_p", fontsize=9)
ax.text(-2.85, 3.1, "A | layer stack (vertical scale schematic, not to scale)",
        fontsize=9.2, fontweight="bold")
ax.set_xlabel("x (schematic)"); ax.set_ylabel("z (schematic)")
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color("0.6")

# ---------- panel B: through-focus scan around the particle ----------
ax2.set_xlim(-2.2, 2.2); ax2.set_ylim(-0.9, 2.9)
ax2.axhline(0, color="0.3", lw=1.6)
ax2.fill(np.cos(th), 0.55*np.sin(th), color="#7a5330", alpha=0.9, zorder=2)
ax2.axhline(0.55, color="#2166ac", lw=0.9, ls="--")
ax2.text(-2.1, 0.62, "z = z_p  (reference focus)", fontsize=8, color="#2166ac")
ax2.plot([-1.6, 1.6], [0.55, 0.55], color="#b2182b", lw=1.0)
ax2.plot([-1.6, 1.6], [2.05, 2.05], color="#b2182b", lw=1.0)
ax2.annotate("", xy=(0, 2.05), xytext=(0, 0.55),
             arrowprops=dict(arrowstyle="<->", lw=1.1, color="#b2182b"))
ax2.text(0.12, 1.3, "zeta = -170 : 2 : +170 nm\n(171 focus planes)",
         fontsize=8.6, color="#b2182b", va="center")
ax2.text(-2.1, 2.35, "B | focus scan (particle fixed, only the focus moves)",
         fontsize=9.2, fontweight="bold")
ax2.text(-2.1, -0.65,
         "per layer:  t_i = 100000 - zeta - (1.52/1.33) z_p   nm   [paper Eq. (7)]\n"
         "x,y = -1200 : 10 : 1200 nm;  array order (zeta, y, x)",
         fontsize=8.3, color="#2166ac")
ax2.set_xlabel("r (schematic)"); ax2.set_ylabel("z (schematic)")
ax2.set_xticks([]); ax2.set_yticks([])
for s in ax2.spines.values(): s.set_color("0.6")

fig.suptitle("F1 | geometry and through-focus scan definition (schematic, not a solution)", fontsize=10.5)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(FIG / "F1_geometry_method.png"); fig.savefig(FIG / "F1_geometry_method.svg")
plt.close(fig)
print("ok")


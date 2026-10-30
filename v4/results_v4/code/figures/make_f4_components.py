"""F4 axial full-component figures, 3 panels (linear J, linear I_ref/I_total, log I_scat/|S|)."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import h5py

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results_v4"; FIG = RES / "figures"; DATA = RES / "data"
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.unicode_minus": True})
for D in (30, 100, 200):
    with h5py.File(DATA / f"D{D:03d}nm" / "cube.h5", "r") as f:
        J = f["signals/I_cross"][:]; Iref = f["signals/I_ref"][:]
        Isc = f["signals/I_scat"][:]; Itot = f["signals/I_total"][:]
        S = f["signals/contrast_fixed_reference"][:]
        z = f["coords/zeta_nm"][:]
    j = J[:, 120, 120]; jmax = float(np.max(np.abs(J)))
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.7), layout="constrained")
    ax = axes[0]
    ax.plot(z, j, lw=1.4, color="#b2182b", label="J = I_cross (common units)")
    ax.plot(z, j / jmax, lw=1.1, ls="--", color="#2166ac", label="J / max_cube|J| (shape)")
    ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.75", lw=0.6, ls=":")
    ax.set_xlabel("zeta (nm)"); ax.set_ylabel("J"); ax.grid(alpha=0.25)
    ax.set_title("(a) J: common vs shape"); ax.legend(fontsize=7)
    ax = axes[1]
    ax.plot(z, Iref[:, 120, 120], lw=1.3, color="0.35", label="I_ref")
    ax.plot(z, Itot[:, 120, 120], lw=1.3, color="#762a83", label="I_total")
    ax.axvline(0, color="0.75", lw=0.6, ls=":")
    ax.set_xlabel("zeta (nm)"); ax.set_ylabel("shared model units"); ax.grid(alpha=0.25)
    ax.set_title("(b) I_ref and I_total (linear)"); ax.legend(fontsize=7)
    ax = axes[2]
    ax.semilogy(z, np.maximum(Isc[:, 120, 120], 1e-30), lw=1.3, color="#1b7837", label="I_scat")
    ax.semilogy(z, np.maximum(np.abs(S[:, 120, 120]), 1e-30), lw=1.3, color="#e08214",
                label="|S_fixed|")
    ax.axvline(0, color="0.75", lw=0.6, ls=":")
    ax.set_xlabel("zeta (nm)"); ax.set_ylabel("shared model units (log)"); ax.grid(alpha=0.25, which="both")
    ax.set_title("(c) I_scat and |S_fixed| (log)"); ax.legend(fontsize=7)
    fig.suptitle(f"Fe3O4 D={D} nm, NA=1.45, lambda0=532 nm | on-axis (x=y=0) axial components | "
                 "saved data, no recentering", fontsize=9.4)
    out = FIG / "F4_axial"
    fig.savefig(out / f"{D:03d}nm_axial_full_components.png", dpi=200)
    fig.savefig(out / f"{D:03d}nm_axial_full_components.svg")
    plt.close(fig)
    print(D, "ok")

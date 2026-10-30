"""Shared helpers for the V4.1 visualisation enhancement pass.

Read-only with respect to the physics: every number shown is read from the
three saved V4.1 HDF5 cubes. Nothing here re-runs the solver.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import h5py
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- paths
ROOT = Path(r"C:\Users\PC\Documents\Codex\2026-10-29\fe3o4-iscat-codex-handoff-v3-agents")
DATA = ROOT / "work" / "v4_final_20261030" / "final_tree" / "results_v4" / "data"
OUT = ROOT / "work" / "v4_visual" / "out" / "results_v4_visual"
FIG = OUT / "figures_main"
HTML = OUT / "html_3d"
EXPORT = OUT / "exported_data"
REPORT = OUT / "report"
CODE = OUT / "code"
LOGS = OUT / "logs"

CASES = [("D030", 30, 15.0), ("D100", 100, 50.0), ("D200", 200, 100.0)]

HALF_NM = 400.0
N_LAYERS = 50
Z_HI = 170.0
Z_LO = -170.0

# ---------------------------------------------------------------- style
BASE_RC = {
    "font.family": "DejaVu Sans",
    "font.size": 8.0,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
}


def apply_style() -> None:
    plt.rcParams.update(BASE_RC)


def cube_path(tag: str) -> Path:
    return DATA / f"{tag}nm" / "cube.h5"


# ---------------------------------------------------------------- data
def load_cube(tag: str, half_nm: float | None = HALF_NM) -> dict:
    with h5py.File(cube_path(tag), "r") as f:
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
        if half_nm is None:
            ix = np.arange(x.size)
        else:
            ix = np.where(np.abs(x) <= half_nm)[0]
        out = {
            "zeta": z,
            "x": x[ix],
            "y": y[ix],
            "ix": ix,
            "I_cross": f["signals/I_cross"][:][:, ix][:, :, ix],
            "I_total": f["signals/I_total"][:][:, ix][:, :, ix],
            "I_ref": f["signals/I_ref"][:][:, ix][:, :, ix],
            "I_scat": f["signals/I_scat"][:][:, ix][:, :, ix],
        }
        out["attrs"] = {k: f.attrs[k] for k in f.attrs}
    return out


def global_stats(tag: str) -> dict:
    """Full-grid statistics (no cropping) for audit and colour scaling."""
    with h5py.File(cube_path(tag), "r") as f:
        j = f["signals/I_cross"][:]
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
    i0 = int(np.argmin(np.abs(x)))
    i1 = int(np.argmin(np.abs(y)))
    iz, iy, ix = np.unravel_index(int(np.abs(j).argmax()), j.shape)
    axis = np.asarray(j[:, i1, i0], dtype=float)
    return {
        "tag": tag,
        "shape": list(j.shape),
        "cube_max_abs_I_cross": float(np.abs(j).max()),
        "cube_min_I_cross": float(j.min()),
        "cube_max_I_cross": float(j.max()),
        "cube_mean_I_cross": float(j.mean()),
        "cube_std_I_cross": float(j.std()),
        "argmax_zeta_nm": float(z[iz]),
        "argmax_y_nm": float(y[iy]),
        "argmax_x_nm": float(x[ix]),
        "axis_peak_zeta_nm": float(z[int(np.argmax(axis))]),
        "axis_peak_I_cross": float(axis.max()),
        "axis_valley_zeta_nm": float(z[int(np.argmin(axis))]),
        "axis_valley_I_cross": float(axis.min()),
        "axis_I_cross_at_center": axis.tolist(),
        "zeta_nm": z.tolist(),
        "n_positive": int((j > 0).sum()),
        "n_negative": int((j < 0).sum()),
        "fraction_negative": float((j < 0).mean()),
        "p99_abs": float(np.percentile(np.abs(j), 99)),
    }


# ---------------------------------------------------------------- layers
def select_layers(zeta: np.ndarray, n: int = N_LAYERS) -> list[dict]:
    """Equal spacing over the full zeta range, snapped to real layers.

    Collisions are resolved by walking to the nearest still-unused layer, so the
    result always contains exactly ``n`` distinct real layers.
    """
    targets = np.linspace(float(zeta[0]), float(zeta[-1]), n)
    used: set[int] = set()
    rows: list[dict] = []
    for k, t in enumerate(targets):
        order = np.argsort(np.abs(zeta - t))
        pick = None
        for cand in order:
            c = int(cand)
            if c not in used:
                pick = c
                break
        assert pick is not None
        used.add(pick)
        rows.append(
            {
                "k": k,
                "target_zeta_nm": round(float(t), 6),
                "index": pick,
                "actual_zeta_nm": float(zeta[pick]),
                "offset_nm": float(zeta[pick] - t),
            }
        )
    assert len(used) == n, (len(used), n)
    rows.sort(key=lambda r: r["index"])
    for k, r in enumerate(rows):
        r["k"] = k
    return rows


def layer_index(tag: str) -> list[dict]:
    with h5py.File(cube_path(tag), "r") as f:
        z = f["coords/zeta_nm"][:]
    return select_layers(z)


# ---------------------------------------------------------------- misc
def common_scale() -> float:
    """Symmetric colour limit shared by the three diameters (max |I_cross|)."""
    vals = []
    for tag, _, _ in CASES:
        with h5py.File(cube_path(tag), "r") as f:
            vals.append(float(np.abs(f["signals/I_cross"][:]).max()))
    return max(vals)


def sparse_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    return [float(v) for v in np.linspace(lo, hi, n)]


class StepLog:
    """Append-only JSONL execution log."""

    def __init__(self, name: str):
        LOGS.mkdir(parents=True, exist_ok=True)
        self.path = LOGS / f"{name}.jsonl"
        self.t0 = time.time()
        self.name = name
        self.record("start", {})

    def record(self, event: str, payload: dict) -> None:
        rec = {
            "step": self.name,
            "event": event,
            "t_rel_s": round(time.time() - self.t0, 3),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def done(self, payload: dict | None = None) -> None:
        self.record("done", payload or {})


def ensure_dirs() -> None:
    for d in (OUT, FIG, HTML, EXPORT, REPORT, CODE, LOGS,
              FIG / "slices_2d", FIG / "supplement", FIG / "previews"):
        d.mkdir(parents=True, exist_ok=True)

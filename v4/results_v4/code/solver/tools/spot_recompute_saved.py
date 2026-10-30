#!/usr/bin/env python3
"""Recompute selected saved-field samples from the frozen configuration.

This is a numerical consistency audit, not a physical certification. It reads
the three stored cubes, recomputes the selected image-plane complex fields from
the source configuration with complex128 arithmetic, and reports reference,
weak-scattering, gamma-scaled scattering and cross-term errors separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import iscat_core as core
from run_dataset import canonical_hash, implementation_hash

ZETA = np.array([-170.0, -86.0, 0.0, 84.0, 170.0])
POINTS = np.array([
    [0.0, 0.0],
    [10.0, 0.0],
    [100.0, 100.0],
    [350.0, 350.0],
    [500.0, -250.0],
    [700.0, 700.0],
    [1000.0, -1000.0],
    [1200.0, 1200.0],
])
THRESHOLD = 1e-3


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def metrics(actual: np.ndarray, saved: np.ndarray) -> dict:
    a = np.asarray(actual, dtype=np.complex128)
    b = np.asarray(saved, dtype=np.complex128)
    d = a - b
    return {
        "relative_l2": float(np.linalg.norm(d) / max(np.linalg.norm(b), 1e-300)),
        "relative_linf": float(np.max(np.abs(d)) / max(np.max(np.abs(b)), 1e-300)),
        "max_absolute": float(np.max(np.abs(d))),
        "saved_l2": float(np.linalg.norm(b)),
        "saved_linf": float(np.max(np.abs(b))),
        "pass_relative_below_1e-3": bool(
            np.linalg.norm(d) / max(np.linalg.norm(b), 1e-300) <= THRESHOLD
            and np.max(np.abs(d)) / max(np.max(np.abs(b)), 1e-300) <= THRESHOLD
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=ROOT / "configs/target_Fe3O4_NA145.json")
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    op = core.optical_params(cfg)
    op["cs_over_cr"] = 1.0
    radii = np.unique(np.hypot(POINTS[:, 0], POINTS[:, 1]))
    geo = {
        "r": np.hypot(POINTS[:, 0], POINTS[:, 1]),
        "sin2": np.zeros(len(POINTS)),
        "cos2": np.zeros(len(POINTS)),
    }
    r2 = POINTS[:, 0] ** 2 + POINTS[:, 1] ** 2
    np.divide(2 * POINTS[:, 0] * POINTS[:, 1], r2, out=geo["sin2"], where=r2 > 0)
    np.divide(POINTS[:, 0] ** 2 - POINTS[:, 1] ** 2, r2, out=geo["cos2"], where=r2 > 0)

    report = {
        "audit_role": "frozen-config independent numerical recomputation of saved samples",
        "physical_validation": False,
        "status": "CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED",
        "config_sha256": canonical_hash(cfg),
        "implementation_sha256": implementation_hash(),
        "zeta_nm": ZETA.tolist(),
        "points_xy_nm": POINTS.tolist(),
        "relative_threshold": THRESHOLD,
        "cases": {},
        "all_numerical_pass": True,
    }

    for diameter in cfg["diameters_nm"]:
        D = float(diameter)
        cube = args.data_root / f"D{int(D):03d}nm" / "cube.h5"
        with h5py.File(cube, "r") as f:
            saved_config = json.loads(f.attrs["configuration_json"])
            if canonical_hash(saved_config) != f.attrs["config_sha256"]:
                raise ValueError(f"D{D:g}: stored configuration hash mismatch")
            scale = float(f.attrs["reference_field_scale"])
            gamma = complex(float(f.attrs["gamma_real"]), float(f.attrs["gamma_imag"]))
            x = f["coords/x_object_nm"][:]
            y = f["coords/y_object_nm"][:]
            z = f["coords/zeta_nm"][:]
            ix = np.array([int(np.flatnonzero(np.isclose(x, p[0]))[0]) for p in POINTS])
            iy = np.array([int(np.flatnonzero(np.isclose(y, p[1]))[0]) for p in POINTS])
            iz = np.array([int(np.flatnonzero(np.isclose(z, zv))[0]) for zv in ZETA])
            er_layers = (f["fields/E_ref_real"][iz].astype("f8")
                         + 1j * f["fields/E_ref_imag"][iz].astype("f8"))
            eu_layers = (f["fields/E_scat_unit_real"][iz].astype("f8")
                         + 1j * f["fields/E_scat_unit_imag"][iz].astype("f8"))
            cross_layers = f["signals/I_cross"][iz].astype("f8")
            er_saved = er_layers[:, iy, ix]
            eu_saved = eu_layers[:, iy, ix]
            cross_saved = cross_layers[:, iy, ix]

        pupil = core.pupil_precompute(op, D, int(cfg["grid_full"]["quadrature_below_critical"]),
                                      int(cfg["grid_full"]["quadrature_above_critical"]))
        radial = core.make_radial_response(op, pupil, D / 2, ZETA, radii)
        er = np.empty((len(ZETA), len(POINTS), 2), dtype=np.complex128)
        eu = np.empty_like(er)
        for k in range(len(ZETA)):
            er[k], eu[k] = core.fields_at_slice(radial, k, radii, geo)
        er /= scale
        eu /= scale
        es = gamma * eu
        cross = 2 * np.real(np.sum(np.conj(er) * es, axis=-1))

        checks = {
            "E_ref_complex": metrics(er, er_saved),
            "E_scat_unit_complex": metrics(eu, eu_saved),
            "E_scat_with_gamma_complex": metrics(es, gamma * eu_saved),
            "I_cross_recomputed_vs_signal": metrics(cross, cross_saved),
        }
        passed = all(v["pass_relative_below_1e-3"] for v in checks.values())
        report["cases"][str(int(D))] = {
            "cube": str(cube.relative_to(args.data_root)),
            "cube_sha256": sha256(cube),
            "reference_field_scale": scale,
            "gamma": [gamma.real, gamma.imag],
            "samples": int(er.size),
            "checks": checks,
            "pass": bool(passed),
        }
        report["all_numerical_pass"] &= passed

    report["interpretation"] = (
        "PASS here means the frozen solver reproduces saved samples to the declared numerical tolerance; "
        "it does not verify the publication's full Jones chain, supercritical interface physics, or absolute amplitude."
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"all_numerical_pass": report["all_numerical_pass"], "out": str(args.out)}, indent=2))
    return 0 if report["all_numerical_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
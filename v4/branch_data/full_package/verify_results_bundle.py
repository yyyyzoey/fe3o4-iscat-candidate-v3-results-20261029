#!/usr/bin/env python3
"""Strict validator for the Fe3O4 iSCAT V4 result bundles (full / light).

Full mode (default) is the only mode that can report a complete archive PASS:
it pins the external ZIP digest/size/entry count, the CRC and manifest, the three
main HDF5 SHA256 values, and then streams *every* layer of all three cubes and
re-checks coordinates, complex fields, signal decomposition, masks and metadata.

Light mode must be requested explicitly with --mode light. It never inspects the
HDF5 cubes (they are absent by design) and reports its scope as
`pass_scope="LIGHT_NO_HDF5"`, never as a full data pass.

Layer checks are adapted from tools/strict_cube_audit.py (same tolerances) and
were validated on the real archive; this file is self-contained so it works
without the audit tooling being installed.

Exit code 0 only on PASS; 1 on any failure (message in the JSON report).
"""
from __future__ import annotations
import argparse, hashlib, io, json, re, shutil, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

import numpy as np

CLASS = "CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED"
ZIP_SHA = "c61f9a3bf7d6d90f0c1746a1e9de104db669cb2e838c84d3d1234f67b8e62a2a"
ZIP_BYTES = 1326369547
ZIP_ENTRIES = 380
H5_SHA = {
    30: "ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46",
    100: "ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49",
    200: "c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2",
}
CONFIG_SHA = "01e910c0a9cf1d3e2be0befe13de2b8bedcdebe502264ef36e4809e51d367815"
CODE_SHA = "1a170ab6124d6283f72d445d3d9b0dbeb841e6fad76cc0ac3eb544d5ac044bc6"
SIGNALS = ("I_ref", "I_scat", "I_cross", "I_total", "contrast_local", "contrast_fixed_reference")
BASIS = ("I_scat_unit", "Q_real", "Q_imag")
FIELDS = ("E_ref_real", "E_ref_imag", "E_scat_unit_real", "E_scat_unit_imag")
MASKS = ("defined_contrast", "stable_reference")
ROOT = "results_v4/"
MANIFEST = ROOT + "SHA256SUMS.txt"


def sha256_stream(stream) -> str:
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(8 << 20), b""):
        h.update(block)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as f:
        return sha256_stream(f)


def fail(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and "\\" not in name


def audit_cube(path: Path, D: int, *, x=None, z=None, enforce_provenance: bool = True) -> dict:
    """Stream one cube layer by layer with independent complex algebra.

    `x`/`z`/`enforce_provenance` exist for synthetic unit tests; the CLI keeps
    the production axes and provenance pins.
    """
    import h5py
    x = np.arange(-1200.0, 1201.0, 10.0) if x is None else np.asarray(x, float)
    z = np.arange(-170.0, 171.0, 2.0) if z is None else np.asarray(z, float)
    shape = (len(z), len(x), len(x))
    max_err = 0.0
    masked_nan = 0
    layers = 0
    with h5py.File(path, "r") as f:
        a = f.attrs
        expected = {"schema": "iscat-through-focus-v3.0", "status": CLASS, "grid_mode": "full",
                    "axis_order": "zeta,y,x", "field_component_order": "Ex,Ey",
                    "diameter_nm": D, "particle_radius_nm": D / 2, "center_height_nm": D / 2,
                    "surface_gap_nm": 0.0, "wavelength_nm": 532.0, "NA": 1.45, "material": "Fe3O4",
                    "completed_slices": len(z), "gamma_real": 0.5, "gamma_imag": 0.0,
                    "absolute_calibration": False, "is_sample_space_field": False,
                    "physical_validation": "NOT_ESTABLISHED"}
        for key, val in expected.items():
            fail(key in a and a[key] == val, f"attribute {key}: expected {val!r}, got {a.get(key)!r}")
        for key, want in (("x_object_nm", x), ("y_object_nm", x), ("zeta_nm", z)):
            got = f["coords/" + key][:]
            fail(got.shape == want.shape and np.isfinite(got).all()
                 and np.allclose(got, want, rtol=0, atol=1e-10), f"wrong coordinate {key}")
        oil = f["coords/oil_thickness_nm"][:]
        fail(oil.shape == z.shape and np.isfinite(oil).all() and (oil > 0).all(), "invalid oil thickness axis")
        scale = float(a["reference_field_scale"])
        fail(np.isfinite(scale) and scale > 0, "invalid reference_field_scale")
        if enforce_provenance:
            cfg = json.loads(a["configuration_json"])
            fail(canonical(cfg) == a["config_sha256"] == CONFIG_SHA, "configuration hash mismatch")
            fail(a["implementation_sha256"] == CODE_SHA, "implementation hash mismatch")
            fail(cfg["diameters_nm"] == [30, 100, 200], "diameters mismatch")
            fail(cfg["model"]["n_particles_per_case"] == 1, "particle count mismatch")
            for key in ("camera_sampling", "background_stray_light", "brownian_motion", "magneto_optical_tensor"):
                fail(cfg["model"].get(key) is False, f"unexpected enabled {key}")
            fail(float(cfg["optics"]["NA"]) == 1.45 and float(cfg["optics"]["wavelength_nm"]) == 532.0,
                 "optics parameters drifted")
        for group, keys in (("signals", SIGNALS), ("basis", BASIS), ("masks", MASKS)):
            for key in keys:
                fail(f[group + "/" + key].shape == shape, f"wrong shape {group}/{key}")
        for key in FIELDS:
            fail(f["fields/" + key].shape == (*shape, 2), f"wrong field shape {key}")
        gamma = complex(a["gamma_real"], a["gamma_imag"])

        for k in range(len(z)):
            v = {n: f["fields/" + n][k].astype("f8") for n in FIELDS}
            fail(all(np.isfinite(w).all() for w in v.values()), f"nonfinite field layer {k}")
            er = v["E_ref_real"] + 1j * v["E_ref_imag"]
            eu = v["E_scat_unit_real"] + 1j * v["E_scat_unit_imag"]
            ir = np.sum(np.abs(er) ** 2, axis=-1)
            u = np.sum(np.abs(eu) ** 2, axis=-1)
            q = np.sum(np.conj(er) * eu, axis=-1)
            isc = abs(gamma) ** 2 * u
            cross = 2 * np.real(gamma * q)
            total = ir + isc + cross
            got = {n: f["signals/" + n][k].astype("f8") for n in ("I_ref", "I_scat", "I_cross", "I_total")}
            for n, want in (("I_ref", ir), ("I_scat", isc), ("I_cross", cross), ("I_total", total)):
                fail(np.isfinite(got[n]).all(), f"nonfinite {n} layer {k}")
                err = float(np.max(np.abs(got[n] - want) / (1.0 + np.abs(want))))
                max_err = max(max_err, err)
                fail(err <= 1e-4, f"algebra mismatch {n} layer {k}: {err:.3e}")
            basis = {n: f["basis/" + n][k].astype("f8") for n in BASIS}
            fail(np.isfinite(basis["I_scat_unit"]).all() and np.isfinite(basis["Q_real"]).all()
                 and np.isfinite(basis["Q_imag"]).all(), f"nonfinite basis layer {k}")
            for n, want in (("I_scat_unit", u), ("Q_real", np.real(q)), ("Q_imag", np.imag(q))):
                err = float(np.max(np.abs(basis[n] - want) / (1.0 + np.abs(want))))
                fail(err <= 1e-4, f"basis mismatch {n} layer {k}: {err:.3e}")
            defined = f["masks/defined_contrast"][k]
            stable = f["masks/stable_reference"][k]
            local = f["signals/contrast_local"][k].astype("f8")
            fixed = f["signals/contrast_fixed_reference"][k].astype("f8")
            fail(set(np.unique(defined)) <= {0, 1} and set(np.unique(stable)) <= {0, 1},
                 f"mask not boolean layer {k}")
            finite_ref = np.isfinite(ir)
            fail(np.array_equal(defined.astype(bool), finite_ref & (ir > 1e-12)),
                 f"defined mask inconsistent layer {k}")
            fail(np.array_equal(stable.astype(bool), finite_ref & (ir >= 0.005 * np.max(ir))),
                 f"stable mask inconsistent layer {k}")
            fail(np.isfinite(fixed).all(), f"nonfinite contrast_fixed_reference layer {k}")
            # contrast_fixed_reference is stored as float32 while isc/cross are recomputed
            # from the float32 field components.  Near cancellation of I_scat and I_cross an
            # absolute 1e-8 bound is below float32 round-off, so use the same normalized
            # metric as the algebra checks (observed worst case 8.1e-8 over all 513 layers).
            e_fixed = float(np.max(np.abs(fixed - (isc + cross)) / (1.0 + np.abs(isc) + np.abs(cross))))
            fail(e_fixed <= 1e-4, f"fixed contrast mismatch layer {k}: {e_fixed:.3e}")
            valid = defined.astype(bool)
            fail(np.isnan(local[~valid]).all(), f"undefined contrast must be NaN layer {k}")
            fail(np.isfinite(local[valid]).all(), f"nonfinite defined contrast layer {k}")
            good = valid & (ir > 1e-12)
            if good.any():
                want = (isc[good] + cross[good]) / ir[good]
                e = float(np.max(np.abs(local[good] - want) / (1.0 + np.abs(want))))
                fail(e <= 1e-4, f"local contrast mismatch layer {k}: {e:.3e}")
            masked_nan += int(np.sum(~valid))
            layers += 1
    return {"pass": True, "diameter_nm": D, "shape": list(shape), "layers_actually_read": layers,
            "reference_field_scale": scale, "max_normalized_algebra_error": max_err,
            "expected_masked_contrast_nan": masked_nan, "unexplained_nonfinite": 0,
            "physical_certification": False}


def audit_archive(path: Path, *, mode: str, expect_sha256: str, expect_bytes: int,
                  expect_entries: int) -> dict:
    fail(mode in ("full", "light"), f"unknown mode {mode}")
    report = {"archive": path.name, "mode": mode, "physical_certification": False,
              "img_bytes": path.stat().st_size,
              "expected_external_sha256": expect_sha256, "failures": [], "cases": {}}
    report["pass_scope"] = "FULL_DATA_AND_HDF5" if mode == "full" else "LIGHT_NO_HDF5"
    fail(path.stat().st_size == expect_bytes, f"outer ZIP size mismatch: {path.stat().st_size} != {expect_bytes}")
    actual = sha256_file(path)
    fail(actual == expect_sha256, f"outer ZIP SHA256 mismatch against pinned trusted hash: {actual}")
    report.update(zip_sha256=actual, bytes=expect_bytes)
    with zipfile.ZipFile(path) as zf:
        entries = zf.infolist()
        names = [i.filename for i in entries]
        fail(len(names) == len(set(names)), "duplicate ZIP names")
        fail(len(names) == expect_entries, f"ZIP entry count mismatch: {len(names)} != {expect_entries}")
        fail(all(safe_name(n) for n in names), "unsafe archive path")
        fail(zf.testzip() is None, "ZIP CRC error")
        files = {i.filename for i in entries if not i.is_dir()}
        fail(MANIFEST in files, f"missing {MANIFEST}")
        expected = {}
        for line in zf.read(MANIFEST).decode("utf-8-sig").splitlines():
            h, rel = line.split("  ", 1)
            fail(bool(re.fullmatch("[0-9a-f]{64}", h)) and safe_name(rel), "bad manifest entry")
            name = ROOT + rel
            fail(name not in expected, f"duplicate manifest entry {name}")
            expected[name] = h
        fail(files == set(expected) | {MANIFEST}, "manifest/file inventory mismatch")
        for name, h in expected.items():
            with zf.open(name) as s:
                fail(sha256_stream(s) == h, f"internal SHA mismatch {name}")
        report.update(entries=len(names), crc_pass=True, manifest_entries_verified=len(expected))
        h5names = {n for n in files if n.endswith("/cube.h5")}
        if mode == "light":
            fail(h5names == set(), f"light bundle unexpectedly contains HDF5 cubes: {sorted(h5names)}")
            report.update(hdf5_present=False, hdf5_checked=False, hdf5_layers_read=0)
        else:
            wanted = {f"{ROOT}data/D{D:03d}nm/cube.h5" for D in H5_SHA}
            fail(h5names == wanted, "exactly three main cubes required; light fallback refused in full mode")
            with tempfile.TemporaryDirectory(prefix="iscat_verify_") as td:
                try:
                    for D, h in H5_SHA.items():
                        name = f"{ROOT}data/D{D:03d}nm/cube.h5"
                        local = Path(td) / f"D{D:03d}.h5"
                        with zf.open(name) as src, local.open("wb") as dst:
                            shutil.copyfileobj(src, dst, 1 << 20)
                        fail(sha256_file(local) == h, f"D{D} pinned cube hash mismatch")
                        report["cases"][str(D)] = audit_cube(local, D)
                        local.unlink()
                except ModuleNotFoundError as e:
                    fail(False, f"h5py unavailable, full mode cannot be completed: {e}")
            layers = sum(c["layers_actually_read"] for c in report["cases"].values())
            fail(layers == 3 * 171, f"hdf5_layers_read={layers}, expected 513")
            scales = {c["reference_field_scale"] for c in report["cases"].values()}
            fail(len(scales) == 1, "reference_field_scale not shared across diameters")
            report.update(hdf5_present=True, hdf5_checked=True, hdf5_layers_read=layers)
        status = json.loads(zf.read(ROOT + "status.json"))
        fail(status.get("absolute_calibration") is False, "incorrect absolute certification")
        fail(status.get("sample_space_near_field") is False, "incorrect near-field classification")
        fail(status.get("formula_fidelity") == "UNVERIFIED", "formula status must remain UNVERIFIED")
        fail(status.get("high_na_model_validation") == "UNVERIFIED", "high-NA status must remain UNVERIFIED")
        fail(status.get("result_class") in ("CANDIDATE", CLASS), "wrong result classification")
        fail(status.get("result_class") != "CERTIFIED", "forbidden certification claim")
    report["pass"] = True
    return report


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", nargs="?", type=Path, default=here / "results_v4_full.zip")
    ap.add_argument("--mode", choices=("full", "light"), default="full",
                    help="full (default) re-reads 513 HDF5 layers; light never does")
    ap.add_argument("--expect-sha256", default=None, help="trusted external digest (default: pinned V4 full)")
    ap.add_argument("--expect-bytes", type=int, default=None)
    ap.add_argument("--expect-entries", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None, help="optional JSON report path")
    a = ap.parse_args(argv)
    if a.mode == "full":
        expect_sha = a.expect_sha256 or ZIP_SHA
        expect_bytes = a.expect_bytes or ZIP_BYTES
        expect_entries = a.expect_entries or ZIP_ENTRIES
    else:
        expect_sha, expect_bytes, expect_entries = a.expect_sha256, a.expect_bytes, a.expect_entries
        if not (expect_sha and expect_bytes and expect_entries):
            raise SystemExit("light mode requires explicit --expect-sha256/--expect-bytes/--expect-entries")
    try:
        report = audit_archive(a.zip, mode=a.mode, expect_sha256=expect_sha,
                               expect_bytes=expect_bytes, expect_entries=expect_entries)
    except Exception as e:  # noqa: BLE001 - reported, never swallowed
        report = {"archive": a.zip.name, "mode": a.mode, "pass": False, "physical_certification": False,
                  "pass_scope": "FULL_DATA_AND_HDF5" if a.mode == "full" else "LIGHT_NO_HDF5",
                  "failures": [f"{type(e).__name__}: {e}"]}
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())

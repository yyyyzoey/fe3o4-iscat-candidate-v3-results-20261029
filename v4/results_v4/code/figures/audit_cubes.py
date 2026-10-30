#!/usr/bin/env python3
"""Independent, layer-by-layer audit of the three saved through-focus cubes.

Reads every slice of every cube, recomputes the stored algebra from the saved
complex fields, checks geometry/oil-film/metadata and reports metrics.
Writes JSON; never modifies the data.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import h5py
import numpy as np

CASES = {"D030nm": 30.0, "D100nm": 100.0, "D200nm": 200.0}
EXPECTED_GAMMA = (0.5, 0.0)
ZETA = np.arange(-170.0, 170.0 + 1.0, 2.0)
XY = np.arange(-1200.0, 1200.0 + 5.0, 10.0)
SHAPE = (171, 241, 241)


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_safe(x):
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    return x


def peak_window(zeta, curve):
    i = int(np.argmax(curve))
    return {"index": i, "zeta_nm": float(zeta[i]), "value": float(curve[i])}


def audit_case(path: Path, D: float) -> dict:
    meta = json.loads(path.with_name("validation.json").read_text(encoding="utf-8")) if path.with_name("validation.json").exists() else {}
    out = {"file": path.name, "diameter_nm": D, "file_bytes": path.stat().st_size,
           "file_sha256": sha256(path), "shape": None, "checks": {}, "failures": []}

    def fail(msg):
        out["failures"].append(msg)

    with h5py.File(path, "r") as f:
        # ---------- metadata / geometry ----------
        a = f.attrs
        cfg = json.loads(a["configuration_json"])
        op = cfg["optics"]
        gamma = complex(float(a["gamma_real"]), float(a["gamma_imag"]))
        z = f["coords/zeta_nm"][:]
        x = f["coords/x_object_nm"][:]
        y = f["coords/y_object_nm"][:]
        out["shape"] = list(f["signals/I_cross"].shape)
        if tuple(out["shape"]) != SHAPE: fail(f"shape {out['shape']} != {SHAPE}")
        if int(a["completed_slices"]) != 171: fail("completed_slices != 171")
        if not np.array_equal(z, ZETA): fail("zeta axis mismatch")
        if not np.array_equal(x, XY): fail("x axis mismatch")
        if not np.array_equal(y, XY): fail("y axis mismatch")
        if a["axis_order"] != "zeta,y,x": fail("axis order")
        if a["field_component_order"] != "Ex,Ey": fail("field order")
        if a["material"] != "Fe3O4": fail("material")
        if float(a["diameter_nm"]) != D: fail("diameter attr")
        if not np.isclose(float(a["particle_radius_nm"]), D / 2): fail("radius != D/2")
        if not np.isclose(float(a["center_height_nm"]), D / 2): fail("center height != D/2")
        if float(a["surface_gap_nm"]) != 0.0: fail("surface gap != 0")
        if float(a["NA"]) != 1.45: fail("NA != 1.45")
        if float(a["wavelength_nm"]) != 532.0: fail("wavelength != 532")
        if op["n_sample"] != 1.33 or op["n_glass"] != 1.52 or op["n_immersion"] != 1.52: fail("refractive indices")
        if op["glass_thickness_nm"] != 170000 or op["immersion_thickness_design_nm"] != 100000: fail("thicknesses")
        if op["magnification"] != 170: fail("magnification")
        if cfg["material"]["n_real"] != 2.3456 or cfg["material"]["k_imag"] != 0.0926: fail("Fe3O4 index")
        if gamma != complex(*EXPECTED_GAMMA): fail("gamma != 0.5+0i")
        if bool(a["absolute_calibration"]): fail("absolute_calibration must be false")
        if bool(a["is_sample_space_field"]): fail("is_sample_space_field must be false")
        if a["status"] != "CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED": fail("status string")
        if a["supercritical_sector"] != "ANALYTIC_CONTINUATION_UNVALIDATED": fail("supercritical label")
        if a["grid_mode"] != "full": fail("grid_mode != full")

        # oil thickness per layer: Eq. (7) with matched glass/immersion
        ti = f["coords/oil_thickness_nm"][:]
        ti_expect = (op["immersion_thickness_design_nm"] - z
                     - (op["n_immersion"] / op["n_sample"]) * (D / 2))
        ti_err = float(np.max(np.abs(ti - ti_expect)))
        out["oil_thickness_nm"] = {"first": float(ti[0]), "center": float(ti[85]), "last": float(ti[-1]),
                                   "max_abs_deviation_from_eq7": ti_err}
        if ti_err > 1e-6: fail(f"oil thickness Eq.(7) deviation {ti_err}")

        # ---------- per-layer recomputation ----------
        g2 = abs(gamma) ** 2
        totals = {"I_ref": [math.inf, -math.inf], "I_scat": [math.inf, -math.inf],
                  "I_cross": [math.inf, -math.inf], "I_total": [math.inf, -math.inf]}
        max_res = {"total_identity": 0.0, "iscalar_basis": 0.0, "cross_basis": 0.0,
                   "local_contrast": 0.0, "fixed_contrast": 0.0, "mask_defined": 0, "mask_stable": 0}
        nonfinite = {"fields": 0, "signals": 0, "basis": 0}
        negative = {"I_ref": 0, "I_scat": 0, "I_total": 0}
        j_pos = j_neg = 0
        mask_defined_mismatch = mask_stable_mismatch = 0
        contrast_bad_nan = contrast_bad_finite = 0
        layer_stats = []

        for iz in range(len(z)):
            er = (f["fields/E_ref_real"][iz].astype("f8")
                  + 1j * f["fields/E_ref_imag"][iz].astype("f8"))
            es = (f["fields/E_scat_unit_real"][iz].astype("f8")
                  + 1j * f["fields/E_scat_unit_imag"][iz].astype("f8"))
            if not (np.isfinite(er).all() and np.isfinite(es).all()):
                nonfinite["fields"] += int(np.size(er) - np.isfinite(er).sum())
                fail(f"nonfinite field at layer {iz}")
            ir = np.sum(np.abs(er) ** 2, axis=-1)
            isu = np.sum(np.abs(es) ** 2, axis=-1)
            q = np.sum(np.conj(er) * es, axis=-1)
            isc = g2 * isu
            cross = 2 * np.real(np.conj(gamma) * q)
            total = np.sum(np.abs(er + gamma * es) ** 2, axis=-1)

            def get(name):
                return f["signals/" + name][iz].astype("f8")

            s_ir, s_isc, s_cross, s_tot = get("I_ref"), get("I_scat"), get("I_cross"), get("I_total")
            s_cl, s_cf = get("contrast_local"), get("contrast_fixed_reference")
            b_isu = f["basis/I_scat_unit"][iz].astype("f8")
            b_qr = f["basis/Q_real"][iz].astype("f8")
            b_qi = f["basis/Q_imag"][iz].astype("f8")
            for name, arr in (("I_ref", s_ir), ("I_scat", s_isc), ("I_cross", s_cross),
                              ("I_total", s_tot), ("I_scat_unit", b_isu),
                              ("Q_real", b_qr), ("Q_imag", b_qi)):
                if not np.isfinite(arr).all(): nonfinite["signals"] += 1
            for name, arr in (("I_ref", s_ir), ("I_scat", s_isc), ("I_total", s_tot)):
                if float(np.min(arr)) < 0: negative[name] += int(np.sum(arr < 0))
            j_pos += int(np.sum(s_cross > 0)); j_neg += int(np.sum(s_cross < 0))
            for k, arr in (("I_ref", s_ir), ("I_scat", s_isc), ("I_cross", s_cross), ("I_total", s_tot)):
                totals[k][0] = min(totals[k][0], float(np.min(arr)))
                totals[k][1] = max(totals[k][1], float(np.max(arr)))

            scale = max(1.0, float(np.max(np.abs(total))))
            max_res["total_identity"] = max(max_res["total_identity"],
                                             float(np.max(np.abs(s_tot - total))) / scale)
            max_res["iscalar_basis"] = max(max_res["iscalar_basis"],
                                            float(np.max(np.abs(s_isc - isc))) / max(1.0, float(np.max(np.abs(isc)))))
            max_res["cross_basis"] = max(max_res["cross_basis"],
                                         float(np.max(np.abs(s_cross - cross))) / max(1.0, float(np.max(np.abs(cross)))))
            valid = ir > 1e-12
            stable = ir >= 0.005
            st_valid = f["masks/defined_contrast"][iz].astype(bool)
            st_stable = f["masks/stable_reference"][iz].astype(bool)
            mask_defined_mismatch += int(np.sum((st_valid != valid) & (np.abs(ir - 1e-12) > 1e-18)))
            mask_stable_mismatch += int(np.sum((st_stable != stable) & (np.abs(ir - 0.005) > 5e-9)))
            cl_expect = np.full(ir.shape, np.nan)
            np.divide(isc + cross, ir, out=cl_expect, where=valid)
            good = st_valid & valid
            if good.any():
                max_res["local_contrast"] = max(max_res["local_contrast"],
                                                float(np.max(np.abs(s_cl[good] - cl_expect[good]) /
                                                             (1 + np.abs(cl_expect[good])))))
            contrast_bad_nan += int(np.sum(~np.isnan(s_cl[~st_valid])))
            contrast_bad_finite += int(np.sum(~np.isfinite(s_cl[st_valid])))
            cf_expect = isc + cross
            max_res["fixed_contrast"] = max(max_res["fixed_contrast"],
                                            float(np.max(np.abs(s_cf - cf_expect))) /
                                            max(1.0, float(np.max(np.abs(cf_expect)))))
            layer_stats.append({"zeta_nm": float(z[iz]), "max_abs_J": float(np.max(np.abs(s_cross))),
                                "min_J": float(np.min(s_cross)), "max_J": float(np.max(s_cross)),
                                "max_I_total": float(np.max(s_tot)),
                                "oil_thickness_nm": float(ti[iz])})

        out["per_layer_written"] = len(layer_stats)
        out["integrity"] = {
            "nonfinite": nonfinite, "negative_voxels": negative,
            "J_positive_voxels": j_pos, "J_negative_voxels": j_neg,
            "mask_defined_mismatch": mask_defined_mismatch,
            "mask_stable_mismatch": mask_stable_mismatch,
            "contrast_undefined_non_nan": contrast_bad_nan,
            "contrast_defined_nonfinite": contrast_bad_finite,
            "max_normalized_residual": max_res,
            "signal_ranges": {k: {"min": v[0], "max": v[1]} for k, v in totals.items()},
            "all_signals_finite": nonfinite["signals"] == 0,
            "all_fields_finite": nonfinite["fields"] == 0,
            "J_has_both_signs": j_pos > 0 and j_neg > 0,
        }
        # ---------- axial curve at x=y=0 ----------
        ix = int(np.argmin(np.abs(x)))
        iy = int(np.argmin(np.abs(y)))
        if x[ix] != 0.0 or y[iy] != 0.0: fail("no exact x=y=0")
        col = {name: f["signals/" + name][:, iy, ix].astype("f8")
               for name in ("I_ref", "I_scat", "I_cross", "I_total", "contrast_fixed_reference")}
        out["axis_xy0"] = {
            "zeta_nm": z.tolist(),
            "I_ref": col["I_ref"].tolist(), "I_scat": col["I_scat"].tolist(),
            "I_cross": col["I_cross"].tolist(), "I_total": col["I_total"].tolist(),
            "contrast_fixed_reference": col["contrast_fixed_reference"].tolist(),
            "peak_abs_J_in_window": peak_window(z, np.abs(col["I_cross"])),
            "max_I_total_in_window": peak_window(z, col["I_total"]),
            "max_I_scat_in_window": peak_window(z, col["I_scat"]),
            "value_at_zeta0": {"I_ref": float(col["I_ref"][85]), "I_scat": float(col["I_scat"][85]),
                               "I_cross": float(col["I_cross"][85]), "I_total": float(col["I_total"][85])},
        }
        out["max_abs_J_cube"] = float(max(s["max_abs_J"] for s in layer_stats))
        out["global_signal_ranges"] = out["integrity"]["signal_ranges"]
        out["layer_stats"] = layer_stats
        out["metadata"] = {k: (a[k].item() if hasattr(a[k], "item") else a[k])
                           for k in ("schema", "status", "diameter_nm", "particle_radius_nm",
                                     "center_height_nm", "surface_gap_nm", "NA", "wavelength_nm",
                                     "material", "axis_order", "field_component_order",
                                     "absolute_calibration", "is_sample_space_field",
                                     "supercritical_sector", "gamma_real", "gamma_imag",
                                     "config_sha256", "implementation_sha256",
                                     "reference_field_scale", "completed_slices", "grid_mode",
                                     "time_convention", "units")}
        out["stored_validation_json"] = meta
    out["checks"]["data_hard_checks_pass"] = len(out["failures"]) == 0 and all(
        out["integrity"][k] == 0 for k in ("mask_defined_mismatch", "mask_stable_mismatch",
                                            "contrast_undefined_non_nan", "contrast_defined_nonfinite")
    ) and out["integrity"]["all_signals_finite"] and out["integrity"]["all_fields_finite"] \
        and out["integrity"]["J_has_both_signs"] and all(v == 0 for v in out["integrity"]["negative_voxels"].values())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.data_root)
    report = {"generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
              "data_root": str(root), "method": "independent per-slice reread and algebra recomputation",
              "cases": {}}
    ok = True
    for name, D in CASES.items():
        p = root / name / "cube.h5"
        rep = audit_case(p, D)
        report["cases"][name] = rep
        ok = ok and rep["checks"]["data_hard_checks_pass"]
    report["summary"] = {
        "all_cases_pass": ok,
        "cases": {k: {"shape": v["shape"], "layers_read": v["per_layer_written"],
                      "sha256": v["file_sha256"], "pass": v["checks"]["data_hard_checks_pass"],
                      "failures": v["failures"]} for k, v in report["cases"].items()},
        "shared_gamma": all(v["metadata"]["gamma_real"] == 0.5 and v["metadata"]["gamma_imag"] == 0.0
                            for v in report["cases"].values()),
        "shared_reference_scale": len({v["metadata"]["reference_field_scale"] for v in report["cases"].values()}) == 1,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(json_safe(report), indent=2), encoding="utf-8")
    print(json.dumps(json_safe(report["summary"]), indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()


"""Step 1 - lock the 50 displayed zeta layers and write the audit tables."""
from __future__ import annotations

import csv
import json
import subprocess

import numpy as np

import vis_common as C


def main() -> int:
    C.apply_style()
    C.ensure_dirs()
    log = C.StepLog("step1_layers")

    base = C.DATA.parent.parent.parent  # ...\work\v4\repo-like anchor, not used for math
    rows_by_case = {}
    for tag, D, h in C.CASES:
        rows = C.layer_index(tag)
        rows_by_case[tag] = rows
        z = np.array([r["actual_zeta_nm"] for r in rows])
        assert len(rows) == 50
        assert len({r["index"] for r in rows}) == 50
        assert np.all(np.diff([r["index"] for r in rows]) > 0)
        assert abs(z[0] + 170.0) < 1e-9 and abs(z[-1] - 170.0) < 1e-9
        log.record("layers", {"tag": tag, "n": len(rows),
                              "z_first": float(z[0]), "z_last": float(z[-1]),
                              "max_offset_nm": float(np.abs([r["offset_nm"] for r in rows]).max())})

    # one shared table (identical selection for all three cubes) + per-case tables
    common = rows_by_case["D030"]
    same = all(
        [r["index"] for r in rows_by_case[t]] == [r["index"] for r in common] for t in rows_by_case
    )
    log.record("identical_selection_all_cases", {"value": bool(same)})

    csv_path = C.EXPORT / "selected_50_zeta_layers.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["k", "target_zeta_nm", "layer_index", "actual_zeta_nm", "offset_nm"])
        for r in common:
            w.writerow([r["k"], f"{r['target_zeta_nm']:.6f}", r["index"],
                        f"{r['actual_zeta_nm']:.6f}", f"{r['offset_nm']:.6f}"])

    payload = {
        "schema": "v4-visual-selected-layers-1.0",
        "n_layers": len(common),
        "zeta_range_nm": [float(C.Z_LO), float(C.Z_HI)],
        "selection_rule": "50 equally spaced targets over [-170,170] nm, snapped to the nearest unused real layer (grid step 2 nm)",
        "identical_across_diameters": bool(same),
        "per_diameter": {
            t: {
                "cube": str(C.cube_path(t)),
                "layers": rows_by_case[t],
                "indices": [r["index"] for r in rows_by_case[t]],
                "zeta_nm": [r["actual_zeta_nm"] for r in rows_by_case[t]],
            }
            for t in rows_by_case
        },
    }
    (C.EXPORT / "selected_50_zeta_layers.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    gs = {}
    for tag, D, h in C.CASES:
        s = C.global_stats(tag)
        s["diameter_nm"] = D
        s["center_height_nm"] = h
        gs[tag] = s
        (C.EXPORT / f"stats_{tag}.json").write_text(
            json.dumps(s, indent=2), encoding="utf-8")

    vmax = C.common_scale()
    reference = sorted(v["cube_max_abs_I_cross"] for v in gs.values())[-1]
    assert abs(vmax - reference) < 1e-12
    common_payload = {
        "schema": "v4-visual-common-scale-1.0",
        "quantity": "I_cross = 2 Re(E_ref * conj(E_scat))",
        "rule": "symmetric linear scale, vmin=-vmax, vmax=+vmax with vmax = max over the three cubes of max|I_cross|",
        "common_vmax": vmax,
        "per_diameter_vmax": {t: gs[t]["cube_max_abs_I_cross"] for t in gs},
        "normalization": "normalized panels use I_cross / max|I_cross| of the same cube",
        "units": "dimensionless, relative to the shared on-axis reference; absolute_calibration=false",
    }
    (C.EXPORT / "common_scale.json").write_text(
        json.dumps(common_payload, indent=2), encoding="utf-8")

    log.done({"csv": str(csv_path), "common_vmax": vmax})
    print(json.dumps({"ok": True, "common_vmax": vmax,
                      "layers": [r["actual_zeta_nm"] for r in common]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

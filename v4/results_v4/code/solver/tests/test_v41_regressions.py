"""Focused regressions for the V4.1 documentation/convention repairs.

These checks are intentionally separate from the historical 40-test baseline so
the baseline counts remain auditable.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import iscat_core as core
import run_dataset as ds

CFG = ROOT / "configs/target_Fe3O4_NA145.json"


class V41Regressions(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(CFG.read_text(encoding="utf-8"))
        self.op = core.optical_params(self.c)
        self.op["cs_over_cr"] = 1.0

    def test_fresnel_return_direction_normal_incidence(self):
        rs, rp, ts, tp, *_ = core.fresnel_glass_sample(np.array([0.0]), self.op)
        expected_return = 2 * 1.33 / (1.33 + 1.52)
        self.assertAlmostEqual(float(np.asarray(ts).reshape(-1)[0].real), expected_return, places=14)
        self.assertAlmostEqual(float(np.asarray(tp).reshape(-1)[0].real), expected_return, places=14)
        self.assertNotAlmostEqual(float(np.asarray(ts).reshape(-1)[0].real), 2 * 1.52 / (1.33 + 1.52), places=8)

    def test_unit_scattering_basis_excludes_eta(self):
        p_unit = core.pupil_precompute(self.op, 30.0, 32, 16)
        op_default = dict(self.op)
        op_default.pop("cs_over_cr")
        p_default = core.pupil_precompute(op_default, 30.0, 32, 16)
        ratio = p_unit["scat_strength"] / p_default["scat_strength"]
        finite = np.abs(p_default["scat_strength"]) > 1e-14
        np.testing.assert_allclose(ratio[finite], 1.0 / p_default["eta"], rtol=1e-12, atol=1e-14)

    def test_gamma_half_applied_once_in_saved_signal_definition(self):
        rng = np.random.default_rng(4101)
        er = rng.normal(size=(2, 3, 2)) + 1j * rng.normal(size=(2, 3, 2))
        eu = rng.normal(size=(2, 3, 2)) + 1j * rng.normal(size=(2, 3, 2))
        gamma = 0.5 + 0.0j
        s, basis, _, _ = ds.decompose(er, eu, gamma)
        np.testing.assert_allclose(s["I_scat"], 0.25 * basis["I_scat_unit"], rtol=1e-13, atol=1e-15)
        np.testing.assert_allclose(s["I_cross"], basis["Q_real"], rtol=1e-13, atol=1e-15)
        self.assertIn("op['cs_over_cr']=1.0", (ROOT / "src/run_dataset.py").read_text(encoding="utf-8"))

    def test_figure_script_honours_explicit_output_directory(self):
        script = ROOT.parent / "figures/make_f1.py"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "isolated_figures"
            r = subprocess.run([sys.executable, str(script), "--out", str(out)],
                               text=True, capture_output=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((out / "F1_geometry_method/F1_geometry_method.png").is_file())


if __name__ == "__main__":
    unittest.main()
"""Destructive-storage and order-invariance checks (no physical certification)."""
from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path
import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import run_dataset as ds

CFG = ROOT / 'configs/target_Fe3O4_NA145.json'


def tiny_config(diameters=(30,)):
    c = json.loads(CFG.read_text(encoding='utf-8'))
    c['diameters_nm'] = list(diameters)
    c['grid_pilot'].update(xy_min_nm=-40, xy_max_nm=40, xy_step_nm=20,
                           zeta_min_nm=-10, zeta_max_nm=10, zeta_step_nm=10,
                           radial_points=81, quadrature_below_critical=32,
                           quadrature_above_critical=16)
    return c


class Robustness(unittest.TestCase):
    def _make(self, tmp, diameters=(30,)):
        p = Path(tmp); p.mkdir(parents=True, exist_ok=True); c = tiny_config(diameters)
        cfg = p / 'config.json'; cfg.write_text(json.dumps(c), encoding='utf-8')
        out = p / 'out'
        summary = ds.run(cfg, out, True, False, True)
        return p, c, out, summary

    def test_truncated_and_tampered_cubes_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, c, out, summary = self._make(tmp)
            cube = out / 'D030nm' / 'cube.h5'
            csha = summary['config_sha256']; code = summary['implementation_sha256']
            ds.validate_cube(cube, csha, code)          # baseline passes

            # 1. schema tampering
            with h5py.File(cube, 'r+') as f:
                f.attrs['schema'] = 'wrong'
            with self.assertRaises(ValueError):
                ds.validate_cube(cube)
            with h5py.File(cube, 'r+') as f:
                f.attrs['schema'] = ds.SCHEMA

            # 2. incomplete slice count
            with h5py.File(cube, 'r+') as f:
                f.attrs['completed_slices'] = 0
            with self.assertRaises(ValueError):
                ds.validate_cube(cube)
            with h5py.File(cube, 'r+') as f:
                f.attrs['completed_slices'] = len(f['coords/zeta_nm'])

            # 3. altered field value breaks the stored algebra
            with h5py.File(cube, 'r+') as f:
                f['fields/E_ref_real'][0, 2, 2, 0] += np.float32(0.1)
            with self.assertRaises(ValueError):
                ds.validate_cube(cube, csha, code)

    def test_truncated_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, c, out, summary = self._make(tmp)
            cube = out / 'D030nm' / 'cube.h5'
            data = cube.read_bytes()
            cube.write_bytes(data[: len(data) // 2])
            with self.assertRaises(Exception):
                ds.validate_cube(cube, summary['config_sha256'], summary['implementation_sha256'])

    def test_config_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, c, out, summary = self._make(tmp)
            cube = out / 'D030nm' / 'cube.h5'
            c['optics']['NA'] = 1.44
            with self.assertRaises(ValueError):
                ds.validate_cube(cube, ds.canonical_hash(c), summary['implementation_sha256'])

    def test_diameter_order_invariance(self):
        with tempfile.TemporaryDirectory() as tmp:
            pa, ca, outa, sa = self._make(Path(tmp) / 'a', (30, 100))
            pb, cb, outb, sb = self._make(Path(tmp) / 'b', (100, 30))
            # shared reference scale must not depend on the case ordering
            self.assertAlmostEqual(sa['reference_field_scale'], sb['reference_field_scale'], places=18)
            self.assertEqual(sa['reference_field_scale'], sb['reference_field_scale'])
            for D in (30, 100):
                va = json.loads((outa / f'D{D:03d}nm' / 'validation.json').read_text())
                vb = json.loads((outb / f'D{D:03d}nm' / 'validation.json').read_text())
                self.assertEqual(va['shape'], vb['shape'])
                self.assertEqual(va['max_normalized_signal_error'], vb['max_normalized_signal_error'])
            # per-voxel identity of the two orderings
            with h5py.File(outa / 'D100nm' / 'cube.h5', 'r') as fa, \
                 h5py.File(outb / 'D100nm' / 'cube.h5', 'r') as fb:
                for name in ('fields/E_ref_real', 'fields/E_scat_unit_imag', 'signals/I_total'):
                    np.testing.assert_array_equal(fa[name][:], fb[name][:])


if __name__ == '__main__':
    unittest.main()

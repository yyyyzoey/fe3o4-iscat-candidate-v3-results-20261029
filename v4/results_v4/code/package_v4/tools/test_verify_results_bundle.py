"""Negative/positive tests for verify_results_bundle.py.

Field-level cases run audit_cube on tiny synthetic HDF5 cubes (real h5py I/O).
Archive-level cases stub audit_cube and exercise the ZIP/hash/inventory logic.
"""
from __future__ import annotations
import hashlib, importlib.util, json, tempfile, unittest, zipfile
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("vrb", HERE / "verify_results_bundle.py")
vrb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vrb)

X = np.array([-10.0, 0.0, 10.0])
Z = np.array([-2.0, 0.0, 2.0])


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def make_cube(path: Path, D: int = 30, mutate=None) -> Path:
    shape = (len(Z), len(X), len(X))
    er = np.ones(shape + (2,), dtype=np.complex128)
    eu = np.full(shape + (2,), 0.01 + 0.01j, dtype=np.complex128)
    gamma = 0.5 + 0j
    ir = np.sum(np.abs(er) ** 2, axis=-1)
    u = np.sum(np.abs(eu) ** 2, axis=-1)
    q = np.sum(np.conj(er) * eu, axis=-1)
    isc = abs(gamma) ** 2 * u
    cross = 2 * np.real(gamma * q)
    total = ir + isc + cross
    defined = ir > 1e-12
    stable = ir >= 0.005 * np.max(ir)
    local = np.full(ir.shape, np.nan)
    np.divide(isc + cross, ir, out=local, where=defined)
    with h5py.File(path, "w") as f:
        f.attrs.update(schema="iscat-through-focus-v3.0", status=vrb.CLASS, grid_mode="full",
                       axis_order="zeta,y,x", field_component_order="Ex,Ey",
                       diameter_nm=D, particle_radius_nm=D / 2, center_height_nm=D / 2,
                       surface_gap_nm=0.0, wavelength_nm=532.0, NA=1.45, material="Fe3O4",
                       completed_slices=len(Z), gamma_real=0.5, gamma_imag=0.0,
                       absolute_calibration=False, is_sample_space_field=False,
                       physical_validation="NOT_ESTABLISHED", reference_field_scale=1.0)
        f.create_dataset("coords/x_object_nm", data=X)
        f.create_dataset("coords/y_object_nm", data=X)
        f.create_dataset("coords/zeta_nm", data=Z)
        f.create_dataset("coords/oil_thickness_nm", data=np.full(len(Z), 100.0))
        fields = {"E_ref_real": er.real, "E_ref_imag": er.imag,
                  "E_scat_unit_real": eu.real, "E_scat_unit_imag": eu.imag}
        for k, v in fields.items():
            f.create_dataset("fields/" + k, data=v.astype("f4"))
        for k, v in {"I_ref": ir, "I_scat": isc, "I_cross": cross, "I_total": total,
                     "contrast_local": local, "contrast_fixed_reference": isc + cross}.items():
            f.create_dataset("signals/" + k, data=v.astype("f4"))
        for k, v in {"I_scat_unit": u, "Q_real": q.real, "Q_imag": q.imag}.items():
            f.create_dataset("basis/" + k, data=v.astype("f4"))
        f.create_dataset("masks/defined_contrast", data=defined.astype("u1"))
        f.create_dataset("masks/stable_reference", data=stable.astype("u1"))
        if mutate:
            mutate(f)
    return path


class FieldLevelTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.p = Path(self.td.name) / "cube.h5"

    def tearDown(self):
        self.td.cleanup()

    def audit(self):
        return vrb.audit_cube(self.p, 30, x=X, z=Z, enforce_provenance=False)

    def test_valid_synthetic_cube_passes(self):
        make_cube(self.p)
        r = self.audit()
        self.assertEqual(r["layers_actually_read"], len(Z))

    def test_masked_nan_outside_defined_region_is_legal(self):
        def zero_ref(f):
            f["fields/E_ref_real"][1, 1, 1, :] = 0.0
            f["fields/E_ref_imag"][1, 1, 1, :] = 0.0
            # Keep stored derived quantities algebraically consistent with the
            # zeroed reference. With E_ref=0, Q vanishes, total intensity is
            # I_scat, and local contrast is undefined (NaN).
            isc = float(f["signals/I_scat"][1, 1, 1])
            f["signals/I_ref"][1, 1, 1] = 0.0
            f["signals/I_cross"][1, 1, 1] = 0.0
            f["signals/I_total"][1, 1, 1] = isc
            f["signals/contrast_fixed_reference"][1, 1, 1] = isc
            f["signals/contrast_local"][1, 1, 1] = np.nan
            f["basis/Q_real"][1, 1, 1] = 0.0
            f["basis/Q_imag"][1, 1, 1] = 0.0
            f["masks/defined_contrast"][1, 1, 1] = 0
            f["masks/stable_reference"][1, 1, 1] = 0
        make_cube(self.p, mutate=zero_ref)
        with h5py.File(self.p, "r+") as f:
            ir = np.sum(np.abs(f["fields/E_ref_real"][1, 1, 1].astype("f8")) ** 2
                        + np.abs(f["fields/E_ref_imag"][1, 1, 1].astype("f8")) ** 2)
            self.assertEqual(ir, 0.0)
            self.assertTrue(np.isnan(f["signals/contrast_local"][1, 1, 1]))
        self.assertEqual(self.audit()["layers_actually_read"], len(Z))

    def test_all_nan_cross_term_rejected(self):
        make_cube(self.p, mutate=lambda f: f["signals/I_cross"].__setitem__(Ellipsis, np.nan))
        with self.assertRaises(ValueError):
            self.audit()

    def test_zero_coordinate_rejected(self):
        make_cube(self.p)
        with self.assertRaises(ValueError):
            vrb.audit_cube(self.p, 30, x=X, z=np.zeros_like(Z), enforce_provenance=False)

    def test_missing_field_rejected(self):
        make_cube(self.p, mutate=lambda f: f.__delitem__("fields/E_ref_imag"))
        with self.assertRaises(Exception):
            self.audit()

    def test_late_layer_nan_rejected(self):
        make_cube(self.p, mutate=lambda f: f["fields/E_ref_real"].__setitem__((2, 0, 0, 0), np.nan))
        with self.assertRaises(ValueError):
            self.audit()

    def test_wrong_parameter_rejected(self):
        make_cube(self.p, mutate=lambda f: f.attrs.__setitem__("NA", 1.40))
        with self.assertRaises(ValueError):
            self.audit()

    def test_wrong_mask_rejected(self):
        make_cube(self.p, mutate=lambda f: f["masks/defined_contrast"].__setitem__(Ellipsis, 0))
        with self.assertRaises(ValueError):
            self.audit()


class ArchiveLevelTests(unittest.TestCase):
    CUBES = (30, 100, 200)

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        self._h5 = vrb.H5_SHA
        self._audit = vrb.audit_cube
        vrb.H5_SHA = {D: sha(self.cube_bytes(D)) for D in self.CUBES}
        vrb.audit_cube = lambda path, D: {"pass": True, "diameter_nm": D,
                                          "layers_actually_read": 171, "reference_field_scale": 1.0}

    def tearDown(self):
        vrb.H5_SHA = self._h5
        vrb.audit_cube = self._audit
        self.td.cleanup()

    @staticmethod
    def cube_bytes(D):
        return f"fake-cube-{D}".encode()

    def build(self, cubes=None, duplicate=False):
        cubes = self.CUBES if cubes is None else cubes
        files = {f"results_v4/data/D{D:03d}nm/cube.h5": self.cube_bytes(D) for D in cubes}
        files["results_v4/status.json"] = json.dumps({
            "absolute_calibration": False, "sample_space_near_field": False,
            "formula_fidelity": "UNVERIFIED", "high_na_model_validation": "UNVERIFIED",
            "result_class": "CANDIDATE"}).encode()
        manifest = "\n".join(f"{sha(b)}  {n[len('results_v4/'):]}" for n, b in files.items())
        files["results_v4/SHA256SUMS.txt"] = manifest.encode()
        p = self.dir / "bundle.zip"
        with zipfile.ZipFile(p, "w") as z:
            for n, b in files.items():
                z.writestr(n, b)
            if duplicate:
                z.writestr("results_v4/status.json", files["results_v4/status.json"])
        return p, len(files) + (1 if duplicate else 0)

    def call(self, p, entries, mode="full", digest=None, size=None):
        blob = p.read_bytes()
        return vrb.audit_archive(p, mode=mode, expect_sha256=digest or sha(blob),
                                 expect_bytes=size or len(blob), expect_entries=entries)

    def test_synthetic_archive_full_mode_passes(self):
        p, n = self.build()
        r = self.call(p, n)
        self.assertTrue(r["pass"])
        self.assertEqual(r["hdf5_layers_read"], 513)

    def test_wrong_external_hash_rejected(self):
        p, n = self.build()
        with self.assertRaises(ValueError):
            self.call(p, n, digest="0" * 64)

    def test_duplicate_zip_names_rejected(self):
        p, n = self.build(duplicate=True)
        with self.assertRaises(ValueError):
            self.call(p, n)

    def test_missing_cube_rejected(self):
        p, n = self.build(cubes=(30, 100))
        with self.assertRaises(ValueError):
            self.call(p, n)

    def test_full_mode_refuses_light_only_archive(self):
        p, n = self.build(cubes=())
        with self.assertRaises(ValueError) as ctx:
            self.call(p, n)
        self.assertIn("light fallback refused", str(ctx.exception))

    def test_light_mode_is_explicit_and_scoped(self):
        p, n = self.build(cubes=())
        r = self.call(p, n, mode="light")
        self.assertEqual(r["pass_scope"], "LIGHT_NO_HDF5")
        self.assertEqual(r["hdf5_layers_read"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

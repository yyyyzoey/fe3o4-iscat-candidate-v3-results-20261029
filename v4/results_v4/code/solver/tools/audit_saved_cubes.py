#!/usr/bin/env python3
"""Independent layer-by-layer audit of saved full cubes against the data contract."""
from pathlib import Path
import argparse, hashlib, json
import h5py
import numpy as np

STATUS = 'CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    root = a.directory
    cfg = json.loads((root/'config_used.json').read_text(encoding='utf-8'))
    exp = np.arange(-170.0, 171.0, 2.0)
    expx = np.arange(-1200.0, 1201.0, 10.0)
    manifest = {}
    for line in (root/'sha256_manifest.txt').read_text(encoding='utf-8').splitlines():
        h, rel = line.split('  ', 1)
        manifest[rel] = h
    report = {'directory': str(root.resolve()), 'data_checks_pass': True,
              'manifest_entries_verified': 0, 'cases': {}, 'failures': []}
    scales = []

    def fail(msg):
        report['data_checks_pass'] = False
        report['failures'].append(msg)

    for rel, expected in sorted(manifest.items()):
        if sha256(root/rel) != expected:
            fail('manifest SHA256 mismatch: '+rel)
        report['manifest_entries_verified'] += 1

    for D in cfg['diameters_nm']:
        rel = f'D{D:03d}nm/cube.h5'; path = root/rel
        case = {'file': str(path.resolve()), 'bytes': path.stat().st_size,
                'layers_read': 0, 'gamma': None,
                'nonfinite_noncontrast': 0, 'negative_intensity_voxels': 0,
                'undefined_contrast_non_nan': 0, 'defined_contrast_nonfinite': 0,
                'defined_mask_mismatch_outside_tolerance': 0,
                'stable_mask_mismatch_outside_tolerance': 0,
                'max_total_identity_normalized_residual': 0.0,
                'max_fixed_contrast_identity_normalized_residual': 0.0}
        with h5py.File(path, 'r') as f:
            z = f['coords/zeta_nm'][:]; x = f['coords/x_object_nm'][:]; y = f['coords/y_object_nm'][:]
            shape = tuple(f['signals/I_total'].shape)
            case['shape'] = list(shape); case['layer_shape'] = [int(shape[1]), int(shape[2])]
            case['file_sha256'] = sha256(path)
            case['manifest_sha256'] = manifest.get(rel)
            case['sha256_matches_manifest'] = case['file_sha256'] == case['manifest_sha256']
            case['completed_slices_attr'] = int(f.attrs['completed_slices'])
            case['zeta_zero_present'] = bool(np.any(z == 0.0))
            case['coordinates_exact'] = bool(np.array_equal(z, exp) and np.array_equal(x, expx) and np.array_equal(y, expx))
            case['metadata'] = {
                'schema': f.attrs['schema'], 'status': f.attrs['status'],
                'diameter_nm': float(f.attrs['diameter_nm']),
                'radius_nm': float(f.attrs['particle_radius_nm']),
                'center_height_nm': float(f.attrs['center_height_nm']),
                'surface_gap_nm': float(f.attrs['surface_gap_nm']),
                'NA': float(f.attrs['NA']), 'wavelength_nm': float(f.attrs['wavelength_nm']),
                'material': f.attrs['material'], 'axis_order': f.attrs['axis_order'],
                'field_component_order': f.attrs['field_component_order'],
                'absolute_calibration': bool(f.attrs['absolute_calibration']),
                'is_sample_space_field': bool(f.attrs['is_sample_space_field']),
                'supercritical_sector': f.attrs['supercritical_sector'],
                'reference_field_scale': float(f.attrs['reference_field_scale']),
            }
            scales.append(float(f.attrs['reference_field_scale']))
            if list(shape) != [171, 241, 241]: fail(f'{rel}: wrong shape {shape}')
            if f.attrs['schema'] != 'iscat-through-focus-v3.0': fail(f'{rel}: wrong schema')
            if f.attrs['status'] != STATUS: fail(f'{rel}: wrong candidate status')
            if int(f.attrs['completed_slices']) != 171: fail(f'{rel}: incomplete slices')
            if not case['coordinates_exact'] or not case['zeta_zero_present']: fail(f'{rel}: coordinates invalid')
            if abs(float(f.attrs['NA'])-1.45) > 1e-15: fail(f'{rel}: NA changed')
            if abs(float(f.attrs['wavelength_nm'])-532.0) > 1e-15: fail(f'{rel}: wavelength changed')
            if abs(float(f.attrs['center_height_nm'])-D/2) > 1e-12 or float(f.attrs['surface_gap_nm']) != 0.0:
                fail(f'{rel}: surface-bound geometry invalid')
            if bool(f.attrs['absolute_calibration']) is not False: fail(f'{rel}: absolute calibration claimed')
            if bool(f.attrs['is_sample_space_field']) is not False: fail(f'{rel}: sample-space field claimed')
            if f.attrs['supercritical_sector'] != 'ANALYTIC_CONTINUATION_UNVALIDATED': fail(f'{rel}: supercritical flag changed')

            for iz in range(len(z)):
                fields = [f['fields/'+n][iz] for n in ('E_ref_real','E_ref_imag','E_scat_unit_real','E_scat_unit_imag')]
                if not all(np.isfinite(q).all() for q in fields):
                    case['nonfinite_noncontrast'] += 1
                values = {n: f['signals/'+n][iz] for n in ('I_ref','I_scat','I_cross','I_total','contrast_fixed_reference')}
                for n, q in values.items():
                    if not np.isfinite(q).all(): case['nonfinite_noncontrast'] += 1
                for n in ('I_scat_unit','Q_real','Q_imag'):
                    if not np.isfinite(f['basis/'+n][iz]).all(): case['nonfinite_noncontrast'] += 1
                valid = f['masks/defined_contrast'][iz].astype(bool)
                stable = f['masks/stable_reference'][iz].astype(bool)
                cl = f['signals/contrast_local'][iz]
                if not np.isnan(cl[~valid]).all(): case['undefined_contrast_non_nan'] += int(np.count_nonzero(~np.isnan(cl[~valid])))
                if not np.isfinite(cl[valid]).all(): case['defined_contrast_nonfinite'] += int(np.count_nonzero(~np.isfinite(cl[valid])))
                ir = values['I_ref']; isc = values['I_scat']; ic = values['I_cross']; it = values['I_total']
                case['negative_intensity_voxels'] += int(np.count_nonzero(ir < 0)+np.count_nonzero(isc < 0)+np.count_nonzero(it < 0))
                expected_valid = ir > np.float32(1e-12)
                bad_valid = np.abs(ir-np.float32(1e-12)) > np.float32(1e-6*1e-12)
                case['defined_mask_mismatch_outside_tolerance'] += int(np.count_nonzero((valid != expected_valid) & bad_valid))
                expected_stable = ir >= np.float32(0.005)
                bad_stable = np.abs(ir-np.float32(0.005)) > np.float32(1e-6*0.005)
                case['stable_mask_mismatch_outside_tolerance'] += int(np.count_nonzero((stable != expected_stable) & bad_stable))
                scale_total = max(1.0, float(np.max(np.abs(it))))
                scale_fixed = max(1.0, float(np.max(np.abs(values['contrast_fixed_reference']))))
                case['max_total_identity_normalized_residual'] = max(
                    case['max_total_identity_normalized_residual'],
                    float(np.max(np.abs(it-(ir+isc+ic)))/scale_total))
                case['max_fixed_contrast_identity_normalized_residual'] = max(
                    case['max_fixed_contrast_identity_normalized_residual'],
                    float(np.max(np.abs(values['contrast_fixed_reference']-(isc+ic)))/scale_fixed))
                case['layers_read'] += 1
        checks = [case['sha256_matches_manifest'], case['completed_slices_attr'] == 171,
                  case['layers_read'] == 171, case['zeta_zero_present'], case['coordinates_exact'],
                  case['nonfinite_noncontrast'] == 0, case['negative_intensity_voxels'] == 0,
                  case['undefined_contrast_non_nan'] == 0, case['defined_contrast_nonfinite'] == 0,
                  case['defined_mask_mismatch_outside_tolerance'] == 0,
                  case['stable_mask_mismatch_outside_tolerance'] == 0,
                  case['max_total_identity_normalized_residual'] <= 1e-5,
                  case['max_fixed_contrast_identity_normalized_residual'] <= 1e-5]
        case['case_pass'] = bool(all(checks))
        if not case['case_pass']: fail(f'D{D}: one or more cube checks failed')
        report['cases'][str(D)] = case

    report['shared_reference_scale'] = all(abs(v-scales[0]) < 1e-30 for v in scales) if scales else False
    if not report['shared_reference_scale']: fail('reference scale differs between diameters')
    report['actual_shapes'] = {k: v['shape'] for k, v in report['cases'].items()}
    report['all_files_171_layers'] = all(v['layers_read'] == 171 for v in report['cases'].values())
    (a.out.parent).mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'data_checks_pass': report['data_checks_pass'],
                      'actual_shapes': report['actual_shapes'],
                      'all_files_171_layers': report['all_files_171_layers'],
                      'manifest_entries_verified': report['manifest_entries_verified'],
                      'report': str(a.out)}, indent=2))
    raise SystemExit(0 if report['data_checks_pass'] else 2)


if __name__ == '__main__':
    main()

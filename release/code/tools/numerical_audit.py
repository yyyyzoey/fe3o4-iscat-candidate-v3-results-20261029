#!/usr/bin/env python3
"""Convergence and independent numerical checks; no experimental validation.

All complex-field comparisons use both detector components at selected planes on
the full 241 x 241 output grid.  Relative and absolute L2/L-infinity errors are
reported without phase alignment or per-plane normalisation.
"""
from pathlib import Path
import argparse, json, sys
import numpy as np
from scipy.interpolate import RectBivariateSpline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import iscat_core as core
from run_dataset import dump, canonical_hash, implementation_hash, file_hash

REL_TOL = 1e-3
MIE_TOL = 1e-6
QUAD_DENSITIES = ((128, 64), (256, 128), (512, 256), (1024, 512))


def metrics(a, b):
    a = np.asarray(a); b = np.asarray(b); d = a-b
    ref_l2 = float(np.linalg.norm(b))
    ref_linf = float(np.max(np.abs(b)))
    return {
        'relative_l2': float(np.linalg.norm(d)/max(ref_l2, 1e-300)),
        'relative_linf': float(np.max(np.abs(d))/max(ref_linf, 1e-300)),
        'absolute_l2': float(np.linalg.norm(d)),
        'absolute_linf': float(np.max(np.abs(d))),
        'reference_l2': ref_l2,
        'reference_linf': ref_linf,
    }


def field_metrics(er_a, es_a, er_b, es_b):
    return {
        'E_ref_all_components': metrics(er_a, er_b),
        'E_scat_unit_all_components': metrics(es_a, es_b),
        'combined_all_components': metrics(np.concatenate((er_a, es_a), axis=-1),
                                           np.concatenate((er_b, es_b), axis=-1)),
    }


def is_pass(errors):
    return all(v['relative_l2'] <= REL_TOL and v['relative_linf'] <= REL_TOL
               for v in errors.values())


def fields_from_radial(rad, z_count, rgrid, geo):
    er = np.empty((z_count, *geo['r'].shape, 2), dtype=np.complex128)
    es = np.empty_like(er)
    for iz in range(z_count):
        er[iz], es[iz] = core.fields_at_slice(rad, iz, rgrid, geo)
    return er, es


def fields_on_coords(rad, z_count, rgrid, xc, yc):
    X, Y = np.meshgrid(xc, yc, indexing='xy')
    r2 = X*X+Y*Y
    safe = np.where(r2 > 0, r2, 1.0)
    geo = {'r': np.sqrt(r2),
           'sin2': np.where(r2 > 0, 2*X*Y/safe, 0.0),
           'cos2': np.where(r2 > 0, (X*X-Y*Y)/safe, 0.0)}
    return fields_from_radial(rad, z_count, rgrid, geo)


def interpolate_complex_grid(grid, values, radii):
    return np.interp(radii, grid, values.real)+1j*np.interp(radii, grid, values.imag)


def mie_truncation_check(op, pup, extra_orders=10):
    a, b = core.mie_coefficients(pup['mie_x'], op['nparticle']/op['ns'])
    a2, b2 = core.mie_coefficients(pup['mie_x'], op['nparticle']/op['ns'],
                                   len(a)+extra_orders)
    mu = -pup['kzs']/op['ns']
    s1, s2 = core.mie_S1_S2(mu, a, b)
    s1b, s2b = core.mie_S1_S2(mu, a2, b2)
    _, _, ts, tp, *_ = core.fresnel_glass_sample(pup['u'], op)
    base = 0.5j*(s1*ts-s2*tp)
    raised = 0.5j*(s1b*ts-s2b*tp)
    change = raised-base
    m = metrics(raised, base)
    critical_index = int(np.argmin(np.abs(pup['u']-op['ns'])))
    return {
        'default_order': int(len(a)),
        'raised_order': int(len(a2)),
        'extra_orders': int(extra_orders),
        'max_absolute_complex_amplitude_change': float(np.max(np.abs(change))),
        'relative_complex_amplitude_change': float(np.max(np.abs(change))/max(np.max(np.abs(base)), 1e-300)),
        'relative_l2_change': m['relative_l2'],
        'relative_linf_change': m['relative_linf'],
        'pass_lt_1e-6': bool(np.max(np.abs(change))/max(np.max(np.abs(base)), 1e-300) < MIE_TOL),
        'u_at_index_closest_to_critical': float(pup['u'][critical_index]),
        'critical_u': float(op['ns']),
    }


def horizontal_midpoint_check(op, pup, zp, z_values, rgrid):
    # 10 nm samples on [-200,200]^2; compare the 5 nm midpoint values directly.
    xc = np.arange(-200.0, 200.0+5.0, 10.0)
    xm = 0.5*(xc[:-1]+xc[1:])
    rad = core.make_radial_response(op, pup, zp, z_values, rgrid)
    erc, esc = fields_on_coords(rad, len(z_values), rgrid, xc, xc)
    erm, esm = fields_on_coords(rad, len(z_values), rgrid, xm, xm)

    def linear(field):
        return 0.25*(field[:, :-1, :-1]+field[:, :-1, 1:] +
                     field[:, 1:, :-1]+field[:, 1:, 1:])

    def cubic(field):
        out = np.empty_like(erm)
        for iz in range(field.shape[0]):
            for ic in range(2):
                rr = RectBivariateSpline(xc, xc, field[iz, :, :, ic].real,
                                         kx=3, ky=3, s=0)
                ii = RectBivariateSpline(xc, xc, field[iz, :, :, ic].imag,
                                         kx=3, ky=3, s=0)
                out[iz, :, :, ic] = rr(xm, xm)+1j*ii(xm, xm)
        return out

    linear_errors = field_metrics(linear(erc), linear(esc), erm, esm)
    cubic_errors = field_metrics(cubic(erc), cubic(esc), erm, esm)
    return {
        'coarse_grid_step_nm': 10.0,
        'direct_evaluation_step_nm': 5.0,
        'coarse_region_nm': [-200.0, 200.0],
        'zeta_values_nm': [float(v) for v in z_values],
        'linear_midpoint_reconstruction': linear_errors,
        'linear_pass': bool(is_pass(linear_errors)),
        'cubic_midpoint_reconstruction': cubic_errors,
        'cubic_pass': bool(is_pass(cubic_errors)),
        'criterion': 'both detector components compared; cubic is the primary sampling test',
    }


def audit(config, out):
    c = json.loads(config.read_text(encoding='utf-8'))
    op = core.optical_params(c); op['cs_over_cr'] = 1.0
    x_full, zeta_full, rrad, geo, _ = core.axis_config(c, False)
    # Selected planes include both window edges, the in-focus plane and off-centre defocus.
    z_idx = [0, 42, 85, 127, 170]
    z_sel = zeta_full[z_idx]
    report = {
        'config_sha256': canonical_hash(c),
        'implementation_sha256': implementation_hash(),
        'audit_script_sha256': file_hash(Path(__file__)),
        'model_status': 'CANDIDATE',
        'thresholds': {'relative_l2': REL_TOL, 'relative_linf': REL_TOL,
                       'mie_relative_amplitude_change': MIE_TOL},
        'sampling': {
            'full_output_grid': [int(len(zeta_full)), int(len(x_full)), int(len(x_full))],
            'quadrature_densities': [list(v) for v in QUAD_DENSITIES],
            'radial_points_full': int(c['grid_full']['radial_points']),
            'selected_zeta_nm': [float(v) for v in z_sel],
            'selected_z_indices': z_idx,
            'full_grid_covers_axis_and_offaxis_to_diagonal_nm': float(np.hypot(1200, 1200)),
        },
        'cases': {},
        'physical_validation': False,
        'interpretation': 'Numerical convergence only; no source/physics certification.',
    }
    all_pass = True
    for D in map(float, c['diameters_nm']):
        responses = {}
        for nb, na in QUAD_DENSITIES:
            p = core.pupil_precompute(op, D, nb, na)
            rad = core.make_radial_response(op, p, D/2, z_sel, rrad)
            er, es = fields_from_radial(rad, len(z_sel), rrad, geo)
            responses[(nb, na)] = {'pupil': p, 'radial': rad, 'E_ref': er, 'E_scat': es}

        successive = []
        for lo, hi in zip(QUAD_DENSITIES[:-1], QUAD_DENSITIES[1:]):
            a, b = responses[lo], responses[hi]
            err = field_metrics(a['E_ref'], a['E_scat'], b['E_ref'], b['E_scat'])
            successive.append({'coarse': list(lo), 'fine': list(hi), 'errors': err,
                               'pass': bool(is_pass(err))})
            all_pass &= is_pass(err)

        p512 = responses[(512, 256)]['pupil']
        formal_512_1024 = successive[-1]

        # Radial resolution: compare the reconstructed 1601-point and 3201-point fields.
        rmax = float(np.sqrt(2)*1200*1.001)
        rg1601 = np.linspace(0.0, rmax, 1601)
        rg3201 = np.linspace(0.0, rmax, 3201)
        rad1601 = core.make_radial_response(op, p512, D/2, z_sel, rg1601)
        rad3201 = core.make_radial_response(op, p512, D/2, z_sel, rg3201)
        er1601, es1601 = fields_from_radial(rad1601, len(z_sel), rg1601, geo)
        er3201, es3201 = fields_from_radial(rad3201, len(z_sel), rg3201, geo)
        radial_errors = field_metrics(er1601, es1601, er3201, es3201)
        radial_pass = is_pass(radial_errors)
        all_pass &= radial_pass

        # Direct evaluation at radial points, including the near-critical radius and far off-axis.
        rtarget = np.array([0.0, 5.0, 10.0*np.sqrt(2), 50.0, 100.0*np.sqrt(2),
                            353.553390593, 500.0, 707.106781186, 1000.0,
                            np.sqrt(2)*1000.0, 1200.0, np.sqrt(2)*1200.0])
        direct = core.make_radial_response(op, p512, D/2, z_sel, rtarget)
        direct_errors = {}
        for name in ('er0', 'er2', 'es0', 'es2'):
            interp1601 = np.array([interpolate_complex_grid(rg1601, row, rtarget)
                                   for row in rad1601[name]])
            interp3201 = np.array([interpolate_complex_grid(rg3201, row, rtarget)
                                   for row in rad3201[name]])
            direct_errors[name+'_1601_vs_direct'] = metrics(interp1601, direct[name])
            direct_errors[name+'_3201_vs_direct'] = metrics(interp3201, direct[name])
        direct_pass = all(v['relative_l2'] <= REL_TOL and v['relative_linf'] <= REL_TOL
                          for v in direct_errors.values())
        all_pass &= direct_pass

        # 10 nm samples vs direct 5 nm midpoint model evaluation, both components.
        horizontal = horizontal_midpoint_check(op, p512, D/2, z_sel, rg1601)
        all_pass &= horizontal['cubic_pass']

        # 2 nm axial samples vs direct 1 nm midpoint evaluation, full complex vectors.
        z2 = zeta_full
        z1 = np.arange(-169.0, 170.0, 2.0)
        rad2 = core.make_radial_response(op, p512, D/2, z2, rrad)
        rad1 = core.make_radial_response(op, p512, D/2, z1, rrad)
        er2, es2 = fields_from_radial(rad2, len(z2), rrad, geo)
        er1, es1 = fields_from_radial(rad1, len(z1), rrad, geo)
        er_mid = 0.5*(er2[:-1]+er2[1:])
        es_mid = 0.5*(es2[:-1]+es2[1:])
        axial_errors = field_metrics(er_mid, es_mid, er1, es1)
        axial_pass = is_pass(axial_errors)
        all_pass &= axial_pass

        mie = mie_truncation_check(op, p512)
        mie_pass = mie['pass_lt_1e-6']
        all_pass &= mie_pass

        critical = p512['u']
        lower = critical[critical <= op['ns']]
        upper = critical[critical >= op['ns']]
        report['cases'][str(int(D))] = {
            'quadrature_successive': successive,
            'quadrature_512_256_vs_1024_512': formal_512_1024,
            'radial_1601_vs_3201_full_field': {
                'errors': radial_errors, 'pass': bool(radial_pass),
                'radial_points': [1601, 3201],
                'radial_span_nm': [0.0, rmax],
            },
            'radial_interpolation_vs_direct_evaluation': {
                'target_radii_nm': [float(v) for v in rtarget],
                'errors': direct_errors, 'pass': bool(direct_pass),
            },
            'horizontal_10nm_vs_direct_5nm_midpoint': horizontal,
            'axial_2nm_midpoint_vs_direct_1nm': {
                'errors': axial_errors, 'pass': bool(axial_pass),
                'coarse_layers': int(len(z2)), 'direct_layers': int(len(z1)),
            },
            'mie_truncation_increase': mie,
            'critical_quadrature': {
                'u_critical': float(op['ns']),
                'largest_u_below_or_at_critical': float(lower.max()),
                'smallest_u_above_or_at_critical': float(upper.min()),
                'points_below': int(np.count_nonzero(critical < op['ns'])),
                'points_above': int(np.count_nonzero(critical > op['ns'])),
            },
        }
    report['numerical_audit_pass'] = bool(all_pass)
    report['linear_midpoint_reconstruction_all_pass'] = bool(
        all(v['horizontal_10nm_vs_direct_5nm_midpoint']['linear_pass']
            for v in report['cases'].values()))
    report['strict_all_including_linear_reconstruction'] = bool(
        all_pass and report['linear_midpoint_reconstruction_all_pass'])
    dump(out, report)
    print(json.dumps({
        'numerical_audit_pass': bool(all_pass),
        'linear_midpoint_reconstruction_all_pass': report['linear_midpoint_reconstruction_all_pass'],
        'strict_all_including_linear_reconstruction': report['strict_all_including_linear_reconstruction'],
        'report': str(out),
    }, indent=2))
    return all_pass


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, default=ROOT/'configs/target_Fe3O4_NA145.json')
    p.add_argument('--out', type=Path, default=ROOT/'results/numerical_audit.json')
    a = p.parse_args()
    sys.exit(0 if audit(a.config, a.out) else 2)

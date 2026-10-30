#!/usr/bin/env python3
"""Read-only views for v3/v4 iSCAT cubes. Does not compute or certify optical fields.

Default accepts the full 171x241x241 target only. --allow-pilot is for tool tests;
all such output is visibly marked PILOT. Source status is never upgraded here.
One chart per figure; HTML galleries arrange existing figures without changing data.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import sys
from pathlib import Path

import h5py
import numpy as np

DIAMETERS = (30, 100, 200)
SIGNALS = ('I_ref', 'I_scat', 'I_cross', 'I_total', 'contrast_fixed_reference')
SLICES = (-170, -128, -86, -42, 0, 42, 86, 128, 170)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def axis_check(a: np.ndarray, name: str) -> None:
    if a.ndim != 1 or len(a) < 3 or not np.isfinite(a).all():
        raise ValueError(f'Invalid {name} coordinates')
    d = np.diff(a)
    if not (d > 0).all() or not np.allclose(d, d[0], rtol=0, atol=1e-8):
        raise ValueError(f'{name} must be uniformly increasing')
    if not np.isclose(a[0], -a[-1]) or not np.any(a == 0):
        raise ValueError(f'{name} must be symmetric and include zero')


def inspect(path: Path, diameter: int, allow_pilot: bool, data_root: Path | None = None) -> dict:
    """Stream saved fields and intensities. This is an algebra/data audit only."""
    with h5py.File(path, 'r') as f:
        x = f['coords/x_object_nm'][:]
        y = f['coords/y_object_nm'][:]
        z = f['coords/zeta_nm'][:]
        for a, name in ((x, 'x'), (y, 'y'), (z, 'zeta')):
            axis_check(a, name)
        if not allow_pilot:
            np.testing.assert_array_equal(x, np.arange(-1200, 1201, 10))
            np.testing.assert_array_equal(y, np.arange(-1200, 1201, 10))
            np.testing.assert_array_equal(z, np.arange(-170, 171, 2))
            if f.attrs.get('grid_mode') != 'full':
                raise ValueError('Pilot is not a final dataset')
        shape = (len(z), len(y), len(x))
        required = {'diameter_nm': diameter, 'center_height_nm': diameter/2,
                    'surface_gap_nm': 0., 'NA': 1.45, 'wavelength_nm': 532.}
        for key, val in required.items():
            if key not in f.attrs or not np.isclose(float(f.attrs[key]), val):
                raise ValueError(f'{path}: metadata mismatch {key}')
        if f.attrs.get('material') != 'Fe3O4':
            raise ValueError('Material must be Fe3O4')
        if f.attrs.get('axis_order') != 'zeta,y,x':
            raise ValueError('Unsupported axis order')
        if bool(f.attrs.get('is_sample_space_field', True)):
            raise ValueError('Not a through-focus dataset')
        if int(f.attrs.get('completed_slices', -1)) != len(z):
            raise ValueError('Incomplete cube')
        gamma = complex(float(f.attrs['gamma_real']), float(f.attrs['gamma_imag']))
        for n in SIGNALS:
            if f['signals/'+n].shape != shape:
                raise ValueError('Unexpected signal shape')
        field_names = ('E_ref_real', 'E_ref_imag', 'E_scat_unit_real', 'E_scat_unit_imag')
        for n in field_names:
            if f['fields/'+n].shape != (*shape, 2):
                raise ValueError('Unexpected field shape')
        maxima = {n: 0. for n in SIGNALS}
        minima = {n: float('inf') for n in SIGNALS}
        peaks = {n: {'value': 0., 'index': None} for n in SIGNALS}
        center = {n: [] for n in SIGNALS}
        worst = {n: 0. for n in SIGNALS}
        ix = int(np.flatnonzero(x == 0)[0]); iy = int(np.flatnonzero(y == 0)[0])
        for iz in range(len(z)):
            er = f['fields/E_ref_real'][iz].astype('f8') + 1j*f['fields/E_ref_imag'][iz].astype('f8')
            eu = f['fields/E_scat_unit_real'][iz].astype('f8') + 1j*f['fields/E_scat_unit_imag'][iz].astype('f8')
            if not np.isfinite(er).all() or not np.isfinite(eu).all():
                raise ValueError('Nonfinite field')
            es = gamma*eu
            ir = np.sum(abs(er)**2, axis=-1)
            isc = np.sum(abs(es)**2, axis=-1)
            cross = 2*np.real(np.sum(np.conj(er)*es, axis=-1))
            truth = {'I_ref': ir, 'I_scat': isc, 'I_cross': cross,
                     'I_total': np.sum(abs(er+es)**2, axis=-1),
                     'contrast_fixed_reference': isc+cross}
            for n in SIGNALS:
                a = f['signals/'+n][iz].astype('f8')
                if not np.isfinite(a).all():
                    raise ValueError('Nonfinite signal: '+n)
                if n in ('I_ref', 'I_scat', 'I_total') and np.min(a) < 0:
                    raise ValueError('Negative intensity: '+n)
                # These files use a shared reference intensity unit. Denominator 1
                # is a storage-algebra scale, not an optical-field convergence metric.
                err = np.max(abs(a-truth[n])) / max(1., float(np.max(abs(truth[n]))))
                worst[n] = max(worst[n], float(err))
                maxima[n] = max(maxima[n], float(np.max(abs(a))))
                minima[n] = min(minima[n], float(np.min(a)))
                loc = np.unravel_index(np.argmax(abs(a)), a.shape)
                if abs(float(a[loc])) > abs(peaks[n]['value']):
                    peaks[n] = {'value': float(a[loc]), 'index': [iz, int(loc[0]), int(loc[1])],
                                'zeta_nm': float(z[iz]), 'y_nm': float(y[loc[0]]), 'x_nm': float(x[loc[1]])}
                center[n].append(float(a[iy, ix]))
        if max(worst.values()) > 1e-5:
            raise ValueError(f'Saved field/signal mismatch: {worst}')
        source_label = path.relative_to(data_root).as_posix() if data_root is not None else path.name
        return dict(diameter_nm=diameter, source=source_label, sha256=digest(path),
                    source_status=str(f.attrs.get('status', 'UNKNOWN')),
                    grid_mode=str(f.attrs.get('grid_mode', 'UNKNOWN')),
                    shape=list(shape), x_nm=x.tolist(), y_nm=y.tolist(), zeta_nm=z.tolist(),
                    gamma=[gamma.real, gamma.imag],
                    reference_field_scale=float(f.attrs['reference_field_scale']),
                    max_abs=maxima, min=minima, peaks=peaks, center=center,
                    storage_errors=worst, data_algebra_pass=True,
                    optical_model_verified_by_this_tool=False)


def edges(a):
    return [float(a[0]-(a[1]-a[0])/2), float(a[-1]+(a[1]-a[0])/2)]


def save_image(data, aa, bb, output, title, xlabel, ylabel, limits, label, dpi):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4.7))
    im = ax.imshow(data, origin='lower', extent=edges(aa)+edges(bb),
                   aspect='equal', interpolation='nearest', vmin=limits[0], vmax=limits[1])
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
    fig.colorbar(im, ax=ax, label=label, shrink=.8)
    fig.tight_layout()
    fig.savefig(Path(str(output)+'.png'), dpi=dpi)
    fig.savefig(Path(str(output)+'.svg'))
    plt.close(fig)


def export_mesh(volume, x, y, z, out, title, step):
    from skimage.measure import marching_cubes
    import plotly.graph_objects as go
    import matplotlib.pyplot as plt
    maximum = float(np.max(abs(volume)))
    traces, surfaces = [], []
    if maximum > 0:
        vn = volume / maximum
        spacing = (float(z[1]-z[0]), float(y[1]-y[0]), float(x[1]-x[0]))
        for level in (-.75, -.5, -.25, .25, .5, .75):
            if not float(vn.min()) < level < float(vn.max()):
                surfaces.append({'level': level, 'present': False})
                continue
            verts, faces, _, _ = marching_cubes(vn, level=level, spacing=spacing,
                                               step_size=step, allow_degenerate=False)
            verts += np.array([z[0], y[0], x[0]])
            vx, vy, vz = verts[:, 2], verts[:, 1], verts[:, 0]
            name = f'J/max|J|={level:+.2f}'
            traces.append(go.Mesh3d(x=vx, y=vy, z=vz, i=faces[:, 0], j=faces[:, 1],
                                   k=faces[:, 2], name=name, showlegend=True,
                                   opacity=.4, hovertemplate='x=%{x:.1f} nm<br>y=%{y:.1f} nm<br>zeta=%{z:.1f} nm<extra>'+name+'</extra>'))
            surfaces.append({'level': level, 'present': True, 'triangles': len(faces),
                             'vertices': len(verts)})
        # Static overview uses the same meshes; no smoothing, hull, or radial rotation.
        fig = plt.figure(figsize=(7, 5))
        ax = fig.add_subplot(111, projection='3d')
        for tr in traces:
            ax.plot_trisurf(np.asarray(tr.x), np.asarray(tr.y), np.asarray(tr.z),
                            triangles=np.column_stack([tr.i, tr.j, tr.k]),
                            alpha=.35, linewidth=0, label=tr.name)
        ax.set(xlabel='x (nm)', ylabel='y (nm)', zlabel='zeta (nm)', title=title+'\nSigned interference iso-surfaces')
        
        if traces: ax.legend(loc='upper left', fontsize=7)
        ax.set_xlim(x[0], x[-1]); ax.set_ylim(y[0], y[-1]); ax.set_zlim(z[0], z[-1])
        ax.set_box_aspect((float(np.ptp(x)), float(np.ptp(y)), float(np.ptp(z))))
        fig.tight_layout(); fig.savefig(out.with_suffix('.png'), dpi=220); plt.close(fig)
    fig = go.Figure(traces)
    fig.update_layout(title=title+'<br>Through-focus coordinates; true axis aspect; surfaces may end at window boundary',
                      scene=dict(xaxis_title='x (nm)', yaxis_title='y (nm)', zaxis_title='zeta (nm, focus scan)',
                                 aspectmode='data'), showlegend=True)
    fig.write_html(str(out.with_suffix('.html')), include_plotlyjs=True, full_html=True)
    return {'normalization_max_abs': maximum, 'mesh_step_size': step,
            'mesh_is_display_only': True, 'aspect': 'data',
            'surface_levels': surfaces, 'not_a_particle_surface': True}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--allow-pilot', action='store_true')
    p.add_argument('--mesh-step', type=int, default=2)
    p.add_argument('--skip-3d', action='store_true', help='Partial export only; recorded as incomplete visualization')
    p.add_argument('--dpi', type=int, default=300)
    args = p.parse_args(argv)
    if args.mesh_step < 1 or args.dpi < 100:
        p.error('mesh-step must be >=1, dpi must be >=100')
    if args.out.exists() and any(args.out.iterdir()):
        p.error('Output must be empty: refusing to overwrite audit evidence')
    args.out.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    records = []
    for d in DIAMETERS:
        path = args.data_root/f'D{d:03d}nm'/'cube.h5'
        if not path.is_file():
            raise FileNotFoundError(path)
        records.append(inspect(path, d, args.allow_pilot, args.data_root))
    for r in records[1:]:
        for key in ('x_nm', 'y_nm', 'zeta_nm', 'gamma'):
            if r[key] != records[0][key]:
                raise ValueError('Incompatible cross-diameter comparison: '+key)
        if r['reference_field_scale'] != records[0]['reference_field_scale']:
            raise ValueError('Not a shared reference normalization')
    common_j = max(r['max_abs']['I_cross'] for r in records)
    common_s = max(r['max_abs']['contrast_fixed_reference'] for r in records)
    if common_j <= 0:
        raise ValueError('All interference terms are zero')
    pages, mesh_log = [], {}
    label_status = 'PILOT / NOT FINAL' if args.allow_pilot else 'SAVED MODEL DATA'
    for r in records:
        d = r['diameter_nm']; dd = args.out/f'D{d:03d}'; dd.mkdir()
        x, y, z = map(np.asarray, (r['x_nm'], r['y_nm'], r['zeta_nm']))
        iy, ix = int(np.flatnonzero(y == 0)[0]), int(np.flatnonzero(x == 0)[0])
        iz0 = int(np.flatnonzero(z == 0)[0]); si = sorted(set(int(np.argmin(abs(z-v))) for v in SLICES))
        base = f'Fe3O4 D={d} nm | {label_status}'
        with h5py.File(args.data_root / r['source'], 'r') as f:
            j = f['signals/I_cross'][:]
            for mode, norm, limits in [('shape', r['max_abs']['I_cross'], (-1, 1)),
                                       ('common', 1., (-common_j, common_j))]:
                if norm <= 0:
                    norm = 1.
                for iz in si:
                    name = f'{mode}_xy_{z[iz]:+07.1f}'
                    save_image(j[iz]/norm, x, y, dd/name,
                               base+f'\nzeta={z[iz]:g} nm | '+mode,
                               'x (nm)', 'y (nm)', limits,
                               'J / max_cube|J|' if mode=='shape' else 'J in shared model units', args.dpi)
                for name, a, axis in [('xz', j[:, iy, :], x), ('yz', j[:, :, ix], y)]:
                    save_image(a/norm, axis, z, dd/f'{mode}_{name}', base+'\n'+mode+' '+name,
                               'x (nm)' if name=='xz' else 'y (nm)', 'zeta (nm, focus scan)', limits,
                               'J / max_cube|J|' if mode=='shape' else 'J in shared model units', args.dpi)
            for n in ('I_ref', 'I_scat', 'I_cross', 'I_total'):
                a = f['signals/'+n][iz0]
                ma = r['max_abs'][n]
                lim = (-ma, ma) if n=='I_cross' else (0, ma)
                if ma == 0: lim = (-1, 1) if n=='I_cross' else (0, 1)
                save_image(a, x, y, dd/f'component_{n}', base+'\nzeta=0 nm | '+n,
                           'x (nm)', 'y (nm)', lim, n+' (shared model units)', args.dpi)
            if not args.skip_3d:
                mesh_log[str(d)] = export_mesh(j, x, y, z, dd/'signed_interference_3d', base,
                                              args.mesh_step)
        with (dd/'axis_values.csv').open('w', newline='', encoding='utf-8-sig') as h:
            w=csv.writer(h);w.writerow(['zeta_nm', *SIGNALS, 'J_div_max_cube_abs_J'])
            for i, v in enumerate(z):
                w.writerow([v, *[r['center'][n][i] for n in SIGNALS],
                            r['center']['I_cross'][i]/max(r['max_abs']['I_cross'], 1e-300)])
        pages.append((d, si, z))
    # Shared-scale and per-case-shape plots are explicitly distinct.
    for signal, mode in [('I_cross', 'common'), ('I_cross', 'shape'),
                         ('contrast_fixed_reference', 'common')]:
        fig, ax = plt.subplots(figsize=(8, 4.8))
        for r in records:
            a = np.asarray(r['center'][signal])
            divisor = r['max_abs'][signal] if mode=='shape' else 1.
            ax.plot(r['zeta_nm'], a/max(divisor, 1e-300), label=f"D={r['diameter_nm']} nm")
        ax.set(xlabel='zeta (nm, focus scan)', ylabel=signal+(' / max_cube_abs' if mode=='shape' else ' (shared model units)'),
               title=label_status+' | '+mode+' | no axial recentering')
        ax.legend();fig.tight_layout()
        name=args.out/f'axis_{signal}_{mode}'
        fig.savefig(name.with_suffix('.png'), dpi=args.dpi);fig.savefig(name.with_suffix('.svg'));plt.close(fig)
    audit = {'role': 'read_only_saved_data_export_NOT_optical_certification',
             'allow_pilot': args.allow_pilot, 'source_statuses': [r['source_status'] for r in records],
             'data_algebra_pass': True, 'visualization_complete': not args.skip_3d,
             'optical_model_verified_by_this_tool': False,
             'common_J_max_abs': common_j, 'common_total_signal_max_abs': common_s,
             'normalization': 'one constant per entire 3D cube for shape; common units for comparison; never per slice',
             'raw_data_changed': False, 'cases': records, 'meshes': mesh_log}
    (args.out/'export_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    lines=['<!doctype html><html><head><meta charset="utf-8"><title>Fe3O4 iSCAT saved-data review</title>',
           '<style>body{font:16px sans-serif;max-width:1600px;margin:30px auto;padding:20px} .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px} img{width:100%}figure{margin:0}code{word-break:break-all}</style></head><body>',
           '<h1>Fe3O4 single-particle through-focus interference</h1>',
           '<p>'+html.escape(label_status)+'. This exporter does not certify optical formulas. Source status: '+html.escape(', '.join(audit['source_statuses']))+'</p>',
           '<p>Third axis: focus offset zeta, not sample-space near field. Shape normalization is constant over each entire cube. Common-scale views retain relative model amplitudes. Surface boundaries may be cropped by the scan window.</p>',
           '<p><a href="export_audit.json">Data/source/export audit</a></p>']
    for d, si, z in pages:
        lines += [f'<h2>D={d} nm</h2>', f'<p><a href="D{d:03d}/axis_values.csv">Axial data CSV</a></p>']
        if not args.skip_3d:
            lines += [f'<p><a href="D{d:03d}/signed_interference_3d.html">Open offline interactive 3D surfaces</a></p>',
                      f'<img src="D{d:03d}/signed_interference_3d.png" style="max-width:700px">']
        for mode in ('shape', 'common'):
            lines += [f'<h3>{mode}: nine xy slices, then x-zeta / y-zeta sections</h3><div class="grid">']
            names=[f'{mode}_xy_{z[i]:+07.1f}' for i in si]+[f'{mode}_xz',f'{mode}_yz']
            for name in names:
                lines.append(f'<figure><img src="D{d:03d}/{name}.png" loading="lazy"><figcaption>{html.escape(name)}</figcaption></figure>')
            lines.append('</div>')
        lines += ['<h3>Field-intensity decomposition at zeta=0</h3><div class="grid">']
        for n in ('I_ref','I_scat','I_cross','I_total'):
            lines.append(f'<figure><img src="D{d:03d}/component_{n}.png" loading="lazy"><figcaption>{n}</figcaption></figure>')
        lines.append('</div>')
    for name in ('axis_I_cross_common','axis_I_cross_shape','axis_contrast_fixed_reference_common'):
        lines.append(f'<h2>{name}</h2><img src="{name}.png" style="max-width:1000px">')
    lines.append('</body></html>')
    (args.out/'index.html').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'data_algebra_pass': True, 'visualization_complete': not args.skip_3d,
                      'pilot_only': args.allow_pilot, 'out': args.out.as_posix(),
                      'optical_certification': False}))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'ERROR: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)

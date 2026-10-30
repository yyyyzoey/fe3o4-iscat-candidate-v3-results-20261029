#!/usr/bin/env python3
"""Extract axial profiles (x=y=0) and per-layer mask statistics from saved cubes."""
from pathlib import Path
import argparse, json
import h5py
import numpy as np

COLUMNS = ['diameter_nm', 'zeta_nm', 'I_ref', 'I_scat', 'I_cross', 'I_total',
           'contrast_local', 'contrast_fixed_reference', 'U', 'Q_real', 'Q_imag',
           'defined_fraction', 'stable_fraction']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--out', type=Path, default=None)
    a = p.parse_args()
    cfg = json.loads((a.directory/'config_used.json').read_text(encoding='utf-8'))
    out = a.out or (a.directory/'axis_profiles.csv')
    rows = [COLUMNS]
    for D in cfg['diameters_nm']:
        with h5py.File(a.directory/f'D{D:03d}nm/cube.h5', 'r') as f:
            z = f['coords/zeta_nm'][:]
            for iz in range(len(z)):
                iy = f['signals/I_ref'].shape[1]//2; ix = f['signals/I_ref'].shape[2]//2
                def val(group, name):
                    return float(f[f'{group}/{name}'][iz, iy, ix])
                rows.append([D, float(z[iz]), val('signals', 'I_ref'), val('signals', 'I_scat'),
                             val('signals', 'I_cross'), val('signals', 'I_total'),
                             val('signals', 'contrast_local'), val('signals', 'contrast_fixed_reference'),
                             val('basis', 'I_scat_unit'), val('basis', 'Q_real'), val('basis', 'Q_imag'),
                             float(np.mean(f['masks/defined_contrast'][iz])),
                             float(np.mean(f['masks/stable_reference'][iz]))])
    import csv
    with out.open('w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerows(rows)
    print(json.dumps({'out': str(out.resolve()), 'rows': len(rows)-1}, indent=2))


if __name__ == '__main__':
    main()

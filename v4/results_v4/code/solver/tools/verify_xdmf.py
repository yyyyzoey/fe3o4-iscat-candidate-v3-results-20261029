#!/usr/bin/env python3
"""Check XDMF wrappers: relative HDF paths, axis order, coordinates and attributes."""
from pathlib import Path
import argparse, json
import xml.etree.ElementTree as ET
import h5py
import numpy as np

EXPECTED = ['I_cross', 'I_total', 'I_ref', 'I_scat', 'contrast_fixed_reference', 'contrast_local']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    cfg = json.loads((a.directory/'config_used.json').read_text(encoding='utf-8'))
    report = {'directory': str(a.directory.resolve()), 'pass': True, 'files': {}, 'failures': []}

    def fail(msg):
        report['pass'] = False
        report['failures'].append(msg)

    expz = np.arange(-170.0, 171.0, 2.0); expx = np.arange(-1200.0, 1201.0, 10.0)
    for D in cfg['diameters_nm']:
        path = a.directory/f'D{D:03d}_focus_stack.xdmf'
        entry = {'xdmf': str(path.resolve()), 'exists': path.is_file()}
        if not path.is_file():
            fail(f'{path.name}: missing'); report['files'][str(D)] = entry; continue
        root = ET.parse(path).getroot()
        grid = root.find('./Domain/Grid')
        topo = grid.find('Topology'); geo = grid.find('Geometry')
        entry['grid_name'] = grid.get('Name'); entry['grid_type'] = grid.get('GridType')
        entry['dimensions'] = topo.get('Dimensions')
        if topo.get('TopologyType') != '3DRectMesh' or topo.get('Dimensions') != '171 241 241':
            fail(f'{path.name}: topology/dimensions wrong')
        if geo.get('GeometryType') != 'VXVYVZ':
            fail(f'{path.name}: geometry must be VXVYVZ (x,y,zeta)')
        coords = {}
        for item in geo.findall('DataItem'):
            h5ref = item.text.strip(); rel, ds = h5ref.split(':', 1)
            target = (path.parent/rel).resolve()
            ok = target.is_file()
            if not ok: fail(f'{path.name}: HDF file not resolvable {rel}')
            with h5py.File(target, 'r') as f:
                arr = f[ds][:]
            coords[ds.rsplit('/', 1)[-1]] = {'hdf': rel, 'dataset': ds, 'shape': list(arr.shape),
                                             'dtype': str(arr.dtype), 'n': int(arr.size)}
            if ok and not (np.array_equal(arr, expx) if 'x_object_nm' in ds or 'y_object_nm' in ds
                           else np.array_equal(arr, expz)):
                fail(f'{path.name}: coordinate values unexpected in {ds}')
        entry['geometry'] = coords
        if [coords.get(k, {}).get('n') for k in ('x_object_nm', 'y_object_nm', 'zeta_nm')] != [241, 241, 171]:
            fail(f'{path.name}: geometry lengths must be 241,241,171 (zeta is the 3rd axis)')
        attrs = {}
        for item in grid.findall('Attribute'):
            h5ref = item.find('DataItem').text.strip(); rel, ds = h5ref.split(':', 1)
            target = (path.parent/rel).resolve()
            with h5py.File(target, 'r') as f:
                ds_obj = f[ds]
                attrs[item.get('Name')] = {'hdf': rel, 'dataset': ds, 'shape': list(ds_obj.shape),
                                           'dtype': str(ds_obj.dtype), 'dims_attr': item.find('DataItem').get('Dimensions')}
            if list(ds_obj.shape) != [171, 241, 241]:
                fail(f'{path.name}: {ds} shape {list(ds_obj.shape)} != (171,241,241)')
            if item.find('DataItem').get('Dimensions') != '171 241 241':
                fail(f'{path.name}: DataItem Dimensions mismatch for {ds}')
        entry['attributes'] = attrs
        if sorted(attrs) != sorted(EXPECTED):
            fail(f'{path.name}: attribute set {sorted(attrs)} != {sorted(EXPECTED)}')
        info = [i.get('Value') for i in grid.findall('Information')]
        entry['information'] = info
        if not any('zeta' in str(v) for v in info):
            fail(f'{path.name}: missing zeta-is-focus-axis note')
        entry['file_bytes'] = path.stat().st_size
        report['files'][str(D)] = entry
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'xdmf_audit_pass': report['pass'], 'failures': report['failures'], 'report': str(a.out)}, indent=2))
    raise SystemExit(0 if report['pass'] else 2)


if __name__ == '__main__':
    main()

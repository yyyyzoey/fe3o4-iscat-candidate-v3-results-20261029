#!/usr/bin/env python3
"""Verify rendered PNG figures decode, match expected names and are not blank/degenerate."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image

EXPECTED = ['axis_comparison.png', 'plot_metadata.json']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    files = sorted(q for q in a.directory.iterdir() if q.suffix == '.png')
    report = {'directory': str(a.directory.resolve()), 'pass': True, 'figures': {}, 'failures': []}
    for D in (30, 100, 200):
        need = [f'D{D:03d}_z-00170.png', f'D{D:03d}_z+00000.png', f'D{D:03d}_z+00170.png',
                f'D{D:03d}_xz.png', f'D{D:03d}_yz.png']
        for name in need:
            if not (a.directory/name).is_file():
                report['pass'] = False; report['failures'].append('missing '+name)
    for name in EXPECTED:
        if not (a.directory/name).is_file():
            report['pass'] = False; report['failures'].append('missing '+name)
    for q in files:
        try:
            with Image.open(q) as im:
                im.load()
                arr = np.asarray(im.convert('L'), dtype=float)
        except Exception as exc:
            report['pass'] = False; report['failures'].append(f'{q.name}: undecodable {exc}')
            continue
        entry = {'bytes': q.stat().st_size, 'size_px': [im.width, im.height],
                 'sha256': hashlib.sha256(q.read_bytes()).hexdigest(),
                 'gray_min': float(arr.min()), 'gray_max': float(arr.max()),
                 'gray_std': float(arr.std()), 'ink_fraction': float(np.mean(arr < 250))}
        if min(im.width, im.height) < 300 or arr.std() < 1.0 or entry['ink_fraction'] < 0.01:
            report['pass'] = False; report['failures'].append(f'{q.name}: blank or too small')
        report['figures'][q.name] = entry
    meta = json.loads((a.directory/'plot_metadata.json').read_text(encoding='utf-8'))
    report['plot_metadata'] = meta
    if meta.get('status') != 'CANDIDATE':
        report['pass'] = False; report['failures'].append('plot_metadata status must stay CANDIDATE')
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'figure_audit_pass': report['pass'], 'count': len(files),
                      'failures': report['failures'], 'report': str(a.out)}, indent=2))
    raise SystemExit(0 if report['pass'] else 2)


if __name__ == '__main__':
    main()

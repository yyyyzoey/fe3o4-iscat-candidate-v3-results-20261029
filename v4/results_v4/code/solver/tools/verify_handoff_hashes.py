#!/usr/bin/env python3
"""Re-verify HANDOFF_SHA256.txt; report which handoff files changed (expected: tools/tests only)."""
from pathlib import Path
import argparse, hashlib, json

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=ROOT/'HANDOFF_SHA256.txt')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    entries = {}
    for line in a.manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        h, rel = line.split('  ', 1)
        entries[rel] = h
    report = {'manifest': str(a.manifest.resolve()), 'entries': len(entries),
              'unchanged': [], 'changed': [], 'missing': [], 'legacy_unchanged': True}
    for rel, expected in sorted(entries.items()):
        path = ROOT/rel
        if not path.is_file():
            report['missing'].append(rel); continue
        actual = sha256(path)
        (report['unchanged'] if actual == expected else report['changed']).append(rel)
    legacy = [r for r in report['changed']+report['missing'] if r.startswith('legacy/')]
    report['legacy_changed_or_missing'] = legacy
    report['legacy_unchanged'] = not legacy
    report['pass'] = bool(report['legacy_unchanged'] and not report['missing'])
    report['note'] = 'Changed entries are the audited edits (tools/, tests/); legacy/ must never change.'
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'pass': report['pass'], 'legacy_unchanged': report['legacy_unchanged'],
                      'changed': report['changed'], 'missing': report['missing'], 'report': str(a.out)}, indent=2))
    raise SystemExit(0 if report['pass'] else 2)


if __name__ == '__main__':
    main()

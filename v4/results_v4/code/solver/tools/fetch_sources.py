#!/usr/bin/env python3
"""Fetch only public, named sources and record full provenance.

Every attempt stores the URL, HTTP status, Content-Type, byte count, SHA256 and
UTC access time. A failed acquisition is recorded verbatim; a cached file is
never reported as a fresh download. Acquisition alone never certifies that a
formula comparison was completed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_FILE_ID = 52761698
SOURCES = {
    'figshare_supplement_file52761698.pdf': [
        f'https://ndownloader.figshare.com/files/{USER_FILE_ID}',
        f'https://opticapublishing.figshare.com/ndownloader/files/{USER_FILE_ID}',
        f'https://api.figshare.com/v2/file/download/{USER_FILE_ID}',
    ],
    'author_preprint_including_supplement.pdf': ['https://arxiv.org/pdf/2209.14508'],
    'figshare_article_metadata.json': ['https://api.figshare.com/v2/articles/22047950'],
    'Querry_full.yml': [
        'https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/'
        'master/database/data/main/Fe3O4/nk/Querry.yml'],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_pages(path: Path) -> int | None:
    exe = shutil.which('pdfinfo')
    if not exe:
        return None
    try:
        out = subprocess.run([exe, str(path)], capture_output=True, text=True,
                             timeout=60).stdout
    except Exception:
        return None
    for line in out.splitlines():
        if line.startswith('Pages:'):
            try:
                return int(line.split(':', 1)[1].strip())
            except ValueError:
                return None
    return None


def attempt(url: str, name: str):
    """One network attempt. Returns (payload|None, record)."""
    stamp = datetime.now(timezone.utc).isoformat()
    record = {'url': url, 'accessed_utc': stamp, 'ok': False}
    request = urllib.request.Request(url, headers={'User-Agent': 'iscat-research-handoff/3.1'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
            record['http_status'] = getattr(response, 'status', None)
            record['content_type'] = response.headers.get('Content-Type')
            record['final_url'] = response.url
            record['bytes'] = len(data)
            record['sha256'] = sha256_bytes(data)
        if name.endswith('.pdf') and not data.startswith(b'%PDF'):
            raise ValueError('Not a PDF; likely blocked HTML')
        if name.endswith('.json'):
            json.loads(data)
        if name.endswith('.yml') and b'Magnetite' not in data:
            raise ValueError('Unexpected material dataset')
        record['ok'] = True
        return data, record
    except Exception as exc:  # noqa: BLE001 - every failure must be recorded
        record['error'] = f'{type(exc).__name__}: {exc}'
        return None, record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'sources/downloaded')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        'retrieval_utc': datetime.now(timezone.utc).isoformat(),
        'user_requested_figshare_file_id': USER_FILE_ID,
        'files': {},
    }
    for name, urls in SOURCES.items():
        path = args.output / name
        cached_sha = sha256_bytes(path.read_bytes()) if path.exists() else None
        payload, attempts = None, []
        for url in urls:
            data, record = attempt(url, name)
            attempts.append(record)
            if data is not None:
                payload = data
                break
        entry = {'attempts': attempts, 'requested_urls': urls}
        if payload is not None:
            path.write_bytes(payload)
            entry.update(downloaded_this_run=True, cache_used=False,
                         sha256=sha256_bytes(payload), bytes=len(payload))
            entry['matches_previous_cache'] = (cached_sha == entry['sha256']
                                               if cached_sha else None)
        elif cached_sha is not None:
            entry.update(downloaded_this_run=False, cache_used=True,
                         sha256=cached_sha, bytes=path.stat().st_size,
                         note='All URLs failed this run; an earlier cache was reused.')
        else:
            entry.update(downloaded_this_run=False, cache_used=False,
                         sha256=None, bytes=0, note='Not obtained.')
        if path.exists() and path.read_bytes().startswith(b'%PDF'):
            entry['pages'] = pdf_pages(path)
        report['files'][name] = entry

    supp = report['files']['figshare_supplement_file52761698.pdf']
    report['exact_supplement_obtained'] = bool(supp.get('sha256'))
    report['exact_supplement_downloaded_this_run'] = bool(supp.get('downloaded_this_run'))
    (args.output / 'retrieval_report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['exact_supplement_obtained'] else 2)


if __name__ == '__main__':
    main()

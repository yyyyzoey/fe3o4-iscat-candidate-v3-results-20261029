#!/usr/bin/env python3
"""Reassemble results_v4_full.zip from 16 MiB parts and verify every part/hash."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=here / "results_v4_full.zip")
    args = ap.parse_args()
    manifest = json.loads((here / "results_v4_full_manifest.json").read_text(encoding="utf-8"))
    rows = manifest["parts"]["files"]
    parts_dir = here / manifest["parts"]["directory"]
    actual = sorted(parts_dir.glob("results_v4_full.zip.part*"))
    if len(actual) != len(rows):
        raise SystemExit(f"part count mismatch: expected {len(rows)}, found {len(actual)}")
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    h = hashlib.sha256()
    with tmp.open("wb") as dst:
        for row in rows:
            p = parts_dir / row["name"]
            if p.stat().st_size != row["bytes"]:
                raise SystemExit(f"size mismatch: {p.name}")
            if sha256_file(p) != row["sha256"]:
                raise SystemExit(f"sha256 mismatch: {p.name}")
            with p.open("rb") as src:
                for chunk in iter(lambda: src.read(8 << 20), b""):
                    dst.write(chunk)
                    h.update(chunk)
    expected = manifest["full_zip"]["sha256"]
    if h.hexdigest() != expected:
        raise SystemExit(f"reassembled sha256 mismatch: {h.hexdigest()} != {expected}")
    tmp.replace(args.output)
    print(f"PASS reassembled={args.output} bytes={args.output.stat().st_size} sha256={expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

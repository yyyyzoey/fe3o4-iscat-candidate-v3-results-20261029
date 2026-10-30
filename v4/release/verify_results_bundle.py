#!/usr/bin/env python3
"""Independently validate a results_v4 ZIP against its embedded SHA256SUMS.txt.

The full ZIP additionally re-reads all three main HDF5 cubes. Requires h5py for that check.
"""
from __future__ import annotations
import argparse, hashlib, io, json, re, sys, zipfile
from pathlib import Path

TAGS = ("D030", "D100", "D200")


def sha_stream(f) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(8 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", nargs="?", type=Path, default=here / "results_v4_full.zip")
    args = ap.parse_args()
    failures = []
    with zipfile.ZipFile(args.zip) as z:
        bad = z.testzip()
        if bad:
            failures.append(f"CRC failure: {bad}")
        names = set(z.namelist())
        sums_name = "results_v4/SHA256SUMS.txt"
        if sums_name not in names:
            raise SystemExit(f"missing {sums_name}")
        expected = {}
        for line in z.read(sums_name).decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            expected["results_v4/" + rel] = digest
        missing = sorted(set(expected) - names)
        has_main_h5 = any(n.endswith("/cube.h5") for n in names)
        allowed_light_missing = set() if has_main_h5 else {n for n in expected if n.endswith(".h5")}
        unexpected_missing = sorted(set(missing) - allowed_light_missing)
        extra = sorted(names - set(expected) - {sums_name})
        if unexpected_missing:
            failures.append(f"missing entries: {unexpected_missing[:5]}")
        if extra:
            failures.append(f"unexpected entries: {extra[:5]}")
        for name, digest in expected.items():
            if name not in names:
                continue
            with z.open(name) as f:
                if sha_stream(f) != digest:
                    failures.append(f"sha256 mismatch: {name}")
        html_names = [n for n in names if n.endswith(".html")]
        for name in html_names:
            txt = z.read(name).decode("utf-8", "replace")
            markup = re.sub(r"<script\b[^>]*>.*?</script>", "", txt, flags=re.I | re.S)
            for ref in re.findall(r'(?:src|href)\s*=\s*"([^"]+)"', markup, re.I):
                if ref.startswith(("#", "mailto:", "javascript:", "data:")) or re.match(r"^(https?:)?//", ref, re.I):
                    continue
                target = (Path(name).parent / ref.split("#", 1)[0].split("?", 1)[0]).as_posix()
                if target not in names:
                    failures.append(f"HTML missing target: {name} -> {ref}")
        if has_main_h5:
            try:
                import h5py
            except Exception as e:
                failures.append(f"h5py unavailable: {e}")
            else:
                for tag in TAGS:
                    h5name = f"results_v4/data/{tag}nm/cube.h5"
                    raw = z.read(h5name)
                    with h5py.File(io.BytesIO(raw), "r") as f:
                        shape = tuple(f["signals/I_cross"].shape)
                        layers = int(f["coords/zeta_nm"].shape[0])
                        done = int(f.attrs.get("completed_slices", -1))
                        if shape != (171, 241, 241) or layers != 171 or done != 171:
                            failures.append(f"{tag}: shape/layers mismatch {shape}/{layers}/{done}")
    report = {"zip": args.zip.name, "bytes": args.zip.stat().st_size,
              "entries": len(names), "hdf5_present": has_main_h5,
              "expected_light_omissions": sorted(allowed_light_missing),
              "failures": failures, "pass": not failures}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

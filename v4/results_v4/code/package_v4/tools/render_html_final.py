#!/usr/bin/env python3
"""Render the delivered HTML pages in a real headless browser with DNS blocked.

Evidence that the pages are self-contained and actually paint, not merely that
the markup parses. Path-parameterised. Writes validation/html_render_audit_final.json
plus one PNG per page under validation/html_render/.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

EDGE_CANDIDATES = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                   Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]
PAGES = [
    ("D030", "views3d/D030_signed_interference_3d.html", "volume"),
    ("D100", "views3d/D100_signed_interference_3d.html", "volume"),
    ("D200", "views3d/D200_signed_interference_3d.html", "volume"),
    ("INDEX", "views3d/index.html", "page"),
    ("START_HERE", "START_HERE.html", "page"),
    ("PREVIEWS", "previews/index.html", "page"),
    ("F3", "figures/F3_sections/index.html", "page"),
    ("F5", "figures/F5_decomposition/index.html", "page"),
    ("F6", "figures/F6_3d_static/index.html", "page"),
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    RES = a.results.resolve()
    edge = next((p for p in EDGE_CANDIDATES if p.is_file()), None)
    if edge is None:
        raise SystemExit("Microsoft Edge not found")
    out = RES / "validation" / "html_render"
    out.mkdir(parents=True, exist_ok=True)
    rows, failures = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp) / "profile"
        for tag, relpage, kind in PAGES:
            src = RES / relpage
            shot = out / f"{tag}_offline_render.png"
            cmd = [str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                   "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                   f"--user-data-dir={profile}", "--host-resolver-rules=MAP * ~NOTFOUND",
                   "--window-size=1400,900", "--virtual-time-budget=25000",
                   f"--screenshot={shot}", src.resolve().as_uri()]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            row = {"html": relpage, "html_bytes": src.stat().st_size,
                   "render_png": shot.relative_to(RES).as_posix(),
                   "browser": f"Microsoft Edge headless ({edge.name})",
                   "dns": "blocked via --host-resolver-rules=MAP * ~NOTFOUND",
                   "exit_code": r.returncode, "kind": kind}
            if not shot.is_file():
                row.update({"pass": False, "reason": "browser produced no screenshot",
                            "stderr_tail": r.stderr.strip()[-300:]})
                failures.append(tag)
                rows[tag] = row
                continue
            rgb = Image.open(shot).convert("RGB")
            arr = np.asarray(rgb)
            x = arr.astype(np.float64)
            nonwhite = float((arr.min(axis=2) < 245).mean())
            row.update({"png_bytes": shot.stat().st_size, "sha256": sha(shot),
                        "png_shape": list(arr.shape),
                        "nonwhite_fraction": round(nonwhite, 5),
                        "pixel_std": round(float(np.asarray(rgb.convert("L"), dtype=np.float64).std()), 3),
                        "unique_colors": int(np.unique(((arr[..., 0].astype(np.uint32) << 16)
                                                        | (arr[..., 1].astype(np.uint32) << 8)
                                                        | arr[..., 2].astype(np.uint32))).size)})
            if kind == "volume":
                row["pass"] = bool(row["png_bytes"] > 20_000 and nonwhite > 0.01
                                   and row["unique_colors"] > 500)
            else:
                row["pass"] = bool(row["png_bytes"] > 10_000 and nonwhite > 0.005
                                   and row["unique_colors"] > 50)
            if not row["pass"]:
                failures.append(tag)
            rows[tag] = row
    rep = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "method": ("headless Edge render of each saved page with DNS resolution disabled; "
                      "3D volume pages must paint >1% non-background pixels and >500 distinct "
                      "colours; static pages must paint >0.5% and >50 colours"),
           "cases": rows, "failures": failures, "pass": not failures}
    (RES / "validation" / "html_render_audit_final.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: v[kk] for kk in ("pass", "png_bytes", "nonwhite_fraction", "unique_colors")}
                      for k, v in rows.items()}, indent=2))
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

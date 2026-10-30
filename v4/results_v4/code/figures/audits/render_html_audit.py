#!/usr/bin/env python3
"""Render each delivered Plotly HTML in a real (headless) browser with DNS blocked.

Evidence that the pages are self-contained and actually draw the 3D volume, not merely
that the XML/HTML parses. Writes validation/html_render_audit.json plus one PNG per case.
"""
from __future__ import annotations
import json, subprocess, tempfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image

RES = Path(__file__).resolve().parents[3]
ROOT = RES.parent
OUT = RES / "validation" / "html_render"
OUT.mkdir(parents=True, exist_ok=True)
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

rows, failures = {}, []
with tempfile.TemporaryDirectory() as tmp:
    profile = Path(tmp) / "profile"
    for tag in ("D030", "D100", "D200"):
        src = RES / "views3d" / f"{tag}_signed_interference_3d.html"
        shot = OUT / f"{tag}_offline_render.png"
        uri = src.resolve().as_uri()
        cmd = [str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               f"--user-data-dir={profile}", "--host-resolver-rules=MAP * ~NOTFOUND",
               "--window-size=1400,900", "--virtual-time-budget=25000",
               f"--screenshot={shot}", uri]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        row = {"html": src.relative_to(RES).as_posix(), "html_bytes": src.stat().st_size,
               "render_png": shot.relative_to(RES).as_posix(),
               "browser": "Microsoft Edge headless", "dns": "blocked via --host-resolver-rules",
               "exit_code": r.returncode}
        if not shot.is_file():
            row["pass"] = False; row["reason"] = "browser produced no screenshot"
            failures.append(tag); rows[tag] = row; continue
        a = np.asarray(Image.open(shot).convert("RGB"))
        # the page background is white; count how much of the canvas is actually painted
        nonwhite = float((a.min(axis=2) < 245).mean())
        row.update({"png_bytes": shot.stat().st_size, "sha256": sha(shot),
                    "png_shape": list(a.shape),
                    "nonwhite_fraction": round(nonwhite, 5),
                    "unique_colors": int(len(np.unique(a.reshape(-1, 3), axis=0)))})
        # a real 3D volume occupies a visible share of the canvas with many distinct colors
        row["pass"] = bool(row["png_bytes"] > 20_000 and nonwhite > 0.01 and row["unique_colors"] > 500)
        if not row["pass"]:
            failures.append(tag)
        rows[tag] = row

rep = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
       "method": "headless Edge render of each saved HTML with DNS resolution disabled; "
                 "pass requires a painted canvas with >1% non-background pixels and >500 distinct colours",
       "cases": rows, "failures": failures, "pass": not failures}
(RES / "validation" / "html_render_audit.json").write_text(
    json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: {kk: v[kk] for kk in ("pass", "png_bytes", "nonwhite_fraction", "unique_colors")} for k, v in rows.items()}, indent=2))
raise SystemExit(0 if rep["pass"] else 1)

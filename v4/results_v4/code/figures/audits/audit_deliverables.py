#!/usr/bin/env python3
"""Formal, read-only audit of the assembled V4 deliverable tree.

Writes validation/*.json. Never modifies data, figures or code.
"""
from __future__ import annotations
import csv, hashlib, json, re, subprocess, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

RES = Path(__file__).resolve().parents[3]          # <deliverable>/results_v4
ROOT = RES.parent
VAL = RES / "validation"
VAL.mkdir(parents=True, exist_ok=True)
NOW = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")

def _jsonable(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)!r}")

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def rel(p: Path) -> str:
    return p.relative_to(RES).as_posix()

TEXT_EXT = {".md", ".txt", ".json", ".csv", ".html", ".py", ".ps1", ".sh",
            ".diff", ".xdmf", ".xml", ".log", ".yml", ".yaml", ".cff"}

# ---------------------------------------------------------------- inventory
files = sorted(p for p in RES.rglob("*") if p.is_file())
inv = {"total_files": len(files), "total_bytes": sum(p.stat().st_size for p in files), "by_suffix": {}}
for p in files:
    e = p.suffix.lower() or "(none)"
    d = inv["by_suffix"].setdefault(e, {"count": 0, "bytes": 0})
    d["count"] += 1
    d["bytes"] += p.stat().st_size

# --------------------------------------------------- nonempty / format check
fmt_fail = []
fmt_checked = 0
for p in files:
    if p.suffix.lower() not in {".png", ".svg", ".csv", ".html", ".json", ".md", ".txt", ".xdmf"}:
        continue
    fmt_checked += 1
    size = p.stat().st_size
    ext = p.suffix.lower()
    if size == 0:
        fmt_fail.append({"file": rel(p), "reason": "empty"}); continue
    if ext == ".png":
        head = p.open("rb").read(8)
        if head != b"\x89PNG\r\n\x1a\n":
            fmt_fail.append({"file": rel(p), "reason": "bad png signature"})
        elif size < 1000:
            fmt_fail.append({"file": rel(p), "reason": f"png too small ({size} bytes)"})
    elif ext == ".svg":
        head = p.open("rb").read(400).decode("utf-8", "replace")
        if "<svg" not in head:
            fmt_fail.append({"file": rel(p), "reason": "no <svg root in first 400 bytes"})
    elif ext == ".csv":
        with p.open("r", encoding="utf-8", newline="") as fh:
            rows = sum(1 for _ in fh)
        if rows < 2:
            fmt_fail.append({"file": rel(p), "reason": f"csv rows={rows}"})
    elif ext == ".json":
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            fmt_fail.append({"file": rel(p), "reason": f"json parse: {e}"})
    elif ext == ".html":
        if "<html" not in p.open("r", encoding="utf-8", errors="replace").read(4000).lower():
            fmt_fail.append({"file": rel(p), "reason": "no <html tag"})
    elif ext == ".xdmf":
        try:
            ET.fromstring(p.read_bytes())
        except Exception as e:
            fmt_fail.append({"file": rel(p), "reason": f"xdmf xml parse: {e}"})

# ------------------------------------------------------------- CSV structure
csv_checks = {}
for name in ("axis_D030.csv", "axis_D100.csv", "axis_D200.csv"):
    p = RES / "tables" / name
    with p.open("r", encoding="utf-8", newline="") as fh:
        rd = list(csv.reader(fh))
    header, body = rd[0], rd[1:]
    z = np.array([float(r[0]) for r in body])
    d = np.diff(z)
    csv_checks[name] = {
        "rows": len(body), "header": header,
        "zeta_first": float(z[0]), "zeta_last": float(z[-1]),
        "zeta_step_unique": sorted({round(float(x), 9) for x in d}),
        "all_rows_same_width": len({len(r) for r in rd}) == 1,
        "finite": bool(np.isfinite(np.array([[float(x) for x in r] for r in body])).all()),
        "pass": bool(len(body) == 171 and abs(z[0] + 170) < 1e-9 and abs(z[-1] - 170) < 1e-9
                     and len({round(float(x), 9) for x in d}) == 1
                     and abs(float(d[0]) - 2.0) < 1e-9 and len({len(r) for r in rd}) == 1),
    }
p = RES / "tables" / "metrics.csv"
with p.open("r", encoding="utf-8", newline="") as fh:
    rd = list(csv.reader(fh))
csv_checks["metrics.csv"] = {"rows": len(rd) - 1, "header": rd[0],
                             "diameters": [float(r[0]) for r in rd[1:]],
                             "pass": len(rd) - 1 == 3}
p = RES / "tables" / "axis_profiles_long_range.csv"
with p.open("r", encoding="utf-8", newline="") as fh:
    n = sum(1 for _ in fh) - 1
csv_checks["axis_profiles_long_range.csv"] = {"rows": n, "pass": n == 513}
for sub, expect in (("target_long", 601), ("paper_control_long", 601)):
    for f in sorted((RES / "diagnostics" / sub).glob("*_axis.csv")):
        with f.open("r", encoding="utf-8", newline="") as fh:
            m = sum(1 for _ in fh) - 1
        csv_checks[f"diagnostics/{sub}/{f.name}"] = {"rows": m, "pass": m == expect}

# --------------------------------------------------------- required figures
req = {}
for tag in ("D030", "D100", "D200"):
    zs = ["-0170.0", "-0128.0", "-0086.0", "-0042.0", "+0000.0",
          "+0042.0", "+0086.0", "+0128.0", "+0170.0"]
    need = []
    for z in zs:
        need += [f"figures/F2_xy_slices/common/{tag}/common_xy_{z}.png",
                 f"figures/F2_xy_slices/common/{tag}/common_xy_{z}.svg",
                 f"figures/F2_xy_slices/shape/{tag}/shape_xy_{z}.png",
                 f"figures/F2_xy_slices/shape/{tag}/shape_xy_{z}.svg"]
    for view in ("common", "shape"):
        for sec in ("xz", "yz"):
            need += [f"figures/F3_sections/{tag}/{view}_{sec}.png",
                     f"figures/F3_sections/{tag}/{view}_{sec}.svg"]
    for comp in ("I_ref", "I_scat", "I_cross", "I_total"):
        need += [f"figures/F5_decomposition/{tag}/component_{comp}.png",
                 f"figures/F5_decomposition/{tag}/component_{comp}.svg"]
    need += [f"figures/F6_3d_static/{tag}_signed_interference_3d.png",
             f"views3d/{tag}_signed_interference_3d.html",
             f"views3d/{tag}_focus_stack.xdmf",
             f"figures/F2_xy_slices/montage/{tag}_shape_montage.png",
             f"figures/F2_xy_slices/montage/{tag}_common_full_montage.png",
             f"figures/F2_xy_slices/montage/{tag}_common_emphasized_montage.png"]
    missing = [n for n in need if not (RES / n).is_file()]
    tiny = [n for n in need if (RES / n).is_file() and (RES / n).stat().st_size < 1000]
    req[tag] = {"required": len(need), "missing": missing, "too_small": tiny,
                "pass": not missing and not tiny}
common_need = ["figures/F1_geometry_method/F1_geometry_method.png",
               "figures/F1_geometry_method/F1_geometry_method.svg",
               "figures/F7_long_range/F7_long_range_diagnostic.png",
               "figures/F7_long_range/F7_long_range_diagnostic.svg",
               "figures/F4_axial/030nm_axial_full_components.png",
               "figures/F4_axial/100nm_axial_full_components.png",
               "figures/F4_axial/200nm_axial_full_components.png",
               "tables/axis_D030.csv", "tables/axis_D100.csv", "tables/axis_D200.csv",
               "tables/metrics.csv"]
MIN_BYTES = {".csv": 200, ".md": 200, ".json": 50}
req["COMMON"] = {"required": len(common_need),
                 "missing": [n for n in common_need if not (RES / n).is_file()],
                 "too_small": [n for n in common_need if (RES / n).is_file()
                               and (RES / n).stat().st_size < MIN_BYTES.get(Path(n).suffix.lower(), 1000)],
                 "pass": all((RES / n).is_file()
                             and (RES / n).stat().st_size >= MIN_BYTES.get(Path(n).suffix.lower(), 1000)
                             for n in common_need)}

figure_checks = {
    "generated_utc": NOW(),
    "root": "results_v4",
    "file_inventory": inv,
    "nonempty_and_format": {"checked": fmt_checked, "failures": fmt_fail, "pass": not fmt_fail},
    "csv_checks": csv_checks,
    "csv_all_pass": all(v["pass"] for v in csv_checks.values()),
    "required_figures": req,
    "all_required_figures_present": all(v["pass"] for v in req.values()),
}
figure_checks["pass"] = bool(figure_checks["nonempty_and_format"]["pass"]
                             and figure_checks["csv_all_pass"]
                             and figure_checks["all_required_figures_present"])
(VAL / "figure_checks.json").write_text(json.dumps(figure_checks, indent=2, ensure_ascii=False), encoding="utf-8")

# ------------------------------------------------------------- HTML audit
TAG_RE = re.compile(r'(?:src|href|data)\s*=\s*"([^"]+)"', re.I)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
html_rows = []
bad_refs = []
for p in sorted(RES.rglob("*.html")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    markup = SCRIPT_RE.sub("", txt)
    refs = TAG_RE.findall(markup)
    local, external, missing = 0, 0, []
    for r in refs:
        if r.startswith(("#", "mailto:", "javascript:", "data:")):
            continue
        if re.match(r"^(https?:)?//", r, re.I):
            external += 1
            continue
        target = (p.parent / r.split("#")[0].split("?")[0]).resolve()
        local += 1
        if not target.is_file():
            missing.append(r)
    stripped = markup
    # A self-contained page must not *load* anything from the network. Vendor bundles
    # may still contain inert literal URLs (Plotly mapbox/topojson defaults), so the
    # load-path test looks at markup attributes, CSS imports and XHR/fetch targets,
    # and those literals are recorded separately as informational evidence.
    load_paths = []
    for m in re.finditer(r"<(script|link|img|iframe|source|video|audio)\b[^>]*?\b(src|href)\s*=\s*\"([^\"]+)\"", txt, re.I):
        v = m.group(3)
        if re.match(r"^(https?:)?//", v, re.I):
            load_paths.append({"where": f"<{m.group(1).lower()} {m.group(2).lower()}>", "url": v[:120]})
    for m in re.finditer(r"@import\s+url\(\s*['\"]?(https?:)?//", txt, re.I):
        load_paths.append({"where": "@import", "url": txt[m.start():m.start() + 120]})
    for m in re.finditer(r"(?:fetch|XMLHttpRequest|importScripts)\s*\(\s*['\"]https?://", txt, re.I):
        load_paths.append({"where": "js-fetch", "url": txt[m.start():m.start() + 120]})
    vendor_literals = {}
    for t in ("cdn.plot.ly", "cdnjs.cloudflare.com", "unpkg.com", "cdn.jsdelivr.net"):
        c = txt.lower().count(t)
        if c:
            vendor_literals[t] = c
    inline_plotly = ("Plotly.newPlot" in txt) or ("plotly" in txt.lower() and len(txt) > 1_000_000)
    row = {"file": rel(p), "bytes": p.stat().st_size, "script_src": bool(re.search(r"<script[^>]+src=", txt, re.I)),
           "external_refs": external, "local_refs": local, "missing": missing,
           "network_load_paths": load_paths, "vendor_literal_urls_inert": vendor_literals,
           "plotly_newplot": inline_plotly,
           "authored_text_chars": len(stripped), "pass": not missing and external == 0 and not load_paths}
    html_rows.append(row)
    if not row["pass"]:
        bad_refs.append(row)
html_audit = {"generated_utc": NOW(), "html_files": len(html_rows), "rows": html_rows,
              "all_local_refs_resolve": all(not r["missing"] for r in html_rows),
              "no_external_or_cdn_dependency": all(r["external_refs"] == 0 and not r["network_load_paths"]
                                                  for r in html_rows),
              "failing": bad_refs, "pass": not bad_refs}
(VAL / "html_audit.json").write_text(json.dumps(html_audit, indent=2, ensure_ascii=False), encoding="utf-8")

# ------------------------------------------------------------- XDMF re-read
import h5py
xd = {"generated_utc": NOW(), "files": {}, "failures": []}
for tag in ("D030", "D100", "D200"):
    p = RES / "views3d" / f"{tag}_focus_stack.xdmf"
    root = ET.fromstring(p.read_bytes())
    items = root.findall(".//DataItem")
    attrs = [a.get("Name") for a in root.findall(".//Attribute")]
    entry = {"xdmf": rel(p), "items": len(items), "attributes": attrs, "datasets": [], "pass": True}
    for it in items:
        spec = it.text.strip()
        fname, dspath = spec.split(":", 1)
        dims = [int(x) for x in it.get("Dimensions").split()]
        hp = (p.parent / fname).resolve()
        if not hp.is_file():
            entry["pass"] = False
            xd["failures"].append(f"{tag}: missing hdf5 {fname}")
            continue
        with h5py.File(hp, "r") as f:
            if dspath not in f:
                entry["pass"] = False
                xd["failures"].append(f"{tag}: missing dataset {dspath}")
                continue
            ds = f[dspath]
            ok = list(ds.shape) == dims
            entry["datasets"].append({"path": dspath, "shape": list(ds.shape),
                                      "expected": dims, "dtype": str(ds.dtype), "pass": ok})
            if not ok:
                entry["pass"] = False
                xd["failures"].append(f"{tag}: shape mismatch {dspath} {ds.shape} != {dims}")
    with h5py.File((RES / "data" / f"{tag}nm" / "cube.h5"), "r") as f:
        z = f["coords/zeta_nm"][:]; x = f["coords/x_object_nm"][:]
    entry["zeta_first_last"] = [float(z[0]), float(z[-1])]
    entry["xy_first_last"] = [float(x[0]), float(x[-1])]
    if not (abs(z[0] + 170) < 1e-9 and abs(z[-1] - 170) < 1e-9 and len(z) == 171):
        entry["pass"] = False; xd["failures"].append(f"{tag}: zeta axis wrong")
    if not (abs(x[0] + 1200) < 1e-9 and abs(x[-1] - 1200) < 1e-9 and len(x) == 241):
        entry["pass"] = False; xd["failures"].append(f"{tag}: x axis wrong")
    xd["files"][tag] = entry
xd["pass"] = all(v["pass"] for v in xd["files"].values()) and not xd["failures"]
(VAL / "xdmf_audit.json").write_text(json.dumps(xd, indent=2, ensure_ascii=False), encoding="utf-8")

# ----------------------------------------------------------------- privacy
patterns = {
    "windows_user_path": r"[A-Za-z]:\\+Users\\+[^\\\s\"']+",
    "posix_home_path": r"(?<![A-Za-z])/(?:home|Users)/[^/\s\"']+",
    "file_url": r"file:" + r"//",
    "github_token": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}",
    "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "bearer_token": r"Bearer\s+[A-Za-z0-9._\-]{20,}",
    "basic_auth": r"Authorization:\s*(?:Basic|Bearer|token)\s+\S{8,}",
}
hits = []
scanned = 0
for p in files:
    if p.suffix.lower() not in TEXT_EXT:
        continue
    if p == VAL / "privacy_scan.json":
        continue  # generated report: it quotes sanitised match prefixes by construction
    if p.suffix.lower() == ".html":
        txt = SCRIPT_RE.sub("", p.read_text(encoding="utf-8", errors="replace"))
    else:
        txt = p.read_text(encoding="utf-8", errors="replace")
    scanned += 1
    for name, pat in patterns.items():
        for m in re.finditer(pat, txt, re.I):
            line = txt.count("\n", 0, m.start()) + 1
            hits.append({"file": rel(p), "line": line, "pattern": name,
                         "match": m.group(0)[:12] + ("..." if len(m.group(0)) > 12 else "")})
privacy = {"generated_utc": NOW(), "files_scanned": scanned, "patterns": list(patterns),
           "hits": hits, "note": "HTML vendor <script> bodies are stripped before scanning.",
           "pass": not hits}
(VAL / "privacy_scan.json").write_text(json.dumps(privacy, indent=2, ensure_ascii=False), encoding="utf-8")

# ------------------------------------------------------------- HDF5 re-read
h5rep = {"generated_utc": NOW(), "cases": {}, "failures": []}
for tag in ("D030", "D100", "D200"):
    p = RES / "data" / f"{tag}nm" / "cube.h5"
    e = {"file": rel(p), "bytes": p.stat().st_size, "sha256": sha(p)}
    with h5py.File(p, "r") as f:
        e["shape"] = list(f["signals/I_cross"].shape)
        e["datasets"] = {k: {"shape": list(f["signals"][k].shape), "dtype": str(f["signals"][k].dtype)}
                         for k in sorted(f["signals"].keys())}
        e["attrs"] = {k: f.attrs[k] for k in sorted(f.attrs)}
        e["completed_slices"] = int(f.attrs.get("completed_slices", -1))
        e["layers"] = int(f["coords/zeta_nm"].shape[0])
        bad = []
        for iz in (0, 42, 84, 85, 128, 170):
            for k in ("I_ref", "I_scat", "I_total"):
                a = f[f"signals/{k}"][iz]
                if not np.isfinite(a).all() or (a < 0).any():
                    bad.append(f"{k}[{iz}] finite/nonneg")
            if not np.isfinite(f["signals/I_cross"][iz]).all():
                bad.append(f"I_cross[{iz}] finite")
            if not np.isfinite(f["signals/contrast_fixed_reference"][iz]).all():
                bad.append(f"S_fixed[{iz}] finite")
        e["sampled_layer_failures"] = bad
        z = f["coords/zeta_nm"][:]; x = f["coords/x_object_nm"][:]
        e["axes"] = {"zeta": [float(z[0]), float(z[-1]), len(z)],
                     "x": [float(x[0]), float(x[-1]), len(x)]}
    e["pass"] = (e["shape"] == [171, 241, 241] and e["completed_slices"] == 171
                 and e["layers"] == 171 and not e["sampled_layer_failures"])
    if not e["pass"]:
        h5rep["failures"].append(tag)
    h5rep["cases"][tag] = e
h5rep["pass"] = not h5rep["failures"]
(VAL / "data_hdf5_check.json").write_text(json.dumps(h5rep, indent=2, ensure_ascii=False, default=_jsonable), encoding="utf-8")

summary = {"figure_checks": figure_checks["pass"], "html": html_audit["pass"],
           "xdmf": xd["pass"], "privacy": privacy["pass"], "hdf5": h5rep["pass"]}
print(json.dumps(summary, indent=2))
sys.exit(0 if all(summary.values()) else 1)

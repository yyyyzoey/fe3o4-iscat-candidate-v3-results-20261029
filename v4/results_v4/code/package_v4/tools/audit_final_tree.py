#!/usr/bin/env python3
"""Final, read-only audit of the assembled V4.1 candidate results tree.

Path-parameterised (--results) so the same tool can audit any assembled
results_v4 tree. Writes validation/*_final.json. Never modifies data, code
or figures; all checks are independent re-reads of the saved artifacts.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

TEXT_EXT = {".md", ".txt", ".json", ".csv", ".html", ".py", ".ps1", ".sh", ".diff",
            ".xdmf", ".xml", ".log", ".yml", ".yaml", ".cff", ".svg"}
SLICES = ["-0170.0", "-0128.0", "-0086.0", "-0042.0", "+0000.0",
          "+0042.0", "+0086.0", "+0128.0", "+0170.0"]
TAGS = ["D030", "D100", "D200"]


def _js(o):
    if isinstance(o, (np.bool_, np.integer, np.floating)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(repr(o))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=None)
    a = ap.parse_args()
    RES = a.results.resolve()
    VAL = (a.out_dir or RES / "validation").resolve()
    VAL.mkdir(parents=True, exist_ok=True)
    now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    rel = lambda p: p.relative_to(RES).as_posix()
    summary = {}

    files = sorted(p for p in RES.rglob("*") if p.is_file())

    # ------------------------------------------------------------- inventory
    inv = {"total_files": len(files),
           "total_bytes": sum(p.stat().st_size for p in files), "by_suffix": {}}
    for p in files:
        e = p.suffix.lower() or "(none)"
        d = inv["by_suffix"].setdefault(e, {"count": 0, "bytes": 0})
        d["count"] += 1
        d["bytes"] += p.stat().st_size

    # ---------------------------------------------- format + PNG blank checks
    fmt_fail, png_rows = [], []
    checked = 0
    for p in files:
        ext = p.suffix.lower()
        if ext not in {".png", ".svg", ".csv", ".html", ".json", ".md", ".txt", ".xdmf"}:
            continue
        checked += 1
        size = p.stat().st_size
        if size == 0:
            fmt_fail.append({"file": rel(p), "reason": "empty"})
            continue
        if ext == ".png":
            try:
                im = Image.open(p)
                im.load()
                rgb = im.convert("RGB")
                arr = np.asarray(rgb)
                gray = np.asarray(rgb.convert("L"), dtype=np.float64)
                packed = ((arr[..., 0].astype(np.uint32) << 16)
                          | (arr[..., 1].astype(np.uint32) << 8)
                          | arr[..., 2].astype(np.uint32)).ravel()
                ncol = int(np.unique(packed).size)
                row = {"file": rel(p), "bytes": size, "shape": list(arr.shape),
                       "pixel_std": round(float(gray.std()), 3),
                       "unique_colors": ncol, "sha256": sha(p)}
                row["pass"] = bool(size >= 1000 and arr.shape[0] >= 100 and arr.shape[1] >= 100
                                   and row["pixel_std"] > 1.0 and ncol >= 8)
                if not row["pass"]:
                    fmt_fail.append({"file": rel(p), "reason": "blank/near-blank or too small"})
                png_rows.append(row)
            except Exception as exc:
                fmt_fail.append({"file": rel(p), "reason": f"png decode: {exc}"})
        elif ext == ".svg":
            try:
                root = ET.fromstring(p.read_bytes())
                if not str(root.tag).endswith("svg"):
                    fmt_fail.append({"file": rel(p), "reason": "svg root is not <svg>"})
            except Exception as exc:
                fmt_fail.append({"file": rel(p), "reason": f"svg xml parse: {exc}"})
        elif ext == ".csv":
            with p.open("r", encoding="utf-8", newline="") as fh:
                n = sum(1 for _ in fh)
            if n < 2:
                fmt_fail.append({"file": rel(p), "reason": f"csv rows={n}"})
        elif ext == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as exc:
                fmt_fail.append({"file": rel(p), "reason": f"json parse: {exc}"})
        elif ext == ".html":
            head = p.open("r", encoding="utf-8", errors="replace").read(4000).lower()
            if "<html" not in head:
                fmt_fail.append({"file": rel(p), "reason": "no <html tag"})
        elif ext == ".xdmf":
            try:
                ET.fromstring(p.read_bytes())
            except Exception as exc:
                fmt_fail.append({"file": rel(p), "reason": f"xdmf xml parse: {exc}"})

    # ---------------------------------------------------------- CSV structure
    csv_checks = {}

    def axis_csv(p: Path, rows: int, zmin: float, zmax: float, step: float) -> dict:
        with p.open("r", encoding="utf-8", newline="") as fh:
            rd = list(csv.reader(fh))
        header, body = rd[0], rd[1:]
        z = np.array([float(r[0]) for r in body])
        vals = np.array([[float(x) for x in r[1:]] for r in body])
        d = np.diff(z)
        return {"rows": len(body), "header": header, "zeta_first": float(z[0]),
                "zeta_last": float(z[-1]), "zeta_step": float(d[0]) if len(d) else None,
                "all_rows_same_width": len({len(r) for r in rd}) == 1,
                "finite": bool(np.isfinite(vals).all()),
                "pass": bool(len(body) == rows and abs(z[0] - zmin) < 1e-6
                             and abs(z[-1] - zmax) < 1e-6
                             and len({round(float(x), 6) for x in d}) == 1
                             and abs(float(d[0]) - step) < 1e-6
                             and len({len(r) for r in rd}) == 1
                             and np.isfinite(vals).all())}

    for tag in TAGS:
        p = RES / "tables" / f"axis_{tag}.csv"
        csv_checks[f"tables/axis_{tag}.csv"] = axis_csv(p, 171, -170.0, 170.0, 2.0)
    p = RES / "tables" / "axis_profiles_long_range.csv"
    with p.open("r", encoding="utf-8", newline="") as fh:
        rd = list(csv.reader(fh))
    groups = {}
    for row in rd[1:]:
        key = f"{row[0]}/{row[1]}"
        groups[key] = groups.get(key, 0) + 1
    csv_checks["tables/axis_profiles_long_range.csv"] = {
        "rows": len(rd) - 1, "header": rd[0], "group_row_counts": groups,
        "pass": len(rd) - 1 == 2404 and len({len(r) for r in rd}) == 1
                and len(groups) == 4 and set(groups.values()) == {601}}
    p = RES / "tables" / "metrics.csv"
    with p.open("r", encoding="utf-8", newline="") as fh:
        rd = list(csv.reader(fh))
    csv_checks["tables/metrics.csv"] = {
        "rows": len(rd) - 1, "header": rd[0],
        "diameters": [float(r[0]) for r in rd[1:]],
        "shapes": [r[1] for r in rd[1:]],
        "pass": len(rd) - 1 == 3 and [float(r[0]) for r in rd[1:]] == [30.0, 100.0, 200.0]
                and all(r[1] == "171x241x241" for r in rd[1:])}
    for sub in ("target_Fe3O4_NA145", "paper_control_NA135"):
        for f in sorted((RES / "diagnostics" / sub).glob("*_axis.csv")):
            csv_checks[f"diagnostics/{sub}/{f.name}"] = axis_csv(f, 601, -3000.0, 3000.0, 10.0)
    for tag in TAGS:
        p = RES / "views3d" / tag / "axis_values.csv"
        with p.open("r", encoding="utf-8", newline="") as fh:
            rd = list(csv.reader(fh))
        z = np.array([float(r[0]) for r in rd[1:]])
        csv_checks[f"views3d/{tag}/axis_values.csv"] = {
            "rows": len(rd) - 1, "header": rd[0],
            "pass": len(rd) - 1 == 171 and abs(z[0] + 170) < 1e-9 and abs(z[-1] - 170) < 1e-9}

    # ------------------------------------------------------- required outputs
    req = {}
    for tag in TAGS:
        need = []
        for v in ("shape", "common"):
            for z in SLICES:
                for ext in ("png", "svg"):
                    need.append(f"views3d/{tag}/{v}_xy_{z}.{ext}")
            for sec in ("xz", "yz"):
                for ext in ("png", "svg"):
                    need.append(f"views3d/{tag}/{v}_{sec}.{ext}")
        for comp in ("I_ref", "I_scat", "I_cross", "I_total"):
            for ext in ("png", "svg"):
                need.append(f"views3d/{tag}/component_{comp}.{ext}")
        need += [f"views3d/{tag}/axis_values.csv",
                 f"views3d/{tag}/signed_interference_3d.png",
                 f"views3d/{tag}/signed_interference_3d.html",
                 f"views3d/D030_focus_stack.xdmf" if tag == "D030" else f"views3d/{tag}_focus_stack.xdmf",
                 f"views3d/{tag}_signed_interference_3d.png",
                 f"views3d/{tag}_signed_interference_3d.html"]
        for kind in ("shape", "common_full", "common_emphasized"):
            for ext in ("png", "svg"):
                need.append(f"figures/F2_xy_slices/montage/{tag}_{kind}_montage.{ext}")
        for kind in ("shape", "common"):
            for ext in ("png", "svg"):
                need.append(f"figures/F2_xy_slices/zoom/{tag}/zoom_{kind}_montage.{ext}")
        for z in ["-170.0", "-128.0", "-86.0", "-42.0", "+0.0", "+42.0", "+86.0", "+128.0", "+170.0"]:
            for v in ("shape", "common"):
                need.append(f"figures/F2_xy_slices/zoom/{tag}/zoom_{v}_xy_{z}.png")
        need += [f"data/{tag}nm/cube.h5"]
        missing = [n for n in need if not (RES / n).is_file()]
        tiny = [n for n in need if (RES / n).is_file() and (RES / n).stat().st_size < 1000]
        req[tag] = {"required": len(need), "missing": missing, "too_small": tiny,
                    "pass": not missing and not tiny}
    common_need = [
        "figures/F1_geometry_method/F1_geometry_method.png",
        "figures/F1_geometry_method/F1_geometry_method.svg",
        "figures/F7_long_range/F7_long_range_diagnostic.png",
        "figures/F7_long_range/F7_long_range_diagnostic.svg",
        "figures/F4_axial/030nm_axial_full_components.png",
        "figures/F4_axial/030nm_axial_full_components.svg",
        "figures/F4_axial/100nm_axial_full_components.png",
        "figures/F4_axial/100nm_axial_full_components.svg",
        "figures/F4_axial/200nm_axial_full_components.png",
        "figures/F4_axial/200nm_axial_full_components.svg",
        "tables/axis_D030.csv", "tables/axis_D100.csv", "tables/axis_D200.csv",
        "tables/metrics.csv", "tables/axis_profiles_long_range.csv",
        "views3d/index.html", "views3d/export_audit.json",
        "validation/jones_chain_numbers.json", "validation/model_conventions.md",
        "validation/numerics.json",
        "provenance/config.json", "provenance/source_hashes.json",
        # V4.1 delivery layer: entry points, reports, previews, execution log
        "status.json",
        "README_打开这里.md",
        "reports/00_汇报摘要_一页.md",
        "reports/01_方法与参数说明.md",
        "reports/02_验收矩阵.csv",
        "reports/03_测试与数值验证.md",
        "reports/04_执行日志索引.md",
        "reports/05_复现说明.md",
        "reports/06_修复与差异摘要.md",
        "reports/physical_limitations.md",
        "logs/README.md",
        "logs/execution_log.md",
        "previews/index.html",
        "previews/preview_manifest.json",
        "previews/preview_2d_three_diameters.png",
        "previews/preview_3d_three_diameters.png",
        "previews/preview_2d_D030.png",
        "previews/preview_2d_D100.png",
        "previews/preview_2d_D200.png",
        "previews/preview_3d_D030.png",
        "previews/preview_3d_D100.png",
        "previews/preview_3d_D200.png",
    ]
    MIN = {".csv": 200, ".md": 200, ".json": 50, ".h5": 1000}
    req["COMMON"] = {"required": len(common_need),
                     "missing": [n for n in common_need if not (RES / n).is_file()],
                     "too_small": [n for n in common_need if (RES / n).is_file()
                                   and (RES / n).stat().st_size < MIN.get(Path(n).suffix.lower(), 1000)]}
    req["COMMON"]["pass"] = not req["COMMON"]["missing"] and not req["COMMON"]["too_small"]

    figure_checks = {"generated_utc": now(), "root": RES.name, "file_inventory": inv,
                     "nonempty_and_format": {"checked": checked, "failures": fmt_fail,
                                             "pass": not fmt_fail},
                     "png_decoded_and_nonblank": {"count": len(png_rows), "rows": png_rows},
                     "csv_checks": csv_checks,
                     "csv_all_pass": all(v["pass"] for v in csv_checks.values()),
                     "required_outputs": req,
                     "all_required_outputs_present": all(v["pass"] for v in req.values())}
    figure_checks["pass"] = bool(figure_checks["nonempty_and_format"]["pass"]
                                 and figure_checks["csv_all_pass"]
                                 and figure_checks["all_required_outputs_present"])
    (VAL / "figure_checks_final.json").write_text(
        json.dumps(figure_checks, indent=2, ensure_ascii=False, default=_js), encoding="utf-8")
    summary["figure_checks"] = figure_checks["pass"]

    # -------------------------------------------------------------- HTML audit
    SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
    TAG_RE = re.compile(r'(?:src|href|data)\s*=\s*"([^"]+)"', re.I)
    rows, bad = [], []
    for p in sorted(RES.rglob("*.html")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        markup = SCRIPT_RE.sub("", txt)
        local, external, missing = 0, 0, []
        for r in TAG_RE.findall(markup):
            if r.startswith(("#", "mailto:", "javascript:", "data:")):
                continue
            if re.match(r"^(https?:)?//", r, re.I):
                external += 1
                continue
            local += 1
            if not (p.parent / r.split("#")[0].split("?")[0]).resolve().is_file():
                missing.append(r)
        load_paths = []
        for m in re.finditer(
                r"<(script|link|img|iframe|source|video|audio)\b[^>]*?\b(src|href)\s*=\s*\"([^\"]+)\"",
                txt, re.I):
            if re.match(r"^(https?:)?//", m.group(3), re.I):
                load_paths.append({"where": f"<{m.group(1).lower()} {m.group(2).lower()}>",
                                   "url": m.group(3)[:120]})
        for m in re.finditer(r"@import\s+url\(\s*['\"]?(https?:)?//", txt, re.I):
            load_paths.append({"where": "@import", "url": txt[m.start():m.start() + 80]})
        for m in re.finditer(r"(?:fetch|XMLHttpRequest|importScripts)\s*\(\s*['\"]https?://", txt, re.I):
            load_paths.append({"where": "js-fetch", "url": txt[m.start():m.start() + 80]})
        vendor = {}
        for t in ("cdn.plot.ly", "cdnjs.cloudflare.com", "unpkg.com", "cdn.jsdelivr.net"):
            c = txt.lower().count(t)
            if c:
                vendor[t] = c
        row = {"file": rel(p), "bytes": p.stat().st_size,
               "script_src_attribute": bool(re.search(r"<script[^>]+src=", txt, re.I)),
               "external_refs": external, "local_refs": local, "missing_local": missing,
               "network_load_paths": load_paths, "vendor_literal_urls_inert": vendor,
               "inline_plotly_bundle": ("Plotly.newPlot" in txt),
               "authored_text_chars": len(markup),
               "pass": not missing and external == 0 and not load_paths}
        rows.append(row)
        if not row["pass"]:
            bad.append(row["file"])
    html_audit = {"generated_utc": now(), "html_files": len(rows), "rows": rows,
                  "failing": bad, "pass": not bad and len(rows) >= 4}
    (VAL / "html_audit_final.json").write_text(
        json.dumps(html_audit, indent=2, ensure_ascii=False, default=_js), encoding="utf-8")
    summary["html_audit"] = html_audit["pass"]

    # ----------------------------------------------------------- privacy scan
    patterns = {
        "windows_user_path": r"[A-Za-z]:\\+Users\\+[^\\\s\"'<>]+",
        "posix_home_path": r"(?<![A-Za-z])/(?:home|Users)/[^/\s\"'<>]+",
        "file_url": r"file:" + r"//",
        "github_token": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}",
        "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
        "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "bearer_token": r"Bearer\s+[A-Za-z0-9._\-]{20,}",
        "basic_auth": r"Authorization:\s*(?:Basic|Bearer|token)\s+\S{8,}",
        "email_address": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    }
    allowed_email_domains = ("doi.org", "arxiv.org", "figshare.com", "github.com")
    hits, scanned = [], 0
    targets = [p for p in files if p.suffix.lower() in TEXT_EXT]
    targets += [p for p in files if p.suffix.lower() == ".h5"]
    for p in targets:
        if p.name.startswith("privacy_scan"):
            continue
        if p.suffix.lower() == ".h5":
            import h5py
            chunks = []
            with h5py.File(p, "r") as f:
                def walk(g):
                    for k, v in g.attrs.items():
                        chunks.append(f"{k}={v}")
                    for name in g:
                        obj = g[name]
                        if isinstance(obj, h5py.Group):
                            walk(obj)
                walk(f)
            txt = "\n".join(chunks)
        elif p.suffix.lower() == ".html":
            txt = SCRIPT_RE.sub("", p.read_text(encoding="utf-8", errors="replace"))
        else:
            txt = p.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        for name, pat in patterns.items():
            for m in re.finditer(pat, txt, re.I):
                hit = {"file": rel(p), "line": txt.count("\n", 0, m.start()) + 1,
                       "pattern": name, "match": m.group(0)[:16]}
                hits.append(hit)
    privacy = {"generated_utc": now(), "files_scanned": scanned,
               "patterns": list(patterns), "hits": hits,
               "note": "HTML vendor <script> bodies stripped; HDF5 scanned via all group/dataset attrs.",
               "pass": not hits}
    (VAL / "privacy_scan_final.json").write_text(
        json.dumps(privacy, indent=2, ensure_ascii=False, default=_js), encoding="utf-8")
    summary["privacy_scan"] = privacy["pass"]

    # ------------------------------------------------- HDF5 sampled re-read
    import h5py
    h5rep = {"generated_utc": now(), "cases": {}, "failures": []}
    for tag in TAGS:
        p = RES / "data" / f"{tag}nm" / "cube.h5"
        e = {"file": rel(p), "bytes": p.stat().st_size, "sha256": sha(p)}
        with h5py.File(p, "r") as f:
            e["shape"] = list(f["signals/I_cross"].shape)
            e["completed_slices"] = int(f.attrs.get("completed_slices", -1))
            e["layers"] = int(f["coords/zeta_nm"].shape[0])
            bad_layers = []
            for iz in (0, 42, 84, 85, 128, 170):
                for k in ("I_ref", "I_scat", "I_total"):
                    arr = f[f"signals/{k}"][iz]
                    if not np.isfinite(arr).all() or (arr < 0).any():
                        bad_layers.append(f"{k}[{iz}] finite/nonneg")
                if not np.isfinite(f["signals/I_cross"][iz]).all():
                    bad_layers.append(f"I_cross[{iz}]")
                if not np.isfinite(f["signals/contrast_fixed_reference"][iz]).all():
                    bad_layers.append(f"contrast_fixed_reference[{iz}]")
            z = f["coords/zeta_nm"][:]
            x = f["coords/x_object_nm"][:]
            e["axes"] = {"zeta": [float(z[0]), float(z[-1]), int(z.size)],
                         "x": [float(x[0]), float(x[-1]), int(x.size)]}
        e["sampled_layer_failures"] = bad_layers
        e["pass"] = bool(e["shape"] == [171, 241, 241] and e["completed_slices"] == 171
                         and e["layers"] == 171 and not bad_layers
                         and abs(e["axes"]["zeta"][0] + 170) < 1e-9
                         and abs(e["axes"]["zeta"][1] - 170) < 1e-9
                         and abs(e["axes"]["x"][0] + 1200) < 1e-9
                         and abs(e["axes"]["x"][1] - 1200) < 1e-9)
        if not e["pass"]:
            h5rep["failures"].append(tag)
        h5rep["cases"][tag] = e
    h5rep["pass"] = not h5rep["failures"]
    (VAL / "data_hdf5_check_final.json").write_text(
        json.dumps(h5rep, indent=2, ensure_ascii=False, default=_js), encoding="utf-8")
    summary["hdf5_sampled_reread"] = h5rep["pass"]

    # ------------------------------------------------- final inventory pass
    # Recomputed *after* every audit report above has been rewritten, so the
    # counts describe the tree as it will be sealed.  This report cannot hash
    # itself, so exactly one path is excluded and named explicitly.
    self_rel = rel(VAL / "figure_checks_final.json")
    files2 = sorted(p for p in RES.rglob("*") if p.is_file() and rel(p) != self_rel)
    inv2 = {"total_files": len(files2),
            "total_bytes": sum(p.stat().st_size for p in files2),
            "excludes": [self_rel],
            "snapshot": "recomputed after all other audit reports were rewritten",
            "by_suffix": {}}
    for p in files2:
        e = p.suffix.lower() or "(none)"
        d = inv2["by_suffix"].setdefault(e, {"count": 0, "bytes": 0})
        d["count"] += 1
        d["bytes"] += p.stat().st_size
    figure_checks["file_inventory"] = inv2
    (VAL / "figure_checks_final.json").write_text(
        json.dumps(figure_checks, indent=2, ensure_ascii=False, default=_js), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if all(summary.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())




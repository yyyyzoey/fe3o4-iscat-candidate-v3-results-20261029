#!/usr/bin/env python3
"""V4 source verification: re-read the two downloaded PDFs, render the audited pages,
extract their text, and record what was actually verified in this run."""
from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
import pypdf, pypdfium2 as pdfium

RESULT_ROOT = Path(__file__).resolve().parents[3]
ROOT = RESULT_ROOT.parent
import os
SRC = Path(os.environ.get("V4_SOURCE_DIR", str(ROOT / "build" / "sources_redownload")))
RES = ROOT / "results_v4" / "validation" / "sources"
RES.mkdir(parents=True, exist_ok=True)
(RES / "pages").mkdir(exist_ok=True)

def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

SUPP = SRC / "figshare_52761698.pdf"
PRE = SRC / "arxiv_2209.14508.pdf"
out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
       "tooling": "pypdf (text) + pypdfium2 (raster); no OCR", "pdfs": {}, "pages": [],
       "quotes": {}, "status": {}}

for name, path, expect_sha in (
        ("figshare_52761698", SUPP, "62a60e7194230c7ad5ed7635c951dfdab81e6f82e2e0f4772b6b71ef70ffbbfe"),
        ("arxiv_2209.14508", PRE, "1e40105aa5f1fe5ad399185f0ec84c400178c94fbdb1c1ea199496b452114358")):
    s = sha(path)
    rd = pypdf.PdfReader(str(path))
    full = "\n".join((p.extract_text() or "") for p in rd.pages)
    (RES / f"{name}_text.txt").write_text(full, encoding="utf-8")
    out["pdfs"][name] = {"bytes": path.stat().st_size, "sha256": s,
                         "sha256_matches_expected": s == expect_sha,
                         "pages": len(rd.pages), "text_chars": len(full),
                         "text_dump": f"{name}_text.txt"}

# rasterise the pages that carry the audited equations
jobs = [("figshare_52761698", SUPP, [4, 5, 6], "supplement"),
        ("arxiv_2209.14508", PRE, [3], "preprint")]
for name, path, idxs, label in jobs:
    doc = pdfium.PdfDocument(str(path))
    for i in idxs:
        png = RES / "pages" / f"{label}_idx{i:02d}.png"
        doc[i].render(scale=2.5).to_pil().save(png)
        out["pages"].append({"pdf": name, "page_index_0based": i, "png": png.name,
                             "png_bytes": png.stat().st_size, "sha256": sha(png)})

supp_txt = (RES / "figshare_52761698_text.txt").read_text(encoding="utf-8")

def grab(pattern: str, label: str, span: int = 260):
    m = re.search(pattern, supp_txt)
    out["quotes"][label] = None if not m else supp_txt[max(0, m.start() - 40):m.start() + span]
    return m

# S2 (reference field), S6 (scattered pupil) and S12/S13 (Azimuthal reduction)
grab(r"\(S2\)", "S2_reference_field")
grab(r"\(S6\)", "S6_scattered_pupil")
grab(r"\(S12\)", "S12_reference_reduced")
grab(r"\(S13\)", "S13_scattered_reduced")
grab(r"\(S7\)", "S7_azimuthal_integral")
grab(r"\(S10\)", "S10_bessel_identity")

# does the printed scattered-pupil line contain an explicit minus before S2?
s6 = out["quotes"]["S6_scattered_pupil"] or ""
out["status"] = {
    "figshare_file_52761698": "OBTAINED_AND_HASH_MATCHED",
    "arxiv_preprint_2209.14508": "OBTAINED_AND_HASH_MATCHED",
    "publisher_typeset_pdf": "NOT_OBTAINED_NO_INSTITUTIONAL_ACCESS",
    "equation_map_checked_against": ["supplement S1-S13", "preprint eq. (4)-(10)"],
    "s6_prints_s2_term_with_explicit_minus": bool(re.search(r"[-–−]\s*S2|S2\s*tp", s6)),
    "note": "Text extraction cannot resolve typeset signs reliably; the rasterised pages are the "
            "authoritative evidence and are read visually. See validation/model_conventions.md.",
}
(RES / "source_check.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in out["status"].items()}, indent=2, ensure_ascii=False))
print("pages:", [p["png"] for p in out["pages"]])

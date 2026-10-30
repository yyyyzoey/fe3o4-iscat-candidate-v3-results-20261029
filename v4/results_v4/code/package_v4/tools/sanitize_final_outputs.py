#!/usr/bin/env python3
"""Sanitise generated artifacts before public release.

1. Redacts third-party author e-mail addresses found in extracted source text
   (the upstream PDFs are public, but republishing contact addresses is not
   needed for the audit trail). 2. Rewrites absolute local paths recorded by
   verify_xdmf.py into tree-relative paths. The unmodified originals stay in
   the local audit directory, outside the published tree.
"""
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path

EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
ALLOWED = ("doi.org", "arxiv.org", "figshare.com", "github.com")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--raw-out", type=Path, required=True)
    a = ap.parse_args()
    RES = a.results.resolve()
    a.raw_out.mkdir(parents=True, exist_ok=True)
    log = {"emails_redacted": {}, "paths_rewritten": [], "raw_copies": []}

    src_dir = RES / "validation" / "sources"
    for p in sorted(src_dir.glob("*_text.txt")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        found = [m.group(0) for m in EMAIL.finditer(txt)]
        keep = [e for e in found if any(e.lower().endswith(d) for d in ALLOWED)]
        if keep:
            raise SystemExit(f"refusing to redact allow-listed address in {p.name}: {keep}")
        if found:
            raw = a.raw_out / (p.name + ".raw")
            shutil.copy2(p, raw)
            log["raw_copies"].append(str(raw))
            txt = EMAIL.sub("[email-redacted]", txt)
            p.write_text(txt, encoding="utf-8")
            log["emails_redacted"][p.name] = len(found)
    if log["emails_redacted"]:
        note = src_dir / "REDACTION_NOTE.md"
        note.write_text(
            "# Source-text redaction\n\n"
            "The extracted text of the public arXiv preprint and the public Figshare\n"
            "supplement contained the authors' contact e-mail addresses. Those addresses\n"
            "are not needed for any audit step, so they were replaced by\n"
            "`[email-redacted]` before this tree was published. Nothing else was changed:\n"
            "the scientific text, equations and figure references are intact, and the\n"
            "unmodified downloads remain in the local (unpublished) audit archive.\n\n"
            f"Files touched: {', '.join(sorted(log['emails_redacted']))}\n"
            f"Addresses replaced: {sum(log['emails_redacted'].values())}\n",
            encoding="utf-8")

    # absolute-path rewrite in the XDMF audit report
    rep = RES / "validation" / "xdmf_audit_final.json"
    if rep.is_file():
        raw = a.raw_out / "xdmf_audit_final.raw.json"
        shutil.copy2(rep, raw)
        log["raw_copies"].append(str(raw))
        txt = rep.read_text(encoding="utf-8")
        prefixes = {str(RES), str(RES).replace("\\", "/"),
                    str(RES).replace("\\", "\\\\")}
        before = txt
        for pre in sorted(prefixes, key=len, reverse=True):
            txt = txt.replace(pre, "<results_v4>")
        doc = json.loads(txt)
        doc["sanitized_absolute_paths"] = True
        doc["sanitization_note"] = ("Absolute local paths written by verify_xdmf.py were rewritten to "
                                    "<results_v4>; the unedited report is retained in the local audit archive.")
        rep.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log["paths_rewritten"].append({"file": rep.name, "changed": before != txt})

    (a.raw_out / "sanitize_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

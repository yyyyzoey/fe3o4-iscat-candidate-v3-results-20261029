# -*- coding: utf-8 -*-
"""Build the light REPORT zip, the FULL zip (with read-only HDF5 copies) and the
external package_verification.json. Nothing here touches the physics."""
from __future__ import annotations

import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path

import vis_common as C
from mk_report4 import write_logs_readme, write_sums

OUT = C.OUT
DEST = C.ROOT / "outputs" / "v4_visual_20261030"
ROOT_NAME = "results_v4_visual"

REPORT_ZIP = DEST / "Fe3O4_iSCAT_V4_1_VISUAL_REPORT.zip"
FULL_ZIP = DEST / "Fe3O4_iSCAT_V4_1_VISUAL_FULL.zip"
VERIFY = DEST / "package_verification.json"
FINAL_LOG = DEST / "step7_package_final.jsonl"


def sha256(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def tree_files() -> list[Path]:
    return sorted((p for p in OUT.rglob("*") if p.is_file()),
                  key=lambda p: p.relative_to(OUT).as_posix())


def add_file(zf: zipfile.ZipFile, path: Path, arcname: str) -> None:
    compress = zipfile.ZIP_STORED if path.suffix.lower() in (".h5", ".hdf5") else zipfile.ZIP_DEFLATED
    zi = zipfile.ZipInfo(arcname.replace("\\", "/"),
                         date_time=time.localtime(path.stat().st_mtime)[:6])
    zi.compress_type = compress
    zi.external_attr = 0o644 << 16
    zi.file_size = path.stat().st_size
    with path.open("rb") as src, zf.open(zi, "w") as dst:
        shutil.copyfileobj(src, dst, 1 << 22)


def build(path: Path, extra: list[tuple[Path, str]]) -> dict:
    files = tree_files()
    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", allowZip64=True) as zf:
        for p in files:
            add_file(zf, p, f"{ROOT_NAME}/{p.relative_to(OUT).as_posix()}")
        for src, arc in extra:
            add_file(zf, src, f"{ROOT_NAME}/{arc}")
    return inspect(path)


def inspect(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        bad = zf.testzip()
        total = sum(i.file_size for i in zf.infolist())
    return {
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "members": len(names),
        "uncompressed_bytes": total,
        "crc_check": "ok" if bad is None else f"BAD:{bad}",
        "contains_hdf5": any(n.lower().endswith((".h5", ".hdf5")) for n in names),
        "hdf5_members": sorted(n for n in names if n.lower().endswith((".h5", ".hdf5"))),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                     time.gmtime(path.stat().st_mtime)),
    }


def member_hashes(path: Path, wanted: list[str]) -> dict:
    out = {}
    with zipfile.ZipFile(path) as zf:
        for w in wanted:
            with zf.open(f"{ROOT_NAME}/{w}") as fh:
                h = hashlib.sha256()
                while True:
                    b = fh.read(1 << 22)
                    if not b:
                        break
                    h.update(b)
            out[w] = h.hexdigest()
    return out


def names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as zf:
        return set(zf.namelist())


def write_external_log(event: str, payload: dict) -> None:
    rec = {
        "step": "step7_package",
        "event": event,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **payload,
    }
    with FINAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    if FINAL_LOG.exists():
        FINAL_LOG.unlink()

    acc = json.loads((OUT / "acceptance.json").read_text(encoding="utf-8"))
    cfg = json.loads((OUT / "config" / "visual_config.json").read_text(encoding="utf-8"))
    sources = cfg["source_data"]

    # The package-internal log must be complete before SHA256SUMS.txt is written,
    # otherwise it cannot be included in the ZIP without invalidating that table.
    log = C.StepLog("step7_package")
    log.record("preflight", {
        "acceptance_overall": acc["overall"],
        "acceptance_checks": acc["n_checks"],
        "acceptance_failures": acc["n_fail"],
        "tree_files_before_sums": len(tree_files()),
        "report_zip": str(REPORT_ZIP),
        "full_zip": str(FULL_ZIP),
        "source_hdf5": [{"tag": r["tag"], "sha256": r["sha256"],
                         "bytes": r["bytes"], "path": r["path"]} for r in sources],
    })
    log.record("build_started", {
        "root_member": ROOT_NAME,
        "report_zip": str(REPORT_ZIP),
        "full_zip": str(FULL_ZIP),
        "note": "This in-tree log ends at build start by design. The final ZIP hashes are in the external step7_package_final.jsonl and package_verification.json.",
    })

    # Refresh logs/README.md after adding step7, then freeze the tree with SHA256SUMS.
    write_logs_readme()
    sums = write_sums()

    try:
        rep = build(REPORT_ZIP, [])
        full = build(FULL_ZIP, [(Path(r["path"]), f"data/{r['tag']}nm/cube.h5") for r in sources])

        check = member_hashes(REPORT_ZIP, ["README.md", "ACCEPTANCE.md", "SHA256SUMS.txt",
                                           "exported_data/selected_50_zeta_layers.csv"])
        local = {k: sha256(OUT / k) for k in check}
        member_ok = check == local

        expected_h5 = {f"{ROOT_NAME}/data/{r['tag']}nm/cube.h5": r["sha256"] for r in sources}
        full_h5_hashes = {}
        with zipfile.ZipFile(FULL_ZIP) as zf:
            for member in sorted(expected_h5):
                with zf.open(member) as fh:
                    h = hashlib.sha256()
                    while True:
                        b = fh.read(1 << 22)
                        if not b:
                            break
                        h.update(b)
                full_h5_hashes[member] = h.hexdigest()
        hdf5_ok = full_h5_hashes == expected_h5
        report_h5_ok = set(rep["hdf5_members"]) == set()
        full_h5_set_ok = set(full["hdf5_members"]) == set(expected_h5)
        extra_members_ok = names(FULL_ZIP) == names(REPORT_ZIP) | set(expected_h5)

        payload = {
            "schema": "v4-visual-package-verification-1.1",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "workspace": str(C.ROOT),
            "source_tree": str(OUT),
            "root_member_name": ROOT_NAME,
            "acceptance": {"overall": acc["overall"], "n_checks": acc["n_checks"],
                           "n_fail": acc["n_fail"], "table": str(OUT / "ACCEPTANCE.md")},
            "sha256_table": sums,
            "packages": {"REPORT": rep, "FULL": full},
            "member_hash_spot_check": {"ok": member_ok, "members": check},
            "hdf5_members": {
                "expected": expected_h5,
                "observed_in_full_zip": full_h5_hashes,
                "report_has_no_hdf5": report_h5_ok,
                "full_has_exactly_expected_hdf5": full_h5_set_ok,
                "sha256_match": hdf5_ok,
            },
            "zip_member_sets": {
                "full_equals_report_plus_three_hdf5": extra_members_ok,
                "report_members": len(names(REPORT_ZIP)),
                "full_members": len(names(FULL_ZIP)),
            },
            "hdf5": [{"tag": r["tag"], "sha256": r["sha256"], "bytes": r["bytes"],
                      "path": r["path"]} for r in sources],
            "final_log": str(FINAL_LOG),
            "verification_file": str(VERIFY),
            "notes": [
                "REPORT zip = figures + html + report + exported_data + code + logs + config; no HDF5.",
                "FULL zip = REPORT content + data/<TAG>nm/cube.h5 read-only copies.",
                "HDF5 are already gzip-compressed inside, so they are stored (not re-deflated).",
                "ZIP SHA256 values above are computed after writing, from the file on disk.",
                "The package-internal step7 log intentionally stops at build_started; completion hashes are external to avoid a self-referential ZIP hash.",
            ],
            "checks": {
                "report_crc": rep["crc_check"] == "ok",
                "full_crc": full["crc_check"] == "ok",
                "report_has_no_hdf5": report_h5_ok,
                "full_has_exactly_expected_hdf5": full_h5_set_ok,
                "hdf5_sha256_match": hdf5_ok,
                "full_equals_report_plus_three_hdf5": extra_members_ok,
                "member_spot_hashes_match": member_ok,
            },
        }
        VERIFY.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        write_external_log("done", {
            "report_zip": {k: rep[k] for k in ("bytes", "sha256", "members", "crc_check")},
            "full_zip": {k: full[k] for k in ("bytes", "sha256", "members", "crc_check")},
            "member_ok": member_ok,
            "hdf5_sha256_match": hdf5_ok,
            "verification_file": str(VERIFY),
        })
    except Exception as exc:
        write_external_log("failed", {"error_type": type(exc).__name__, "error": str(exc)})
        raise

    all_ok = all(payload["checks"].values())
    print(json.dumps({
        "REPORT": {k: rep[k] for k in ("bytes", "sha256", "members", "crc_check")},
        "FULL": {k: full[k] for k in ("bytes", "sha256", "members", "crc_check")},
        "checks": payload["checks"],
        "member_ok": member_ok,
        "hdf5_sha256_match": hdf5_ok,
        "sha256_table": sums,
        "verification_file": str(VERIFY),
        "final_log": str(FINAL_LOG),
    }, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
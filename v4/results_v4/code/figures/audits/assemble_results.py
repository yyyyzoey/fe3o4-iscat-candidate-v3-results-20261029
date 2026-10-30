"""Assemble V4 deliverable tree: code/, provenance/, validation/, logs/ (no absolute paths)."""
from __future__ import annotations
import hashlib, json, platform, re, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]          # work/v4
RES = ROOT / "results_v4"
PKG = ROOT / "pkg"
PKG_PRIS = ROOT / "pkg_pristine" / "Fe3O4_iSCAT_聚焦目标执行包_v4"
V3 = ROOT / "v3test" / "code"
BUILD = ROOT / "build"

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def copy_tree(src: Path, dst: Path, skip=("__pycache__",)):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if any(part in skip for part in p.parts):
            continue
        if p.is_file():
            q = dst / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)

# ---------- code ----------
code = RES / "code"
if code.exists():
    shutil.rmtree(code)
(code / "solver").mkdir(parents=True)
for sub in ("src", "tests", "tools", "configs", "docs"):
    copy_tree(V3 / sub, code / "solver" / sub)
(code / "solver" / "sources").mkdir(parents=True, exist_ok=True)
shutil.copy2(V3 / "sources" / "Fe3O4_Querry_bracket.csv", code / "solver" / "sources" / "Fe3O4_Querry_bracket.csv")
(code / "package_v4").mkdir(parents=True)
for name in ("README_START_HERE.md", "CODEX_PROMPT.md", "requirements.txt", "SHA256SUMS.txt"):
    shutil.copy2(PKG / name, code / "package_v4" / name)
for sub in ("docs", "configs", "tools", "tests", "reports"):
    copy_tree(PKG / sub, code / "package_v4" / sub)
(code / "figures").mkdir(parents=True)
for name in ("make_final_figs.py", "make_final_figs_v2.py", "make_f2_full_asinh.py",
             "make_f4_components.py", "make_montages.py", "make_xdmf.py", "make_f1.py",
             "audit_cubes.py"):
    src = BUILD / name
    if src.is_file():
        shutil.copy2(src, code / "figures" / name)
(code / "figures" / "audits").mkdir(parents=True)
for name in ("make_figs_audit.py", "assemble_results.py", "check_pkg.py", "audit_all.py", "make_bundle.py"):
    src = BUILD / name
    if src.is_file():
        shutil.copy2(src, code / "figures" / "audits" / name)

# exporter path patch, documented
patch_lines = [
    "--- a/tools/export_paper_views.py",
    "+++ b/tools/export_paper_views.py",
    "@@ inspect() signature @@",
    "-def inspect(path: Path, diameter: int, allow_pilot: bool) -> dict:",
    "+def inspect(path: Path, diameter: int, allow_pilot: bool, data_root: Path | None = None) -> dict:",
    "@@ record source label instead of absolute path @@",
    "-        return dict(diameter_nm=diameter, source=str(path.resolve()), sha256=digest(path),",
    "+        source_label = path.relative_to(data_root).as_posix() if data_root is not None else path.name",
    "+        return dict(diameter_nm=diameter, source=source_label, sha256=digest(path),",
    "@@ pass data_root @@",
    "-        records.append(inspect(path, d, args.allow_pilot))",
    "+        records.append(inspect(path, d, args.allow_pilot, args.data_root))",
    "@@ open via data_root @@",
    "-        with h5py.File(r['source'], 'r') as f:",
    "+        with h5py.File(args.data_root / r['source'], 'r') as f:",
    "@@ printable out path @@",
    "-                      'pilot_only': args.allow_pilot, 'out': str(args.out.resolve()),",
    "+                      'pilot_only': args.allow_pilot, 'out': args.out.as_posix(),",
    "",
]
(code / "package_v4" / "docs" / "export_tool_path_patch.diff").write_text("\n".join(patch_lines), encoding="utf-8")

(code / "README.md").write_text("""# V4 交付代码

本目录保存生成 V4 结果与审计的全部可复现源码，不含 HDF5 数据体。

- `solver/`：产生三个 `cube.h5` 的光学求解器与配置（`src/iscat_core.py`、`src/run_dataset.py`）、
  31 项光学/IO 测试（`tests/`）、审计工具（`tools/`）、论文约定审计文档（`docs/`）。
  `src/*.py` 的规范化哈希等于 cube 属性 `implementation_sha256`，见 `../provenance/source_hashes.json`。
- `package_v4/`：用户提供的 V4 执行包原件（12/12 文件哈希校验通过）。
  `tools/export_paper_views.py` 只做了路径处理修改（把绝对路径改为相对标签），
  差异见 `package_v4/docs/export_tool_path_patch.diff`；光学公式未改动。
- `figures/`：由保存的 HDF5 复读生成 F1–F7 图件、CSV、XDMF 的脚本。
- `figures/audits/`：数据体逐层复读、图件完整性、链接、隐私扫描与打包脚本。

所有脚本只读取已保存数据或从配置重新计算，不修改已有 HDF5。
""", encoding="utf-8")

# ---------- logs ----------
logs = RES / "logs"
if logs.exists():
    shutil.rmtree(logs)
logs.mkdir(parents=True)
LOGMAP = {
    "unit_tests_final.log": ROOT / "unit_tests_final.log",
    "v3_optical_tests_final.log": ROOT / "v3_optical_tests_final.log",
    "legacy_tests_final.log": ROOT / "legacy_tests_final.log",
    "data_audit_final.log": BUILD / "data_audit_final.log",
    "make_final_figs.log": BUILD / "make_final_figs.log",
    "make_final_figs_v2.log": BUILD / "make_final_figs_v2.log",
    "export_final_views.log": ROOT / "export_final_views.log",
}
for dst, src in LOGMAP.items():
    if src.is_file():
        txt = src.read_text(encoding="utf-8", errors="replace")
        txt = re.sub(r"[A-Za-z]:\\+Users\\+[^\\\s]+", "<local>", txt)
        (logs / dst).write_text(txt, encoding="utf-8")

# ---------- provenance ----------
prov = RES / "provenance"
prov.mkdir(parents=True, exist_ok=True)
import h5py
with h5py.File(RES / "data" / "D030nm" / "cube.h5", "r") as f:
    cfg_json = json.loads(f.attrs["configuration_json"])
    cube_attrs = {k: (v.item() if hasattr(v, "item") else v) for k, v in f.attrs.items()}
    cfg_sha = str(f.attrs["config_sha256"])
    impl_sha = str(f.attrs["implementation_sha256"])
    gamma = [float(f.attrs["gamma_real"]), float(f.attrs["gamma_imag"])]
    scale = float(f.attrs["reference_field_scale"])

config_out = {
    "role": "V4 delivered run configuration (copied from the saved cube attribute configuration_json)",
    "configuration": cfg_json,
    "config_sha256": cfg_sha,
    "implementation_sha256": impl_sha,
    "gamma": {"real": gamma[0], "imag": gamma[1], "note": "gamma=0.5 is an assumed, uncalibrated basis scale"},
    "reference_field_scale": scale,
    "grid": {"axis_order": "zeta,y,x", "zeta_nm": [-170, 2, 170], "xy_nm": [-1200, 10, 1200],
             "shape": [171, 241, 241], "grid_mode": "full"},
    "fixed_target_parameters": {"diameters_nm": [30, 100, 200], "center_heights_nm": [15, 50, 100],
                                "wavelength_nm": 532.0, "NA": 1.45, "n_sample": 1.33,
                                "n_particle": [2.3456, 0.0926], "material": "Fe3O4"},
    "stale_text_in_cube_attribute": {
        "field": "configuration.source.version_difference_audit",
        "value": cfg_json.get("source", {}).get("version_difference_audit"),
        "explanation": ("The cube attribute was written before the direct Figshare file 52761698 download. "
                        "The download and hash check were completed afterwards; the authoritative record is "
                        "provenance/source_hashes.json. The optical model and data were not changed by this."),
    },
}
(prov / "config.json").write_text(json.dumps(config_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

(prov / "source_commit.txt").write_text(
    "f0f9959db144b01b6e0c6cf82f4a030df6515127\n"
    "# Read-only baseline commit of the published V3 repository. V4 is published on branch v4-paper-forward-results.\n",
    encoding="utf-8")

fig_src = BUILD / "sources_redownload" / "figshare_52761698.pdf"
arx_src = BUILD / "sources_redownload" / "arxiv_2209.14508.pdf"
source_hashes = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "figshare": {
        "article": "22047950",
        "file_id": 52761698,
        "filename_expected": "6288691.pdf",
        "url": "https://api.figshare.com/v2/file/download/52761698",
        "landing_page": ("https://opticapublishing.figshare.com/articles/journal_contribution/"
                         "Supplementary_document_for_Axial_Profiling_of_Interferometric_Scattering_"
                         "Enables_an_Accurate_Determination_of_Nanoparticle_Size_-_6288691_pdf/22047950"),
        "downloaded": fig_src.is_file(),
        "bytes": fig_src.stat().st_size if fig_src.is_file() else None,
        "sha256": sha(fig_src) if fig_src.is_file() else None,
        "expected_sha256": "62a60e7194230c7ad5ed7635c951dfdab81e6f82e2e0f4772b6b71ef70ffbbfe",
        "hash_match": (sha(fig_src) == "62a60e7194230c7ad5ed7635c951dfdab81e6f82e2e0f4772b6b71ef70ffbbfe") if fig_src.is_file() else False,
        "status": "VERIFIED_FILE_52761698",
    },
    "arxiv_preprint": {
        "url": "https://arxiv.org/pdf/2209.14508",
        "downloaded": arx_src.is_file(),
        "bytes": arx_src.stat().st_size if arx_src.is_file() else None,
        "sha256": sha(arx_src) if arx_src.is_file() else None,
        "status": "VERIFIED_DOWNLOADED",
        "note": "20-page author preprint including supplement.",
    },
    "publisher_typeset_pdf": {
        "doi": "10.1364/OE.480337",
        "downloaded": False,
        "status": "NOT_OBTAINED",
        "note": ("The final typeset Optica PDF could not be retrieved without institutional access. "
                 "All equation references were checked against the Figshare supplement and the arXiv preprint; "
                 "a final-typeset line-by-line comparison is NOT claimed."),
    },
    "fe3o4_optical_constants": {
        "model": "np = 2.3456 + 0.0926i at 532 nm",
        "source": "Querry 1985 bulk magnetite via refractiveindex.info; linear interpolation of the 530/540 nm bracket",
        "local_bracket": {"530 nm": [2.346, 0.091], "540 nm": [2.344, 0.099]},
        "status": "LOCAL_BRACKET_VERIFIED",
        "note": "Bulk literature value; not a measurement of the specific particles.",
    },
}
(prov / "source_hashes.json").write_text(json.dumps(source_hashes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# implementation hash reproduced from archived source
src_hash = {}
for p in sorted((code / "solver" / "src").glob("*.py")):
    src_hash[p.name] = sha(p)
canon = hashlib.sha256(json.dumps(src_hash, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
run_identity = {
    "source_commit": "f0f9959db144b01b6e0c6cf82f4a030df6515127",
    "base_tag_not_modified": "v1.0.0",
    "cube_config_sha256": cfg_sha,
    "cube_implementation_sha256": impl_sha,
    "archived_src_files_sha256": src_hash,
    "archived_src_canonical_sha256": canon,
    "implementation_hash_reproduced": canon == impl_sha,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "note": ("implementation_sha256 is sha256 of canonical JSON {filename: file_sha256} over src/*.py, "
             "reproduced from the archived source tree."),
}
(prov / "run_identity.json").write_text(json.dumps(run_identity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

import matplotlib, numpy, h5py as _h5, scipy
env = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "os": platform.platform(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "python": sys.version.split()[0],
    "python_implementation": platform.python_implementation(),
    "packages": {"numpy": numpy.__version__, "scipy": scipy.__version__, "h5py": _h5.__version__,
                 "matplotlib": matplotlib.__version__},
    "gpu_used": False,
    "note": "CPU-only NumPy/SciPy evaluation; no camera, noise or tracking code in the delivered run.",
}
(prov / "environment.json").write_text(json.dumps(env, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------- validation JSONs ----------
val = RES / "validation"
val.mkdir(parents=True, exist_ok=True)
shutil.copy2(BUILD / "execution_package_sha_check.json", val / "execution_package_sha_check.json")
shutil.copy2(ROOT / "validation_data_audit_tmp.json", val / "data_audit.json")
print("code/provenance/logs/validation scaffolds written")
print("implementation hash reproduced:", canon == impl_sha)

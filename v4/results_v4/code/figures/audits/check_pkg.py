import hashlib, json
from pathlib import Path
root = Path(r"work/v4/pkg_pristine/Fe3O4_iSCAT_聚焦目标执行包_v4")
sums = {}
for line in (root/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    h, name = line.split(None, 1)
    sums[name.strip()] = h.lower()
rows = []
ok = True
for name, expect in sums.items():
    p = root/name
    if not p.is_file():
        rows.append(dict(file=name, expected=expect, actual=None, pass_=False, reason="missing"))
        ok = False
        continue
    a = hashlib.sha256(p.read_bytes()).hexdigest()
    good = a == expect
    ok &= good
    rows.append(dict(file=name, expected=expect, actual=a, bytes=p.stat().st_size, pass_=good))
zip_path = Path(r"work/v4/v4.zip")
out = dict(
    execution_package="Fe3O4_iSCAT_聚焦目标执行包_v4.zip",
    zip_bytes=zip_path.stat().st_size,
    zip_sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
    manifest_file="SHA256SUMS.txt",
    files_checked=len(sums),
    files_passed=sum(1 for r in rows if r["pass_"]),
    all_pass=ok,
    files=rows,
    note="Pristine extraction of the delivered V4 zip; hashes compared with the package's own SHA256SUMS.txt.",
)
Path(r"work/v4/build/execution_package_sha_check.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "files"}, indent=1, ensure_ascii=False))

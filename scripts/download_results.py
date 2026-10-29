#!/usr/bin/env python3
"""Download and verify the split Fe3O4 iSCAT result bundle from GitHub.

The repository is public, so no token is required. GITHUB_TOKEN is optional and
is used only if the anonymous API rate limit is hit. A token, when supplied, is
never written to disk or printed.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OWNER = "yyyyzoey"
REPO = "fe3o4-iscat-candidate-v3-results-20261029"
API = "https://api.github.com"
MANIFEST_NAME = "results_bundle.zip.manifest.json"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def asset_endpoint(asset, token):
    """Use the direct browser URL anonymously; the API asset URL when authenticated."""
    if token:
        return f"/repos/{OWNER}/{REPO}/releases/assets/{asset['id']}"
    return asset["browser_download_url"]


def api_request(path, token, accept="application/vnd.github+json", retries=6):
    url = path if path.startswith("http") else API + path
    headers = {
        "Accept": accept,
        "User-Agent": "Fe3O4-results-downloader",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    last = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with OPENER.open(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308):
                location = exc.headers["Location"]
                # Pre-signed object-storage URL: do not forward the GitHub token.
                with urllib.request.urlopen(location, timeout=300) as resp:
                    return resp.read()
            last = exc
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:500]
            except Exception:
                pass
            print(f"API retry {attempt}/{retries}: HTTP {exc.code} {detail}", file=sys.stderr)
        except Exception as exc:
            last = exc
            print(f"API retry {attempt}/{retries}: {type(exc).__name__}: {exc}", file=sys.stderr)
        time.sleep(min(2 ** (attempt - 1), 20))
    raise RuntimeError(f"request failed: {url}: {last}")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="v1.0.0")
    parser.add_argument("--out", default=".")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--keep-parts", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()  # optional for the public repo

    out = Path(args.out).resolve()
    parts_dir = out / "results_bundle.zip.parts"
    out.mkdir(parents=True, exist_ok=True)
    parts_dir.mkdir(parents=True, exist_ok=True)

    release = json.loads(api_request(f"/repos/{OWNER}/{REPO}/releases/tags/{args.tag}", token))
    assets = {a["name"]: a for a in release.get("assets", [])}
    if MANIFEST_NAME not in assets:
        raise SystemExit(f"Release asset not found: {MANIFEST_NAME}")
    manifest_data = api_request(
        asset_endpoint(assets[MANIFEST_NAME], token),
        token, accept="application/octet-stream",
    )
    manifest = json.loads(manifest_data.decode("utf-8"))
    manifest_path = out / MANIFEST_NAME
    manifest_path.write_bytes(manifest_data)
    print(f"manifest: {manifest['part_count']} parts, {manifest['total_bytes']} bytes")
    print(f"manifest sha256: {sha256_bytes(manifest_data)}")

    if manifest.get("original_name") != "results_bundle.zip":
        raise SystemExit("Unexpected archive name in manifest")
    if len(manifest.get("parts", [])) != manifest.get("part_count"):
        raise SystemExit("Manifest part count mismatch")

    def download_one(item):
        name = item["name"]
        dest = parts_dir / name
        if dest.exists() and dest.stat().st_size == item["bytes"] and sha256_file(dest) == item["sha256"]:
            return name, "cached"
        asset = assets.get(name)
        if not asset:
            raise RuntimeError(f"Release asset missing: {name}")
        last = None
        for attempt in range(1, 5):
            try:
                data = api_request(
                    asset_endpoint(asset, token),
                    token, accept="application/octet-stream", retries=4,
                )
                if len(data) != item["bytes"]:
                    raise ValueError(f"size {len(data)} != {item['bytes']}")
                digest = sha256_bytes(data)
                if digest != item["sha256"]:
                    raise ValueError(f"sha256 {digest} != {item['sha256']}")
                tmp = dest.with_suffix(dest.suffix + ".tmp")
                tmp.write_bytes(data)
                tmp.replace(dest)
                return name, "downloaded"
            except Exception as exc:
                last = exc
                print(f"{name} retry {attempt}/4: {exc}", file=sys.stderr)
                time.sleep(min(2 ** (attempt - 1), 10))
        raise RuntimeError(f"failed to download {name}: {last}")

    pending = []
    for item in manifest["parts"]:
        dest = parts_dir / item["name"]
        if not (dest.exists() and dest.stat().st_size == item["bytes"] and sha256_file(dest) == item["sha256"]):
            pending.append(item)
    print(f"parts pending: {len(pending)}/{manifest['part_count']}")
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(download_one, item): item for item in pending}
        done = 0
        for fut in as_completed(futures):
            name, state = fut.result()
            done += 1
            print(f"[{done}/{len(pending)}] {name} {state}")
            if done % 8 == 0 or done == len(pending):
                print(f"download progress: {done}/{len(pending)}")

    archive = out / manifest["original_name"]
    h = hashlib.sha256()
    total = 0
    with archive.open("wb") as dst:
        for item in sorted(manifest["parts"], key=lambda x: x["index"]):
            src = parts_dir / item["name"]
            if src.stat().st_size != item["bytes"] or sha256_file(src) != item["sha256"]:
                raise SystemExit(f"Part verification failed: {src}")
            with src.open("rb") as f:
                for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                    dst.write(chunk)
                    h.update(chunk)
                    total += len(chunk)
    actual = h.hexdigest()
    print(f"reassembled: {archive}")
    print(f"bytes: {total}")
    print(f"sha256: {actual}")
    if total != manifest["total_bytes"] or actual != manifest["sha256"]:
        raise SystemExit("FINAL ARCHIVE VERIFICATION FAILED")
    print("FINAL ARCHIVE VERIFICATION PASSED")
    if not args.keep_parts:
        for item in manifest["parts"]:
            (parts_dir / item["name"]).unlink(missing_ok=True)
        try:
            parts_dir.rmdir()
        except OSError:
            pass
        print("part files removed after successful verification")


if __name__ == "__main__":
    main()

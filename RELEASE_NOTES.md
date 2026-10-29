# v1.0.0 — Fe₃O₄ iSCAT candidate results

This release publishes the complete, direct full-grid results for surface-bound single Fe₃O₄ spheres at 532 nm and target NA=1.45.

## Assets

The complete archive is published as **76 lossless 16 MiB parts** whose numeric order reconstructs the original ZIP:

- `results_bundle.zip.part000` ... `results_bundle.zip.part075`
- Reassembled name: `results_bundle.zip`
- Reassembled bytes: `1,273,486,344` (about 1.19 GiB)
- Reassembled SHA256: `fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7`
- `results_bundle.zip.manifest.json` (SHA256 `07b8d5a19ce260b4f7e57898e16b7a978c82b94cdf384e628f682a08700188df`)
- `results_bundle.zip.parts.sha256`
- `download_results.py`, `DOWNLOAD_RESULTS.md`
- `reassemble_results.ps1`, `reassemble_results.sh`

The parts are not independent datasets. Concatenate them in numeric order, then verify the final size and SHA256. The recommended downloader verifies every part and the final archive automatically:

```powershell
python .\download_results.py --tag v1.0.0 --out .\download
```

The repository is public (since 2026-10-29); the downloader works anonymously and no GitHub token is required.

Contents: 139 ZIP members rooted at `release/`, including three complete `(171,241,241)` HDF5 cubes, XDMF files, figures, diagnostics, source/configuration, and SHA256 manifests.

## Verification

- 83 release assets re-read through the GitHub API; all 76 part assets are `uploaded` with server-side size and digest matching the manifest.
- The published `download_results.py` was run end-to-end: all 76 parts downloaded and verified, the ZIP was reassembled, and the final size/SHA256 plus ZIP integrity test passed.
- See `verification/github_release_audit.md` and `verification/github_e2e_download.json`.

## Status

- `data_generation=COMPLETE`
- `numerical_validation=PARTIAL`
- `source_version_audit=VERIFIED` only for the specified Figshare v3 file and author-preprint locator
- `formula_fidelity=UNVERIFIED`
- `high_na_model_validation=UNVERIFIED`
- `absolute_calibration=false`
- `result_class=CANDIDATE`

The complete Jones-chain closure, supercritical high-NA physics, relative complex amplitude, and absolute calibration remain unverified. The 10->5 nm bilinear midpoint test remains above the `1e-3` threshold. This is not a claim of strict paper reproduction or complete physical certification.

See the repository `README.md`, `RESULTS.md`, and the bundled `release/review.md` for evidence and limitations.

# Fe3O₄ iSCAT V4.1 — 50-layer visual report (candidate branch)

This branch is the read-only visualisation deliverable derived from:

- repository: `yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029`
- base branch: `v4-audit-final-candidate`
- fixed base commit: `0a58aff466d053bbd3f82fe9fc77fb57511edd2c`
- branch: `v4-visual-report-candidate`

Nothing in the optical model or the three stored HDF5 cubes was modified or recomputed.

## Contents

- `results_v4_visual/` — complete REPORT tree: 50-layer 2D montages and atlases, 50-plane 3D stacks, orthoviews, signal decomposition, comparisons, six self-contained HTML viewers, reports, logs, code, configuration and per-file SHA256.
- `v4_visual_release/package_verification.json` — independent ZIP integrity and HDF5-member hash audit.
- `v4_visual_release/step7_package_final.jsonl` — packaging completion record with ZIP SHA256.
- `v4_visual_release/SHA256SUMS_PACKAGES.txt` — package hashes.

The large ZIPs are Release assets, not Git objects. The FULL ZIP contains only three read-only HDF5 copies; the REPORT ZIP contains no HDF5.

## Visualisation boundary

```text
result_class                     = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
through_focus                    = true   (NOT sample-space near field)
full_jones_chain                 = UNVERIFIED
high_na_model_validation         = UNVERIFIED
paper_convention_checks          = UNVERIFIED
absolute_calibration             = false
sample_space_near_field          = false
publisher_typeset_pdf            = NOT_OBTAINED
linear_midpoint_reconstruction   = FAILED_KEPT
```

`I_cross = 2 Re(E_ref* conj(E_scat))` is signed; no absolute value was applied.
`zeta` is the through-focus scan coordinate, not sample depth.
All figures are display products of the existing candidate data and do not constitute physical certification.

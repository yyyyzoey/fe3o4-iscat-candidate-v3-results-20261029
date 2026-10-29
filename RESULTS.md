# Results summary

## Scope actually executed

| Item | Value |
|---|---|
| Wavelength | 532 nm |
| Requested / integrated NA | 1.45 / 1.45 |
| Sample medium | water, `n_s=1.33` |
| Diameters | 30, 100, 200 nm |
| Geometry | one surface-bound sphere; center height `D/2` = 15, 50, 100 nm |
| through-focus axis | `zeta = -170:2:170 nm`, 171 slices |
| lateral grid | `x,y = -1200:10:1200 nm`, 241 x 241 points |
| array order | `(zeta, y, x)` |
| field component order | `(Ex, Ey)` |
| calculation / storage precision | `complex128,float64` / `float32` |
| mode | full grid, not a pilot upsampled by interpolation |

No 520 nm, 400 Hz, Brownian motion, camera model, floating-height scan, or background/stray-light model was introduced.

## HDF5 files in the Release archive

The archive root is `release/`.

| D (nm) | Member | Depth read | Shape | Uncompressed voxels | SHA256 |
|---:|---|---:|---|---:|---|
| 30 | `release/D030nm/cube.h5` | 171/171 | `(171,241,241)` | 9,931,851 | `ecbbea68c663246f1404acc7dc588164f1f89d6f7d9e6ac082a359d35473ad46` |
| 100 | `release/D100nm/cube.h5` | 171/171 | `(171,241,241)` | 9,931,851 | `ffca89836461eae774e3d7917fc02f5aa64c5bd507d33979170abb1b4d919c49` |
| 200 | `release/D200nm/cube.h5` | 171/171 | `(171,241,241)` | 9,931,851 | `c94e7be2d5550fbe3173d4f5eacdc611e95c1edcf28e5814943f9e54b86de9d2` |

All three files were read back layer by layer after writing. The saved-cube audit reports exact coordinates, `completed_slices=171`, `zeta=0` present, no non-finite non-contrast values, no negative intensity voxels, and matching file/manifest SHA256 values.

## Post-package verification

`verification/post_package_verification.json` records **20/20 PASS**, including:

- manifest parse and release inventory;
- SHA256 of all 138 manifest entries;
- SHA256 and CRC test of the 1,273,486,344-byte ZIP;
- ZIP member inventory and member hashes;
- required release files and status semantics;
- task-parameter integrity and exactly three HDF5 cubes.

The 20 checks verify packaging/storage integrity. They do not upgrade the physical-model status beyond `CANDIDATE`.

## Numerical checks: passed and failed

Passed:

- angular integration and direct azimuthal checks;
- 512/256 -> 1024/512 quadrature comparison;
- radial 1601 -> 3201 comparison and direct radial evaluation;
- 1 nm axial midpoint check;
- Mie order increase by 10 orders;
- critical-sector integration convergence;
- Mie special-function oracles and Rayleigh limits;
- saved-file identity and storage checks.

Not passed:

| D (nm) | 10->5 nm bilinear relative L2 | bilinear relative Linf | cubic relative L2 | cubic relative Linf |
|---:|---:|---:|---:|---:|
| 30 | 1.955e-3 | 2.133e-3 | 6.494e-6 | 1.043e-5 |
| 100 | 1.543e-3 | 1.699e-3 | 4.742e-6 | 7.597e-6 |
| 200 | 2.159e-3 | 2.399e-3 | 7.505e-6 | 1.260e-5 |

Therefore `numerical_validation=PARTIAL`. The stored fields are direct 10 nm evaluations; this result limits claims about representing finer lateral structure.

## Test status

- current suite: 31/31 PASS;
- legacy suite: 7/7 PASS;
- see `release/tests.json` for names and exit information.

## Remaining physical blockers

1. `full_Jones_chain`: no independent end-to-end QWP/PBS/Fresnel/objective/lens matrix closure.
2. `supercritical_high_NA_physical_validation`: NA=1.45 exceeds `n_s=1.33`; analytic continuation is used, but numerical convergence is not a finite sphere-interface Maxwell validation.
3. `relative_complex_amplitude`: `gamma=0.5+0i` is a demonstration convention, not a calibrated sample ratio.
4. `linear_midpoint_reconstruction`: bilinear 10->5 nm test remains above threshold.
5. XDMF was structurally audited, but not opened in ParaView for this report.

`absolute_calibration=false`; the data are not camera counts or an absolutely calibrated scattering cross-section.

## Data semantics

The saved arrays are the image-plane through-focus response on `(zeta,y,x)`. `zeta` is a focus-scan coordinate, not a sample-space near-field coordinate, and the fixed +/-170 nm window is not a measured depth-of-field claim. The fields are not the electromagnetic field distribution in the sample volume.


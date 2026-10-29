# Full HDF5 data

The three complete HDF5 cubes are distributed through the GitHub Release `v1.0.0`, not in ordinary Git. The original `results_bundle.zip` is published as 76 lossless parts:

```text
results_bundle.zip.part000
...
results_bundle.zip.part075
```

Reassembled size: `1,273,486,344` bytes.

Reassembled SHA256: `fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7`

See [DOWNLOAD_RESULTS.md](DOWNLOAD_RESULTS.md) for the recommended token-authenticated downloader, manual download, per-part verification, and reassembly commands. The reassembled archive has this layout:

```text
release/
  D030nm/cube.h5
  D100nm/cube.h5
  D200nm/cube.h5
  D030_focus_stack.xdmf
  D100_focus_stack.xdmf
  D200_focus_stack.xdmf
  ...
```

To use an XDMF file, extract the archive without renaming directories, then open the corresponding `D0xx_focus_stack.xdmf` in an XDMF-capable viewer. The XDMF files reference `D0xxnm/cube.h5` by relative path.

The cube axes are `(zeta,y,x)`. These are through-focus image responses, not sample-space near-field volumes.

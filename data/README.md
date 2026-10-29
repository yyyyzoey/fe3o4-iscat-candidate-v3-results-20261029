# Full HDF5 data

The three complete HDF5 cubes are distributed in the GitHub Release asset `results_bundle.zip`, not in ordinary Git.

Archive layout:

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

Verify the archive first:

```powershell
$expected='fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7'
$actual=(Get-FileHash .\results_bundle.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if($actual -ne $expected){ throw "SHA256 mismatch: $actual" }
```

The cube axes are `(zeta,y,x)`. These are through-focus image responses, not sample-space near-field volumes.

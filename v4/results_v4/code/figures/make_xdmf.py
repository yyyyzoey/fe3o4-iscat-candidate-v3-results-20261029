"""Write XDMF wrappers pointing at ../data/<case>/cube.h5 and verify every DataItem."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json
import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results_v4"
OUT = RES / "views3d"
CASES = (("D030nm", 30), ("D100nm", 100), ("D200nm", 200))
ATTRS = [("I_cross", "J = 2 Re(conj(E_ref).E_scat); signed interference term"),
         ("I_total", "I_ref + I_scat + I_cross"),
         ("I_ref", "reference intensity"),
         ("I_scat", "scattered intensity (gamma=0.5 applied)"),
         ("contrast_fixed_reference", "(I_scat+J)/I_ref0 with shared reference scale"),
         ("contrast_local", "(I_scat+J)/I_ref; NaN where reference is near zero")]

TPL = """<?xml version="1.0" encoding="utf-8"?>
<Xdmf Version="3.0">
  <Domain>
    <Grid Name="{name}" GridType="Uniform">
      <Information Name="warning" Value="third axis is the through-focus scan coordinate zeta, not a sample-space near-field z; not absolutely calibrated"/>
      <Information Name="status" Value="CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED"/>
      <Topology TopologyType="3DRectMesh" Dimensions="171 241 241"/>
      <Geometry GeometryType="VXVYVZ">
        <DataItem Dimensions="241" NumberType="Float" Precision="8" Format="HDF">{h5}:/coords/x_object_nm</DataItem>
        <DataItem Dimensions="241" NumberType="Float" Precision="8" Format="HDF">{h5}:/coords/y_object_nm</DataItem>
        <DataItem Dimensions="171" NumberType="Float" Precision="8" Format="HDF">{h5}:/coords/zeta_nm</DataItem>
      </Geometry>
{attrs}
    </Grid>
  </Domain>
</Xdmf>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"pass": True, "files": {}, "failures": []}
    for case, D in CASES:
        h5rel = f"../data/{case}/cube.h5"
        attrs = "\n".join(
            f'      <Attribute Name="{n}" AttributeType="Scalar" Center="Node">\n'
            f'        <Information Name="meaning" Value="{d}"/>\n'
            f'        <DataItem Dimensions="171 241 241" NumberType="Float" Precision="4" Format="HDF">{h5rel}:/signals/{n}</DataItem>\n'
            f'      </Attribute>' for n, d in ATTRS)
        xml = TPL.format(name=f"Fe3O4_D{D}nm_through_focus_CANDIDATE", h5=h5rel, attrs=attrs)
        path = OUT / f"D{D:03d}_focus_stack.xdmf"
        path.write_text(xml, encoding="utf-8")

        # ---- verify ----
        e = {"xdmf": path.name, "hdf5": h5rel, "items": 0, "attributes": []}
        try:
            root = ET.parse(path).getroot()
            grid = root.find("./Domain/Grid")
            topo = grid.find("Topology"); geo = grid.find("Geometry")
            assert grid.get("GridType") == "Uniform"
            assert topo.get("TopologyType") == "3DRectMesh"
            assert topo.get("Dimensions") == "171 241 241"
            assert geo.get("GeometryType") == "VXVYVZ"
            h5abs = (path.parent / h5rel).resolve()
            assert h5abs.is_file(), h5abs
            with h5py.File(h5abs, "r") as f:
                for item in list(geo.findall("DataItem")) + [i for a in grid.findall("Attribute") for i in a.findall("DataItem")]:
                    ref = item.text.strip(); rel, ds = ref.split(":", 1)
                    tgt = (path.parent / rel).resolve()
                    assert tgt.is_file(), f"missing {rel}"
                    assert tgt == h5abs
                    dims = [int(v) for v in item.get("Dimensions").split()]
                    assert ds in f, f"dataset {ds} missing"
                    dset = f[ds]
                    assert list(dset.shape) == dims, f"{ds}: {dset.shape} != {dims}"
                    e["items"] += 1
                # axis monotonic
                for ax in ("x_object_nm", "y_object_nm", "zeta_nm"):
                    v = f["coords/" + ax][:]
                    assert np.all(np.diff(v) > 0), ax
                e["zeta_first_last"] = [float(f["coords/zeta_nm"][0]), float(f["coords/zeta_nm"][-1])]
                e["xy_first_last"] = [float(f["coords/x_object_nm"][0]), float(f["coords/x_object_nm"][-1])]
                for a in grid.findall("Attribute"):
                    e["attributes"].append(a.get("Name"))
                assert len(e["attributes"]) == len(ATTRS)
            e["pass"] = True
        except Exception as exc:  # noqa: BLE001
            e["pass"] = False
            e["error"] = repr(exc)
            report["pass"] = False
            report["failures"].append(f"{path.name}: {exc}")
        report["files"][case] = e
        print(case, e["pass"], e["items"])
    (RES / "validation" / "xdmf_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("ALL PASS" if report["pass"] else "FAILURES")


if __name__ == "__main__":
    main()

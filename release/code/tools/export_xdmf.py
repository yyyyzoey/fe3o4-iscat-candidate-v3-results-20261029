#!/usr/bin/env python3
"""ParaView-compatible wrappers for existing HDF5 scalars; no data duplication.
The third axis is focus displacement, NOT actual sample-space height.
"""
from pathlib import Path
import argparse,json,xml.etree.ElementTree as ET
import h5py

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
    c=json.loads((a.directory/'config_used.json').read_text(encoding='utf-8'))
    for D in c['diameters_nm']:
        rel=f'D{D:03d}nm/cube.h5'
        with h5py.File(a.directory/rel,'r') as f:
            nx=len(f['coords/x_object_nm']);ny=len(f['coords/y_object_nm']);nz=len(f['coords/zeta_nm'])
        root=ET.Element('Xdmf',Version='3.0');domain=ET.SubElement(root,'Domain');grid=ET.SubElement(domain,'Grid',Name=f'D{D}_CANDIDATE_focus_stack',GridType='Uniform')
        ET.SubElement(grid,'Information',Name='warning',Value='z axis is zeta focus scan; not a spatial near-field distribution')
        ET.SubElement(grid,'Topology',TopologyType='3DRectMesh',Dimensions=f'{nz} {ny} {nx}')
        geo=ET.SubElement(grid,'Geometry',GeometryType='VXVYVZ')
        for name,n in [('x_object_nm',nx),('y_object_nm',ny),('zeta_nm',nz)]:
            ET.SubElement(geo,'DataItem',Dimensions=str(n),NumberType='Float',Precision='8',Format='HDF').text=f'{rel}:/coords/{name}'
        for name in ['I_cross','I_total','I_ref','I_scat','contrast_fixed_reference','contrast_local']:
            attr=ET.SubElement(grid,'Attribute',Name=name,AttributeType='Scalar',Center='Node')
            ET.SubElement(attr,'DataItem',Dimensions=f'{nz} {ny} {nx}',NumberType='Float',Precision='4',Format='HDF').text=f'{rel}:/signals/{name}'
        ET.indent(root);ET.ElementTree(root).write(a.directory/f'D{D:03d}_focus_stack.xdmf',encoding='utf-8',xml_declaration=True)
if __name__=='__main__':main()

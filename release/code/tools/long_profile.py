#!/usr/bin/env python3
"""Write long-range axial/x-zeta diagnostic sections without a huge 3D cube."""
from pathlib import Path
import argparse,json,sys
import h5py,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import iscat_core as core
from run_dataset import decompose,dump,canonical_hash,implementation_hash,STATUS

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/target_Fe3O4_NA145.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    c=json.loads(a.config.read_text(encoding='utf-8'));op=core.optical_params(c);op['cs_over_cr']=1.
    if a.output.exists() and list(a.output.iterdir()):raise FileExistsError('Choose an empty diagnostic directory')
    a.output.mkdir(parents=True,exist_ok=True)
    z=np.arange(-3000.,3001.,10.);x=np.arange(-1200.,1201.,20.);r=np.unique(abs(x));gamma=complex(*c['model']['basis_scale_gamma'])
    p0=core.pupil_precompute(op,c['diameters_nm'][0],512,256);rr=core.make_radial_response(op,p0,0.,np.array([0.]),np.array([0.]));scale=abs(rr['er0'][0,0])
    for D in c['diameters_nm']:
        pp=core.pupil_precompute(op,D,512,256);rad=core.make_radial_response(op,pp,D/2,z,r)
        geo={'r':abs(x)[None,:],'sin2':np.zeros((1,len(x))),'cos2':np.ones((1,len(x)))};geo['cos2'][0,len(x)//2]=0
        columns=[]
        with h5py.File(a.output/f'D{D:03d}_long_xz.h5','w') as f:
            f.attrs.update(status=STATUS,config_sha256=canonical_hash(c),implementation_sha256=implementation_hash(),diameter_nm=D,NA=op['NA'],kind='long_range_diagnostic_only')
            f.create_dataset('zeta_nm',data=z);f.create_dataset('x_object_nm',data=x)
            datasets={key:f.create_dataset(key,shape=(len(z),len(x)),dtype='f8',compression='gzip') for key in ('I_ref','I_scat','I_cross','I_total','contrast_local','contrast_fixed_reference')}
            for i in range(len(z)):
                er,es=core.fields_at_slice(rad,i,r,geo);sig,*_=decompose(er/scale,es/scale,gamma)
                for name,v in sig.items():datasets[name][i]=v[0]
                columns.append([z[i]]+[sig[n][0,len(x)//2] for n in datasets])
        np.savetxt(a.output/f'D{D:03d}_axis.csv',columns,delimiter=',',header='zeta_nm,I_ref,I_scat,I_cross,I_total,contrast_local,contrast_fixed_reference',comments='')
    dump(a.output/'status.json',{'status':STATUS,'kind':'diagnostic_sections_not_final_3d','span_nm':[-3000,3000],'step_nm':10,'config_sha256':canonical_hash(c),'implementation_sha256':implementation_hash()})
if __name__=='__main__':main()

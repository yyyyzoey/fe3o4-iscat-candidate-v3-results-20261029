#!/usr/bin/env python3
"""Plot only saved HDF5 data; one plot per figure, shared scales across diameters."""
from pathlib import Path
import argparse,json
import h5py,numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a.output.mkdir(parents=True,exist_ok=True);cases=[]
    cfg=json.loads((a.directory/'config_used.json').read_text(encoding='utf-8'))
    for D in cfg['diameters_nm']:
        with h5py.File(a.directory/f'D{D:03d}nm/cube.h5','r') as f:
            x=f['coords/x_object_nm'][:];z=f['coords/zeta_nm'][:];mid=len(x)//2
            zi=[0,len(z)//2,len(z)-1]
            cases.append((D,x,z,[(i,f['signals/contrast_fixed_reference'][i]) for i in zi],f['signals/contrast_fixed_reference'][:,mid,:],f['signals/contrast_fixed_reference'][:,:,mid],f['signals/contrast_fixed_reference'][:,mid,mid]))
    vmax=max(float(np.max(abs(case[4]))) for case in cases);vmax=max(vmax,1e-12)
    for D,x,z,layers,xz,yz,axis in cases:
        data=[(f'z{z[i]:+06.0f}',image,[x[0],x[-1],x[0],x[-1]],'x (nm)','y (nm)') for i,image in layers]
        data += [('xz',xz,[x[0],x[-1],z[0],z[-1]],'x (nm)','zeta (nm, focus scan)'),('yz',yz,[x[0],x[-1],z[0],z[-1]],'y (nm)','zeta (nm, focus scan)')]
        for label,image,extent,xlabel,ylabel in data:
            fig=plt.figure(figsize=(6,5));ax=fig.add_subplot(111)
            im=ax.imshow(image,origin='lower',extent=extent,aspect='auto',interpolation='nearest',vmin=-vmax,vmax=vmax)
            ax.set(xlabel=xlabel,ylabel=ylabel,title=f'D={D} nm | {label} | CANDIDATE, uncalibrated')
            fig.colorbar(im,ax=ax,label='(I_s + I_cross) / shared I_ref,0');fig.tight_layout()
            fig.savefig(a.output/f'D{D:03d}_{label}.png',dpi=160);plt.close(fig)
    fig=plt.figure(figsize=(8,4));ax=fig.add_subplot(111)
    for D,x,z,_,_,_,axis in cases:ax.plot(z,axis,label=f'D={D} nm')
    ax.set(xlabel='zeta (nm, focus scan)',ylabel='Fixed-reference contrast',title='CANDIDATE | common normalization | no axial recentering');ax.legend();fig.tight_layout();fig.savefig(a.output/'axis_comparison.png',dpi=160);plt.close(fig)
    (a.output/'plot_metadata.json').write_text(json.dumps({'source':str(a.directory),'shared_limits':[-vmax,vmax],'signal':'contrast_fixed_reference','interpolation':'nearest','status':'CANDIDATE'},indent=2)+'\n')
if __name__=='__main__':main()

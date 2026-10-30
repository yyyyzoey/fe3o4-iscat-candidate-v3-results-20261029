#!/usr/bin/env python3
"""Transactional, resumable dataset generator for the explicitly CANDIDATE model.

This tool does NOT upgrade a calculation to a validated optical reproduction.
It stores a unit-scattering basis so uncertain relative complex gain is exposed.
All calculations are complex128/float64; only persisted arrays are float32.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
import h5py
import numpy as np
from iscat_core import (optical_params, pupil_precompute, make_radial_response,
                        fields_at_slice, axis_config)

SCHEMA='iscat-through-focus-v3.0'
STATUS='CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED'
ROOT=Path(__file__).resolve().parents[1]


def dump(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(temp,path)


def file_hash(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def implementation_hash():
    return canonical_hash({p.name:file_hash(p) for p in sorted((ROOT/'src').glob('*.py'))})


def make_axis(lo,hi,step):
    if not np.isfinite([lo,hi,step]).all() or step<=0 or hi<=lo:
        raise ValueError('Invalid finite increasing grid')
    n=(hi-lo)/step
    if not np.isclose(n,round(n),rtol=0,atol=1e-9):
        raise ValueError('Endpoints must lie on the requested grid')
    arr=np.linspace(lo,hi,int(round(n))+1)
    if len(arr)%2!=1 or not np.isclose(lo,-hi) or not np.isclose(arr[len(arr)//2],0):
        raise ValueError('Axes must be symmetric with an explicit zero center')
    return arr


def validate_config(c, pilot):
    op=optical_params(c)
    if not 0<op['NA']<min(op['ni'],op['ng']):raise ValueError('NA must lie below oil and glass index')
    if op['ns']<=0 or op['lam']<=0 or op['M']<=0:raise ValueError('Nonphysical optics')
    if c['material']['k_imag']<0:raise ValueError('Passive exp(-i wt) convention requires k>=0')
    D=np.asarray(c['diameters_nm'],float)
    if not (D>0).all() or len(np.unique(D))!=len(D):raise ValueError('Diameters must be positive and unique')
    for k in ('camera_sampling','background_stray_light','brownian_motion','magneto_optical_tensor','particle_interface_multiple_scattering'):
        if c['model'].get(k,False):raise ValueError(f'{k} is outside this model')
    if c['model']['n_particles_per_case']!=1:raise ValueError('Only one particle per case')
    g=c['grid_pilot' if pilot else 'grid_full']
    x=make_axis(g['xy_min_nm'],g['xy_max_nm'],g['xy_step_nm'])
    z=make_axis(g['zeta_min_nm'],g['zeta_max_nm'],g['zeta_step_nm'])
    gamma=np.asarray(c['model']['basis_scale_gamma'],float)
    if gamma.shape!=(2,) or not np.isfinite(gamma).all():raise ValueError('gamma must be [real,imag]')
    if c['model']['absolute_calibration']:raise ValueError('This candidate backend cannot claim absolute calibration')
    for key,value in {'float_dtype':'float32','complex_calculation':'complex128','intensity_calculation':'float64','compression':'gzip','compression_level':1,'chunk_z':1,'save_basis':True,'contrast_stable_Iref_fraction':0.005}.items():
        if c['storage'].get(key)!=value:raise ValueError(f'Unsupported storage option {key}: update implementation/tests before changing it')
    return op,g,x,z,complex(*gamma)


def decompose(er,es_unit,gamma):
    """Inputs are complex128. Q=conj(Er).Es_unit preserves phase."""
    ir=np.sum(np.abs(er)**2,axis=-1)
    is_unit=np.sum(np.abs(es_unit)**2,axis=-1)
    q=np.sum(np.conj(er)*es_unit,axis=-1)
    es=gamma*es_unit
    isc=abs(gamma)**2*is_unit
    cross=2*np.real(gamma*q)
    total=np.sum(np.abs(er+es)**2,axis=-1)
    valid=ir>1e-12
    stable=ir>=0.005
    contrast=np.full(ir.shape,np.nan,dtype=np.float64)
    np.divide(isc+cross,ir,out=contrast,where=valid)
    return {'I_ref':ir,'I_scat':isc,'I_cross':cross,'I_total':total,
            'contrast_local':contrast,'contrast_fixed_reference':isc+cross}, \
           {'I_scat_unit':is_unit,'Q_real':q.real,'Q_imag':q.imag},valid,stable


def alloc(f,path,shape,dtype='f4'):
    return f.create_dataset(path,shape=shape,dtype=dtype,chunks=(1,*shape[1:]),
                            compression='gzip',compression_opts=1,shuffle=True)


def validate_cube(path: Path, expected_cfg_sha=None, expected_code_sha=None):
    """Full, slice-streaming storage and algebra check; no claim of optical truth."""
    worst=0.;worst_c=0.;count_valid=0;count_stable=0
    with h5py.File(path,'r') as f:
        if f.attrs.get('schema')!=SCHEMA:raise ValueError('Wrong HDF5 schema')
        if expected_cfg_sha and f.attrs['config_sha256']!=expected_cfg_sha:raise ValueError('Config hash mismatch')
        if expected_code_sha and f.attrs['implementation_sha256']!=expected_code_sha:raise ValueError('Code hash mismatch')
        z=f['coords/zeta_nm'][:];x=f['coords/x_object_nm'][:];y=f['coords/y_object_nm'][:]
        shape=(len(z),len(y),len(x))
        saved_config=json.loads(f.attrs['configuration_json'])
        if canonical_hash(saved_config)!=f.attrs['config_sha256']:raise ValueError('Stored config was modified')
        mode=f.attrs['grid_mode']
        if mode not in ('pilot','full'):raise ValueError('Invalid grid mode')
        _,_,xx,zz,gg=validate_config(saved_config,mode=='pilot')
        np.testing.assert_array_equal(x,xx);np.testing.assert_array_equal(y,xx);np.testing.assert_array_equal(z,zz)
        D=float(f.attrs['diameter_nm'])
        if D not in saved_config['diameters_nm'] or not np.isclose(f.attrs['center_height_nm'],D/2) or f.attrs['surface_gap_nm']!=0:
            raise ValueError('Invalid surface-bound geometry')
        if f.attrs['NA']!=saved_config['optics']['NA'] or f.attrs['wavelength_nm']!=saved_config['optics']['wavelength_nm']:
            raise ValueError('Optical metadata mismatch')
        if complex(f.attrs['gamma_real'],f.attrs['gamma_imag'])!=gg:raise ValueError('Gamma mismatch')
        for group,names in {'signals':('I_ref','I_scat','I_cross','I_total','contrast_local','contrast_fixed_reference'),
                            'basis':('I_scat_unit','Q_real','Q_imag'),
                            'masks':('defined_contrast','stable_reference')}.items():
            for name in names:
                if f[group+'/'+name].shape!=shape:raise ValueError('Scalar/mask shape mismatch')
        if int(f.attrs.get('completed_slices',-1))!=len(z):raise ValueError('Incomplete file')
        for a in (z,x,y):
            if not np.all(np.diff(a)>0) or not np.isclose(a[0],-a[-1]) or not np.any(a==0):raise ValueError('Invalid coordinates')
        gamma=complex(f.attrs['gamma_real'],f.attrs['gamma_imag'])
        for name in ('E_ref_real','E_ref_imag','E_scat_unit_real','E_scat_unit_imag'):
            if f['fields/'+name].shape!=(*shape,2):raise ValueError('Field shape mismatch')
        for iz in range(len(z)):
            er=f['fields/E_ref_real'][iz].astype('f8')+1j*f['fields/E_ref_imag'][iz].astype('f8')
            es=f['fields/E_scat_unit_real'][iz].astype('f8')+1j*f['fields/E_scat_unit_imag'][iz].astype('f8')
            if not np.isfinite(er).all() or not np.isfinite(es).all():raise ValueError('Nonfinite complex field')
            sig,basis,valid,stable=decompose(er,es,gamma)
            stored_valid=f['masks/defined_contrast'][iz].astype(bool)
            # Threshold comparisons can differ by float32 roundoff only very close to cutoff.
            ir=sig['I_ref']; threshold=1e-12
            if np.any((stored_valid!=valid)&(np.abs(ir-threshold)>1e-6*threshold)):
                raise ValueError('Defined contrast mask is inconsistent')
            stored_stable=f['masks/stable_reference'][iz].astype(bool)
            if np.any((stored_stable!=stable)&(np.abs(ir-0.005)>1e-6*0.005)):
                raise ValueError('Stable reference mask is inconsistent')
            for name,data in sig.items():
                saved=f['signals/'+name][iz].astype('f8')
                if name=='contrast_local':
                    if not np.isnan(saved[~stored_valid]).all():raise ValueError('Undefined contrast must be NaN')
                    good=stored_valid&valid
                    err=float(np.max(np.abs(saved[good]-data[good])/(1+np.abs(data[good])))) if good.any() else 0.
                    worst_c=max(worst_c,err)
                else:
                    if not np.isfinite(saved).all():raise ValueError('Nonfinite non-contrast signal')
                    err=float(np.max(np.abs(saved-data))/max(1.,float(np.max(np.abs(data)))))
                    worst=max(worst,err)
            for name,data in basis.items():
                saved=f['basis/'+name][iz].astype('f8')
                if not np.isfinite(saved).all():raise ValueError('Nonfinite basis')
                worst=max(worst,float(np.max(np.abs(saved-data))/max(1.,float(np.max(np.abs(data))))))
            if np.min(f['signals/I_total'][iz])<0:raise ValueError('Negative directly calculated intensity')
            count_valid+=int(stored_valid.sum());count_stable+=int(f['masks/stable_reference'][iz].sum())
        if worst>1e-5 or worst_c>1e-4:raise ValueError(f'Storage/algebra tolerance failed {worst}, {worst_c}')
        return {'numerical_storage_pass':True,'shape':list(shape),'max_normalized_signal_error':worst,
                'max_normalized_local_contrast_error':worst_c,'defined_voxels':count_valid,'stable_voxels':count_stable,
                'total_voxels':int(np.prod(shape)),'physical_validation':'NOT_ESTABLISHED',
                'diameter_nm':float(f.attrs['diameter_nm']),'NA':float(f.attrs['NA'])}


def run(config: Path,output: Path,pilot: bool,resume: bool,accept_candidate: bool):
    if not accept_candidate:raise ValueError('Pass --accept-candidate-model only after reading the model limitations.')
    c=json.loads(config.read_text(encoding='utf-8'))
    op,g,x,z,gamma=validate_config(c,pilot)
    csha=canonical_hash(c);code_sha=implementation_hash()
    output.mkdir(parents=True,exist_ok=True)
    runid={'config_sha256':csha,'implementation_sha256':code_sha,'mode':'pilot' if pilot else 'full'}
    stamp=output/'run_identity.json'
    if stamp.exists():
        if not resume:raise FileExistsError('Output exists. Use a new directory or --resume with identical inputs.')
        if json.loads(stamp.read_text(encoding='utf-8'))!=runid:raise ValueError('Cannot resume across changed configuration/code/mode')
    else:
        if list(output.iterdir()):raise FileExistsError('Output directory is not empty and has no identity')
        dump(stamp,runid)
    # 4 field arrays with 2 components + 6 signals + 3 basis arrays + 2 masks.
    estimate=int(len(c['diameters_nm'])*len(z)*len(x)**2*70)
    free=shutil.disk_usage(output).free
    required=int(estimate*c['storage']['disk_safety_factor'])+c['storage']['reserve_disk_bytes']
    if not resume and free<required:raise OSError(f'Insufficient free disk: require {required} bytes; have {free}')
    dump(output/'config_used.json',c)
    op['cs_over_cr']=1.0 # the unit-scattering basis, actual gamma applied afterwards
    _,_,rrad,geo,_=axis_config(c,pilot)
    nbelow=int(g['quadrature_below_critical']);nabove=int(g['quadrature_above_critical'])
    p0=pupil_precompute(op,float(c['diameters_nm'][0]),nbelow,nabove)
    r0=make_radial_response(op,p0,0.,np.array([0.]),np.array([0.]))
    scale=float(abs(r0['er0'][0,0]))
    if scale<=1e-30 or not np.isfinite(scale):raise ValueError('Reference normalization is undefined')
    summary={'status':STATUS,**runid,'grid_shape':[len(z),len(x),len(x)],'calculation_precision':'complex128,float64',
             'stored_precision':'float32','expected_uncompressed_array_bytes':estimate,
             'reference_field_scale':scale,'absolute_calibration':False,'cases':{},
             'dataset_complete':False,
             'open_gates':['published_supplement_version','full_Jones_chain','supercritical_sector','relative_complex_amplitude'],
             'data_semantics':'through_focus_image_response_not_sample_space_near_field',
             'NA_requested':op['NA'],'NA_integrated':op['NA'],'created_utc':datetime.now(timezone.utc).isoformat()}
    for D in map(float,c['diameters_nm']):
        sub=output/f'D{int(D):03d}nm';sub.mkdir(exist_ok=True)
        final=sub/'cube.h5';partial=sub/'cube.part.h5'
        if final.exists():
            if not resume:raise FileExistsError(final)
            result=validate_cube(final,csha,code_sha)
            summary['cases'][str(int(D))]=result;dump(output/'run_summary.json',summary);continue
        pup=pupil_precompute(op,D,nbelow,nabove)
        radial=make_radial_response(op,pup,D/2,z,rrad)
        new=not partial.exists()
        if not new and not resume:raise FileExistsError(partial)
        with h5py.File(partial,'w' if new else 'r+') as f:
            shape=(len(z),len(x),len(x));fshape=(*shape,2)
            if new:
                f.attrs.update(schema=SCHEMA,status=STATUS,grid_mode='pilot' if pilot else 'full',config_sha256=csha,implementation_sha256=code_sha,
                               diameter_nm=D,particle_radius_nm=D/2,center_height_nm=D/2,surface_gap_nm=0.,
                               NA=op['NA'],wavelength_nm=op['lam'],material=c['material']['material_name'],
                               gamma_real=gamma.real,gamma_imag=gamma.imag,reference_field_scale=scale,
                               absolute_calibration=False,physical_validation='NOT_ESTABLISHED',
                               is_sample_space_field=False,completed_slices=0,
                               field_component_order='Ex,Ey',axis_order='zeta,y,x',
                               time_convention='exp(-i omega t)',
                               units='dimensionless field relative to shared on-axis reference; no V/m or W/m^2',
                               supercritical_sector='ANALYTIC_CONTINUATION_UNVALIDATED',
                               configuration_json=json.dumps(c,ensure_ascii=False))
                for name,arr in [('x_object_nm',x),('y_object_nm',x),('zeta_nm',z),('oil_thickness_nm',radial['oil_thickness_nm'])]:
                    ds=f.create_dataset('coords/'+name,data=arr);ds.attrs['units']='nm'
                for name in ('E_ref_real','E_ref_imag','E_scat_unit_real','E_scat_unit_imag'):alloc(f,'fields/'+name,fshape)
                for name in ('I_ref','I_scat','I_cross','I_total','contrast_local','contrast_fixed_reference'):alloc(f,'signals/'+name,shape)
                for name in ('I_scat_unit','Q_real','Q_imag'):alloc(f,'basis/'+name,shape)
                for name in ('defined_contrast','stable_reference'):alloc(f,'masks/'+name,shape,'u1')
            else:
                if f.attrs['config_sha256']!=csha or f.attrs['implementation_sha256']!=code_sha:raise ValueError('Partial file fingerprint mismatch')
            start=int(f.attrs['completed_slices'])
            print(f'D={D:g}nm; starting slice {start}/{len(z)}; candidate model',flush=True)
            for iz in range(start,len(z)):
                er,es=fields_at_slice(radial,iz,rrad,geo);er=er/scale;es=es/scale
                sig,basis,valid,stable=decompose(er,es,gamma)
                if not np.isfinite(er).all() or not np.isfinite(es).all():raise FloatingPointError('Nonfinite field')
                for name,arr in [('E_ref_real',er.real),('E_ref_imag',er.imag),('E_scat_unit_real',es.real),('E_scat_unit_imag',es.imag)]:
                    f['fields/'+name][iz]=arr.astype('f4')
                for name,arr in sig.items():f['signals/'+name][iz]=arr.astype('f4')
                for name,arr in basis.items():f['basis/'+name][iz]=arr.astype('f4')
                f['masks/defined_contrast'][iz]=valid.astype('u1');f['masks/stable_reference'][iz]=stable.astype('u1')
                f.flush();f.attrs.modify('completed_slices',iz+1);f.flush()
        result=validate_cube(partial,csha,code_sha)
        os.replace(partial,final)
        result['sha256']=file_hash(final);result['mie_size_parameter']=pup['mie_x']
        dump(sub/'validation.json',result)
        summary['cases'][str(int(D))]=result;dump(output/'run_summary.json',summary)
    summary['dataset_complete']=len(summary['cases'])==len(c['diameters_nm'])
    if implementation_hash()!=code_sha:raise RuntimeError('Source files changed during execution')
    dump(output/'run_summary.json',summary)
    lines=[]
    for p in sorted(output.rglob('*')):
        if p.is_file() and p.name!='sha256_manifest.txt' and not p.name.endswith('.tmp'):
            lines.append(f'{file_hash(p)}  {p.relative_to(output).as_posix()}')
    (output/'sha256_manifest.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=ROOT/'configs/target_Fe3O4_NA145.json')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pilot',action='store_true');p.add_argument('--resume',action='store_true')
    p.add_argument('--accept-candidate-model',action='store_true')
    a=p.parse_args()
    try:run(a.config,a.output,a.pilot,a.resume,a.accept_candidate_model)
    except Exception as exc:
        a.output.mkdir(parents=True,exist_ok=True)
        dump(a.output/'error.json',{'status':'FAILED','error_type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
        raise

if __name__=='__main__':main()

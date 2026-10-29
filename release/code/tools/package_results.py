#!/usr/bin/env python3
"""Create a result bundle only after full target files and review records exist."""
import argparse,json,shutil,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from run_dataset import validate_cube,file_hash,canonical_hash,dump,implementation_hash
REQUIRED=('status.json','review.md','source_audit.md','formula_audit.md','tests.json','convergence.json','environment.txt','commands.log')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);p.add_argument('--review-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--zip',dest='zip_path',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.zip_path.exists():raise FileExistsError('Use new release and ZIP paths; never overwrite a release')
    for name in REQUIRED:
        if not (a.review_dir/name).is_file():raise FileNotFoundError('Missing final review artifact: '+name)
    c=json.loads((a.data/'config_used.json').read_text(encoding='utf-8'))
    if c['diameters_nm']!=[30,100,200] or c['optics']['NA']!=1.45:raise ValueError('This is not the target dataset')
    status=json.loads((a.review_dir/'status.json').read_text(encoding='utf-8'))
    if status.get('data_generation')!='COMPLETE':raise ValueError('Use a separate PARTIAL package for incomplete tasks')
    if status.get('absolute_calibration') is not False:raise ValueError('Candidate backend does not establish absolute calibration')
    actual={}
    for D in c['diameters_nm']:
        result=validate_cube(a.data/f'D{D:03d}nm/cube.h5',canonical_hash(c),implementation_hash())
        if result['shape']!=[171,241,241]:raise ValueError('Pilot or wrong grid cannot be packaged as full')
        actual[str(D)]=result['shape']
    if status.get('actual_shapes')!=actual:raise ValueError('Review actual_shapes does not match files')
    a.output.mkdir(parents=True)
    for name in REQUIRED:shutil.copy2(a.review_dir/name,a.output/name)
    for name in ('config_used.json','run_identity.json','run_summary.json'):shutil.copy2(a.data/name,a.output/name)
    for D in c['diameters_nm']:shutil.copytree(a.data/f'D{D:03d}nm',a.output/f'D{D:03d}nm')
    for pth in a.data.glob('*.xdmf'):shutil.copy2(pth,a.output/pth.name)
    if (a.review_dir/'figures').is_dir():shutil.copytree(a.review_dir/'figures',a.output/'figures')
    if (a.review_dir/'diagnostics').is_dir():shutil.copytree(a.review_dir/'diagnostics',a.output/'diagnostics')
    for sub in ('src','tools','configs','tests','docs'):shutil.copytree(ROOT/sub,a.output/'code'/sub,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    lines=[f'{file_hash(pth)}  {pth.relative_to(a.output).as_posix()}' for pth in sorted(a.output.rglob('*')) if pth.is_file()]
    (a.output/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    a.zip_path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
        for pth in sorted(a.output.rglob('*')):
            if pth.is_file():z.write(pth,Path(a.output.name)/pth.relative_to(a.output))
    checksum=file_hash(a.zip_path);a.zip_path.with_suffix(a.zip_path.suffix+'.sha256').write_text(f'{checksum}  {a.zip_path.name}\n')
    print(json.dumps({'zip':str(a.zip_path),'sha256':checksum,'actual_shapes':actual},indent=2))
if __name__=='__main__':main()

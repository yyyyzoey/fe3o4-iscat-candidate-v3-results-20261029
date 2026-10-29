#!/usr/bin/env python3
"""Validate all stored cubes against their saved config and input manifest."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from run_dataset import validate_cube,canonical_hash,file_hash,dump

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    config=json.loads((a.directory/'config_used.json').read_text(encoding='utf-8'));stamp=json.loads((a.directory/'run_identity.json').read_text(encoding='utf-8'))
    reports={}
    for D in config['diameters_nm']:
        path=a.directory/f'D{D:03d}nm/cube.h5'
        reports[str(D)]=validate_cube(path,canonical_hash(config),stamp['implementation_sha256'])
    mf=a.directory/'sha256_manifest.txt'
    for line in mf.read_text(encoding='utf-8').splitlines():
        h,rel=line.split('  ',1)
        if file_hash(a.directory/rel)!=h:raise ValueError(f'Checksum mismatch: {rel}')
    output={'data_checks_pass':True,'cases':reports,'physical_validation':'NOT_ESTABLISHED_BY_THIS_TOOL'}
    if a.out:dump(a.out,output)
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

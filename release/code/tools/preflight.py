#!/usr/bin/env python3
"""Offline, non-mutating package/environment check; does not run a simulation."""
from pathlib import Path
import argparse,hashlib,importlib,json,platform,shutil,sys
ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-manifest',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    if sys.version_info<(3,10):raise RuntimeError('Python 3.10+ is required; tested lock may require 3.11+')
    versions={}
    for name in ('numpy','scipy','h5py','matplotlib','mpmath'):
        m=importlib.import_module(name);versions[name]=m.__version__
    c=json.loads((ROOT/'configs/target_Fe3O4_NA145.json').read_text(encoding='utf-8'))
    assert c['diameters_nm']==[30,100,200] and c['optics']['NA']==1.45 and c['optics']['wavelength_nm']==532
    checks=[]
    if a.verify_manifest:
        for line in (ROOT/'HANDOFF_SHA256.txt').read_text(encoding='utf-8').splitlines():
            expected,rel=line.split('  ',1);path=ROOT/rel
            if not path.is_file() or sha(path)!=expected:raise RuntimeError('Package checksum mismatch: '+rel)
            checks.append(rel)
    report={'offline_preflight_pass':True,'python':sys.version,'platform':platform.platform(),'versions':versions,
            'free_disk_bytes':shutil.disk_usage(ROOT).free,'files_hash_verified':len(checks),
            'note':'This verifies packaging/environment only. Published-model fidelity is not established.'}
    if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

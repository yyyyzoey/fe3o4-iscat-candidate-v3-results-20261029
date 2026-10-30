#!/usr/bin/env python3
"""Reproduce the two identified legacy convention issues without editing legacy."""
import argparse,importlib.util,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import iscat_core as candidate
from run_dataset import dump,file_hash

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'results/legacy_audit.json');a=p.parse_args()
    path=ROOT/'legacy/src/run_iscat.py';spec=importlib.util.spec_from_file_location('archived_legacy',path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    s1,s2=old.mie_S1_S2(np.array([-1.]),np.array([1.+0j]),np.array([0.+0j]))
    rad={'er0':np.array([[0,0]],complex),'er2':np.array([[2,2]],complex),'es0':np.array([[0,0]],complex),'es2':np.array([[3,3]],complex)}
    geo={'r':np.array([[.5]]),'sin2':np.array([[.8]]),'cos2':np.array([[.6]])}
    aold,bold=old.fields_at_slice(rad,0,np.array([0.,1.]),geo);anew,bnew=candidate.fields_at_slice(rad,0,np.array([0.,1.]),geo)
    report={'legacy_sha256':file_hash(path),'dipole_backward':{'S1_real':float(s1[0].real),'S2_real':float(s2[0].real),'old_combination_real':float((s1+s2)[0].real),'returning_p_basis_combination_real':float((s1-s2)[0].real)},'detector_Ex_sign':{'old_Ex_real':float(aold[0,0,0].real),'candidate_Ex_real':float(anew[0,0,0].real)},'interpretation':'Observed algebraic differences; returning-p repair still requires full Jones-chain validation.'}
    dump(a.out,report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()

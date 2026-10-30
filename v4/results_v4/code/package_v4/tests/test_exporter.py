"""Tool-level tests only; synthetic arrays below are NOT optical simulations."""
import sys, tempfile, unittest
from pathlib import Path
import h5py
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from export_paper_views import axis_check, inspect


def fixture(path, break_intensity=False):
    a=np.array([-2.,0.,2.]);shape=(3,3,3)
    er=np.zeros((*shape,2),complex);er[...,1]=1
    eu=np.zeros_like(er);eu[...,1]=np.linspace(-.2,.4,27).reshape(shape)+.03j
    es=.5*eu
    ir=np.sum(abs(er)**2,axis=-1);isc=np.sum(abs(es)**2,axis=-1)
    cross=2*np.real(np.sum(np.conj(er)*es,axis=-1))
    sig={'I_ref':ir,'I_scat':isc,'I_cross':cross,
         'I_total':np.sum(abs(er+es)**2,axis=-1),'contrast_fixed_reference':isc+cross}
    if break_intensity:sig['I_total'][0,0,0]+=.5
    with h5py.File(path,'w') as f:
        f.attrs.update(diameter_nm=30,center_height_nm=15,surface_gap_nm=0,
                       NA=1.45,wavelength_nm=532,material='Fe3O4',axis_order='zeta,y,x',
                       is_sample_space_field=False,completed_slices=3,
                       gamma_real=.5,gamma_imag=0,reference_field_scale=1,
                       status='SYNTHETIC_UNIT_TEST_NOT_SIMULATION',grid_mode='pilot')
        for n in ('x_object_nm','y_object_nm','zeta_nm'):f.create_dataset('coords/'+n,data=a)
        for n,v in sig.items():f.create_dataset('signals/'+n,data=v.astype('f4'))
        for n,v in [('E_ref_real',er.real),('E_ref_imag',er.imag),
                    ('E_scat_unit_real',eu.real),('E_scat_unit_imag',eu.imag)]:
            f.create_dataset('fields/'+n,data=v.astype('f4'))

class Tests(unittest.TestCase):
    def test_axis(self):axis_check(np.array([-2.,0.,2.]),'z')
    def test_axis_not_centered(self):
        with self.assertRaises(ValueError):axis_check(np.array([0.,1.,2.]),'z')
    def test_axis_not_uniform(self):
        with self.assertRaises(ValueError):axis_check(np.array([-2.,0.,1.,2.]),'z')
    def test_saved_algebra(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cube.h5';fixture(p);r=inspect(p,30,True)
            self.assertTrue(r['data_algebra_pass']);self.assertFalse(r['optical_model_verified_by_this_tool'])
            self.assertLess(r['min']['I_cross'],0)
            self.assertEqual(r['gamma'],[.5,0.])
    def test_corrupt_signal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cube.h5';fixture(p,True)
            with self.assertRaises(ValueError):inspect(p,30,True)
    def test_pilot_not_final(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cube.h5';fixture(p)
            with self.assertRaises(AssertionError):inspect(p,30,False)
    def test_diameter_not_radius(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cube.h5';fixture(p)
            with h5py.File(p,'a') as f:f.attrs['diameter_nm']=15
            with self.assertRaises(ValueError):inspect(p,30,True)
    def test_gamma_positive_shape_invariance(self):
        q=np.array([1+.3j,-.4+.7j,.2-.1j]);j=2*np.real(q)
        for g in (.1,.5,2.):np.testing.assert_allclose(g*j/max(abs(g*j)),j/max(abs(j)))
    def test_gamma_phase_not_cancelled(self):
        q=np.array([1+.3j,-.4+.7j,.2-.1j]);a=2*np.real(q);b=2*np.real(1j*q)
        self.assertFalse(np.allclose(a/max(abs(a)),b/max(abs(b))))

if __name__=='__main__':unittest.main(verbosity=2)

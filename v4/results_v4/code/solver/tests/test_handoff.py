"""Independent algebraic/numerical tests. These do not certify the published model."""
from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import mpmath as mp
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import iscat_core as core
import run_dataset as ds
CFG=ROOT/'configs/target_Fe3O4_NA145.json'

class CoreChecks(unittest.TestCase):
    def setUp(self):
        self.c=json.loads(CFG.read_text(encoding='utf-8'));self.op=core.optical_params(self.c);self.op['cs_over_cr']=1.

    def test_target_parameters_locked(self):
        self.assertEqual(self.c['diameters_nm'],[30,100,200]);self.assertEqual(self.op['NA'],1.45)
        self.assertEqual(self.op['lam'],532);self.assertEqual(self.c['material']['material_name'],'Fe3O4')
        x,z,*_=core.axis_config(self.c,False);self.assertEqual((len(z),len(x)),(171,241))
        np.testing.assert_allclose(z, np.arange(-170,171,2));np.testing.assert_allclose(x,np.arange(-1200,1201,10))

    def test_material_interpolation(self):
        a=np.loadtxt(ROOT/'sources/Fe3O4_Querry_bracket.csv',delimiter=',',skiprows=1)
        self.assertAlmostEqual(np.interp(.532,a[:,0],a[:,1]),2.3456)
        self.assertAlmostEqual(np.interp(.532,a[:,0],a[:,2]),.0926)

    def test_fresnel_normal(self):
        rs,rp,ts,tp,*_=core.fresnel_glass_sample(np.array([0.]),self.op)
        for r in (rs,rp):np.testing.assert_allclose(r,(1.52-1.33)/(1.52+1.33),atol=1e-14)
        for t in (ts,tp):np.testing.assert_allclose(t,2*1.33/(1.52+1.33),atol=1e-14)

    def test_fresnel_s_power_conservation_below_critical(self):
        u=np.linspace(0,1.30,41);rs,_,ts,_,ks,kg=core.fresnel_glass_sample(u,self.op)
        # transmission is sample -> glass; reverse reflection sign does not change |r|^2
        np.testing.assert_allclose(abs(rs)**2+(kg/ks).real*abs(ts)**2,1,atol=1e-12)

    def test_zero_scattering_matched_index(self):
        for x in (.236,.785,1.571):
            a,b=core.mie_coefficients(x,1.+0j);self.assertLess(max(abs(a).max(),abs(b).max()),1e-12)

    def test_mie_rayleigh_amplitude_phase(self):
        m=complex(1.8,.07);x=.001;a,_=core.mie_coefficients(x,m)
        expected=-1j*2/3*(m*m-1)/(m*m+2)*x**3
        self.assertLess(abs(a[0]/expected-1),1e-6)

    def test_mie_passivity_and_lossless(self):
        for m in (1.59/1.33,complex(2.3456,.0926)/1.33):
            for x in (.236,.785,1.571):
                a,b=core.mie_coefficients(x,m);n=np.arange(1,len(a)+1)
                qs=2/x**2*np.sum((2*n+1)*(abs(a)**2+abs(b)**2))
                qe=2/x**2*np.sum((2*n+1)*np.real(a+b))
                self.assertGreaterEqual(qe-qs,-1e-11)
                if np.imag(m)==0:self.assertLess(abs(qe-qs),1e-11)

    def test_mie_high_precision_cylindrical_bessel_oracle(self):
        mp.mp.dps=60
        def psi(n,z):return mp.sqrt(mp.pi*z/2)*mp.besselj(n+mp.mpf('.5'),z)
        def xi(n,z):return mp.sqrt(mp.pi*z/2)*(mp.besselj(n+mp.mpf('.5'),z)+1j*mp.bessely(n+mp.mpf('.5'),z))
        for x in (.236,.785,1.571):
            m=complex(2.3456,.0926)/1.33;a,b=core.mie_coefficients(x,m)
            for n in range(1,5):
                xx=mp.mpf(x);mm=mp.mpc(m);px=psi(n,xx);pm=psi(n,mm*xx)
                dpx=mp.diff(lambda z:psi(n,z),xx);dpm=mp.diff(lambda z:psi(n,z),mm*xx)
                xxh=xi(n,xx);dxh=mp.diff(lambda z:xi(n,z),xx)
                aa=(mm*pm*dpx-px*dpm)/(mm*pm*dxh-xxh*dpm)
                bb=(pm*dpx-mm*px*dpm)/(pm*dxh-mm*xxh*dpm)
                np.testing.assert_allclose(a[n-1],complex(aa),rtol=1e-8,atol=1e-14)
                np.testing.assert_allclose(b[n-1],complex(bb),rtol=1e-8,atol=1e-14)

    def test_mie_angular_legendre_polynomial_oracle(self):
        from numpy.polynomial.legendre import Legendre
        mu=np.array([-.99,-.5,0,.3,.97,1.2j],complex)
        rng=np.random.default_rng(427);a=rng.normal(size=8)+1j*rng.normal(size=8);b=a[::-1]*.3
        e1=np.zeros_like(mu);e2=e1.copy()
        for n in range(1,9):
            p=Legendre.basis(n);pi=p.deriv(1)(mu);tau=mu*pi-(1-mu*mu)*p.deriv(2)(mu)
            f=(2*n+1)/(n*(n+1));e1+=f*(a[n-1]*pi+b[n-1]*tau);e2+=f*(a[n-1]*tau+b[n-1]*pi)
        s1,s2=core.mie_S1_S2(mu,a,b)
        np.testing.assert_allclose(s1,e1,rtol=1e-11,atol=1e-10);np.testing.assert_allclose(s2,e2,rtol=1e-11,atol=1e-10)

    def test_backscatter_returning_p_basis(self):
        # Analytic electric dipole: S1=3a1/2, S2=-3a1/2 at theta=pi.
        # Original Mie e_theta points opposite the returning-ray transverse p.
        s1,s2=core.mie_S1_S2(np.array([-1.]),np.array([1.+0j]),np.array([0.+0j]))
        np.testing.assert_allclose(s1+s2,0,atol=1e-14)
        np.testing.assert_allclose(s1-s2,3,atol=1e-14)
        phi=.37;etheta=np.array([-np.cos(phi),-np.sin(phi)])
        ephi=np.array([-np.sin(phi),np.cos(phi)])
        direct=np.exp(1j*phi)*(s2[0]*etheta+1j*s1[0]*ephi)
        np.testing.assert_allclose(direct,1.5*np.array([1.,1j]),atol=1e-14)

    def test_pupil_candidate_uses_returning_p_basis(self):
        p=core.pupil_precompute(self.op,100,64,32)
        a,b=core.mie_coefficients(p['mie_x'],self.op['nparticle']/self.op['ns'])
        s1,s2=core.mie_S1_S2(-p['kzs']/self.op['ns'],a,b)
        _,_,ts,tp,*_=core.fresnel_glass_sample(p['u'],self.op)
        np.testing.assert_allclose(p['scat_strength'],.5j*(s1*ts-s2*tp),rtol=1e-13,atol=1e-14)

    def test_azimuthal_direct_integral_sign(self):
        # Independent direct phi integration of S2/S6 transverse vector;
        # minus in pupil Ex becomes PLUS after the J2 Fourier integral.
        phi=np.arange(8192)*2*np.pi/8192;q=2.7;phid=.31;c=.92
        e=np.exp(1j*q*np.cos(phi-phid))
        v=np.stack((-(1-c)*np.sin(2*phi),(1+c)+(1-c)*np.cos(2*phi)),axis=-1)
        num=np.mean(v*e[:,None],axis=0)
        from scipy.special import jv
        exact=np.array([(1-c)*jv(2,q)*np.sin(2*phid),(1+c)*jv(0,q)-(1-c)*jv(2,q)*np.cos(2*phid)])
        np.testing.assert_allclose(num,exact,atol=1e-13)

    def test_reduced_RW_against_direct_phi(self):
        p=core.pupil_precompute(self.op,100,80,40);xx,yy=93.,127.;r=np.hypot(xx,yy);phid=np.arctan2(yy,xx)
        z=np.array([-80.,0.,130.]);rad=core.make_radial_response(self.op,p,50,z,np.array([0.,r]))
        phi=np.arange(4096)*2*np.pi/4096;cd=p['cos_td'][:,None]
        e=np.exp(1j*2*np.pi/self.op['lam']*p['u'][:,None]*r*np.cos(phi[None,:]-phid))
        vx=-(1-cd)*np.sin(2*phi)[None,:];vy=(1+cd)+(1-cd)*np.cos(2*phi)[None,:]
        av=np.stack((np.mean(vx*e,axis=1),np.mean(vy*e,axis=1)),axis=-1)
        ref,scat,_=core.axial_opd_nm(self.op,p,50,z)
        for kind,opd in [('er',ref[:,None]),('es',scat)]:
            strength=p['ref_strength' if kind=='er' else 'scat_strength']
            numerical=(np.exp(1j*2*np.pi/self.op['lam']*opd)*p['common'][None,:]*strength[None,:])@av
            reduced=np.stack((rad[kind+'2'][:,1]*np.sin(2*phid),rad[kind+'0'][:,1]-rad[kind+'2'][:,1]*np.cos(2*phid)),axis=-1)
            np.testing.assert_allclose(numerical,reduced,rtol=1e-8,atol=1e-18)

    def test_branch_passive_decay(self):
        p=core.pupil_precompute(self.op,100,64,64);mask=p['u']>self.op['ns']
        self.assertTrue(mask.any());self.assertTrue((p['kzs'][mask].imag>0).all())
        a=np.exp(1j*2*np.pi/self.op['lam']*p['kzs'][mask]*20)
        b=np.exp(1j*2*np.pi/self.op['lam']*p['kzs'][mask]*100)
        self.assertTrue((np.abs(b)<np.abs(a)).all())
        self.assertAlmostEqual(float(p['wu'].sum()),1.45,places=13)

    def test_homogeneous_OPD_identity(self):
        op=dict(self.op);op.update(ns=1.52,ng=1.52,ni=1.52,nig=1.52,ngg=1.52,NA=1.3)
        p=core.pupil_precompute(op,100,64,0);z=np.array([-170.,0.,170.]);zp=50
        ref,scat,oil=core.axial_opd_nm(op,p,zp,z)
        np.testing.assert_allclose(oil,op['tig']-z-zp,atol=1e-10)
        np.testing.assert_allclose(ref,-2*1.52*(z+zp),atol=1e-9)
        np.testing.assert_allclose(scat,-z[:,None]*(p['kz_i'][None,:]+1.52),atol=1e-9)

    def test_reference_magnitude_scan_invariant(self):
        p=core.pupil_precompute(self.op,100,64,32);z=np.array([-170.,0.,170.])
        rad=core.make_radial_response(self.op,p,50,z,np.array([0.,100.]))
        np.testing.assert_allclose(abs(rad['er0']),np.broadcast_to(abs(rad['er0'][0]),rad['er0'].shape),atol=1e-17)

    def test_complex_amplitude_basis_identity(self):
        rng=np.random.default_rng(7);er=rng.normal(size=(4,5,2))+1j*rng.normal(size=(4,5,2));es=er*.1+(rng.normal(size=er.shape)+1j*rng.normal(size=er.shape))*.03
        for gamma in [0,1,.5,1j,.3-.2j]:
            s,b,_,_=ds.decompose(er,es,gamma)
            np.testing.assert_allclose(s['I_total'],s['I_ref']+s['I_scat']+s['I_cross'],atol=1e-13)
            np.testing.assert_allclose(s['I_cross'],2*(complex(gamma).real*b['Q_real']-complex(gamma).imag*b['Q_imag']),atol=1e-13)

    def test_phase_flip_only_cross_changes(self):
        er=np.ones((2,2,2),complex)*(1+.5j);es=np.ones_like(er)*(.3-.1j)
        s,*_=ds.decompose(er,es,.5);t,*_=ds.decompose(-er,es,.5)
        np.testing.assert_allclose(s['I_cross'],-t['I_cross']);np.testing.assert_allclose(s['I_scat'],t['I_scat'])

    def test_reference_null_mask(self):
        er=np.zeros((2,2,2),complex);es=np.ones_like(er)
        s,b,valid,stable=ds.decompose(er,es,1)
        self.assertFalse(valid.any());self.assertFalse(stable.any());self.assertTrue(np.isnan(s['contrast_local']).all())
        self.assertTrue(np.isfinite(s['I_total']).all());self.assertTrue(np.isfinite(s['contrast_fixed_reference']).all())

    def test_axis_rejects_invalid_endpoints(self):
        with self.assertRaises(ValueError):ds.make_axis(-170,170,3)
        with self.assertRaises(ValueError):ds.make_axis(-170,160,10)

class IOChecks(unittest.TestCase):
    def test_tiny_roundtrip_resume_and_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);c=json.loads(CFG.read_text(encoding='utf-8'))
            c['diameters_nm']=[30]
            c['grid_pilot'].update(xy_min_nm=-40,xy_max_nm=40,xy_step_nm=20,zeta_min_nm=-10,zeta_max_nm=10,zeta_step_nm=10,radial_points=81,quadrature_below_critical=32,quadrature_above_critical=16)
            cfg=p/'config.json';cfg.write_text(json.dumps(c),encoding='utf-8');out=p/'out'
            with self.assertRaises(ValueError):ds.run(cfg,out,True,False,False)
            r=ds.run(cfg,out,True,False,True);self.assertTrue(r['cases']['30']['numerical_storage_pass'])
            ds.run(cfg,out,True,True,True)
            with self.assertRaises(FileExistsError):ds.run(cfg,out,True,False,True)
            c['optics']['NA']=1.44;cfg.write_text(json.dumps(c),encoding='utf-8')
            with self.assertRaises(ValueError):ds.run(cfg,out,True,True,True)

if __name__=='__main__':unittest.main()

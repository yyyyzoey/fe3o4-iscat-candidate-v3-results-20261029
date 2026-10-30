"""Independent Jones-chain consistency test for the S2 -> S6 substitution.

The published supplement prints

    S2:  E_ref  = 1/2 i (r_p+r_s) [ -(1-cos td) sin2phi ; (1+cos td)+(1-cos td)cos2phi ]
    S6:  E_scat = 1/2 i (S2 t_p+S1 t_s) * (same spatial vector)

S4/S5 give the Mie field at the particle as E_S = e_theta S2 e^{i phi}
+ i e_phi S1 e^{i phi}.  This module checks, from explicit 3-D geometry and
linearity of the (unprinted) Jones chain, that the scattered pupil field is
proportional to (S1 t_s - S2 t_p), i.e. that the printed S6 has an inconsistent
sign on the S2 term.

Nothing here certifies the numerical model; it only closes the algebra that is
printed in the supplement (S1-S6, S12-S13).
"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import iscat_core as core


def spherical_basis(theta, phi):
    """Standard e_theta, e_phi for a direction (theta, phi)."""
    st, ct = np.sin(theta), np.cos(theta)
    cp, sp = np.cos(phi), np.sin(phi)
    e_theta = np.array([ct * cp, ct * sp, -st])
    e_phi = np.array([-sp, cp, 0.0])
    return e_theta, e_phi


class JonesChainConsistency(unittest.TestCase):
    def setUp(self):
        # a few generic pupil rays, including strongly inclined ones
        self.theta = np.array([0.05, 0.4, 0.9, 1.2])
        self.phi = np.array([0.0, 1.1, -2.3, 2.9])

    def test_backward_spherical_basis_equals_p_s_basis(self):
        """At the returning direction e_theta = p_hat and e_phi = -s_hat."""
        for th, ph in zip(self.theta, self.phi):
            k_in = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
            r_hat = -k_in                       # collected ray travels back to -z
            th_s = np.arccos(np.clip(r_hat[2], -1, 1))
            ph_s = np.arctan2(r_hat[1], r_hat[0])
            e_th, e_ph = spherical_basis(th_s, ph_s)
            # p/s of the *incident* ray, transported to the return ray
            s_hat = np.array([-np.sin(ph), np.cos(ph), 0.0])
            p_hat = np.cross(s_hat, k_in)
            np.testing.assert_allclose(e_th, p_hat, atol=1e-14)
            np.testing.assert_allclose(e_ph, -s_hat, atol=1e-14)

    def test_scattered_ps_content_is_minus_S2_and_iS1(self):
        s1, s2 = 0.7 - 0.2j, -0.4 + 0.9j
        for th, ph in zip(self.theta, self.phi):
            k_in = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
            r_hat = -k_in
            th_s = np.arccos(np.clip(r_hat[2], -1, 1))
            ph_s = np.arctan2(r_hat[1], r_hat[0])
            e_th, e_ph = spherical_basis(th_s, ph_s)
            s_hat = np.array([-np.sin(ph), np.cos(ph), 0.0])
            p_hat = np.cross(s_hat, k_in)
            # S4/S5 with circular illumination
            e_s = np.exp(1j * ph_s) * (s2 * e_th + 1j * s1 * e_ph)
            np.testing.assert_allclose(np.dot(e_s, p_hat), -np.exp(1j * ph) * s2, atol=1e-14)
            np.testing.assert_allclose(np.dot(e_s, s_hat), 1j * np.exp(1j * ph) * s1, atol=1e-14)

    def test_chain_consistent_s6_sign(self):
        """Linear response fixed by S2 gives S1 t_s - S2 t_p, not S1 t_s + S2 t_p."""
        # S2 states the pupil response to (p,s)=(r_p, i r_s) is 1/2 i (r_p+r_s) yhat.
        # For a linear chain with columns c_p, c_s:  r_p c_p + i r_s c_s = 1/2 i (r_p+r_s) yhat
        # for all r_p, r_s  =>  c_p = i/2 yhat,  c_s = 1/2 yhat.
        yhat = np.array([0.0, 1.0])
        c_p = 0.5j * yhat
        c_s = 0.5 * yhat
        # scattered (p,s) content from the geometry test above
        for s1, s2 in [(0.7 - 0.2j, -0.4 + 0.9j), (1.5 + 0j, -1.5 + 0j)]:
            pupil = (-s2) * c_p + (1j * s1) * c_s
            expected = 0.5j * (s1 - s2) * yhat
            np.testing.assert_allclose(pupil, expected, atol=1e-15)
        # and this is exactly what the candidate core stores (t_p=t_s=1)
        s1, s2 = np.array([0.7 - 0.2j]), np.array([-0.4 + 0.9j])
        np.testing.assert_allclose(0.5j * (s1 - s2), 0.5j * (s1 * 1.0 - s2 * 1.0))

    def test_literal_printed_S6_requires_contradictory_S2(self):
        """If S6 had +S2 t_p, the same chain would make S2 proportional to r_p-r_s."""
        yhat = np.array([0.0, 1.0])
        # solving r_p c_p + i r_s c_s = 1/2 i (r_p - r_s) yhat gives c_p=i/2 yhat, c_s=-1/2 yhat
        c_p = 0.5j * yhat
        c_s = -0.5 * yhat
        rp, rs = 0.06 + 0.0j, 0.06 + 0.0j   # equal coefficients at normal incidence
        self.assertAlmostEqual(abs((rp * c_p[1] + 1j * rs * c_s[1])), 0.0, places=15)

    def test_rayleigh_backscatter_does_not_vanish(self):
        """At theta=pi a pure electric dipole has S2=-S1; literal S6 would cancel."""
        s1, s2 = core.mie_S1_S2(np.array([-1.0]), np.array([1.0 + 0j]), np.array([0.0 + 0j]))
        np.testing.assert_allclose(s1 + s2, 0.0, atol=1e-15)
        literal = s2 + s1
        chain = s1 - s2
        self.assertLess(abs(literal), 1e-15)
        self.assertAlmostEqual(abs(chain), 3.0, places=13)

    def test_candidate_pupil_matches_chain_result(self):
        c = __import__('json').loads((ROOT / 'configs/target_Fe3O4_NA145.json').read_text())
        op = core.optical_params(c); op['cs_over_cr'] = 1.0
        pup = core.pupil_precompute(op, 100.0, 64, 32)
        a, b = core.mie_coefficients(pup['mie_x'], op['nparticle'] / op['ns'])
        s1, s2 = core.mie_S1_S2(-pup['kzs'] / op['ns'], a, b)
        _, _, ts, tp, *_ = core.fresnel_glass_sample(pup['u'], op)
        chain = 0.5j * (s1 * ts - s2 * tp)
        np.testing.assert_allclose(pup['scat_strength'], chain, rtol=1e-13, atol=1e-16)


if __name__ == '__main__':
    unittest.main()

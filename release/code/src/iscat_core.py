#!/usr/bin/env python3
"""CANDIDATE research core, not a certified replication.

Derived from the supplied legacy implementation. Two explicit convention repairs:
(1) positive J2 sin(2 phi) in detector Ex (supplement S12/S13);
(2) returning-ray p basis reverses the Mie e_theta coefficient for backward
    scattering. The full published Jones chain STILL REQUIRES independent audit.
NA>n_sample analytic continuation and relative field normalization remain open.
No camera, no Brownian motion, no free particle-height scan.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import jv, spherical_jn, spherical_yn


def _complex_sqrt_positive_imag(value: np.ndarray) -> np.ndarray:
    """Choose k_z with Im(k_z)>=0 for exp(+i k_z z), exp(-i omega t)."""
    root = np.sqrt(np.asarray(value, dtype=np.complex128))
    return np.where(root.imag < 0, -root, root)


def mie_coefficients(x: float, m: complex, nmax: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Complex-index, nonmagnetic, homogeneous sphere; outgoing Hankel(1)."""
    if not (np.isfinite(x) and x > 0):
        raise ValueError("Mie size parameter x must be positive")
    nmax = max(5, int(np.ceil(x + 4*x**(1/3) + 2)) + 3) if nmax is None else int(nmax)
    if nmax < 1:
        raise ValueError("nmax must be >=1")
    n = np.arange(1, nmax + 1)
    mx = m*x
    psi_x = x*spherical_jn(n, x)
    psi_mx = mx*spherical_jn(n, mx)
    dpsi_x = spherical_jn(n, x) + x*spherical_jn(n, x, derivative=True)
    dpsi_mx = spherical_jn(n, mx) + mx*spherical_jn(n, mx, derivative=True)
    xi_x = x*(spherical_jn(n, x) + 1j*spherical_yn(n, x))
    dxi_x = (spherical_jn(n, x) + 1j*spherical_yn(n, x) +
             x*(spherical_jn(n, x, derivative=True) +
                1j*spherical_yn(n, x, derivative=True)))
    a = (m*psi_mx*dpsi_x - psi_x*dpsi_mx) / (m*psi_mx*dxi_x - xi_x*dpsi_mx)
    b = (psi_mx*dpsi_x - m*psi_x*dpsi_mx) / (psi_mx*dxi_x - m*xi_x*dpsi_mx)
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise FloatingPointError("Non-finite Mie coefficients")
    return a, b


def mie_S1_S2(mu: np.ndarray, a: np.ndarray, b: np.ndarray):
    """Vectorized Mie angular amplitudes via pi_n/tau_n recurrence.

    mu = cos(scattering angle), may be complex in analytic continuation.
    """
    mu = np.asarray(mu, dtype=np.complex128)
    pi_nm2 = np.zeros_like(mu)
    pi_nm1 = np.ones_like(mu)
    s1 = np.zeros_like(mu)
    s2 = np.zeros_like(mu)
    for n in range(1, len(a)+1):
        if n == 1:
            pi_n = pi_nm1
        else:
            pi_n = ((2*n-1)/(n-1))*mu*pi_nm1 - (n/(n-1))*pi_nm2
        tau_n = n*mu*pi_n - (n+1)*pi_nm1 if n > 1 else mu
        f = (2*n+1)/(n*(n+1))
        s1 += f*(a[n-1]*pi_n + b[n-1]*tau_n)
        s2 += f*(a[n-1]*tau_n + b[n-1]*pi_n)
        if n > 1:
            pi_nm2, pi_nm1 = pi_nm1, pi_n
    return s1, s2


def quadrature_u(NA: float, ns: float, ni: float, below: int, above: int):
    """Gauss-Legendre pupil integration in u=n_i*sin(theta), branch-split at u=ns."""
    if NA <= 0 or NA >= ni:
        raise ValueError("NA must be 0 < NA < n_immersion for this model")
    limits = [(0., min(ns, NA), below)]
    if NA > ns:
        if above <= 0:
            raise ValueError("Need supercritical quadrature points for NA > ns")
        limits.append((ns, NA, above))
    points, weights = [], []
    for left, right, n in limits:
        if right <= left:
            continue
        q, w = leggauss(n)
        points.append((q+1)*(right-left)/2+left)
        weights.append(w*(right-left)/2)
    return np.concatenate(points), np.concatenate(weights)


def optical_params(config: dict):
    op = config['optics']
    m = config['material']
    p = complex(m['n_real'], m['k_imag'])
    return dict(lam=float(op['wavelength_nm']),
                ns=float(op['n_sample']), ng=float(op['n_glass']),
                ni=float(op['n_immersion']), na=float(op['n_detector']),
                nig=float(op['n_immersion_design']),
                ngg=float(op['n_glass_design']),
                tg=float(op['glass_thickness_nm']),
                tgg=float(op['glass_thickness_design_nm']),
                tig=float(op['immersion_thickness_design_nm']),
                M=float(op['magnification']), NA=float(op['NA']),
                nparticle=p)


def fresnel_glass_sample(u: np.ndarray, op: dict):
    """Glass->sample reflection; sample->glass transmission, consistent
    tangential amplitude sign convention for r_p+r_s at normal incidence.
    The supercritical branch is analytically continued (not rigorous near field).
    """
    ns, ng = op['ns'], op['ng']
    kz_g = _complex_sqrt_positive_imag(ng**2-u**2)
    kz_s = _complex_sqrt_positive_imag(ns**2-u**2)
    rs = (kz_g-kz_s)/(kz_g+kz_s)
    rp = (ng**2*kz_s-ns**2*kz_g)/(ng**2*kz_s+ns**2*kz_g)
    ts = 2*kz_s/(kz_s+kz_g)
    tp = 2*ns*ng*kz_s/(ng**2*kz_s+ns**2*kz_g)
    return rs, rp, ts, tp, kz_s, kz_g


def pupil_precompute(op: dict, D_nm: float, n_below: int, n_above: int):
    """Mie+Fresnel pupil strengths and high-NA apodization."""
    u, wu = quadrature_u(op['NA'], op['ns'], op['ni'], n_below, n_above)
    rs, rp, ts, tp, kzs, kzg = fresnel_glass_sample(u, op)
    cos_ti = np.sqrt(1-(u/op['ni'])**2)
    cos_td = np.sqrt(1-(u/(op['M']*op['na']))**2)
    apod = np.sqrt(op['ni']*cos_td/(op['na']*cos_ti))
    x = 2*np.pi*op['ns']*(D_nm/2)/op['lam']
    a, b = mie_coefficients(x, op['nparticle']/op['ns'])
    # Illumination propagates from glass to sample (+z), collected backward (-z).
    # Complex mu is a *model choice*; paper does not validate this for u>ns.
    mu_back = -kzs/op['ns']
    S1, S2 = mie_S1_S2(mu_back, a, b)
    eta = np.arcsin(min(op['NA']/op['ns'], 1.0))/np.pi
    cr, cs = 1., op.get('cs_over_cr', eta)
    ref_strength = 0.5j*cr*(rp+rs)
    # Candidate convention repair: global Mie backward theta and returning p
    # basis have opposite e_theta. This is NOT a proof of the full Jones chain.
    # S2_return=-S2_Mie, S1_return=S1_Mie; see docs/FORMULA_AUDIT.md.
    scat_strength = 0.5j*cs*(-S2*tp + S1*ts)
    # Equations S11-S13 with u=n_i sin(theta),
    # sin(2theta)dtheta=2u/n_i^2 du: common -i k0/M^2.
    pref = (-1j*(2*np.pi/op['lam'])/op['M']**2)
    common = pref*wu*u*apod
    return dict(u=u, wu=wu, kzs=kzs, kzg=kzg,
                kz_i=_complex_sqrt_positive_imag(op['ni']**2-u**2),
                kz_id=_complex_sqrt_positive_imag(op['nig']**2-u**2),
                kz_gd=_complex_sqrt_positive_imag(op['ngg']**2-u**2),
                cos_td=cos_td, ref_strength=ref_strength,
                scat_strength=scat_strength, common=common,
                mie_x=float(x), mie_order=int(len(a)), eta=float(eta))


def axial_opd_nm(op: dict, pup: dict, zp_nm: float, zeta_nm: np.ndarray):
    """Original Eqs. (7)-(10) of Zambochova et al.; reference and scatter OPD."""
    zeta_nm = np.atleast_1d(zeta_nm).astype(float)
    ti = op['ni']*(-zeta_nm/op['ni'] + op['tgg']/op['ngg'] -
                   op['tg']/op['ng'] + op['tig']/op['nig'] - zp_nm/op['ns'])
    if np.any(ti <= 0):
        raise ValueError('Scan position results in nonpositive immersion thickness')
    ref = 2*(op['ni']*ti-op['nig']*op['tig']+op['ng']*op['tg']-op['ngg']*op['tgg'])
    Lam = (zp_nm*pup['kzs'][None, :] + ti[:, None]*pup['kz_i'][None, :] -
           op['tig']*pup['kz_id'][None, :] + op['tg']*pup['kzg'][None, :] -
           op['tgg']*pup['kz_gd'][None, :])
    scat = Lam + zp_nm*op['ns'] + (op['ni']*ti-op['nig']*op['tig']+
                                   op['ng']*op['tg']-op['ngg']*op['tgg'])[:, None]
    return ref, scat, ti


def make_radial_response(op: dict, pup: dict, zp_nm: float,
                         zeta_nm: np.ndarray, r_nm: np.ndarray):
    """Precompute 4 radial Hankel integrals (reference/scatter x J0/J2).
    Return z-by-r complex radial field coefficients A0, A2.
    """
    k0 = 2*np.pi/op['lam']
    ref_opd, scat_opd, ti = axial_opd_nm(op, pup, zp_nm, zeta_nm)
    # q=k0*u*r_object; equivalent to detector radius M*r_object.
    q = k0*np.outer(pup['u'], r_nm)
    J0 = jv(0, q)
    J2 = jv(2, q)
    wref = (np.exp(1j*k0*ref_opd[:, None]) *
            pup['common'][None, :]*pup['ref_strength'][None, :])
    wscat = (np.exp(1j*k0*scat_opd) *
             pup['common'][None, :]*pup['scat_strength'][None, :])
    cplus = 1+pup['cos_td']
    cminus = 1-pup['cos_td']
    er0 = (wref*cplus[None, :]) @ J0
    er2 = (wref*cminus[None, :]) @ J2
    es0 = (wscat*cplus[None, :]) @ J0
    es2 = (wscat*cminus[None, :]) @ J2
    return dict(er0=er0, er2=er2, es0=es0, es2=es2, oil_thickness_nm=ti)


def _interp_complex(grid: np.ndarray, vals: np.ndarray, radii: np.ndarray):
    real = np.interp(radii, grid, vals.real)
    imag = np.interp(radii, grid, vals.imag)
    return real+1j*imag


def fields_at_slice(rad: dict, idx: int, r_grid: np.ndarray, geo: dict):
    """Supplement S12-S13: E_x=+A2 sin2phi, E_y=A0-A2 cos2phi."""
    exr2 = _interp_complex(r_grid, rad['er2'][idx], geo['r'])
    eyr0 = _interp_complex(r_grid, rad['er0'][idx], geo['r'])
    exs2 = _interp_complex(r_grid, rad['es2'][idx], geo['r'])
    eys0 = _interp_complex(r_grid, rad['es0'][idx], geo['r'])
    ref = np.stack([exr2*geo['sin2'], eyr0-exr2*geo['cos2']], axis=-1)
    scat = np.stack([exs2*geo['sin2'], eys0-exs2*geo['cos2']], axis=-1)
    return ref, scat


def axis_config(config: dict, pilot: bool):
    g = config['grid_pilot'] if pilot else config['grid_full']
    xs = np.arange(g['xy_min_nm'], g['xy_max_nm']+g['xy_step_nm']/2,
                   g['xy_step_nm'], dtype=float)
    zeta = np.arange(g['zeta_min_nm'], g['zeta_max_nm']+g['zeta_step_nm']/2,
                     g['zeta_step_nm'], dtype=float)
    if not (np.isclose(xs[0], -xs[-1]) and np.isclose(zeta[0], -zeta[-1])
            and np.any(np.isclose(zeta, 0))):
        raise ValueError('Grid must be symmetric and include zeta=0')
    rmax = np.hypot(abs(xs).max(),abs(xs).max())
    rrad = np.linspace(0., rmax*1.001, g['radial_points'])
    X, Y = np.meshgrid(xs, xs, indexing='xy')
    r2 = X*X+Y*Y
    safe = np.where(r2 > 0, r2, 1)
    geo = dict(r=np.sqrt(r2), sin2=2*X*Y/safe,
               cos2=(X*X-Y*Y)/safe)
    geo['sin2'][r2==0] = 0
    geo['cos2'][r2==0] = 0
    return xs,zeta,rrad,geo,g



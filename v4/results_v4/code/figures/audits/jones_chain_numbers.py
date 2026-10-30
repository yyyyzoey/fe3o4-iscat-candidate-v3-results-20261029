#!/usr/bin/env python3
"""Direct matrix/number check for the S2 -> S6 substitution.

For a few explicit pupil rays this records, in one table:
  * the standard backward-scattering Mie amplitudes S1, S2 (mu = -kz/ns);
  * the Fresnel transmission coefficients t_p, t_s at the same ray;
  * the p/s content obtained by projecting the 3-D Mie field of S4/S5 onto the
    returning-ray (p_hat, s_hat) basis;
  * the two candidate scalars  i(S2 t_p + S1 t_s)  [printed S6]  and
    i(S1 t_s - S2 t_p)  [what the S2 reference-field chain implies];
  * the ratio between the candidate core value and each scalar.
Writes validation/jones_chain_numbers.json.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

RES = Path(__file__).resolve().parents[3]
ROOT = RES.parent
sys.path.insert(0, str(RESULT_ROOT / "code" / "solver" / "src"))
import iscat_core as core

cfg = json.loads((RESULT_ROOT / "code" / "solver" / "configs" / "target_Fe3O4_NA145.json").read_text())
op = core.optical_params(cfg)
op["cs_over_cr"] = 1.0
lam, ns, NA = op["lam"], op["ns"], op["NA"]

D = 100.0
x = np.pi * ns * D / lam
a, b = core.mie_coefficients(x, op["nparticle"] / ns)

rows = []
# theta is the *incident* polar angle inside the sample; the collected ray returns along -k_in
for theta_deg, phi_deg in [(0.0, 0.0), (30.0, 0.0), (30.0, 65.0), (60.0, -40.0), (75.0, 120.0)]:
    th = np.deg2rad(theta_deg); ph = np.deg2rad(phi_deg)
    u = ns * np.sin(th)
    k_in = np.array([np.sin(th)*np.cos(ph), np.sin(th)*np.sin(ph), np.cos(th)])
    r_hat = -k_in                                  # returning ray direction
    th_s = np.arccos(np.clip(r_hat[2], -1, 1))
    ph_s = np.arctan2(r_hat[1], r_hat[0])
    e_th = np.array([np.cos(th_s)*np.cos(ph_s), np.cos(th_s)*np.sin(ph_s), -np.sin(th_s)])
    e_ph = np.array([-np.sin(ph_s), np.cos(ph_s), 0.0])
    s_hat = np.array([-np.sin(ph), np.cos(ph), 0.0])
    p_hat = np.cross(s_hat, k_in)
    kzs = core._complex_sqrt_positive_imag(ns**2 - u**2)
    mu = -kzs / ns
    S1, S2 = core.mie_S1_S2(np.array([mu]), a, b)
    S1, S2 = complex(S1[0]), complex(S2[0])
    _, _, ts, tp, *_ = core.fresnel_glass_sample(np.array([u]), op)
    ts, tp = complex(ts[0]), complex(tp[0])
    # S4/S5 field at the particle for circular illumination, expressed in the return basis
    e_s = np.exp(1j*ph_s) * (S2*e_th + 1j*S1*e_ph)
    a_p = complex(np.dot(e_s, p_hat))   # p content
    a_s = complex(np.dot(e_s, s_hat))   # s content
    printed = 1j * (S2*tp + S1*ts)
    chain = 1j * (S1*ts - S2*tp)
    # the core stores scat_strength = 0.5j*(-S2*tp + S1*ts)
    core_val = 0.5j * (-S2*tp + S1*ts)
    rows.append({
        "theta_deg": theta_deg, "phi_deg": phi_deg, "u": u, "mu_back": [mu.real, mu.imag],
        "S1": [S1.real, S1.imag], "S2": [S2.real, S2.imag],
        "t_p": [tp.real, tp.imag], "t_s": [ts.real, ts.imag],
        "ps_content_from_3d_projection": {"p": [a_p.real, a_p.imag], "s": [a_s.real, a_s.imag]},
        "minus_S2_over_S2_expect_a_p": [(-S2).real, (-S2).imag],
        "iS1_expect_a_s": [(1j*S1).real, (1j*S1).imag],
        "printed_S6_i_S2tp_plus_S1ts": [printed.real, printed.imag],
        "chain_i_S1ts_minus_S2tp": [chain.real, chain.imag],
        "core_scat_strength": [core_val.real, core_val.imag],
        "core_over_printed": [float(np.real(core_val/printed)), float(np.imag(core_val/printed))],
        "core_over_chain": [float(np.real(core_val/chain)), float(np.imag(core_val/chain))],
    })

# pure electric dipole backscatter: literal S6 cancels, chain does not
s1d, s2d = core.mie_S1_S2(np.array([-1.0+0j]), np.array([1.0+0j]), np.array([0.0+0j]))
dipole = {"S1": float(np.real(s1d[0])), "S2": float(np.real(s2d[0])),
          "printed_sum_abs": float(abs(s2d[0] + s1d[0])),
          "chain_abs": float(abs(s1d[0] - s2d[0]))}

rep = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
       "case": {"material": "Fe3O4", "diameter_nm": D, "wavelength_nm": lam,
                "n_sample": ns, "NA": NA, "mie_size_parameter": x},
       "convention": "theta measured from +z for the incoming ray; the collected ray travels along -k_in; "
                     "mu_back = -kz_s/n_s; exp(-i omega t)",
       "rows": rows, "pure_electric_dipole_backscatter": dipole,
       "reading": "core_over_chain == [0.5, 0.5] would mean the stored value equals 0.5*i*(S1 t_s - S2 t_p) "
                  "up to the -i global prefactor convention; core_over_printed shows the printed S6 differs.",
       "certification": "algebra only; does NOT certify the full optical chain or the physics"}
out = RESULT_ROOT / "validation" / "jones_chain_numbers.json"
out.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
for r in rows:
    print(f"theta={r['theta_deg']:5.1f} phi={r['phi_deg']:6.1f} "
          f"S1={r['S1'][0]:+.4f}{r['S1'][1]:+.4f}j S2={r['S2'][0]:+.4f}{r['S2'][1]:+.4f}j "
          f"printed={r['printed_S6_i_S2tp_plus_S1ts'][0]:+.4e}{r['printed_S6_i_S2tp_plus_S1ts'][1]:+.4e}j "
          f"chain={r['chain_i_S1ts_minus_S2tp'][0]:+.4e}{r['chain_i_S1ts_minus_S2tp'][1]:+.4e}j "
          f"core/chain={r['core_over_chain']}")
print("dipole:", dipole)
print("->", out)

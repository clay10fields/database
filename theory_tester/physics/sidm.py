"""Gravothermal evolution of a self-interacting halo: the parametric model of Yang et al. 2023
(JCAP 02, 032; arXiv:2305.16176), calibrated on N-body SIDM simulations covering core formation
AND core collapse. Coefficients are copied from eq. (2.4) of the paper's LaTeX (cached e-print).

Given the halo's collisionless (CDM/NFW) parameters, an effective cross-section and the time the
halo has been evolving, it returns the present (rho_s, r_s, r_c) of the profile
    rho(r) = rho_s / [ (r^4 + r_c^4)^(1/4) / r_s * (1 + r/r_s)^2 ].
tau = t / t_c < ~0.2: core grows (lower central density). tau -> 1: core collapse (higher density).
"""
from __future__ import annotations

import numpy as np

from physics.halos import G, nfw_vmax_rmax

CM2G_TO_KPC2_MSUN = 1.98847e33 / (3.08568e21) ** 2      # 1 cm^2/g in kpc^2/Msun
KMS_KPC_TO_INV_GYR = 1.02271
C_CAL = 0.75
LN1E3 = np.log(0.001)


def collapse_time_gyr(sigma_m, rhos, rs):
    """t_c = 150/C / (sigma/m rho_s r_s) / sqrt(4 pi G rho_s)   [Yang+2023 eq. 2.3]"""
    s = np.maximum(sigma_m, 1e-12) * CM2G_TO_KPC2_MSUN
    return 150.0 / C_CAL / (s * rhos * rs) / (np.sqrt(4 * np.pi * G * rhos) * KMS_KPC_TO_INV_GYR)


def evolve(rhos0, rs0, tau):
    tau = np.clip(tau, 0.0, 1.0)     # Yang+2023 truncate deeply collapsed halos at tau = 1
    lt = np.log(tau + 0.001) / LN1E3
    rhos = rhos0 * (2.033 + 0.7381 * tau + 7.264 * tau ** 5 - 12.73 * tau ** 7 + 9.915 * tau ** 9 + (1 - 2.033) * lt)
    rs = rs0 * (0.7178 - 0.1026 * tau + 0.2474 * tau ** 2 - 0.4079 * tau ** 3 + (1 - 0.7178) * lt)
    rc = rs0 * (2.555 * np.sqrt(tau) - 3.632 * tau + 2.131 * tau ** 2 - 1.415 * tau ** 3 + 0.4683 * tau ** 4)
    return rhos, rs, np.maximum(rc, 1e-6 * rs0)


def formation_lookback_gyr(M):
    """Halo formation redshift (Correa+2015 as used by Yang+2023 eq. 3.1) -> lookback time (eq. 3.2)."""
    x = np.log10(M / 1e10)
    zf = -0.0064 * x ** 2 - 0.1043 * x + 1.4807
    return 13.647 - 11.020 * np.log(1.5800 / (1 + zf) ** 1.5 + np.sqrt(1 + 2.4965 / (1 + zf) ** 3))


def nu_eff(rhos0, rs0):
    vmax, _ = nfw_vmax_rmax(rhos0, rs0)
    return 0.64 * vmax


def sidm_profile(rhos0, rs0, M200, sigma_eff_m, t_age=None):
    t = formation_lookback_gyr(M200) if t_age is None else t_age
    if sigma_eff_m <= 0:
        return rhos0, rs0, 1e-6 * rs0, 0.0
    tau = t / collapse_time_gyr(sigma_eff_m, rhos0, rs0)
    rhos, rs, rc = evolve(rhos0, rs0, tau)
    return rhos, rs, rc, float(min(tau, 1.0))

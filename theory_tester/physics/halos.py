"""Dark-matter halo profiles and rotation-curve pieces (kpc, km/s, Msun)."""
from __future__ import annotations

import numpy as np
from scipy.special import i0, i1, k0, k1

G = 4.30091e-6          # kpc (km/s)^2 / Msun
H0_REF = 67.4           # km/s/Mpc used for halo definitions (Planck 2018)
RHO_CRIT = 3 * (H0_REF / 1000) ** 2 / (8 * np.pi * G)   # Msun/kpc^3 (H in km/s/kpc)


def m_nfw_shape(x):
    return np.log1p(x) - x / (1 + x)


def nfw_from_m200(M200, c):
    """(rho_s [Msun/kpc^3], r_s [kpc], R200 [kpc]) for 200x critical."""
    R200 = (3 * M200 / (4 * np.pi * 200 * RHO_CRIT)) ** (1 / 3)
    rs = R200 / c
    rhos = M200 / (4 * np.pi * rs ** 3 * m_nfw_shape(c))
    return rhos, rs, R200


def c200_dutton_maccio(M200):
    """Dutton & Maccio 2014 (Planck cosmology, z=0, 200c): log10 c = 0.905 - 0.101 log10(M200 h / 1e12); scatter 0.11 dex."""
    h = H0_REF / 100
    return 10 ** (0.905 - 0.101 * np.log10(M200 * h / 1e12))


C_SCATTER_DEX = 0.11


def nfw_vmax_rmax(rhos, rs):
    rmax = 2.1626 * rs
    vmax = 1.648 * rs * np.sqrt(G * rhos)
    return vmax, rmax


def v_nfw(r, rhos, rs):
    return np.sqrt(4 * np.pi * G * rhos * rs ** 3 * m_nfw_shape(r / rs) / r)


# --------------------------------------------------------------------- cored (SIDM) profile of Yang+2023
_BETA = 4.0
_XGRID = np.logspace(-5, 3, 1600)        # r / r_s grid for the dimensionless mass integral


def _mass_table(rc_over_rs: float):
    x = _XGRID
    q = rc_over_rs
    dens = 1.0 / ((x ** _BETA + q ** _BETA) ** (1 / _BETA) * (1 + x) ** 2)
    integrand = dens * x ** 3     # d m / d ln x  (times 4 pi rho_s r_s^3)
    lnx = np.log(x)
    m = np.concatenate([[dens[0] * x[0] ** 3 / 3], np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(lnx))])
    m[1:] += m[0]
    return m


def m_cored(r, rhos, rs, rc):
    m = _mass_table(rc / rs)
    return 4 * np.pi * rhos * rs ** 3 * np.interp(np.log(r / rs), np.log(_XGRID), m)


def rho_cored(r, rhos, rs, rc):
    return rhos / ((r ** _BETA + rc ** _BETA) ** (1 / _BETA) / rs * (1 + r / rs) ** 2)


def v_cored(r, rhos, rs, rc):
    return np.sqrt(G * m_cored(r, rhos, rs, rc) / r)


# --------------------------------------------------------------------- discs and point masses
def v_exp_disc(r, Mdisc, Rd):
    """Razor-thin exponential disc (Freeman 1970)."""
    y = np.maximum(r / (2 * Rd), 1e-6)
    sigma0 = Mdisc / (2 * np.pi * Rd ** 2)
    return np.sqrt(np.maximum(4 * np.pi * G * sigma0 * Rd * y ** 2 * (i0(y) * k0(y) - i1(y) * k1(y)), 0.0))


def v_point(r, M):
    return np.sqrt(G * M / r)

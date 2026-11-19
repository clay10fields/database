"""Reproduction check of arXiv:2610.26877 (Oct 2026), 'Revisiting self-interacting dark matter with DESI DR2
BAO observations'.

What the paper actually fits (read from its LaTeX, cached): the whole cosmic fluid obeys
    drho/dt + 3 H rho + kappa rho^2 - Psi = 0,   Psi = C1 (n+3) a^n H + kappa C1^2 a^(2n),
kappa = <sigma v>/M_chi an ANNIHILATION parameter, Psi a particle-CREATION rate. Three cases:
    SIDM1: n = 0, kappa != 0      SIDM2: n != 0, kappa = 0  (=> rho = C1 a^n + a^-3/C2, i.e. wCDM, w = -1 - n/3)
    SIDM3: n != 0, kappa != 0
Data in the paper: DESI DR2 BAO with r_d free + Pantheon+ (+ cosmic chronometers, not reproduced here: H0 does
not affect n or kappa once r_d and the SN magnitude are free).

Their headline numbers (DESI+Pantheon+): SIDM2 n = -0.55 +- 0.12 (w = -0.82 +- 0.04), Omega_2 = 0.295 +- 0.010;
SIDM1 log10(kappa C1 / Gyr^-1) best -4.36 (upper limit -3.93), Omega_2 = 0.312 +- 0.008.

Important for Clayten's hypothesis: this 'SIDM' is an annihilation/creation fluid, not velocity-dependent
elastic scattering through a light mediator. Its only cosmological signature is a modified expansion history,
which for SIDM2 is literally constant-w dark energy. We reproduce it and then add the Planck priors.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from fit.cosmo_fit import CosmoModel
from physics.cosmology import Background, OMEGA_R, omega_nu, growth_smooth_fast

H_FIXED = 0.68       # degenerate with r_d (BAO) and M (SN); any value gives the same chi^2
GYR_H0 = 0.1022712   # H0 in 1/Gyr per unit h

PAPER = {"SIDM2_n": (-0.55, 0.12), "SIDM2_w": (-0.82, 0.04), "SIDM2_Om2": (0.295, 0.010),
         "SIDM1_logkC1_best": -4.36, "SIDM1_logkC1_ul": -3.93, "SIDM1_Om2": (0.312, 0.008),
         "SIDM3_n": (-0.74, None), "source": "arXiv:2610.26877, Sect. 3 (DESI+Pantheon+)"}


def _E2_fluid(Om2, n, logkC1, zmax=2.6):
    """Solve the paper's Boltzmann equation for x = rho/rho_c0 backwards from a = 1 (x = 1)."""
    Om1 = 1 - Om2
    kC1 = 10 ** logkC1 if logkC1 is not None else 0.0
    H0 = H_FIXED * GYR_H0
    if kC1 == 0.0:
        return lambda a: Om1 * a ** n + Om2 * a ** -3

    def rhs(lna, x):
        a = np.exp(lna)
        xx = max(x[0], 1e-12)
        H = H0 * np.sqrt(xx)
        psi = Om1 * (n + 3) * a ** n * H + kC1 * Om1 * a ** (2 * n)
        return [-3 * xx - ((kC1 / Om1) * xx ** 2 - psi) / H]
    lna = np.linspace(0, -np.log(1 + zmax), 400)
    sol = solve_ivp(rhs, [0, lna[-1]], [1.0], t_eval=lna, rtol=1e-8, atol=1e-10)
    if not sol.success or np.any(~np.isfinite(sol.y[0])) or np.any(sol.y[0] <= 0):
        return None
    la, xs = lna[::-1], sol.y[0][::-1]
    return lambda a: np.interp(np.log(a), la, xs)


def _bg_from_E2(E2):
    """Wrap the paper's E^2(a) (valid for z < 2.6, all the data) as a Background. Above z = 2.6 it is continued
    as matter-like only so that distance integrals are well defined; no datum used here reaches that range."""
    h = H_FIXED
    a_lo = 1 / 3.6
    rest = lambda a: OMEGA_R * a ** -4 + omega_nu(a) + 1e-12 * a ** -3

    def dark(a):
        a = np.asarray(a, float)
        inside = h ** 2 * E2(np.clip(a, a_lo, 1.0)) - rest(a)
        edge = h ** 2 * E2(a_lo) - rest(a_lo)
        return np.where(a >= a_lo, inside, edge * (a / a_lo) ** -3)
    return Background(h=h, omega_b=1e-12, dark=dark, omega_m_early=0.3 * h ** 2)


def model(kind: str) -> CosmoModel:
    if kind == "LCDM":
        names, bounds, start = ["Omega_2", "r_d"], [(0.2, 0.45), (120, 170)], [0.3, 147]
        bgf = lambda p: _bg_from_E2(_E2_fluid(p[0], 0.0, None))
    elif kind == "SIDM1":
        names, bounds, start = ["Omega_2", "log10_kC1", "r_d"], [(0.2, 0.45), (-7, -1.5), (120, 170)], [0.3, -5, 147]
        bgf = lambda p: (lambda E2: None if E2 is None else _bg_from_E2(E2))(_E2_fluid(p[0], 0.0, p[1]))
    elif kind == "SIDM2":
        names, bounds, start = ["Omega_2", "n", "r_d"], [(0.2, 0.45), (-1.5, 1.0), (120, 170)], [0.3, -0.5, 147]
        bgf = lambda p: _bg_from_E2(_E2_fluid(p[0], p[1], None))
    elif kind == "SIDM3":
        names, bounds, start = (["Omega_2", "n", "log10_kC1", "r_d"], [(0.1, 0.45), (-1.5, 1.0), (-7, -1.0), (120, 170)],
                                [0.28, -0.6, -3, 147])
        bgf = lambda p: (lambda E2: None if E2 is None else _bg_from_E2(E2))(_E2_fluid(p[0], p[1], p[2]))
    else:
        raise ValueError(kind)
    return CosmoModel("2610-" + kind, f"arXiv:2610.26877 {kind}", names, bounds, start, bgf, rd_free=True)


def wcdm_with_planck() -> CosmoModel:
    """SIDM2 is wCDM; with Planck distance priors the early universe must be physical: baryons + CDM + radiation,
    the a^n part acting as dark energy with w = -1 - n/3."""
    def bg(p):
        h, wb, wc, w = p
        wde = h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc
        return Background(h=h, omega_b=wb, dark=lambda a: wc * a ** -3 + wde * a ** (-3 * (1 + w)), omega_m_early=wb + wc)
    return CosmoModel("2610-SIDM2+Planck", "SIDM2 (= wCDM) with Planck priors", ["h", "omega_b", "omega_c", "w"],
                      [(0.5, 0.85), (0.015, 0.03), (0.05, 0.2), (-1.6, -0.4)], [0.67, 0.0224, 0.12, -0.9], bg,
                      growth=lambda p, b, z: growth_smooth_fast(b, lambda a: (p[1] + p[2]) * a ** -3 + omega_nu(a), z))

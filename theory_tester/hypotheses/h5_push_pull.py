"""Hypothesis 5 (Clayten): push-pull unification — one dark substance that pulls where dense and pushes where
spread out. Three concrete versions are tested:

 (a) Generalised Chaplygin gas (GCG; Kamenshchik+2001, Bento+2002): p = -A / rho^alpha.
     rho(a) = rho0 [A_s + (1 - A_s) a^(-3(1+alpha))]^(1/(1+alpha)). Behaves like matter early (pull) and like a
     cosmological constant late (push). alpha = 0 is exactly Lambda-CDM. Its sound speed c_s^2 = -alpha w is the
     known weak spot: alpha > 0 makes perturbations oscillate (no structure), alpha < 0 makes them blow up.
     Growth is solved with the unified-fluid perturbation equations (physics/cosmology.growth_unified_fluid).
 (b) Farnes (2018) negative-mass fluid, as written in that paper: a constant-density (continuously created)
     negative-mass component rho_- < 0 in place of both dark matter and Lambda, which forces an open universe
     (k = -1; Farnes eq. 26-28). Also run with the sign left free, to see what sign the data want.
     Galaxies: a spherical negative-mass halo can only subtract from the inward pull inside it (shell theorem),
     which the SPARC fit tests directly.
 (c) Environment-dependent push: the dark-energy density is a volume-weighted mix of a void value and a
     crowded-region value, rho_DE = rho_void F_v(a) + rho_crowd (1 - F_v(a)), with the void volume fraction
     growing with structure, F_v(a) = F_v0 D(a)/D(1), F_v0 = 0.6. This gives rho_DE(a) = rho_DE0[1 + beta(D(a)-1)]
     with beta = F_v0(r-1)/(1+F_v0(r-1)), r = rho_void/rho_crowd. Dark matter stays as the 'pull' (CDM).
"""
from __future__ import annotations

import numpy as np

from fit.cosmo_fit import CosmoModel
from fit.galaxies import fit_one, baryon_v2
from physics.cosmology import Background, OMEGA_R, omega_nu, growth_smooth_fast, growth_unified_fluid
from physics.halos import G, m_nfw_shape

ID = "H5"
NAME = "Push-pull unification (Chaplygin / negative mass / environment)"


# ------------------------------------------------------------------ (a) GCG
def gcg_rho(a, wg, As, alpha):
    return wg * (As + (1 - As) * a ** (-3 * (1 + alpha))) ** (1 / (1 + alpha))


def gcg_background(p):
    h, wb, As, alpha = p
    wg = h ** 2 - OMEGA_R - wb - omega_nu(1.0)
    if wg <= 0:
        return None
    return Background(h=h, omega_b=wb, dark=lambda a: gcg_rho(a, wg, As, alpha),
                      omega_m_early=wb + wg * (1 - As) ** (1 / (1 + alpha)), label="GCG")


def gcg_growth(p, bg, z, k_hmpc=0.1):
    h, wb, As, alpha = p
    wg = h ** 2 - OMEGA_R - wb - omega_nu(1.0)
    w_fn = lambda a: -As / (As + (1 - As) * a ** (-3 * (1 + alpha)))
    cs2 = lambda a: -alpha * w_fn(a)
    return growth_unified_fluid(bg, w_fn, cs2, lambda a: gcg_rho(a, wg, As, alpha), z, k_hmpc=k_hmpc)


def gcg_model() -> CosmoModel:
    return CosmoModel("H5a", "Generalised Chaplygin gas", ["h", "omega_b", "A_s", "alpha"],
                      [(0.55, 0.85), (0.015, 0.030), (0.5, 0.95), (-0.3, 1.0)], [0.685, 0.02253, 0.739, 0.0],
                      gcg_background, growth=gcg_growth)


# ------------------------------------------------------------------ (b) Farnes negative mass
def farnes_background(p):
    h, wb, Om_neg = p
    wneg = Om_neg * h ** 2
    ok = 1 - (OMEGA_R + wb + omega_nu(1.0) + wneg) / h ** 2
    return Background(h=h, omega_b=wb, dark=lambda a: wneg + 0 * a, omega_m_early=wb, omega_k=ok,
                      label="negative-mass fluid")


def _baryon_growth(p, bg, z):
    wb = p[1]
    return growth_smooth_fast(bg, lambda a: wb * a ** -3 + omega_nu(a), z)


def farnes_model(free_sign=False) -> CosmoModel:
    lo = -1.5 if not free_sign else -1.5
    hi = 0.0 if not free_sign else 1.5
    return CosmoModel("H5b" + ("-free" if free_sign else ""),
                      "Farnes negative-mass fluid" + (" (sign left free)" if free_sign else " (rho_- < 0, as published)"),
                      ["h", "omega_b", "Omega_-"], [(0.40, 0.95), (0.010, 0.060), (lo, hi)],
                      [0.68, 0.0224, -0.1 if not free_sign else 0.7], farnes_background, growth=_baryon_growth)


def farnes_total_v2(g, yd, yb, hp):
    """Baryons plus a spherical NFW-shaped halo of NEGATIVE mass M_- (scale r_n): it removes G|M_-(<r)|/r."""
    Mneg, rn = 10 ** hp[0], 10 ** hp[1]
    vneg2 = G * Mneg * m_nfw_shape(g.r / rn) / m_nfw_shape(30.0) / g.r
    return baryon_v2(g, yd, yb) - vneg2


def farnes_galaxy_worker(g):
    return fit_one(g, farnes_total_v2, [(2.0, 1.0), (8.0, 0.5)], [(0.0, 13.0), (-1.0, 2.0)],
                   lambda gg, hp: 0.0, ["logM_neg", "log_rn"])


def farnes_dwarf_chi2(d):
    """Negative or zero dark density predicted at 150 pc vs a measured positive density (linear errors)."""
    return float((d.rho150 / d.erho_lo) ** 2)


# ------------------------------------------------------------------ (c) environment-dependent push
F_V0 = 0.6


def _d_template(a, om=0.31):
    """Linear growth D(a)/D(1) of a reference flat LCDM (Carroll, Press & Turner 1992 fit)."""
    def g(a):
        oma = om / (om + (1 - om) * a ** 3)
        ola = 1 - oma
        return 2.5 * oma / (oma ** (4 / 7) - ola + (1 + oma / 2) * (1 + ola / 70))
    return a * g(a) / g(1.0)


def env_background(p):
    h, wb, wc, beta = p
    wde = h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc
    if np.any(1 + beta * (_d_template(np.array([1e-6, 0.1, 0.5])) - 1) <= 0):
        return None
    return Background(h=h, omega_b=wb, dark=lambda a: wc * a ** -3 + wde * (1 + beta * (_d_template(a) - 1)),
                      omega_m_early=wb + wc, label="env push")


def env_model() -> CosmoModel:
    return CosmoModel("H5c", "Environment-dependent push (void vs crowded)", ["h", "omega_b", "omega_c", "beta"],
                      [(0.55, 0.85), (0.015, 0.030), (0.05, 0.20), (-0.99, 3.0)], [0.68, 0.0224, 0.119, 0.0],
                      env_background,
                      growth=lambda p, bg, z: growth_smooth_fast(bg, lambda a: (p[1] + p[2]) * a ** -3 + omega_nu(a), z))


def void_to_crowd_ratio(beta):
    return 1 + beta / (F_V0 * (1 - beta)) if beta < 1 else np.inf

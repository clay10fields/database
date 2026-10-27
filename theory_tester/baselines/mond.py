"""Hypothesis 2 baseline: MOND with the 'standard' interpolation function mu(x) = x / sqrt(1 + x^2).

Inverting mu(g/a0) g = g_N gives g = g_N * sqrt( (1 + sqrt(1 + 4/y^2)) / 2 ),  y = g_N / a0.
Predictions:
  v(r) (SPARC)        : from the baryons alone, global a0 free, per-galaxy stellar M/L (same priors as LCDM).
  dwarf rho(150 pc)   : 'phantom' dark matter density MOND implies at 150 pc from the stars (+gas). The external
                        field effect of the Milky Way is ignored, which can only make MOND's prediction for the
                        satellites larger (more favourable to MOND), not smaller.
  cluster offsets     : no dark matter, so lensing mass follows the baryons, ~85% of which is hot gas:
                        predicted lag beta = gas share of baryons.
  cosmology           : MOND is a galaxy-scale law, not a cosmology. The only cosmology it fixes on its own
                        is 'no dark matter at all' (baryons + Lambda). That is what is scored. Relativistic MOND
                        completions (e.g. Skordis & Zlosnik 2021 AeST) add a field that behaves like dust in the
                        early universe; those are not this hypothesis and are not scored here.
"""
from __future__ import annotations

import numpy as np

from fit.galaxies import fit_one, baryon_v2
from physics.cosmology import Background, OMEGA_R, omega_nu
from physics.halos import G

NAME = "MOND (standard mu)"
A0_SI_REF = 1.2e-10
SI_TO_KPC = 3.08568e19 / 1e6        # (m/s^2) -> (km/s)^2/kpc


def nu_standard(y):
    y = np.maximum(y, 1e-12)
    return np.sqrt((1 + np.sqrt(1 + 4 / y ** 2)) / 2)


def mond_v2(r, vbar2, a0_si):
    a0 = a0_si * SI_TO_KPC
    gn = vbar2 / r
    return np.sign(gn) * np.abs(gn) * nu_standard(np.abs(gn) / a0) * r


# ------------------------------------------------------------------ SPARC
def galaxy_worker(g, a0_si):
    def total_v2(gg, yd, yb, hp):
        return mond_v2(gg.r, baryon_v2(gg, yd, yb), a0_si)
    return fit_one(g, total_v2, None, [], lambda gg, hp: 0.0, [])


# ------------------------------------------------------------------ dwarfs
def dwarf_log_rho150(d, rng, a0_si=A0_SI_REF, n=400):
    """Phantom density at r = 150 pc. Stars: Plummer sphere with scale = projected half-light radius.
    Gas (dIrrs): exponential disc treated as spherical shell mass M(<r) = M(1 - (1+x)e^-x). Stellar masses
    are scattered by 0.15 dex to propagate their uncertainty."""
    out = np.empty(n)
    mfac = 10 ** rng.normal(0, 0.15, n)
    rr = np.array([0.14, 0.15, 0.16])
    for i in range(n):
        Ms = d.Mstar * mfac[i]
        Mb = Ms * rr ** 3 / (rr ** 2 + d.Rhalf ** 2) ** 1.5
        if d.Mgas > 0 and np.isfinite(d.Rgas):
            x = rr / d.Rgas
            Mb = Mb + d.Mgas * (1 - (1 + x) * np.exp(-x))
        gN = G * Mb / rr ** 2
        g = gN * nu_standard(gN / (a0_si * SI_TO_KPC))
        r2g = rr ** 2 * g
        rho_tot = np.gradient(r2g, rr)[1] / (4 * np.pi * G * rr[1] ** 2)
        rho_bar = np.gradient(G * Mb, rr)[1] / (4 * np.pi * G * rr[1] ** 2)
        out[i] = np.log10(max(rho_tot - rho_bar, 1.0))
    return out


# ------------------------------------------------------------------ clusters
def cluster_beta(_p=None):
    from data.literature import CLUSTER_GAS_FRACTION_OF_BARYONS as f
    return f["value"], f["err"]


# ------------------------------------------------------------------ cosmology: no dark matter
COSMO_PARAMS = ["h", "omega_b"]
COSMO_BOUNDS = [(0.40, 0.95), (0.010, 0.060)]
COSMO_START = [0.68, 0.0224]


def background(p) -> Background:
    h, wb = p[:2]
    wl = h ** 2 - OMEGA_R - wb - omega_nu(1.0)
    return Background(h=h, omega_b=wb, dark=lambda a: wl + 0 * a, omega_m_early=wb, label="baryons+Lambda")


def clustering(p):
    wb = p[1]
    return lambda a: wb * a ** -3 + omega_nu(a)

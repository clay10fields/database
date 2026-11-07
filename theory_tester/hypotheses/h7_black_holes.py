"""Hypothesis 7 (Clayten): many black holes. One supermassive black hole at each galaxy's centre plus a large
population of primordial black holes (PBHs) that make up a fraction f_PBH of the dark matter.

Predictions:
  v(r) SPARC     : PBHs are cold, collisionless dark matter on galaxy scales -> NFW halo; plus a central point mass
                   M_BH with a prior from the Kormendy & Ho (2013) M_BH - M_bulge relation (bulgeless galaxies:
                   log M_BH ~ N(5.5, 1)). This tests whether SPARC can see the central black hole at all.
  H(z), CMB      : PBHs are matter -> Lambda-CDM background (accretion onto PBHs is the separate Planck limit).
  dwarfs, clusters: collisionless -> as Lambda-CDM (PBH heating of dwarfs is the Eridanus II limit).
  PBH limits     : every limit in data item 8, for single-mass (monochromatic) and log-normal mass spectra.
                   Extended mass functions use the Carr+2017 method: for each constraint,
                   f_PBH <= [ integral psi(M) / f_max(M) dM ]^-1, then the tightest constraint wins.
"""
from __future__ import annotations

import numpy as np

from data.loaders import load_pbh_bound
from fit.galaxies import fit_one, halo_c_prior, starts_halo, baryon_v2
from physics.halos import nfw_from_m200, v_nfw, v_point

ID = "H7"
NAME = "Many black holes (central SMBH + primordial black holes)"
MSUN_G = 1.98847e33
HALO_BOUNDS = [(6.0, 14.5), (0.0, np.log10(60.0)), (3.0, 10.5)]

# The limits Clayten listed (data item 8), grouped by physical probe
PBH_LIMITS = {
    "Subaru HSC microlensing": "HSC",
    "OGLE microlensing": "OGLE-2019",
    "EROS microlensing": "EROS",
    "MACHO microlensing": "M",
    "Eridanus II / ultra-faint dwarf heating": "UFdwarfs",
    "Wide binaries": "WideBinaries",
    "Planck CMB accretion": "CMB",
    "Hawking evaporation: gamma-ray background": "EGRB",
    "Hawking evaporation: Voyager e+e-": "Voyager",
    "Hawking evaporation: 511 keV line": "511keV",
    "Hawking evaporation: CMB": "CMBevap",
    "LIGO/Virgo mergers": "LIGO",
}


def bulge_mass(g, yb):
    """Bulge stellar mass from the outermost bulge velocity point (enclosed mass ~ total for a compact bulge)."""
    if not g.has_bulge:
        return 0.0
    i = int(np.argmax(g.r * g.vbul ** 2))
    return yb * g.vbul[i] ** 2 * g.r[i] / 4.30091e-6


def total_v2(g, yd, yb, hp):
    rhos, rs, _ = nfw_from_m200(10 ** hp[0], 10 ** hp[1])
    return baryon_v2(g, yd, yb) + v_nfw(g.r, rhos, rs) ** 2 + v_point(g.r, 10 ** hp[2]) ** 2


def galaxy_worker(g):
    def prior(gg, hp):
        mb = bulge_mass(g, 0.7)
        mu = np.log10(0.49e9 * (mb / 1e11) ** 1.16) if mb > 1e8 else 5.5
        sd = 0.29 if mb > 1e8 else 1.0
        return halo_c_prior(hp[0], hp[1]) + ((hp[2] - mu) / sd) ** 2
    starts = [tuple(s) + (6.0,) for s in starts_halo(g)]
    return fit_one(g, total_v2, starts, HALO_BOUNDS, prior, ["logM200", "logc", "logM_BH"])


# ------------------------------------------------------------------ PBH limits
def load_limits():
    return {k: load_pbh_bound(v) for k, v in PBH_LIMITS.items()}


def fmax_monochromatic(M_msun, limits):
    """Tightest f_PBH limit at each mass (constraints apply only inside their digitised mass range)."""
    M = np.atleast_1d(M_msun)
    best = np.full(M.shape, np.inf)
    who = np.array([""] * M.size, dtype=object)
    for k, (m, f) in limits.items():
        inside = (M >= m.min()) & (M <= m.max())
        val = np.full(M.shape, np.inf)
        val[inside] = 10 ** np.interp(np.log10(M[inside]), np.log10(m), np.log10(f))
        better = val < best
        best[better] = val[better]
        who[better] = k
    return best, who


def fmax_lognormal(Mc, sigma, limits, n=400):
    """Carr+2017: f <= 1 / max_i int psi(M)/f_i(M) dM, psi log-normal in M with width sigma (natural log)."""
    lnM = np.linspace(np.log(Mc) - 5 * sigma, np.log(Mc) + 5 * sigma, n)
    psi = np.exp(-(lnM - np.log(Mc)) ** 2 / (2 * sigma ** 2)) / np.sqrt(2 * np.pi * sigma ** 2)
    M = np.exp(lnM)
    worst, who = 0.0, ""
    for k, (m, f) in limits.items():
        inside = (M >= m.min()) & (M <= m.max())
        if not inside.any():
            continue
        fi = np.full(M.shape, np.inf)
        fi[inside] = 10 ** np.interp(np.log10(M[inside]), np.log10(m), np.log10(f))
        s = np.trapezoid(psi / fi, lnM)
        if s > worst:
            worst, who = s, k
    return (1 / worst if worst > 0 else np.inf), who

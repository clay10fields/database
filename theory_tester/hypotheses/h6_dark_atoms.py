"""Hypothesis 6 (Clayten): dark atoms / double-disc dark matter (Fan, Katz, Randall & Reece 2013;
Cyr-Racine & Sigurdson 2013).

A fraction f of the dark matter is a dissipative 'dark atom' component (dark proton + dark electron + dark
photon). It cools and settles into a thin dark disc; the remaining (1 - f) is ordinary cold dark matter.

Predictions:
  v(r) SPARC        : (1 - f) * NFW halo + exponential dark disc with mass f * M200 (all of the dissipative
                      component in the halo cools: the most optimistic case for a visible signal) and scale length
                      lambda * R_d (R_d = SPARC stellar disc scale length). Global f and lambda; per-galaxy halo.
                      Thickness does not change the midplane rotation curve, so SPARC cannot see it.
  Gaia (Milky Way)  : local dark-disc surface density Sigma_DD(R_sun) = f M200_MW / (2 pi R_DD^2) exp(-R_sun/R_DD)
                      against the Gaia limits vs scale height h (Buch+2019, Widmark+2021) and local DM density.
  Planck            : at most ~5% of dark matter can be strongly coupled to dark radiation (Cyr-Racine+2014).
  dwarfs            : (1 - f) * NFW (a dwarf's dark disc is negligible at 150 pc in spherical average).
  clusters          : the dissipative part behaves like gas in a collision: predicted lag beta ~ f.
  H(z), CMB         : dark atoms are matter -> Lambda-CDM background (cosmology block inherits LCDM; the Planck
                      interaction limit is applied as its own block).
"""
from __future__ import annotations

import numpy as np

from fit.galaxies import fit_one, halo_c_prior, starts_halo, baryon_v2
from physics.halos import nfw_from_m200, v_nfw, v_exp_disc

ID = "H6"
NAME = "Dark atoms / dark disc"
F_GRID = np.array([0.0, 0.001, 0.003, 0.01, 0.02, 0.05, 0.10])   # f_disc = M_DD / M200
LAMBDA_GRID = np.array([0.5, 1.0, 2.0])
HALO_BOUNDS = [(6.0, 14.5), (0.0, np.log10(60.0))]

# Milky Way inputs for the Gaia test (Bland-Hawthorn & Gerhard 2016 review values)
MW_M200 = 1.1e12
MW_RD_KPC = 2.6
R_SUN_KPC = 8.2


def _total_v2_factory(f, lam):
    def total_v2(g, yd, yb, hp):
        M = 10 ** hp[0]
        rhos, rs, _ = nfw_from_m200(M, 10 ** hp[1])
        v2 = baryon_v2(g, yd, yb) + (1 - f) * v_nfw(g.r, rhos, rs) ** 2
        if f > 0:
            v2 = v2 + v_exp_disc(g.r, f * M, lam * max(g.Rdisk, 0.1)) ** 2
        return v2
    return total_v2


def galaxy_worker(g):
    out = []
    starts = starts_halo(g)
    for f in F_GRID:
        for lam in LAMBDA_GRID:
            if f == 0 and lam != LAMBDA_GRID[0]:
                out.append(dict(out[-1], lam=float(lam)))
                continue
            fit = fit_one(g, _total_v2_factory(f, lam), starts, HALO_BOUNDS,
                          lambda gg, hp: halo_c_prior(hp[0], hp[1]), ["logM200", "logc"])
            out.append(dict(f=float(f), lam=float(lam), chi2_data=fit.chi2_data, chi2_prior=fit.chi2_prior,
                            params=fit.params))
    return dict(name=g.name, npts=len(g.r), grid=out)


def sigma_dd_sun(f, lam, m200=MW_M200):
    rdd = lam * MW_RD_KPC
    return f * m200 / (2 * np.pi * (rdd * 1e3) ** 2) * np.exp(-R_SUN_KPC / rdd)   # Msun/pc^2


def gaia_sigma_max(h_pc):
    """Upper limit on a thin dark disc's surface density vs its scale height h (Msun/pc^2).
    h <= 50 pc: Widmark+2021 ~5. 50-100 pc: Buch+2019 5-12 (interpolated linearly in log h).
    h > 100 pc: the disc acts like extra local dark matter; require rho_DD(0) = Sigma/(4h) (sech^2 profile)
    below the 2-sigma local DM density bound of Buch+2019 (0.016 + 2x0.010 Msun/pc^3)."""
    h = np.asarray(h_pc, float)
    lim = np.where(h <= 50, 5.0, np.where(h <= 100, 5.0 + 7.0 * np.log(h / 50) / np.log(2), 4 * h * 0.036))
    return np.maximum(lim, np.where(h > 100, 4 * h * 0.036, 0))


def gaia_chi2(f, lam, h_pc):
    """One-sided: limits are ~95% (2 sigma)."""
    s = sigma_dd_sun(f, lam)
    lim = gaia_sigma_max(h_pc)
    return float((s / (lim / 2.0)) ** 2) if s > 0 else 0.0


def planck_chi2(f):
    from data.literature import PLANCK_INTERACTING_FRACTION as P
    return float((f / (P["fmax"] / 2.0)) ** 2)


def cluster_beta(f):
    return float(f), 0.0

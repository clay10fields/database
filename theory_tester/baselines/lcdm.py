"""Hypothesis 1 baseline: flat Lambda-CDM.

Predictions:
  H(z), distances, CMB distance priors : flat LCDM with free (h, omega_b, omega_c), sigma8 free (linear).
  v(r) (SPARC)                         : NFW halo, Dutton & Maccio (2014) concentration prior.
  dwarf rho(150 pc)                    : NFW with the paper's M200 and the c(M) relation (scatter 0.11 dex).
  cluster offsets                      : collisionless DM -> beta = 0.
"""
from __future__ import annotations

import numpy as np

from fit.galaxies import fit_one, halo_c_prior, starts_halo, baryon_v2
from physics.cosmology import Background, OMEGA_R, omega_nu
from physics.halos import nfw_from_m200, v_nfw, c200_dutton_maccio, C_SCATTER_DEX

NAME = "Lambda-CDM"

# ------------------------------------------------------------------ cosmology
COSMO_PARAMS = ["h", "omega_b", "omega_c"]
COSMO_BOUNDS = [(0.55, 0.85), (0.015, 0.030), (0.05, 0.20)]
COSMO_START = [0.68, 0.0224, 0.119]


def background(p) -> Background:
    h, wb, wc = p[:3]
    wl = h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc
    return Background(h=h, omega_b=wb, dark=lambda a: wc * a ** -3 + wl + 0 * a, omega_m_early=wb + wc, label="LCDM")


def clustering(p):
    wb, wc = p[1], p[2]
    return lambda a: (wb + wc) * a ** -3 + omega_nu(a)


# ------------------------------------------------------------------ SPARC
def v2_nfw(g, hp):
    logM, logc = hp[0], hp[1]
    rhos, rs, _ = nfw_from_m200(10 ** logM, 10 ** logc)
    return v_nfw(g.r, rhos, rs) ** 2


def prior_nfw(g, hp):
    return halo_c_prior(hp[0], hp[1])


HALO_BOUNDS = [(6.0, 14.5), (np.log10(1.0), np.log10(60.0))]


def total_v2(g, yd, yb, hp):
    return baryon_v2(g, yd, yb) + v2_nfw(g, hp)


def galaxy_worker(g):
    return fit_one(g, total_v2, starts_halo(g), HALO_BOUNDS, prior_nfw, ["logM200", "logc"])


# ------------------------------------------------------------------ dwarfs
def dwarf_log_rho150(d, rng, n=400):
    """Monte-Carlo distribution of log10 rho_DM(150 pc) for an NFW halo of the quoted M200 +- error."""
    M = np.clip(rng.normal(d.M200, d.eM200, n), 0.1 * d.M200, None)
    logc = np.log10(c200_dutton_maccio(M)) + rng.normal(0, C_SCATTER_DEX, n)
    rhos, rs, _ = nfw_from_m200(M, 10 ** logc)
    x = 0.15 / rs
    return np.log10(rhos / (x * (1 + x) ** 2))


# ------------------------------------------------------------------ clusters
def cluster_beta(_p=None):
    return 0.0, 0.0

"""Hypothesis 3: evolving dark energy, w(a) = w0 + wa (1 - a) (Chevallier-Polarski-Linder), flat, smooth.

Predictions: H(z), distances and CMB distance priors from the CPL background; growth in GR with smooth dark
energy. Galaxies, dwarfs and clusters: identical to Lambda-CDM (dark energy is irrelevant on those scales), so
those blocks inherit the Lambda-CDM scores."""
from __future__ import annotations

import numpy as np

from fit.cosmo_fit import CosmoModel
from physics.cosmology import Background, OMEGA_R, omega_nu, growth_smooth_fast

ID = "H3"
NAME = "Evolving dark energy (w0-wa)"
PARAMS = ["h", "omega_b", "omega_c", "w0", "wa"]
BOUNDS = [(0.50, 0.85), (0.015, 0.030), (0.05, 0.20), (-2.0, 0.0), (-3.5, 2.0)]
START = [0.67, 0.0224, 0.119, -0.8, -0.6]


def de_ratio(a, w0, wa):
    return a ** (-3 * (1 + w0 + wa)) * np.exp(-3 * wa * (1 - a))


def background(p) -> Background:
    h, wb, wc, w0, wa = p
    if w0 + wa >= 0:          # dark energy would dominate at early times
        return None
    wde = h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc
    return Background(h=h, omega_b=wb, dark=lambda a: wc * a ** -3 + wde * de_ratio(a, w0, wa), omega_m_early=wb + wc,
                      label="w0wa")


def clustering(p):
    wb, wc = p[1], p[2]
    return lambda a: (wb + wc) * a ** -3 + omega_nu(a)


def cosmo_model() -> CosmoModel:
    return CosmoModel("H3", NAME, PARAMS, BOUNDS, START, background,
                      growth=lambda p, bg, z: growth_smooth_fast(bg, clustering(p), z))

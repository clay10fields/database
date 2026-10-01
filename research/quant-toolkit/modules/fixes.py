"""Corrections found while applying the CRM modules to the database strategies (2026-10-01). The copied modules are kept
verbatim; corrected versions live here and say why.

evt.tail_augmented_bootstrap (and the same pattern inside barrier.p_touch_bootstrap) replaces EVERY bar with probability
N_u/n by a fresh tail loss. The block-resampled path already carries its own ~N_u/n exceedances, so the as-coded version
roughly DOUBLES how often a tail loss happens, on top of letting it be larger than any seen. That is not "fat tails", it is
twice the crash frequency. Measured on book E daily returns: P(1-year drawdown < -30%) goes 1.4% (plain) -> 22.6% (as coded).
The corrected version keeps the frequency and only redraws the SIZE: bars that already exceed u are replaced by u + GPD draw.
"""
from __future__ import annotations
import numpy as np
from scipy import stats
from modules import evt, _null


def tail_augmented_bootstrap_fixed(returns, g, *, block: int = 24, rng=None):
    gen = _null._rng(rng)
    path = evt.block_bootstrap(returns, block=block, rng=gen)
    hit = -path > g.u
    k = int(hit.sum())
    if k:
        path[hit] = -(g.u + stats.genpareto.rvs(g.xi, loc=0.0, scale=g.beta, size=k, random_state=gen))
    return path

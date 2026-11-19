"""Hypothesis 1: Lambda-CDM (the baseline every other hypothesis is scored against).
All predictions live in baselines/lcdm.py; this file only registers them."""
from baselines.lcdm import *  # noqa: F401,F403
from baselines import lcdm as _b
from fit.cosmo_fit import CosmoModel
from physics.cosmology import growth_smooth_fast

ID = "H1"


def cosmo_model() -> CosmoModel:
    return CosmoModel("H1", "Lambda-CDM", _b.COSMO_PARAMS, _b.COSMO_BOUNDS, _b.COSMO_START, _b.background,
                      growth=lambda p, bg, z: growth_smooth_fast(bg, _b.clustering(p), z))

"""Hypothesis 2: MOND with the standard interpolation function. Predictions in baselines/mond.py."""
from baselines.mond import *  # noqa: F401,F403
from baselines import mond as _b
from fit.cosmo_fit import CosmoModel
from physics.cosmology import growth_smooth_fast

ID = "H2"


def cosmo_model() -> CosmoModel:
    """'No dark matter' cosmology: baryons + Lambda. Growth: Newtonian growth of baryons alone (MOND's enhanced
    growth in the deep-MOND regime is not part of linear theory on these scales and is not modelled)."""
    return CosmoModel("H2", "MOND cosmology (baryons + Lambda, no DM)", _b.COSMO_PARAMS, _b.COSMO_BOUNDS,
                      _b.COSMO_START, _b.background,
                      growth=lambda p, bg, z: growth_smooth_fast(bg, _b.clustering(p), z))

"""Cosmology fitting: scipy global optimisation for the best fit, then emcee for the posterior.

Datasets (any subset):
  'DESI DR2'  DESI DR2 BAO (13 numbers, full covariance)
  'DESI DR1'  DESI DR1 BAO (12 numbers) — used as a cross-check of DR2, never combined with it
  'Planck'    Planck 2018 distance priors (R, l_A, omega_b), Chen+2019
  'Pantheon+' 1590 SNe, z > 0.01, STAT+SYS covariance, M marginalised
  'fsigma8'   Gold-2017 growth, sigma8_0 profiled analytically
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
from scipy.optimize import differential_evolution, minimize

from physics import cosmology as cz

BIG = 1e10


@dataclass
class CosmoModel:
    key: str
    name: str
    params: list
    bounds: list
    start: list
    background: Callable
    growth: Optional[Callable] = None          # (p, bg, z) -> (D, f) or (None, None)
    prior_chi2: Callable = field(default=lambda p: 0.0)
    rd_free: bool = False                      # treat r_d as a free parameter (last entry of p)


class Data:
    def __init__(self, loaders):
        self.bao = {"DESI DR2": loaders.load_desi("dr2"), "DESI DR1": loaders.load_desi("dr1")}
        self.cmb = loaders.load_planck_priors()
        self.sn = loaders.load_pantheon()
        self.gd = loaders.load_fsigma8()

    def npts(self, ds):
        return {"DESI DR2": len(self.bao["DESI DR2"].z), "DESI DR1": len(self.bao["DESI DR1"].z), "Planck": 3,
                "Pantheon+": self.sn.n, "fsigma8": len(self.gd.z)}[ds]


def chi2_parts(model: CosmoModel, p, data: Data, datasets) -> dict:
    p = np.asarray(p, float)
    for v, (lo, hi) in zip(p, model.bounds):
        if not (lo <= v <= hi):
            return {d: BIG for d in datasets}
    try:
        bg = model.background(p)
    except (ValueError, FloatingPointError, ZeroDivisionError):
        return {d: BIG for d in datasets}
    if bg is None or not bg.valid():
        return {d: BIG for d in datasets}
    out = {}
    with np.errstate(all="ignore"):
        for d in sorted(datasets, key=lambda x: x == "fsigma8"):
            if d.startswith("DESI"):
                rd = p[-1] if model.rd_free else None
                out[d] = cz.chi2_bao(bg, data.bao[d], rd)
            elif d == "Planck":
                out[d] = cz.chi2_cmb(bg, data.cmb)
            elif d == "Pantheon+":
                out[d] = cz.chi2_sn(bg, data.sn)
            elif d == "fsigma8":
                others = sum(v for k, v in out.items() if not k.startswith("_"))
                if others > 1e5:
                    # the point is already excluded by >300 sigma; skip the (expensive) growth solve
                    out[d] = 0.0
                    out["_growth_skipped"] = 1.0
                    continue
                D, f = model.growth(p, bg, data.gd.z)
                if D is None or not np.all(np.isfinite(D)) or not np.all(np.isfinite(f)):
                    out[d] = BIG
                else:
                    s8, c2 = cz.best_sigma8(bg, (D, f), data.gd)
                    out[d] = c2 if s8 > 0 else BIG
                    out["_sigma8"] = s8
            if not np.isfinite(out[d]):
                out[d] = BIG
    out["_prior"] = float(model.prior_chi2(p))
    return out


def total(parts, datasets):
    return float(sum(parts[d] for d in datasets) + parts.get("_prior", 0.0))


def best_fit(model: CosmoModel, data: Data, datasets, seed=0, maxiter=120, popsize=12):
    f = lambda p: total(chi2_parts(model, p, data, datasets), datasets)
    r = differential_evolution(f, model.bounds, seed=seed, maxiter=maxiter, popsize=popsize, tol=1e-7,
                               polish=False, init="sobol", x0=np.clip(model.start, [b[0] for b in model.bounds],
                                                                       [b[1] for b in model.bounds]))
    best = r
    # polish from the global-search result AND from the model's physical starting point (for nested models such as
    # the Chaplygin gas the start is the Lambda-CDM limit, so the fit can never end up worse than its own limit)
    for x0 in (r.x, np.clip(model.start, [b[0] for b in model.bounds], [b[1] for b in model.bounds])):
        r2 = minimize(f, x0, method="Nelder-Mead", options=dict(maxiter=2000, xatol=1e-7, fatol=1e-7))
        if r2.fun < best.fun:
            best = r2
    parts = chi2_parts(model, best.x, data, datasets)
    return dict(p=[float(x) for x in best.x], chi2=float(total(parts, datasets)),
                parts={k: float(v) for k, v in parts.items()})


def run_mcmc(model: CosmoModel, data: Data, datasets, p0, nsteps=1500, burn=500, seed=1, pool=None):
    import emcee
    ndim = len(model.params)
    nw = max(4 * ndim, 16)
    rng = np.random.default_rng(seed)
    scale = np.array([(hi - lo) * 1e-3 for lo, hi in model.bounds])
    start = np.array(p0) + rng.normal(0, 1, (nw, ndim)) * scale
    start = np.clip(start, [b[0] for b in model.bounds], [b[1] for b in model.bounds])
    lp = _LogProb(model, data, datasets)
    sampler = emcee.EnsembleSampler(nw, ndim, lp, pool=pool)
    sampler.run_mcmc(start, nsteps, progress=False)
    chain = sampler.get_chain(discard=burn, flat=True)
    try:
        tau = float(np.max(sampler.get_autocorr_time(discard=burn, quiet=True)))
    except Exception:
        tau = float("nan")
    q = np.percentile(chain, [2.5, 16, 50, 84, 97.5], axis=0)
    summ = {n: dict(mean=float(chain[:, i].mean()), sd=float(chain[:, i].std()), p2_5=float(q[0, i]),
                    p16=float(q[1, i]), median=float(q[2, i]), p84=float(q[3, i]), p97_5=float(q[4, i]))
            for i, n in enumerate(model.params)}
    return dict(summary=summ, nwalkers=nw, nsteps=nsteps, burn=burn, autocorr_max=tau,
                acceptance=float(np.mean(sampler.acceptance_fraction))), chain


class _LogProb:
    def __init__(self, model, data, datasets):
        self.model, self.data, self.datasets = model, data, datasets

    def __call__(self, p):
        c = total(chi2_parts(self.model, p, self.data, self.datasets), self.datasets)
        return -0.5 * c if c < BIG / 2 else -np.inf

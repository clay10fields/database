"""Per-galaxy rotation-curve fitting for SPARC, shared by every hypothesis.

Model: V_model^2 = total_v2(galaxy, Y_d, Y_b, halo params), e.g. baryons + halo for dark-matter models or
nu(g_N/a0) g_N r for MOND. Nuisance parameters and priors are IDENTICAL for every hypothesis (as in Li, Lelli &
McGaugh 2018) and their prior chi^2 is reported separately from the data chi^2:
  log10 Y_d ~ N(log10 0.5, 0.1), log10 Y_b ~ N(log10 0.7, 0.1)
  distance  : log10(D/D_SPARC) ~ N(0, e_D/(D ln10)); radii scale as D, baryonic velocities as sqrt(D)
  inclination ~ N(i_SPARC, e_i); observed velocities and errors scale as sin(i_SPARC)/sin(i)
  halo models: log10 c ~ N(Dutton & Maccio 2014 c(M), 0.11)
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
from scipy.optimize import minimize

from physics.halos import c200_dutton_maccio, C_SCATTER_DEX

LOGYD0, LOGYB0, SIG_Y = np.log10(0.5), np.log10(0.7), 0.1


@dataclass
class GalaxyFit:
    name: str
    chi2_data: float
    chi2_prior: float
    npts: int
    nparams: int
    params: dict


def baryon_v2(g, yd, yb):
    return g.vgas * np.abs(g.vgas) + yd * g.vdisk ** 2 + yb * g.vbul ** 2


def nworkers():
    return int(os.environ.get("TT_WORKERS", os.cpu_count() or 1))


def _nuisance(g):
    sd = max(g.D * 0.01, getattr(g, "eD", 0.0)) if hasattr(g, "eD") else 0.1 * g.D
    sdl = max(sd / (g.D * np.log(10)), 0.01)
    si = max(getattr(g, "einc", 5.0), 1.0)
    return sdl, si


def scaled(g, dlogD, inc):
    """The galaxy as it would look at distance D*10^dlogD and inclination inc."""
    f = 10 ** dlogD
    s = np.sin(np.radians(g.inc)) / np.sin(np.radians(inc))
    return SimpleNamespace(r=g.r * f, vobs=g.vobs * s, err=g.err * s, vgas=g.vgas * np.sqrt(f),
                           vdisk=g.vdisk * np.sqrt(f), vbul=g.vbul * np.sqrt(f), has_bulge=g.has_bulge,
                           Rdisk=g.Rdisk * f, name=g.name, D=g.D * f)


def fit_one(g, total_v2, x0_list, bounds, prior_fn, names):
    """p = [log Yd, (log Yb), dlogD, inc, *model params]"""
    nb = 2 if g.has_bulge else 1
    sdl, si = _nuisance(g)
    inc_lo, inc_hi = max(g.inc - 3 * si, 10.0), min(g.inc + 3 * si, 90.0)

    def objective(p, split=False):
        yd = 10 ** p[0]
        yb = 10 ** p[1] if g.has_bulge else 0.0
        dlogD, inc = p[nb], p[nb + 1]
        hp = p[nb + 2:]
        gg = scaled(g, dlogD, inc)
        v2 = total_v2(gg, yd, yb, hp)
        v = np.sign(v2) * np.sqrt(np.abs(v2))
        cd = float(np.sum(((v - gg.vobs) / gg.err) ** 2))
        cp = (((p[0] - LOGYD0) / SIG_Y) ** 2 + (((p[1] - LOGYB0) / SIG_Y) ** 2 if g.has_bulge else 0.0)
              + (dlogD / sdl) ** 2 + ((inc - g.inc) / si) ** 2 + prior_fn(gg, hp))
        if not np.isfinite(cd):
            cd = 1e12
        return (cd, cp) if split else cd + cp

    yb_b = [(np.log10(0.2), np.log10(2.0))] if g.has_bulge else []
    bnds = [(np.log10(0.1), np.log10(2.0))] + yb_b + [(-3 * sdl, 3 * sdl), (inc_lo, inc_hi)] + list(bounds)
    best = None
    for x0 in (x0_list or [[]]):
        p0 = [LOGYD0] + ([LOGYB0] if g.has_bulge else []) + [0.0, g.inc] + list(x0)
        p0 = [min(max(v, lo), hi) for v, (lo, hi) in zip(p0, bnds)]
        r = minimize(objective, p0, method="L-BFGS-B", bounds=bnds)
        r2 = minimize(objective, r.x, method="Nelder-Mead", bounds=bnds,
                      options=dict(maxiter=4000, xatol=1e-5, fatol=1e-6))
        cand = r2 if r2.fun < r.fun else r
        if best is None or cand.fun < best.fun:
            best = cand
    cd, cp = objective(best.x, split=True)
    pn = ["logYd"] + (["logYb"] if g.has_bulge else []) + ["dlogD", "inc"] + list(names)
    return GalaxyFit(g.name, cd, cp, len(g.r), len(best.x), dict(zip(pn, map(float, best.x))))


def halo_c_prior(logM, logc):
    return ((logc - np.log10(c200_dutton_maccio(10 ** logM))) / C_SCATTER_DEX) ** 2


def starts_halo(g):
    vf = g.Vflat if g.Vflat > 0 else max(g.vobs)
    logM0 = np.log10(max(1e7, 1.2e12 * (vf / 200.0) ** 3.3))
    return [(logM0 + d, np.log10(c200_dutton_maccio(10 ** (logM0 + d)))) for d in (-0.7, 0.0, 0.7)]


def fit_many(gals, worker, *args):
    with ProcessPoolExecutor(max_workers=nworkers()) as ex:
        return list(ex.map(worker, gals, *[[a] * len(gals) for a in args]))


def summarize(fits):
    return dict(chi2_data=float(sum(f.chi2_data for f in fits)), chi2_prior=float(sum(f.chi2_prior for f in fits)),
                npts=int(sum(f.npts for f in fits)), nparams=int(sum(f.nparams for f in fits)), ngal=len(fits))

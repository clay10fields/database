"""M17 — tails beyond the sample: extreme value theory (CRM.md §M17).

Sample quantiles cannot exceed the worst observed loss; the next crash will. Peaks-over-threshold
with a generalised Pareto tail:

    x = -r ;  u = 95th percentile ;  y = x[x > u] - u ;  (xi, beta) = genpareto.fit(y, floc=0)
    VaR_p = u + (beta/xi) * ( ((n/N_u) * (1-p))^(-xi) - 1 )
    ES_p  = VaR_p / (1-xi) + (beta - xi*u) / (1-xi)          (xi < 1)

xi = 1/alpha (Hill) — both are printed and disagreement is flagged. xi >= 0.5 means infinite
variance: sigma-based numbers are meaningless there. The tail-augmented block bootstrap keeps
vol clustering and allows losses larger than any seen.

Losses are POSITIVE numbers inside this module (x = -r). Returns are log returns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from modules import _null

FloatArray: TypeAlias = NDArray[np.float64]

INFINITE_VARIANCE_XI = 0.5
HILL_GPD_TOLERANCE = 0.15


@dataclass(frozen=True)
class GPD:
    xi: float
    beta: float
    u: float
    n: int
    n_u: int
    xi_ci: tuple[float, float]
    hill_alpha: float
    hill_gpd_disagree: bool
    infinite_variance: bool

    def describe(self) -> str:
        var = ""
        if self.infinite_variance:
            var = "INFINITE VARIANCE in the tail; sigma-based numbers are meaningless"
        dis = "  Hill and GPD DISAGREE" if self.hill_gpd_disagree else ""
        return (
            f"xi={self.xi:.3f} [{self.xi_ci[0]:.3f}, {self.xi_ci[1]:.3f}]  beta={self.beta:.5f}  "
            f"u={self.u:.5f}  N_u={self.n_u}/{self.n}  Hill alpha={self.hill_alpha:.2f} "
            f"(1/alpha={1 / self.hill_alpha:.3f}){dis}  {var}"
        )


def losses(returns: FloatArray) -> FloatArray:
    return -np.asarray(returns, dtype=np.float64)


def hill_index(x: FloatArray, *, k_frac: float = 0.05) -> float:
    """alpha = 1 / ((1/k) * sum ln(x_(i) / x_(k))) on the k largest losses."""
    xs = np.sort(x[x > 0])[::-1]
    k = max(int(k_frac * len(xs)), 10)
    if len(xs) <= k:
        raise ValueError("too few positive losses for a Hill estimate")
    top, xk = xs[:k], xs[k]
    return float(1.0 / np.mean(np.log(top / xk)))


def fit_gpd(
    returns: FloatArray,
    *,
    q: float = 0.95,
    k_frac: float = 0.05,
    n_boot: int = 200,
    rng: np.random.Generator | None = None,
) -> GPD:
    """POT fit at threshold u = q-quantile of losses; bootstrap CI on xi; Hill beside it."""
    x = losses(returns)
    n = len(x)
    if n < 500:
        raise ValueError("need >= 500 observations for a tail fit")
    u = float(np.quantile(x, q))
    y = x[x > u] - u
    if len(y) < 30:
        raise ValueError("fewer than 30 exceedances; lower q")
    xi, _, beta = stats.genpareto.fit(y, floc=0)
    g = _null._rng(rng)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        yb = g.choice(y, size=len(y), replace=True)
        boots[i] = stats.genpareto.fit(yb, floc=0)[0]
    lo, hi = float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))
    alpha = hill_index(x, k_frac=k_frac)
    # Both estimators carry different finite-sample biases (GPD at a 95% threshold reads ~0.28 on
    # t(3), Hill at k=5% reads ~0.38; the truth is 1/3), so the flag is a tolerance on the gap,
    # not a CI membership test — that fired on every t(3) draw and would flag reality daily.
    disagree = abs(xi - 1.0 / alpha) > HILL_GPD_TOLERANCE
    return GPD(
        float(xi), float(beta), u, n, len(y), (lo, hi), alpha, bool(disagree),
        bool(xi >= INFINITE_VARIANCE_XI),
    )


def var_es(g: GPD, *, p: float) -> tuple[float, float]:
    """VaR_p and ES_p as losses (positive). p = 0.999 is the 1-in-1000-bar loss."""
    if not g.u < 1e300 or not 0.0 < p < 1.0:
        raise ValueError("bad inputs")
    tail_frac = (g.n / g.n_u) * (1.0 - p)
    if abs(g.xi) < 1e-6:
        var = g.u - g.beta * math.log(tail_frac)
        es = var + g.beta
        return float(var), float(es)
    var = g.u + (g.beta / g.xi) * (tail_frac ** (-g.xi) - 1.0)
    if g.xi >= 1.0:
        return float(var), float("inf")
    es = var / (1.0 - g.xi) + (g.beta - g.xi * g.u) / (1.0 - g.xi)
    return float(var), float(es)


def xi_stability(
    returns: FloatArray, *, quantiles: tuple[float, ...] = (0.90, 0.92, 0.95, 0.97, 0.98)
) -> dict[float, float]:
    """xi at several thresholds; stable across [90th, 98th] is what makes u = 95th defensible.
    Needs enough exceedances per threshold to mean anything: ~300 at the 99.5th of n=60k is noise."""
    x = losses(returns)
    out: dict[float, float] = {}
    for q in quantiles:
        u = float(np.quantile(x, q))
        y = x[x > u] - u
        out[q] = float(stats.genpareto.fit(y, floc=0)[0]) if len(y) >= 30 else float("nan")
    return out


def mean_excess_plot_data(returns: FloatArray, *, n_points: int = 30) -> tuple[FloatArray, FloatArray]:
    """e(u) = mean(x - u | x > u) on a grid of thresholds; linear above u is the GPD signature."""
    x = losses(returns)
    us = np.quantile(x, np.linspace(0.80, 0.99, n_points))
    me = np.array([float(np.mean(x[x > u] - u)) if np.any(x > u) else np.nan for u in us])
    return us.astype(np.float64), me


def block_bootstrap(
    returns: FloatArray, *, block: int = 24, rng: np.random.Generator | None = None
) -> FloatArray:
    """Circular block bootstrap: keeps vol clustering; can NEVER produce a loss larger than any seen."""
    r = np.asarray(returns, dtype=np.float64)
    g = _null._rng(rng)
    n = len(r)
    starts = g.integers(0, n, size=math.ceil(n / block))
    idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
    return r[idx]


def tail_augmented_bootstrap(
    returns: FloatArray, g: GPD, *, block: int = 24, rng: np.random.Generator | None = None
) -> FloatArray:
    """Block-resample, then replace each bar with probability N_u/n by a fresh loss u + GPD(xi, beta).
    Keeps vol clustering, allows losses larger than any seen. Caps use THIS, not the plain bootstrap."""
    gen = _null._rng(rng)
    path = block_bootstrap(returns, block=block, rng=gen)
    n = len(path)
    hit = gen.uniform(size=n) < (g.n_u / g.n)
    k = int(hit.sum())
    if k:
        draws = stats.genpareto.rvs(g.xi, loc=0.0, scale=g.beta, size=k, random_state=gen)
        path[hit] = -(g.u + draws)
    return path

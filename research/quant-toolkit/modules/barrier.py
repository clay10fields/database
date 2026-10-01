"""M6 — touching the liquidation level, and ruin (CRM.md §M6).

The question is P(TOUCH level at any point), not P(close beyond it). The closed form is a
sanity check only; the primary number is 10,000 block-bootstrapped paths of real returns, plain
and tail-augmented (M17). Caps use the tail-augmented number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from modules import _null, evt

FloatArray: TypeAlias = NDArray[np.float64]


def p_touch_gbm(*, s0: float, level: float, mu: float, sigma: float, horizon_years: float) -> float:
    """GBM, barrier L below S0: b = ln(L/S0), nu = mu - sigma^2/2,
    P = Phi((b - nu T)/(sigma sqrt T)) + exp(2 nu b / sigma^2) Phi((b + nu T)/(sigma sqrt T))."""
    if level >= s0:
        return 1.0
    b = math.log(level / s0)
    nu = mu - sigma**2 / 2.0
    st = sigma * math.sqrt(horizon_years)
    return float(stats.norm.cdf((b - nu * horizon_years) / st)
                 + math.exp(2.0 * nu * b / sigma**2) * stats.norm.cdf((b + nu * horizon_years) / st))


def p_ruin_closed(*, p: float, i: int, n: int) -> float:
    """Gambler's ruin, even-money bets: P_ruin = ((q/p)^i - (q/p)^n) / (1 - (q/p)^n); p = q -> 1 - i/n."""
    q = 1.0 - p
    if abs(p - q) < 1e-12:
        return 1.0 - i / n
    r = q / p
    return float((r**i - r**n) / (1.0 - r**n))


@dataclass(frozen=True)
class Touch:
    plain: float
    tail_augmented: float
    closed_form: float
    fat_tail_penalty: float       # plain / closed_form
    unseen_tail_penalty: float    # tail_augmented / plain


def _paths(r: FloatArray, *, horizon: int, n_paths: int, block: int, g: np.random.Generator) -> FloatArray:
    n = len(r)
    nb = math.ceil(horizon / block)
    starts = g.integers(0, n, size=(n_paths, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_paths, -1)[:, :horizon] % n
    return r[idx]


def p_touch_bootstrap(
    r: FloatArray,
    *,
    level_pct: float,
    horizon_bars: int,
    n_paths: int = 10_000,
    block: int = 24,
    rng: np.random.Generator | None = None,
) -> Touch:
    """Fraction of block-bootstrapped paths whose running minimum crosses the level; then the same
    paths with tail augmentation (common random numbers, so the unseen-tail penalty is a clean
    ratio). level_pct is negative for a barrier below."""
    g = _null._rng(rng)
    x = np.asarray(r, dtype=np.float64)
    if level_pct >= 0:
        raise ValueError("level_pct must be negative (a barrier below)")
    lb = math.log1p(level_pct)
    base = _paths(x, horizon=horizon_bars, n_paths=n_paths, block=block, g=g)
    plain = float(np.mean(np.min(np.cumsum(np.log1p(base), axis=1), axis=1) <= lb))
    gp = evt.fit_gpd(x, n_boot=50, rng=g)
    aug = base.copy()
    hit = g.uniform(size=aug.shape) < gp.n_u / gp.n
    k = int(hit.sum())
    if k:
        aug[hit] = -(gp.u + stats.genpareto.rvs(gp.xi, loc=0.0, scale=gp.beta, size=k, random_state=g))
    aug_p = float(np.mean(np.min(np.cumsum(np.log1p(np.maximum(aug, -0.999999)), axis=1), axis=1) <= lb))
    mu_bar, sd_bar = float(x.mean()), float(x.std(ddof=1))
    closed = p_touch_gbm(s0=1.0, level=1.0 + level_pct, mu=mu_bar * horizon_bars,
                         sigma=sd_bar * math.sqrt(horizon_bars), horizon_years=1.0)
    return Touch(plain, aug_p, closed, plain / closed if closed > 0 else float("inf"),
                 aug_p / plain if plain > 0 else float("inf"))


def p_ruin_simulated(
    r: FloatArray,
    *,
    size: float,
    n_trades: int = 500,
    n_sims: int = 10_000,
    dd_limit: float = 0.5,
    rng: np.random.Generator | None = None,
) -> float:
    """Fraction of resampled trade sequences whose wealth drawdown reaches dd_limit at size x."""
    g = _null._rng(rng)
    x = np.asarray(r, dtype=np.float64)
    idx = g.integers(0, len(x), size=(n_sims, n_trades))
    w = np.cumprod(np.maximum(1.0 + size * x[idx], 1e-12), axis=1)
    peak = np.maximum.accumulate(np.concatenate([np.ones((n_sims, 1)), w], axis=1), axis=1)[:, 1:]
    dd = 1.0 - w / peak
    return float(np.mean(dd.max(axis=1) >= dd_limit))

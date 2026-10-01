"""M10 — what size costs (CRM.md §M10).

Kyle's lambda from 5-minute buckets of signed taker flow vs mid change, OLS with HAC errors, in
bps per $1M. The square-root law for our own orders, impact_bps = Y sigma_daily_bps sqrt(Q/V),
Y = 0.7 until refit from fills. Amihud as a cross-check. Liquidation impact vs matched voluntary
trades against a timestamp-shuffled null. Almgren–Chriss for our own schedule.

In cascades spreads go 3-5 bps -> 10-15 bps and a realistic round trip is ~28-30 bps; fit
impact separately in cascade windows and calm, and any result that trades in cascades uses the
cascade cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from modules import _null

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

SQRT_LAW_Y = 0.7


@dataclass(frozen=True)
class Kyle:
    lam: float                  # bps per $1M
    ci: tuple[float, float]
    r2: float
    n: int


def kyle_lambda(q_usd: FloatArray, dp_bps: FloatArray, *, maxlags: int = 6) -> Kyle:
    """dP_bps = lambda * (Q / $1M) + e, HAC standard errors (maxlags=6)."""
    import statsmodels.api as sm  # noqa: PLC0415

    q = np.asarray(q_usd, dtype=np.float64) / 1e6
    y = np.asarray(dp_bps, dtype=np.float64)
    X = sm.add_constant(q)
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    lam = float(res.params[1])
    se = float(res.bse[1])
    return Kyle(lam, (lam - 1.96 * se, lam + 1.96 * se), float(res.rsquared), len(y))


def sqrt_impact_bps(
    *, q_usd: float, v_daily_usd: float, sigma_daily_bps: float, y: float = SQRT_LAW_Y
) -> float:
    return float(y * sigma_daily_bps * np.sqrt(q_usd / v_daily_usd))


def amihud(r: FloatArray, dollar_volume: FloatArray) -> float:
    return float(np.mean(np.abs(np.asarray(r)) / np.asarray(dollar_volume)))


def fit_y_by_regime(
    *, q_usd: FloatArray, v_daily_usd: FloatArray, sigma_daily_bps: FloatArray, impact_bps: FloatArray,
    regime: NDArray[np.str_],
) -> dict[str, float]:
    """Refit the square-root Y separately per regime label (cascade vs calm)."""
    out: dict[str, float] = {}
    x = np.sqrt(np.asarray(q_usd) / np.asarray(v_daily_usd)) * np.asarray(sigma_daily_bps)
    for lab in np.unique(regime):
        m = np.asarray(regime) == lab
        denom = float(np.dot(x[m], x[m]))
        out[str(lab)] = float(np.dot(x[m], np.asarray(impact_bps)[m]) / denom) if denom > 0 else float("nan")
    return out


@dataclass(frozen=True)
class LiqImpact:
    liq_markout_bps: dict[int, float]
    vol_markout_bps: dict[int, float]
    p_value: dict[int, float]


def _markout(mid: FloatArray, idx: IntArray, side: FloatArray, h: int) -> FloatArray:
    return side * (mid[idx + h] - mid[idx]) / mid[idx] * 1e4


def liquidation_impact(
    mid: FloatArray,
    liq_idx: IntArray,
    vol_idx: IntArray,
    *,
    side: FloatArray,
    horizons: tuple[int, ...] = (1, 5, 15),
    n_shuffles: int = 1000,
    rng: np.random.Generator | None = None,
) -> LiqImpact:
    """Signed mid move after each liquidation vs matched voluntary trades; null = shuffle which
    timestamps carry the 'liquidation' label. side = -1 for a long liquidated (a forced sell)."""
    g = _null._rng(rng)
    m = np.asarray(mid, dtype=np.float64)
    li = np.asarray(liq_idx, dtype=np.int64)
    vi = np.asarray(vol_idx, dtype=np.int64)
    s_l = np.asarray(side, dtype=np.float64)
    pool = np.concatenate([li, vi])
    s_pool = np.concatenate([s_l, s_l[: len(vi)] if len(vi) <= len(s_l) else np.resize(s_l, len(vi))])
    nl = len(li)
    liq_m, vol_m, pv = {}, {}, {}
    for h in horizons:
        a = float(np.mean(_markout(m, li, s_l, h)))
        b = float(np.mean(_markout(m, vi, s_pool[nl:], h)))
        obs = a - b
        worse = 0
        for _ in range(n_shuffles):
            perm = g.permutation(len(pool))
            pi, ps = pool[perm], s_pool[perm]
            d = float(np.mean(_markout(m, pi[:nl], ps[:nl], h)) - np.mean(_markout(m, pi[nl:], ps[nl:], h)))
            worse += int(d >= obs)
        liq_m[h], vol_m[h], pv[h] = a, b, (1 + worse) / (n_shuffles + 1)
    return LiqImpact(liq_m, vol_m, pv)


def almgren_chriss_schedule(
    *, shares: float, n_steps: int, sigma: float, eta: float, lam_risk: float, tau: float = 1.0
) -> FloatArray:
    """Optimal liquidation trajectory x_k (remaining) with kappa^2 ~ lam sigma^2 / (eta tau):
    faster when vol is high relative to impact. lam_risk = 0 -> straight line (TWAP)."""
    if lam_risk <= 0:
        return shares * (1.0 - np.arange(n_steps + 1) / n_steps)
    kappa = np.sqrt(lam_risk * sigma**2 / (eta * tau))
    k = np.arange(n_steps + 1)
    return shares * np.sinh(kappa * (n_steps - k) * tau) / np.sinh(kappa * n_steps * tau)

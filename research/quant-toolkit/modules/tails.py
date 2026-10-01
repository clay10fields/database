"""M2 — real worst case, vol regime, cascade fuel (CRM.md §M2).

Empirical tails and their ratio to the Gaussian so the bell curve's error is visible; the Hill
index and, through M17, the GPD tail; vol clustering (ACF of rolling realised vol, GARCH(1,1)
persistence, Hurst on returns and on vol); HAR-RV against GARCH out of sample; the HIGH/LOW vol
flag; the fuel gauge and the MINSKY flag.

Not yet here (follow-up in this PR): BOCPD change-point probabilities, Bai-Perron break dummies
inside HAR (the `breaks` argument takes them when found), the 14-window calendar replay and
taker-flow variance compression — each needs a feature the store does not carry yet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from modules import evt

FloatArray: TypeAlias = NDArray[np.float64]

TAIL_PS = (0.005, 0.01, 0.05)
CLUSTER_LB_P = 1e-3


# ---------------------------------------------------------------------------------------------
# tails
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Tails:
    q: dict[float, float]
    ratio_to_gaussian: dict[float, float]
    hill_alpha: float
    xi: float
    gpd: evt.GPD
    sentence: str


def empirical_tails(returns: FloatArray) -> Tails:
    """Empirical 0.5/1/5% quantiles of returns and their ratio to mean + sigma*Phi^-1(p)."""
    r = np.asarray(returns, dtype=np.float64)
    mu, sd = float(r.mean()), float(r.std(ddof=1))
    q = {p: float(np.quantile(r, p)) for p in TAIL_PS}
    ratio = {p: float(q[p] / (mu + sd * stats.norm.ppf(p))) for p in TAIL_PS}
    g = evt.fit_gpd(r)
    if g.hill_alpha < 2.0 or g.infinite_variance:
        sentence = (
            f"Hill alpha={g.hill_alpha:.2f}, xi={g.xi:.2f}: variance is INFINITE in the tail; "
            "sigma-based risk numbers are meaningless."
        )
    else:
        sentence = (
            f"Hill alpha={g.hill_alpha:.2f}, xi={g.xi:.2f}; the 1% loss is {ratio[0.01]:.2f}x what a "
            "Gaussian with the same sigma predicts."
        )
    return Tails(q, ratio, g.hill_alpha, g.xi, g, sentence)


# ---------------------------------------------------------------------------------------------
# vol clustering
# ---------------------------------------------------------------------------------------------

def realised_vol(returns: FloatArray, *, window: int) -> FloatArray:
    """rolling sqrt(sum r^2 / w); NaN until the window fills"""
    r = np.asarray(returns, dtype=np.float64)
    out = np.full(len(r), np.nan)
    if len(r) >= window:
        c = np.cumsum(np.concatenate([[0.0], r**2]))
        out[window - 1 :] = np.sqrt((c[window:] - c[:-window]) / window)
    return out


def acf(x: FloatArray, *, lags: int) -> FloatArray:
    x = np.asarray(x, dtype=np.float64)
    x = x[~np.isnan(x)]
    x = x - x.mean()
    d = float(np.dot(x, x))
    if d <= 0:
        return np.zeros(lags)
    return np.array([float(np.dot(x[:-k], x[k:]) / d) for k in range(1, lags + 1)])


def hurst_rs(x: FloatArray) -> float:
    """Rescaled-range Hurst exponent on the series (0.5 = no memory)."""
    x = np.asarray(x, dtype=np.float64)
    x = x[~np.isnan(x)]
    n = len(x)
    sizes = [s for s in (16, 32, 64, 128, 256, 512, 1024) if s * 4 <= n]
    if len(sizes) < 3:
        raise ValueError("series too short for a Hurst estimate")
    rs = []
    for s in sizes:
        chunks = x[: (n // s) * s].reshape(-1, s)
        vals = []
        for c in chunks:
            d = c - c.mean()
            z = np.cumsum(d)
            rng_ = z.max() - z.min()
            sd = c.std(ddof=1)
            if sd > 0:
                vals.append(rng_ / sd)
        rs.append(np.mean(vals))
    slope, _ = np.polyfit(np.log(sizes), np.log(rs), 1)
    return float(slope)


def garch_persistence(returns: FloatArray) -> float:
    """alpha + beta of a GARCH(1,1) fitted by `arch`; expect 0.9–0.99 on crypto."""
    from arch import arch_model  # noqa: PLC0415  (heavy import kept local)

    r = np.asarray(returns, dtype=np.float64) * 100.0
    res = arch_model(r, mean="Zero", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    p = res.params
    return float(p["alpha[1]"] + p["beta[1]"])


@dataclass(frozen=True)
class Clustering:
    acf_rv: FloatArray
    ljung_box_p: float
    clustered: bool
    garch_persistence: float
    hurst_ret: float
    hurst_vol: float


def vol_clustering(returns: FloatArray, *, window: int = 24, lags: int = 48) -> Clustering:
    """ACF of rolling realised vol at lags 1..48; Ljung–Box on r^2 decides `clustered`."""
    from statsmodels.stats.diagnostic import acorr_ljungbox  # noqa: PLC0415

    r = np.asarray(returns, dtype=np.float64)
    rv = realised_vol(r, window=window)
    a = acf(rv, lags=lags)
    lb = acorr_ljungbox(r**2, lags=[window], return_df=True)
    p = float(lb["lb_pvalue"].iloc[0])
    return Clustering(a, p, p < CLUSTER_LB_P, garch_persistence(r), hurst_rs(r), hurst_rs(rv))


# ---------------------------------------------------------------------------------------------
# HAR-RV vs GARCH, out of sample
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class HarRV:
    oos_r2_har: float
    oos_r2_garch: float
    coef: FloatArray
    holdout_days: int


def _daily_rv(returns: FloatArray, *, bars_per_day: int) -> tuple[FloatArray, FloatArray]:
    r = np.asarray(returns, dtype=np.float64)
    days = len(r) // bars_per_day
    m = r[: days * bars_per_day].reshape(days, bars_per_day)
    rv = np.sum(m**2, axis=1)
    bv = (math.pi / 2.0) * np.sum(np.abs(m[:, 1:]) * np.abs(m[:, :-1]), axis=1)
    return rv, np.maximum(rv - bv, 0.0)


def har_rv(
    returns: FloatArray, *, bars_per_day: int, holdout_days: int, breaks: FloatArray | None = None
) -> HarRV:
    """log RV_{d+1} on log RV_d, its 5-day and 22-day means, the jump component and any break
    dummies; OOS R2 on the last `holdout_days` against a GARCH(1,1) fitted on the same train slice."""
    rv, jump = _daily_rv(returns, bars_per_day=bars_per_day)
    lrv = np.log(rv + 1e-18)
    n = len(lrv)
    if n < holdout_days + 60:
        raise ValueError("not enough days")
    cols = [np.ones(n), lrv]
    for w in (5, 22):
        cols.append(np.array([lrv[max(0, i - w + 1) : i + 1].mean() for i in range(n)]))
    cols.append(np.log(jump + 1e-18))
    if breaks is not None:
        for b in np.asarray(breaks):
            cols.append((np.arange(n) >= b).astype(float))
    X = np.column_stack(cols)[:-1]
    y = lrv[1:]
    tr = slice(0, n - 1 - holdout_days)
    te = slice(n - 1 - holdout_days, n - 1)
    coef, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
    pred = X[te] @ coef
    r2_har = 1.0 - float(np.sum((y[te] - pred) ** 2) / np.sum((y[te] - y[te].mean()) ** 2))

    # GARCH(1,1) on daily returns, fitted on train, recursion carried through the holdout
    from arch import arch_model  # noqa: PLC0415

    daily = np.asarray(returns, dtype=np.float64)[: n * bars_per_day].reshape(n, bars_per_day)
    daily = daily.sum(axis=1) * 100
    res = arch_model(daily[: n - 1 - holdout_days], mean="Zero", vol="GARCH", p=1, q=1).fit(disp="off")
    om, al, be = (float(res.params[k]) for k in ("omega", "alpha[1]", "beta[1]"))
    s2 = np.empty(n)
    s2[0] = float(np.var(daily[: n - 1 - holdout_days]))
    for i in range(1, n):
        s2[i] = om + al * daily[i - 1] ** 2 + be * s2[i - 1]
    g_pred = np.log(s2[1:] / 1e4 + 1e-18)[te]
    r2_g = 1.0 - float(np.sum((y[te] - g_pred) ** 2) / np.sum((y[te] - y[te].mean()) ** 2))
    return HarRV(r2_har, r2_g, coef, holdout_days)


# ---------------------------------------------------------------------------------------------
# regime, fuel, Minsky
# ---------------------------------------------------------------------------------------------

def vol_regime(returns: FloatArray, *, window: int = 24, lookback: int = 24 * 30) -> NDArray[np.str_]:
    """HIGH when rolling realised vol is above its rolling median over `lookback`, else LOW.
    (The forecast-based version feeds har_rv's prediction in place of the realised value.)"""
    rv = realised_vol(returns, window=window)
    out = np.array(["LOW"] * len(rv), dtype="<U4")
    for i in range(len(rv)):
        past = rv[max(0, i - lookback) : i + 1]
        past = past[~np.isnan(past)]
        if len(past) >= 10 and rv[i] > np.median(past):
            out[i] = "HIGH"
    return out


def fuel_gauge(oi: FloatArray, *, bars_per_day: int, days: int = 30) -> FloatArray:
    """OI over its rolling 30-day mean. > 1 = fuel building. (M16 mass within 2% replaces this.)"""
    x = np.asarray(oi, dtype=np.float64)
    w = days * bars_per_day
    out = np.full(len(x), np.nan)
    c = np.cumsum(np.concatenate([[0.0], x]))
    for i in range(len(x)):
        lo = max(0, i - w + 1)
        out[i] = x[i] / ((c[i + 1] - c[lo]) / (i + 1 - lo))
    return out


def minsky_flag(returns: FloatArray, oi: FloatArray, *, bars_per_day: int) -> NDArray[np.bool_]:
    """oi_z90 > 1 AND daily realised vol below its 90-day median: stability breeding leverage.
    Catches build-up-type cascades only; shocks have no precursor."""
    r = np.asarray(returns, dtype=np.float64)
    x = np.asarray(oi, dtype=np.float64)
    w = 90 * bars_per_day
    rv = realised_vol(r, window=bars_per_day)
    out = np.zeros(len(r), dtype=bool)
    for i in range(len(r)):
        lo = max(0, i - w + 1)
        seg = x[lo : i + 1]
        if len(seg) < bars_per_day * 10 or seg.std() == 0:
            continue
        z = (x[i] - seg.mean()) / seg.std()
        v = rv[lo : i + 1]
        v = v[~np.isnan(v)]
        out[i] = bool(z > 1.0 and len(v) and rv[i] < np.median(v))
    return out

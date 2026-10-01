"""M7 — how far any forecast reaches (CRM.md §M7). Run once per series.

Robust version: AR(p) chosen by AIC on the first 70%; forecast the last 30% at h in {1, 2, 4,
... 64}; out-of-sample R2 and sign accuracy - 50% against the shuffled 95th percentile; the
horizon is the largest h that beats it. The Lyapunov exponent is reported beside it against a
shuffled surrogate — noise also gives a large lambda, so lambda_real ~ lambda_shuffled means
"indistinguishable from noise; horizon ~ 0".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from modules import _null

FloatArray: TypeAlias = NDArray[np.float64]

HORIZONS: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)


def _ar_fit(x: FloatArray, p: int) -> tuple[FloatArray, float]:
    """OLS AR(p) with intercept; returns (coef [c, a1..ap], AIC)."""
    n = len(x)
    X = np.column_stack([np.ones(n - p)] + [x[p - k : n - k] for k in range(1, p + 1)])
    y = x[p:]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    s2 = float(np.mean(resid**2))
    aic = (n - p) * np.log(s2 + 1e-300) + 2 * (p + 1)
    return coef, float(aic)


def _ar_forecast(x: FloatArray, coef: FloatArray, *, h: int) -> FloatArray:
    """h-step-ahead forecasts for every origin t >= p (iterated), aligned to target index t + h."""
    p = len(coef) - 1
    n = len(x)
    hist = np.column_stack([x[p - k : n - k] for k in range(1, p + 1)]) if p else np.zeros((n, 0))
    cur = hist.copy()
    for _ in range(h):
        nxt = coef[0] + cur @ coef[1:]
        cur = np.column_stack([nxt, cur[:, :-1]]) if p > 1 else nxt[:, None]
    return nxt


@dataclass(frozen=True)
class Horizon:
    horizon: int
    p: int
    oos_r2: dict[int, float]
    sign_acc_minus_half: dict[int, float]
    shuffled_95: dict[int, float]


def _score(
    x: FloatArray, *, p: int, horizons: tuple[int, ...], split: float
) -> tuple[dict[int, float], dict[int, float]]:
    n = len(x)
    cut = int(n * split)
    coef, _ = _ar_fit(x[:cut], p)
    r2: dict[int, float] = {}
    sa: dict[int, float] = {}
    for h in horizons:
        f = _ar_forecast(x, coef, h=h)              # row j: last observed x[p+j-1], predicts x[p+j+h-1]
        origins = np.arange(p, n) - 1                # index of the last observed value per row
        tgt = origins + h
        ok = (tgt < n) & (origins >= cut)
        y, yhat = x[tgt[ok]], f[ok]
        if len(y) < 10:
            r2[h], sa[h] = float("nan"), float("nan")
            continue
        r2[h] = 1.0 - float(np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2))
        sa[h] = float(np.mean(np.sign(y) == np.sign(yhat))) - 0.5
    return r2, sa


def forecast_horizon(
    x: FloatArray,
    *,
    horizons: tuple[int, ...] = HORIZONS,
    max_p: int = 10,
    split: float = 0.7,
    n_shuffles: int = 200,
    rng: np.random.Generator | None = None,
) -> Horizon:
    g = _null._rng(rng)
    s = np.asarray(x, dtype=np.float64)
    s = (s - s.mean()) / (s.std() + 1e-300)
    cut = int(len(s) * split)
    p = min(range(1, max_p + 1), key=lambda k: _ar_fit(s[:cut], k)[1])
    r2, sa = _score(s, p=p, horizons=horizons, split=split)
    null: dict[int, list[float]] = {h: [] for h in horizons}
    for _ in range(n_shuffles):
        sh = _null.shuffle(s, rng=g)
        nr2, _ = _score(sh, p=p, horizons=horizons, split=split)
        for h in horizons:
            null[h].append(nr2[h])
    q95 = {h: float(np.nanquantile(null[h], 0.95)) for h in horizons}
    beats = [h for h in horizons if np.isfinite(r2[h]) and r2[h] > q95[h]]
    return Horizon(max(beats) if beats else 0, p, r2, sa, q95)


@dataclass(frozen=True)
class Lyapunov:
    lam_real: float
    lam_shuffled: float
    sentence: str


def rosenstein_lyapunov(
    x: FloatArray, *, emb_dim: int = 5, lag: int = 1, min_tsep: int = 10, trajectory_len: int = 20
) -> float:
    """Rosenstein et al. (1993) largest Lyapunov exponent, hand-rolled.

    nolds.lyap_r is the spec's reference, but the installed nolds cannot be imported on Python
    3.11 (its datasets module calls importlib.resources.files() on a module, which 3.11 rejects).
    CRM §5.1's rule for tick applies: use the library only if it installs, otherwise hand-roll.
    Delay-embed, find each point's nearest neighbour at least min_tsep apart in time, follow the
    pair for trajectory_len steps, average log divergence per step, fit the slope.
    """
    s = np.asarray(x, dtype=np.float64)
    n = len(s) - (emb_dim - 1) * lag
    if n <= trajectory_len + 2 * min_tsep:
        raise ValueError("series too short for the embedding")
    emb = np.column_stack([s[i * lag : i * lag + n] for i in range(emb_dim)])
    usable = n - trajectory_len
    e = emb[:usable]
    d = np.sqrt(((e[:, None, :] - e[None, :, :]) ** 2).sum(axis=2))
    idx = np.arange(usable)
    d[np.abs(idx[:, None] - idx[None, :]) < min_tsep] = np.inf
    nn = np.argmin(d, axis=1)
    div = np.zeros(trajectory_len)
    for k in range(trajectory_len):
        dk = np.linalg.norm(emb[idx + k] - emb[nn + k], axis=1)
        good = dk > 0
        div[k] = float(np.mean(np.log(dk[good]))) if good.any() else np.nan
    ks = np.arange(trajectory_len)
    ok = np.isfinite(div)
    slope, _ = np.polyfit(ks[ok], div[ok], 1)
    return float(slope)


def _lyap(s: FloatArray) -> float:
    try:
        import nolds  # noqa: PLC0415

        return float(nolds.lyap_r(s, emb_dim=5, lag=1, min_tsep=10, trajectory_len=20))
    except Exception:  # noqa: BLE001 - nolds fails at import on py3.11; the hand-rolled one is the same estimator
        return rosenstein_lyapunov(s, emb_dim=5, lag=1, min_tsep=10, trajectory_len=20)


def lyapunov_vs_surrogate(x: FloatArray, *, rng: np.random.Generator | None = None) -> Lyapunov:
    """Rosenstein largest Lyapunov exponent on standardised log returns vs the same on a shuffled
    surrogate. Noise also gives a large lambda, so lambda_real ~ lambda_shuffled means
    'indistinguishable from noise; horizon ~ 0'."""
    g = _null._rng(rng)
    s = np.asarray(x, dtype=np.float64)
    s = (s - s.mean()) / (s.std() + 1e-300)
    lam = _lyap(s)
    lam_s = _lyap(_null.shuffle(s, rng=g))
    if lam <= 0 or lam <= 1.15 * lam_s:
        sentence = (
            f"lambda_real={lam:.3f} vs lambda_shuffled={lam_s:.3f}: indistinguishable from noise; "
            "forecast horizon ~ 0."
        )
    else:
        sentence = f"lambda_real={lam:.3f} exceeds lambda_shuffled={lam_s:.3f}; horizon ~ {1 / lam:.1f} bars."
    return Lyapunov(lam, lam_s, sentence)

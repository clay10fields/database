"""M4 — edge -> size guidance (CRM.md §M4). The machine sizes nothing; this is the number printed
in the alert, with the binding cap named so the cost of oversizing is impossible to miss.

Net returns first. Kelly binary f = p - (1-p)/b; continuous f = mu/sigma^2. Growth at fraction c
of Kelly is (2c - c^2) G*: c = 2 is zero growth, and estimation error always pushes toward
overbetting. So: shrink toward zero by how noisy the estimate is, take a quarter of what is
left, then cap four ways and take the minimum.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from modules import _null

FloatArray: TypeAlias = NDArray[np.float64]

SECONDS_PER_YEAR = 31_536_000.0
KELLY_FRACTION = 0.25
LEVERAGE_CAP = 3.0
MAX_SINGLE_LOSS_PCT = 0.05
MAX_P_TOUCH = 0.01
MAX_P_RUIN = 0.01
MIN_REGISTRY_FOR_TAU = 10


def kelly_binary(*, p: float, b: float) -> float:
    return p - (1.0 - p) / b


def kelly_continuous(*, mu: float, sigma: float) -> float:
    if sigma <= 0:
        raise ValueError("sigma must be > 0")
    return mu / sigma**2


def growth_at_fraction(*, c: float) -> float:
    """growth at fraction c of full Kelly, as a multiple of G*: (2c - c^2)"""
    return 2.0 * c - c**2


# ---------------------------------------------------------------------------------------------
# shrinkage Kelly
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ShrunkEdge:
    mu_hat: float
    s2: float               # bootstrap variance of mu_hat
    tau2: float             # variance of mu_hat across registry hypotheses (= s2 if registry < 10)
    mu_shrunk: float
    shrink_factor: float    # tau2 / (tau2 + s2)
    ci: tuple[float, float]
    sentence: str


def shrunk_edge(
    r: FloatArray,
    *,
    tau2: float | None,
    n_registry: int,
    n_boot: int = 1000,
    rng: np.random.Generator | None = None,
) -> ShrunkEdge:
    """mu_shrunk = mu_hat * tau2 / (tau2 + s2). Most tested edges are noise, so the estimate is
    pulled toward zero by how noisy it is. With fewer than 10 registry entries tau2 = s2, which
    halves every edge — deliberate conservatism until the registry knows its own dispersion."""
    g = _null._rng(rng)
    x = np.asarray(r, dtype=np.float64)
    n = len(x)
    if n < 5:
        raise ValueError("need >= 5 trades")
    mu = float(x.mean())
    boots = np.array([float(g.choice(x, size=n, replace=True).mean()) for _ in range(n_boot)])
    s2 = float(boots.var(ddof=1))
    if tau2 is None or n_registry < MIN_REGISTRY_FOR_TAU:
        tau2 = s2
    factor = tau2 / (tau2 + s2) if (tau2 + s2) > 0 else 0.0
    shrunk = mu * factor
    ci = (float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))
    sentence = f"shrink factor {factor:.2f}: " + (
        "more than half this edge is noise." if factor < 0.5 else "the estimate mostly survives shrinkage."
    )
    if factor == 0.5 and n_registry < MIN_REGISTRY_FOR_TAU:
        sentence += f" (registry has {n_registry} < {MIN_REGISTRY_FOR_TAU} entries: tau2 = s2 by rule)"
    return ShrunkEdge(mu, s2, tau2, shrunk, factor, ci, sentence)


# ---------------------------------------------------------------------------------------------
# size guidance with four caps
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class SizeGuidance:
    size_fraction: float           # of manual_capital, as notional multiple (1.0 = capital)
    binding: str
    kelly_full: float
    kelly_quarter: float
    caps: dict[str, float]
    edge: ShrunkEdge
    dollars: float
    sentence: str


def size_guidance(
    r: FloatArray,
    *,
    es_99: float,
    p_touch: float,
    p_ruin: float,
    manual_capital: float,
    tau2: float | None = None,
    n_registry: int = 0,
    rng: np.random.Generator | None = None,
) -> SizeGuidance:
    """Quarter-Kelly on the shrunk edge, then the minimum of four caps: tail
    (MAX_SINGLE_LOSS_PCT / ES_0.99), touch (P_touch < 1% over the holding period), ruin
    (P_ruin over 500 trades < 1%), leverage <= 3x. CI on the edge including zero -> size 0."""
    x = np.asarray(r, dtype=np.float64)
    edge = shrunk_edge(x, tau2=tau2, n_registry=n_registry, rng=rng)
    sigma = float(x.std(ddof=1))
    f_full = kelly_continuous(mu=edge.mu_shrunk, sigma=sigma) if sigma > 0 else 0.0
    f_quarter = KELLY_FRACTION * f_full
    caps = {
        "quarter-Kelly": max(f_quarter, 0.0),
        "tail (MAX_SINGLE_LOSS / ES_0.99)": MAX_SINGLE_LOSS_PCT / es_99 if es_99 > 0 else float("inf"),
        "leverage <= 3x": LEVERAGE_CAP,
    }
    if edge.ci[0] <= 0.0 <= edge.ci[1] or edge.mu_shrunk <= 0.0:
        size, binding = 0.0, "edge CI includes zero"
    elif p_touch >= MAX_P_TOUCH:
        size, binding = 0.0, "touch P < 1%"
    elif p_ruin >= MAX_P_RUIN:
        size, binding = 0.0, "ruin P < 1%"
    else:
        binding = min(caps, key=lambda k: caps[k])
        size = caps[binding]
    sentence = (
        f"size {size:.2f}x capital (${size * manual_capital:,.0f}); binder: {binding}. "
        f"Full Kelly {f_full:.2f}x, quarter {f_quarter:.2f}x. {edge.sentence}"
    )
    return SizeGuidance(size, binding, f_full, f_quarter, caps, edge, size * manual_capital, sentence)


# ---------------------------------------------------------------------------------------------
# legging, multi-asset, business math
# ---------------------------------------------------------------------------------------------

def legging_bps(*, sigma_annual: float, seconds: float) -> float:
    """sigma_leg(dt) = sigma_annual * sqrt(dt / 31,536,000), in bps. By hand, legs land 1-5
    minutes apart: 60 s ~ 5.5-8.3 bps and 5 min ~ 12-19 bps at 40-60% vol — against an ~8 bps
    fee bar, so a two-leg signal needs a dislocation well above 25 bps that lasts minutes."""
    return float(sigma_annual * math.sqrt(seconds / SECONDS_PER_YEAR) * 1e4)


def ledoit_wolf(panel: FloatArray) -> FloatArray:
    """Ledoit–Wolf (2004) shrinkage of the sample covariance toward scaled identity."""
    x = np.asarray(panel, dtype=np.float64)
    t, n = x.shape
    xc = x - x.mean(axis=0)
    s = xc.T @ xc / t
    mu = float(np.trace(s) / n)
    f = mu * np.eye(n)
    d2 = float(np.sum((s - f) ** 2))
    b2 = 0.0
    for i in range(t):
        xi = xc[i][:, None]
        b2 += float(np.sum((xi @ xi.T - s) ** 2))
    b2 = min(b2 / t**2, d2)
    delta = b2 / d2 if d2 > 0 else 0.0
    return delta * f + (1.0 - delta) * s


def multi_asset_kelly(panel: FloatArray) -> FloatArray:
    """f* = Sigma^-1 mu with a Ledoit–Wolf-shrunk Sigma. With one dominant factor, per-asset
    Kelly over-bets by ~N/N_eff; this is what to print beside it."""
    x = np.asarray(panel, dtype=np.float64)
    mu = x.mean(axis=0)
    sig = ledoit_wolf(x)
    out: FloatArray = np.linalg.solve(sig, mu)
    return out


@dataclass(frozen=True)
class BusinessMath:
    hurdle: float
    margin_drag: float
    minimum_capital: float
    sentence: str


def business_math(
    *,
    t_bill: float,
    operating_cost_per_year: float,
    capital: float,
    idle_collateral_frac: float,
    collateral_yield: float,
    net_edge: float,
) -> BusinessMath:
    """hurdle = T-bill + operating cost/capital + margin drag; margin drag = idle collateral x
    (risk_free - collateral_yield); minimum_capital = operating_cost / (net_edge - hurdle) —
    below this the machine loses money by existing."""
    drag = idle_collateral_frac * (t_bill - collateral_yield)
    hurdle = t_bill + operating_cost_per_year / capital + drag
    min_cap = operating_cost_per_year / (net_edge - hurdle) if net_edge > hurdle else float("inf")
    sentence = (
        f"hurdle {hurdle:.2%} (T-bill {t_bill:.2%} + cost {operating_cost_per_year / capital:.2%} + "
        f"margin drag {drag:.2%}); minimum capital ${min_cap:,.0f} at net edge {net_edge:.2%}"
        if math.isfinite(min_cap)
        else f"hurdle {hurdle:.2%} exceeds net edge {net_edge:.2%}: no capital makes this pay"
    )
    return BusinessMath(hurdle, drag, min_cap, sentence)

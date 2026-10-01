"""M1 — the gate that stops us believing noise (CRM.md §M1).

Input: out-of-sample trade returns, their times, the underlying's aligned returns, and what was tried.
Verdict in {NOTHING, REAL}. REAL requires ALL of: power check passed; p_shuffle below the current
alpha level; DSR >= 0.95; hedged version significant; alpha (not beta) significant.

Everything here takes arrays and returns numbers. It never reads a feed, never places anything.

Nulls come from modules/_null.py only. Gaussian noise is never a null.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from modules import _null

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

EULER_GAMMA = 0.5772156649
HARD_FLOOR_TRADES = 100
DSR_FLOOR = 0.95
E_LIVE = 20.0
E_RETIRE_MONTHS = 2


# ---------------------------------------------------------------------------------------------
# 1. independent trades, not calendar days
# ---------------------------------------------------------------------------------------------

def cluster_ids(times: IntArray, *, holding: float) -> IntArray:
    """Events whose gap to the previous event is < holding period are one cluster.
    'one practitioner's 910 VPIN events were 95 clusters.'"""
    t = np.asarray(times, dtype=np.float64)
    if len(t) == 0:
        return np.zeros(0, dtype=np.int64)
    if np.any(np.diff(t) < 0):
        raise ValueError("times must be sorted")
    new = np.concatenate([[True], np.diff(t) >= holding])
    return np.cumsum(new).astype(np.int64) - 1


def n_clusters(times: IntArray, *, holding: float) -> int:
    ids = cluster_ids(times, holding=holding)
    return int(ids[-1] + 1) if len(ids) else 0


def cluster_returns(returns: FloatArray, ids: IntArray) -> FloatArray:
    """Sum the returns inside each cluster: one number per independent event."""
    r = np.asarray(returns, dtype=np.float64)
    k = int(ids.max()) + 1 if len(ids) else 0
    return np.bincount(ids, weights=r, minlength=k).astype(np.float64)


def effective_bets(panel: FloatArray) -> float:
    """N_eff = (sum lambda)^2 / sum lambda^2 on the correlation matrix's eigenvalues.
    16 perfectly correlated assets are one bet."""
    p = np.asarray(panel, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] < 1:
        raise ValueError("panel must be (T, N)")
    if p.shape[1] == 1:
        return 1.0
    c = np.corrcoef(p, rowvar=False)
    lam = np.clip(np.linalg.eigvalsh(c), 0.0, None)
    return float(lam.sum() ** 2 / np.sum(lam**2))


def marchenko_pastur_edge(*, n_assets: int, n_obs: int) -> float:
    """Eigenvalues below (1 + sqrt(N/T))^2 are noise."""
    return float((1.0 + math.sqrt(n_assets / n_obs)) ** 2)


# ---------------------------------------------------------------------------------------------
# 2. power before testing
# ---------------------------------------------------------------------------------------------

def n_required(s: float, alpha: float, *, power: float = 0.8) -> int:
    """n ~ ((z_{1-alpha} + z_power) / s)^2, one-sided. s = per-trade Sharpe."""
    if s <= 0.0:
        raise ValueError("per-trade Sharpe must be > 0 for a power calculation")
    z = stats.norm.ppf(1.0 - alpha) + stats.norm.ppf(power)
    return int(round((z / s) ** 2))


def min_detectable_sharpe(*, n_trades: int, alpha: float, power: float = 0.8) -> float:
    """The s detectable from n independent trades at this alpha. If the mechanism can't
    plausibly deliver it, don't run the test — it only spends alpha."""
    z = stats.norm.ppf(1.0 - alpha) + stats.norm.ppf(power)
    return float(z / math.sqrt(max(n_trades, 1)))


def power_check(*, n_independent: int, s: float, alpha: float, power: float = 0.8) -> bool:
    """Hard floor of 100 independent trades regardless, then n >= n_required(s)."""
    if n_independent < HARD_FLOOR_TRADES or s <= 0.0:
        return False
    return n_independent >= n_required(s, alpha, power=power)


# ---------------------------------------------------------------------------------------------
# 3. shuffle null
# ---------------------------------------------------------------------------------------------

def sharpe(r: FloatArray) -> float:
    r = np.asarray(r, dtype=np.float64)
    sd = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    return float(np.mean(r) / sd) if sd > 0 else 0.0


def shuffle_test(
    returns: FloatArray,
    *,
    metric: Callable[[FloatArray], float] = sharpe,
    n_shuffles: int,
    block: int = 1,
    rng: np.random.Generator | None = None,
) -> tuple[float, FloatArray]:
    """Label-shuffle null on trade returns: the label is the DIRECTION. Each shuffle keeps every
    trade's size |r| and vol clustering (block-wise) and randomises the sign, so the null is
    'the same trades with no directional skill'. Shuffling the returns themselves would leave
    the mean and the Sharpe untouched and test nothing.

    Returns (p, null metrics). p = fraction of nulls beating the real metric.
    """
    g = _null._rng(rng)
    r = np.asarray(returns, dtype=np.float64)
    real = metric(r)
    mag = np.abs(r)
    nulls = np.empty(n_shuffles)
    for i in range(n_shuffles):
        signs = g.choice(np.array([-1.0, 1.0]), size=len(r))
        if block > 1:
            signs = _null.block_shuffle(signs, block=block, rng=g)
        nulls[i] = metric(mag * signs)
    return _null.shuffle_pvalue(real, nulls), nulls


# ---------------------------------------------------------------------------------------------
# 4. multiple testing — online FDR with e-values; Bonferroni and BH printed beside it
# ---------------------------------------------------------------------------------------------

def bonferroni_level(alpha: float, n_tests: int) -> float:
    return alpha / max(n_tests, 1)


def bh_rejections(pvalues: FloatArray, alpha: float) -> NDArray[np.bool_]:
    """Benjamini–Hochberg step-up; the conservative bound printed beside the online verdict."""
    p = np.asarray(pvalues, dtype=np.float64)
    m = len(p)
    if m == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p)
    thresh = alpha * (np.arange(1, m + 1) / m)
    ok = p[order] <= thresh
    k = int(np.max(np.nonzero(ok)[0])) + 1 if ok.any() else 0
    out = np.zeros(m, dtype=bool)
    out[order[:k]] = True
    return out


class OnlineFDR:
    """LORD++ with e-values (Javanmard–Montanari 2018; Ramdas et al. 2017/2018; the e-value form
    e-LORD, arXiv 2506.01452, builds on Foster–Stine 2008 alpha-investing).

    Level for test t:   level_t = gamma_t * w0 + sum_{j : tau_j < t} gamma_{t - tau_j} * b0
    where tau_j are the rejection times, w0 + b0 = alpha, and gamma is a spending sequence that
    sums to 1. The second term is the mechanism: every discovery starts a NEW spending sequence
    from gamma_1, so the level is earned back and never collapses to zero the way 0.05/n_tests does
    as the registry grows. Rejection with an e-value: e_t >= 1/level_t (Markov: P(e >= 1/l) <= l
    under the null), valid under dependence between tests — ours share data. The order of tests
    is pre-registered, highest prior first (registry's job). Bonferroni and BH are printed beside
    it as conservative bounds; if they disagree on a verdict, say so.
    """

    def __init__(self, alpha: float, *, w0: float | None = None) -> None:
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha in (0,1)")
        self.alpha = alpha
        self.w0 = alpha / 2.0 if w0 is None else w0
        if not 0.0 < self.w0 <= alpha:
            raise ValueError("0 < w0 <= alpha")
        self.b0 = alpha - self.w0
        self.t = 0
        self.rejections: list[int] = []
        self.levels: list[float] = []
        self.wealth = self.w0          # bookkeeping only: w0 + b0*discoveries - sum(levels spent)

    @staticmethod
    def gamma(j: int) -> float:
        """sum_{j>=1} (j+1)^-1.1 = zeta(1.1) - 1 ~ 9.5845; normalised so the sequence sums to 1."""
        return float((1.0 / (j + 1) ** 1.1) / 9.5845)

    def _level(self, t: int) -> float:
        lvl = self.gamma(t) * self.w0
        for tau in self.rejections:
            if tau < t:
                lvl += self.gamma(t - tau) * self.b0
        return lvl

    def current_level(self) -> float:
        return self._level(self.t + 1)

    def test(self, *, e_value: float) -> bool:
        if e_value < 0.0 or not math.isfinite(e_value):
            raise ValueError("e-value must be finite and >= 0")
        self.t += 1
        lvl = self._level(self.t)
        self.levels.append(lvl)
        self.wealth -= lvl
        reject = lvl > 0.0 and e_value >= 1.0 / lvl
        if reject:
            self.rejections.append(self.t)
            self.wealth += self.b0
        return bool(reject)


# ---------------------------------------------------------------------------------------------
# 5. deflated Sharpe ratio (Bailey & López de Prado 2014)
# ---------------------------------------------------------------------------------------------

def deflated_sharpe(
    *, sr: float, n_periods: int, skew: float, kurt: float, n_variants: int, var_sr: float
) -> tuple[float, float]:
    """SR per-period (not annualised). kurt is the raw fourth moment ratio (Gaussian = 3).
        SR0 = sqrt(V) * ((1-g) Phi^-1(1 - 1/N) + g Phi^-1(1 - 1/(N e)))
        DSR = Phi((SR - SR0) sqrt(T-1) / sqrt(1 - g3 SR + ((g4-1)/4) SR^2))
    N = 1 -> SR0 = 0 (probabilistic Sharpe). The gap SR - SR0 is 'how much of this Sharpe is
    selection'."""
    if n_variants < 1:
        raise ValueError("n_variants >= 1")
    if n_variants == 1 or var_sr <= 0.0:
        sr0 = 0.0
    else:
        n = float(n_variants)
        sr0 = math.sqrt(var_sr) * (
            (1.0 - EULER_GAMMA) * stats.norm.ppf(1.0 - 1.0 / n)
            + EULER_GAMMA * stats.norm.ppf(1.0 - 1.0 / (n * math.e))
        )
    denom = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr**2
    if denom <= 0.0 or n_periods < 2:
        return sr0, 0.0
    z = (sr - sr0) * math.sqrt(n_periods - 1.0) / math.sqrt(denom)
    return float(sr0), float(stats.norm.cdf(z))


# ---------------------------------------------------------------------------------------------
# 6. beta gate
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class BetaGate:
    beta: float
    r2: float
    alpha: float
    alpha_p: float
    hedged_p: float          # t-test on strat - beta*underlying: the spread-first check
    beta_share_pct: float    # share of the strategy's mean return explained by beta
    sentence: str


def _ols(y: FloatArray, x: FloatArray) -> tuple[float, float, float, float, float]:
    """slope, intercept, r2, p_slope, p_intercept with plain OLS standard errors."""
    n = len(y)
    if n < 4:
        raise ValueError("need >= 4 observations")
    xm, ym = x.mean(), y.mean()
    sxx = float(np.sum((x - xm) ** 2))
    if sxx <= 0.0:
        raise ValueError("underlying has no variance")
    b = float(np.sum((x - xm) * (y - ym)) / sxx)
    a = float(ym - b * xm)
    resid = y - (a + b * x)
    s2 = float(np.sum(resid**2) / (n - 2))
    se_b = math.sqrt(s2 / sxx)
    se_a = math.sqrt(s2 * (1.0 / n + xm**2 / sxx))
    sst = float(np.sum((y - ym) ** 2))
    r2 = 1.0 - float(np.sum(resid**2)) / sst if sst > 0 else 0.0
    p_b = float(2.0 * stats.t.sf(abs(b / se_b), n - 2)) if se_b > 0 else 0.0
    p_a = float(2.0 * stats.t.sf(abs(a / se_a), n - 2)) if se_a > 0 else 0.0
    return b, a, r2, p_b, p_a


def beta_gate(strategy: FloatArray, underlying: FloatArray) -> BetaGate:
    """Regress per-trade returns on the underlying's return over the same holding window.
    Spread-first: the hedged version (strategy - beta*underlying) must itself be significant;
    if it isn't, the directional version is presumed beta."""
    y = np.asarray(strategy, dtype=np.float64)
    x = np.asarray(underlying, dtype=np.float64)
    if len(y) != len(x):
        raise ValueError("strategy and underlying must align trade by trade")
    b, a, r2, _, p_a = _ols(y, x)
    hedged = y - b * x
    hedged_p = float(stats.ttest_1samp(hedged, 0.0).pvalue) if np.std(hedged) > 0 else 1.0
    ym = float(y.mean())
    share = float(b * x.mean() / ym * 100.0) if abs(ym) > 1e-12 else float("nan")
    share_txt = f"{share:.0f}%" if math.isfinite(share) else "an undefined share (mean return ~ 0)"
    sentence = (
        f"{share_txt} of this strategy's return is underlying beta (beta={b:.2f}, R2={r2:.2f}); "
        f"alpha={a:.5f} per trade, p={p_a:.3f}; hedged version p={hedged_p:.3f}."
    )
    return BetaGate(b, r2, a, p_a, hedged_p, share, sentence)


# ---------------------------------------------------------------------------------------------
# 7. arcsine warning
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Arcsine:
    frac_above_start: float
    last_lead_change: int
    sentence: str


def arcsine_warning(equity: FloatArray) -> Arcsine:
    """Fraction of time the curve is above its start and the time of the last lead change.
    Under pure noise the density of that fraction is 1/(pi sqrt(x(1-x))) — U-shaped — so
    'up most of the time' is typical of noise."""
    e = np.asarray(equity, dtype=np.float64)
    if len(e) == 0:
        raise ValueError("empty equity curve")
    above = e > e[0]
    frac = float(above.mean())
    changes = np.nonzero(np.diff(above.astype(int)) != 0)[0]
    last = int(changes[-1] + 1) if len(changes) else 0
    sentence = (
        f"The equity curve is above its start {frac:.0%} of the time; last lead change at bar "
        f"{last} of {len(e)}. Under pure noise that fraction has density 1/(pi*sqrt(x(1-x))) — "
        "U-shaped — so 'up most of the time' is the expected shape of noise, not evidence."
    )
    return Arcsine(frac, last, sentence)


# ---------------------------------------------------------------------------------------------
# 8. Doob check — edge or sizing?
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Doob:
    leak_suspected: bool
    mean_final_wealth_demeaned: float
    ci_low: float
    ci_high: float
    edge_from_bets: float
    contribution_of_sizing: float
    martingale_warning: bool
    ruin: bool


def growth(r: FloatArray) -> float:
    """time-average growth rate; -inf (RUIN) if any 1 + r <= 0"""
    r = np.asarray(r, dtype=np.float64)
    if np.any(1.0 + r <= 0.0):
        return float("-inf")
    return float(np.mean(np.log1p(r)))


def doob_check(
    returns: FloatArray,
    *,
    sizing_rule: Callable[[FloatArray], FloatArray],
    n_shuffles: int = 1000,
    rng: np.random.Generator | None = None,
) -> Doob:
    """Demean the returns; run the actual sizing rule over shuffles; mean final wealth must equal
    the start within its CI or the implementation leaks the future (optional stopping: no sizing
    or timing rule turns a fair game into a favourable one). Then split growth into what the bets
    earn at constant size and what the sizing rule adds. Hard warning if size rises after losses."""
    g = _null._rng(rng)
    r = np.asarray(returns, dtype=np.float64)
    r0 = r - r.mean()
    finals = np.empty(n_shuffles)
    for i in range(n_shuffles):
        x = _null.shuffle(r0, rng=g)
        finals[i] = float(np.sum(np.asarray(sizing_rule(x), dtype=np.float64) * x))
    m = float(finals.mean())
    se = float(finals.std(ddof=1) / math.sqrt(n_shuffles)) if n_shuffles > 1 else 0.0
    lo, hi = m - 3.0 * se, m + 3.0 * se
    leak = not (lo <= 0.0 <= hi)

    size = np.asarray(sizing_rule(r), dtype=np.float64)
    g_const = growth(r)
    g_rule = growth(size * r)
    ruin = not math.isfinite(g_rule)
    contribution = (g_rule - g_const) if not ruin else float("-inf")

    after_loss = size[1:][r[:-1] < 0]
    after_win = size[1:][r[:-1] >= 0]
    martingale = bool(
        len(after_loss) and len(after_win) and after_loss.mean() > after_win.mean() * 1.05
    )
    return Doob(leak, m, lo, hi, g_const, contribution, martingale, ruin)


# ---------------------------------------------------------------------------------------------
# 9. Simpson check
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Simpson:
    flagged: bool
    reasons: list[str]
    table: dict[str, dict[str, float]]


def simpson_check(returns: FloatArray, labels: dict[str, NDArray[np.str_]]) -> Simpson:
    """Split by every label set (vol regime, weekday/weekend, year, half-year). Flag if the pooled
    sign disagrees with every sub-group, or if trade-weighted and time-weighted (equal weight per
    group) averages disagree in sign."""
    r = np.asarray(returns, dtype=np.float64)
    pooled = float(r.mean())
    reasons: list[str] = []
    table: dict[str, dict[str, float]] = {}
    for name, lab in labels.items():
        lab = np.asarray(lab)
        if len(lab) != len(r):
            raise ValueError(f"label set {name!r} does not align with returns")
        groups = {str(k): float(r[lab == k].mean()) for k in np.unique(lab)}
        table[name] = groups
        signs = [np.sign(v) for v in groups.values()]
        if len(groups) > 1 and pooled != 0.0 and all(s != 0 and s != np.sign(pooled) for s in signs):
            reasons.append(f"{name}: pooled sign {np.sign(pooled):+.0f} disagrees with every sub-group")
        time_weighted = float(np.mean(list(groups.values())))
        if pooled != 0.0 and time_weighted != 0.0 and np.sign(pooled) != np.sign(time_weighted):
            reasons.append(
                f"{name}: trade-weighted mean {pooled:+.5f} and time-weighted mean "
                f"{time_weighted:+.5f} disagree in sign"
            )
    return Simpson(bool(reasons), reasons, table)


# ---------------------------------------------------------------------------------------------
# 10. decay monitoring with an e-process
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class EProcess:
    E: FloatArray
    sup: float
    live_eligible: bool
    retire: bool


def e_process(monthly_pvalues: FloatArray) -> EProcess:
    """Each month on NEW non-overlapping OOS data: e_m = 1/(2 sqrt(p_m)), E_M = prod e_m.
    E[e_m] = 1 under the null, so by Ville P(sup E_M >= 20) <= 5%. Live-eligible when E_M >= 20;
    retired when E_M < 1 for two consecutive months. Repeated monthly p-values are repeated peeking;
    this is not."""
    p = np.clip(np.asarray(monthly_pvalues, dtype=np.float64), 1e-300, 1.0)
    e = 1.0 / (2.0 * np.sqrt(p))
    E = np.cumprod(e)
    below = E < 1.0
    retire = (
        any(bool(below[i] and below[i + 1]) for i in range(len(E) - 1))
        if len(E) >= E_RETIRE_MONTHS
        else False
    )
    return EProcess(E, float(E.max()) if len(E) else 0.0, bool(len(E) and E[-1] >= E_LIVE), retire)


# ---------------------------------------------------------------------------------------------
# the verdict
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    verdict: str                      # "REAL" | "NOTHING"
    reasons: list[str]                # why NOTHING; empty when REAL
    n_events: int
    n_clusters: int
    n_independent: int
    sharpe: float
    min_detectable_sharpe: float
    power_passed: bool
    p_shuffle: float
    alpha_level: float
    sr0: float
    dsr: float
    beta_gate: BetaGate
    arcsine: Arcsine
    doob: Doob | None = None
    simpson: Simpson | None = None
    null_metrics: FloatArray = field(default_factory=lambda: np.zeros(0))


def validate(
    *,
    trade_returns: FloatArray,
    trade_times: IntArray,
    holding: float,
    underlying_returns: FloatArray,
    alpha_level: float,
    n_variants: int = 1,
    var_sr: float = 0.0,
    expected_sharpe: float | None = None,
    n_eff_scale: float = 1.0,
    n_shuffles: int | None = None,
    block: int = 1,
    sizing_rule: Callable[[FloatArray], FloatArray] | None = None,
    regime_labels: dict[str, NDArray[np.str_]] | None = None,
    rng: np.random.Generator | None = None,
) -> Verdict:
    """Run every step of M1 on out-of-sample trades and return the verdict with its reasons.

    `alpha_level` is the CURRENT level from the online FDR (registry), not 0.05 by habit.
    `n_eff_scale` = N_eff / N when the trades span several assets (effective_bets).
    `expected_sharpe` is the mechanism's plausible per-trade Sharpe for the power check; if None
    the observed Sharpe is used, which is circular and says so in the reasons.
    """
    r = np.asarray(trade_returns, dtype=np.float64)
    u = np.asarray(underlying_returns, dtype=np.float64)
    t = np.asarray(trade_times)
    if not (len(r) == len(u) == len(t)):
        raise ValueError("returns, underlying and times must align trade by trade")
    reasons: list[str] = []

    ids = cluster_ids(t, holding=holding)
    cr = cluster_returns(r, ids)
    cu = cluster_returns(u, ids)
    n_ind = int(round(len(cr) * n_eff_scale))
    sr = sharpe(cr)

    mds = min_detectable_sharpe(n_trades=n_ind, alpha=alpha_level)
    s_plan = expected_sharpe if expected_sharpe is not None else max(sr, 1e-9)
    if expected_sharpe is None:
        reasons_power_note = "power check used the OBSERVED Sharpe (circular); register expected_sharpe"
    else:
        reasons_power_note = ""
    power = power_check(n_independent=n_ind, s=s_plan, alpha=alpha_level)
    if not power:
        reasons.append(
            f"power: {n_ind} independent trades (floor {HARD_FLOOR_TRADES}); needs "
            f"{n_required(s_plan, alpha_level) if s_plan > 0 else 'inf'} at s={s_plan:.3f}; "
            f"min detectable s={mds:.3f}" + (f"; {reasons_power_note}" if reasons_power_note else "")
        )

    n_sh = n_shuffles if n_shuffles is not None else _null.n_shuffles(alpha_level)
    p, nulls = shuffle_test(cr, n_shuffles=n_sh, block=block, rng=rng)
    if not p < alpha_level:
        reasons.append(f"shuffle: p={p:.4f} is not below the current alpha level {alpha_level:.4f}")

    skew = float(stats.skew(cr)) if len(cr) > 2 else 0.0
    kurt = float(stats.kurtosis(cr, fisher=False)) if len(cr) > 3 else 3.0
    sr0, dsr = deflated_sharpe(sr=sr, n_periods=len(cr), skew=skew, kurt=kurt,
                               n_variants=n_variants, var_sr=var_sr)
    if not dsr >= DSR_FLOOR:
        reasons.append(f"DSR={dsr:.3f} < {DSR_FLOOR} (SR={sr:.3f}, SR0={sr0:.3f}: the gap is selection)")

    bg = beta_gate(cr, cu)
    if not bg.hedged_p < alpha_level:
        reasons.append(
            f"hedged version not significant (p={bg.hedged_p:.3f}); directional result presumed beta"
        )
    if not bg.alpha_p < alpha_level:
        reasons.append(f"alpha not significant (p={bg.alpha_p:.3f}); {bg.sentence}")

    arc = arcsine_warning(np.cumsum(cr))
    doob = doob_check(cr, sizing_rule=sizing_rule, rng=rng) if sizing_rule is not None else None
    simp = simpson_check(r, regime_labels) if regime_labels else None
    if simp is not None and simp.flagged:
        reasons.append("SIMPSON: " + "; ".join(simp.reasons))

    verdict = "REAL" if not reasons else "NOTHING"
    return Verdict(verdict, reasons, len(r), len(cr), n_ind, sr, mds, power, p, alpha_level, sr0, dsr,
                   bg, arc, doob, simp, nulls)

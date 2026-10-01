"""The nulls. One implementation each; every module imports from here (CRM.md §5.9).

Nothing is real until it beats shuffled or block-shuffled REAL data after correction for how
many things were tested. Gaussian noise is never a null, anywhere — a test greps for it.

    shuffle          label-shuffle; destroys all serial dependence
    block_shuffle    permutes contiguous blocks; keeps vol clustering inside each block
    circular_shift   rolls the series; keeps every autocorrelation, breaks alignment with the other series
    placebo_onsets   matched fake event times for directional tests (§7.2b)
    n_shuffles       N >= 20/alpha, minimum 10,000 — the count must resolve the threshold
    shuffle_pvalue   fraction of nulls beating the real metric

Plain shuffles destroy vol clustering and make regime-dependent strategies look real — use
block_shuffle for anything with serial dependence, and build tick-level nulls on dollar bars (M18).
"""

from __future__ import annotations

import math
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

MIN_SHUFFLES = 10_000


def _rng(rng: np.random.Generator | None) -> np.random.Generator:
    return np.random.default_rng() if rng is None else rng


def shuffle(x: FloatArray, *, rng: np.random.Generator | None = None) -> FloatArray:
    """Permute every element. Destroys ALL serial dependence — that is the point and the trap:
    a strategy whose 'edge' is vol clustering beats this null and is still noise."""
    return _rng(rng).permutation(np.asarray(x, dtype=np.float64))


def block_shuffle(
    x: FloatArray, *, block: int = 24, rng: np.random.Generator | None = None
) -> FloatArray:
    """Permute the ORDER of contiguous blocks; the inside of each block is untouched, so
    within-block dependence (vol clustering, intraday seasonality up to `block`) survives.
    A ragged tail is its own block. Default block=24 bars per §5.9."""
    x = np.asarray(x, dtype=np.float64)
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    n = len(x)
    starts = np.arange(0, n, block)
    order = _rng(rng).permutation(len(starts))
    return np.concatenate([x[starts[i] : starts[i] + block] for i in order]) if n else x.copy()


def circular_shift(
    x: FloatArray, *, min_shift: int, rng: np.random.Generator | None = None
) -> tuple[FloatArray, int]:
    """Roll the series by a random k with min_shift <= k <= n - min_shift. Every autocorrelation
    is preserved (up to the wrap); only the alignment with OTHER series is broken — the null for
    lead-lag and cross-series claims (M19, M22). Returns (shifted, k)."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    lo, hi = min_shift, n - min_shift
    if min_shift < 1 or lo > hi:
        raise ValueError(f"min_shift={min_shift} leaves no admissible shift for n={n}")
    k = int(_rng(rng).integers(lo, hi + 1))
    return np.roll(x, k), k


def placebo_onsets(
    real_onsets: IntArray,
    candidates: IntArray,
    *,
    n: int = 300,
    exclude_within: int = 0,
    strata: NDArray[np.str_] | None = None,
    real_strata: NDArray[np.str_] | None = None,
    rng: np.random.Generator | None = None,
) -> IntArray:
    """n fake onset times drawn from `candidates`, none within `exclude_within` of a real onset.

    With `strata` (one label per candidate) and `real_strata` (one per real onset) the draw is
    stratified to the real onsets' label counts — §7.2b's 'matched on volatility, hour and
    distance', so BTC's drift and the calendar cannot flatter a directional signal.

    Fails loudly when a stratum runs out of admissible candidates. A placebo set that silently
    came up short is a null with the wrong fingerprint.
    """
    g = _rng(rng)
    real = np.asarray(real_onsets, dtype=np.int64)
    cands = np.asarray(candidates, dtype=np.int64)
    if exclude_within > 0 and len(real):
        near = np.zeros(len(cands), dtype=bool)
        for r in real:
            near |= np.abs(cands - r) <= exclude_within
        admissible = ~near
    else:
        admissible = np.ones(len(cands), dtype=bool)

    if strata is None:
        pool = cands[admissible]
        if len(pool) < n:
            raise ValueError(f"only {len(pool)} admissible candidates for n={n} placebos")
        return np.sort(g.choice(pool, size=n, replace=False))

    if real_strata is None or len(real_strata) != len(real):
        raise ValueError("strata given: real_strata must label every real onset")
    labels, counts = np.unique(np.asarray(real_strata), return_counts=True)
    # allocate n across strata in the real onsets' proportions (largest remainder)
    raw = counts / counts.sum() * n
    alloc = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - alloc))[: n - alloc.sum()]:
        alloc[i] += 1
    out: list[IntArray] = []
    for label, k in zip(labels, alloc, strict=True):
        pool = cands[admissible & (np.asarray(strata) == label)]
        if len(pool) < k:
            raise ValueError(f"stratum {label!r}: {len(pool)} admissible candidates for {k} placebos")
        out.append(g.choice(pool, size=int(k), replace=False))
    return np.sort(np.concatenate(out))


def n_shuffles(alpha: float, *, minimum: int = MIN_SHUFFLES) -> int:
    """§5.9: the shuffle count must resolve the threshold — N >= 20/alpha, never below 10,000.
    At alpha = 0.0023 that is still 10,000; at 1e-4 it is 200,000."""
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    return max(minimum, math.ceil(20.0 / alpha))


def shuffle_pvalue(real: float, nulls: FloatArray) -> float:
    """M1 step 3: p = fraction of shuffles beating the real metric. Higher metric = better."""
    nulls = np.asarray(nulls, dtype=np.float64)
    if len(nulls) == 0:
        raise ValueError("no null draws")
    return float(np.mean(nulls >= real))

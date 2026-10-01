"""M3 — what I actually make (CRM.md §M3).

Arithmetic mean mu_a vs geometric growth g = mean(ln(1 + r)); the gap is volatility drag,
g ~ mu_a - sigma^2/2. Leverage curve g(L) = mean(ln(1 + L r)) for L in {1, 1.5, 2, 3, 5, 10};
RUIN where any 1 + L r <= 0.

Ito's lemma: for dS = mu S dt + sigma S dW, d(ln S) = (mu - sigma^2/2) dt + sigma dW. The
-sigma^2/2 is the geometry of compounding a random path, and leverage scales it to -L^2 sigma^2/2,
which is why the curve is a downward parabola: doubling size doubles the drift and quadruples
the drag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]

LEVERAGE_CURVE: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0, 5.0, 10.0)


def growth_rate(r: FloatArray, *, leverage: float = 1.0) -> float:
    """time-average growth at leverage L; -inf (RUIN) if any 1 + L r <= 0"""
    x = leverage * np.asarray(r, dtype=np.float64)
    if np.any(1.0 + x <= 0.0):
        return float("-inf")
    return float(np.mean(np.log1p(x)))


@dataclass(frozen=True)
class Growth:
    arithmetic: float
    geometric: float
    drag: float                          # arithmetic - geometric
    leverage_curve: tuple[float, ...]
    growth_at: dict[float, float]        # -inf marks RUIN
    ruin_at_leverage: float | None       # first L on the curve with RUIN
    first_negative_leverage: float | None
    peak_leverage: float | None

    def describe(self) -> str:
        parts = []
        for lv in self.leverage_curve:
            g = self.growth_at[lv]
            parts.append(f"L={lv:g}: {'RUIN' if g == float('-inf') else f'{g:+.4%}'}")
        return (
            f"arithmetic {self.arithmetic:+.4%}  geometric {self.geometric:+.4%}  drag {self.drag:.4%}  |  "
            + "  ".join(parts)
        )


def growth_report(r: FloatArray, *, leverage_curve: tuple[float, ...] = LEVERAGE_CURVE) -> Growth:
    r = np.asarray(r, dtype=np.float64)
    if len(r) == 0:
        raise ValueError("empty returns")
    arith = float(np.mean(r))
    geo = growth_rate(r)
    at = {lv: growth_rate(r, leverage=lv) for lv in leverage_curve}
    ruin = next((lv for lv in leverage_curve if at[lv] == float("-inf")), None)
    first_neg = next((lv for lv in leverage_curve if at[lv] < 0.0), None)
    finite = {lv: g for lv, g in at.items() if g > float("-inf")}
    peak = max(finite, key=lambda k: finite[k]) if finite else None
    return Growth(arith, geo, arith - geo, tuple(leverage_curve), at, ruin, first_neg, peak)

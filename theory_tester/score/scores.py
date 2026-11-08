"""Scores: chi-squared, AIC, BIC per dataset block and combined, plus tension flags.

AIC = chi2 + 2k, BIC = chi2 + k ln N (k free parameters fitted to that block, N data points in it).
Delta values are always 'hypothesis minus Lambda-CDM': negative = the hypothesis does better.
Tension flags:
  goodness  : p-value of a block's chi^2 at the joint best fit (dof = N - k); flagged if p < 0.01
  PG test   : parameter-goodness-of-fit (Maltoni & Schwetz 2003) between cosmology datasets:
              chi2_PG = chi2_joint_min - sum_i chi2_i,min, dof = sum_i k_i - k_joint; flagged if p < 0.01
"""
from __future__ import annotations

import numpy as np
from scipy.stats import chi2 as chi2dist, norm


def aic(c, k):
    return float(c + 2 * k)


def bic(c, k, n):
    return float(c + k * np.log(max(n, 1)))


def pvalue(c, dof):
    dof = max(int(round(dof)), 1)
    return float(chi2dist.sf(c, dof))


def sigma_from_p(p):
    return float(norm.isf(max(p, 1e-300) / 2))


def delta_chi2_to_sigma(dchi2, dk):
    """Significance (Gaussian sigma) of an improvement dchi2 > 0 bought with dk extra parameters."""
    if dchi2 <= 0:
        return 0.0
    return sigma_from_p(chi2dist.sf(dchi2, max(dk, 1)))


def block(chi2, k, n):
    return dict(chi2=float(chi2), k=int(k), n=int(n), aic=aic(chi2, k), bic=bic(chi2, k, n),
                p_good=pvalue(chi2, n - k), flag_bad_fit=bool(pvalue(chi2, n - k) < 0.01))


def pg_test(chi2_joint, k_joint, singles):
    """singles: list of (chi2_min_i, k_i)."""
    c = chi2_joint - sum(s[0] for s in singles)
    dof = sum(s[1] for s in singles) - k_joint
    p = pvalue(c, dof)
    return dict(chi2_pg=float(c), dof=int(dof), p=p, sigma=sigma_from_p(p), flag=bool(p < 0.01))

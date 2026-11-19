"""Momentum-transfer cross-section for dark matter scattering through a Yukawa potential
V(r) = -/+ alpha_D exp(-m_phi r) / r  (light mediator, 'short-range force').

Analytic regimes of Tulin, Yu & Zurek 2013 (PRD 87, 115007; arXiv:1302.3898):
  Born       alpha m_chi / m_phi < 1
  classical  m_chi v / m_phi > 1   (Khrapak+2003 / Feng, Kaplinghat & Yu 2010 fits)
  resonant   otherwise            (Hulthen-potential s-wave phase shift, kappa = 1.6)
v is the relative velocity. Units: GeV internally; returned as sigma/m in cm^2/g.
"""
from __future__ import annotations

import numpy as np
from scipy.special import loggamma

C_KMS = 299792.458
GEV2_TO_CM2 = 0.389379e-27
GEV_TO_G = 1.782662e-24
KAPPA = 1.6


def sigma_T_over_m(v_kms, m_chi, m_phi, alpha, attractive: bool = True):
    """sigma_T / m_chi [cm^2/g] at relative speed v (km/s). m_chi, m_phi in GeV."""
    with np.errstate(all="ignore"):
        out = _sigma_T(np.atleast_1d(np.asarray(v_kms, float)) / C_KMS, m_chi, m_phi, alpha, attractive)
    return np.nan_to_num(out, nan=0.0, posinf=0.0) * GEV2_TO_CM2 / (m_chi * GEV_TO_G)


def _sigma_T(v, m_chi, m_phi, alpha, attractive):
    out = np.empty_like(v)
    born = alpha * m_chi / m_phi < 1.0
    R = m_chi * v / m_phi
    if born:
        s = 8 * np.pi * alpha ** 2 / (m_chi ** 2 * v ** 4) * (np.log1p(R ** 2) - R ** 2 / (1 + R ** 2))
        out[:] = s
    else:
        cl = R > 1.0
        if np.any(cl):
            vv = v[cl]
            beta = 2 * alpha * m_phi / (m_chi * vv ** 2)
            if attractive:
                s = np.where(beta < 0.1, 4 * np.pi / m_phi ** 2 * beta ** 2 * np.log1p(1 / beta),
                     np.where(beta < 1e3, 8 * np.pi / m_phi ** 2 * beta ** 2 / (1 + 1.5 * beta ** 1.65),
                              np.pi / m_phi ** 2 * (1 + np.log(beta) - 1 / (2 * np.log(np.maximum(beta, 1.0001)))) ** 2))
            else:
                s = np.where(beta < 1, 2 * np.pi / m_phi ** 2 * beta ** 2 * np.log1p(beta ** -2),
                             np.pi / m_phi ** 2 * (np.log(2 * beta) - np.log(np.log(2 * beta))) ** 2)
            out[cl] = s
        rs = ~cl
        if np.any(rs):
            vv = v[rs]
            sgn = 1.0 if attractive else -1.0
            a = vv / (2 * alpha)
            b = alpha * m_chi / m_phi
            c = 1j * a * b / KAPPA            # i m_chi v / (2 kappa m_phi)
            root = np.sqrt((sgn * b / KAPPA - (a * b / KAPPA) ** 2).astype(complex))
            lp, lm = 1 + c + root, 1 + c - root
            # delta_0 = arg[ i Gamma(2c) / (Gamma(l+) Gamma(l-)) ]; take the phase from the log so nothing overflows
            delta = np.pi / 2 + np.imag(loggamma(2 * c) - loggamma(lp) - loggamma(lm))
            out[rs] = 16 * np.pi * np.sin(delta) ** 2 / (m_chi ** 2 * vv ** 2)
    return out


_U = np.linspace(1e-3, 9.0, 220)   # v / (2 nu): Maxwellian kernel lives below ~6


def sigma_eff_over_m(nu_kms, m_chi, m_phi, alpha, attractive=True):
    """Effective cross-section of Yang & Yu 2022 / Yang+2023 eq. (2.1), with sigma_T standing in for the
    viscosity-weighted differential cross-section: weight v^7 exp(-v^2/4nu^2). nu = 0.64 Vmax for a halo."""
    nu = np.atleast_1d(np.asarray(nu_kms, float))
    out = np.empty_like(nu)
    w = _U ** 7 * np.exp(-_U ** 2)
    for i, n in enumerate(nu):
        s = sigma_T_over_m(2 * n * _U, m_chi, m_phi, alpha, attractive)
        out[i] = np.trapezoid(w * s, _U) / np.trapezoid(w, _U)
    return out


def sigma_mean_over_m(vmean_kms, m_chi, m_phi, alpha, attractive=True):
    """<sigma v>/<v> for a Maxwellian of relative speeds with mean <v> (how Kaplinghat+16 / Sagunski+21 /
    Andrade+22 define their halo-averaged cross-sections)."""
    nu = np.asarray(vmean_kms, float) * np.sqrt(np.pi) / 4
    nu = np.atleast_1d(nu)
    out = np.empty_like(nu)
    w = _U ** 3 * np.exp(-_U ** 2)
    for i, n in enumerate(nu):
        s = sigma_T_over_m(2 * n * _U, m_chi, m_phi, alpha, attractive)
        out[i] = np.trapezoid(w * s, _U) / np.trapezoid(w, _U)
    return out

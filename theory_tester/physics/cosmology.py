"""Background expansion, distances, sound horizon, CMB distance priors and linear growth.

A model is a `Background`: physical baryon density omega_b, h, and a callable `dark(a)` that
returns the physical density (in omega = Omega h^2 units) of everything that is not baryons or
radiation, plus optional curvature. Every hypothesis supplies its own `dark(a)`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
from scipy.integrate import cumulative_trapezoid, solve_ivp

C_KMS = 299792.458
OMEGA_GAMMA = 2.4728e-5            # T_CMB = 2.7255 K
NEFF = 3.046
OMEGA_NU = 0.000645                # one massive neutrino of 0.06 eV (today's density)
_OMEGA_NU_REL = OMEGA_GAMMA * 0.22711 * NEFF / 3     # that species' density while relativistic (a^-4 coefficient)
OMEGA_R = OMEGA_GAMMA * (1 + 0.22711 * NEFF) - _OMEGA_NU_REL   # photons + the two massless species
_A_NR = _OMEGA_NU_REL / OMEGA_NU


def omega_nu(a):
    """Massive-neutrino density: radiation-like before a ~ 0.009, matter-like after (smooth interpolation)."""
    return OMEGA_NU * a ** -3 * np.sqrt(1 + (_A_NR / a) ** 2)

# fine grid in x = ln(1+z), shared by every distance computation
_X = np.concatenate([np.linspace(0, np.log(1 + 3.0), 1500)[:-1], np.linspace(np.log(1 + 3.0), np.log(1 + 1200.0), 1500)])
_Z = np.expm1(_X)


@dataclass
class Background:
    h: float
    omega_b: float
    dark: Callable[[np.ndarray], np.ndarray]      # physical density of non-baryonic, non-radiation stuff (omega units)
    omega_m_early: float                           # omega of everything that scales as a^-3 at z ~ 1000 (for R)
    omega_k: float = 0.0                           # curvature density parameter Omega_k (not h^2)
    label: str = ""
    _cache: dict = field(default_factory=dict, repr=False)

    # ---------------------------------------------------------------- expansion
    def E(self, z):
        a = 1.0 / (1.0 + np.asarray(z, float))
        h2 = self.h ** 2
        rho = OMEGA_R * a ** -4 + self.omega_b * a ** -3 + omega_nu(a) + self.dark(a)
        return np.sqrt(np.maximum(rho / h2 + self.omega_k * a ** -2, 1e-30))

    def valid(self) -> bool:
        a = 1.0 / (1.0 + _Z)
        rho = OMEGA_R * a ** -4 + self.omega_b * a ** -3 + omega_nu(a) + self.dark(a)
        e2 = rho / self.h ** 2 + self.omega_k * a ** -2
        # flatness/closure: E(0) must be 1
        return bool(np.all(np.isfinite(e2)) and np.all(e2 > 0) and abs(e2[0] - 1) < 1e-6)

    # ---------------------------------------------------------------- distances (Mpc)
    def _chi(self):
        if "chi" not in self._cache:
            invE = 1.0 / self.E(_Z)
            self._cache["chi"] = cumulative_trapezoid(invE * (1 + _Z), _X, initial=0.0) * C_KMS / (100 * self.h)
        return self._cache["chi"]

    def DM(self, z):
        chi = np.interp(z, _Z, self._chi())
        if abs(self.omega_k) < 1e-8:
            return chi
        dh = C_KMS / (100 * self.h)
        sk = np.sqrt(abs(self.omega_k)) / dh
        return np.sinh(sk * chi) / sk if self.omega_k > 0 else np.sin(sk * chi) / sk

    def DH(self, z):
        return C_KMS / (100 * self.h * self.E(z))

    def DV(self, z):
        return (z * self.DM(z) ** 2 * self.DH(z)) ** (1 / 3)

    # ---------------------------------------------------------------- sound horizon
    def rs(self, zstar: float) -> float:
        """Comoving sound horizon at redshift zstar, by direct integration (Mpc)."""
        lna = np.linspace(np.log(1e-9), np.log(1 / (1 + zstar)), 4000)
        a = np.exp(lna)
        Rb = 3 * self.omega_b / (4 * OMEGA_GAMMA) * a
        cs = C_KMS / np.sqrt(3 * (1 + Rb))
        H = 100 * self.h * self.E(1 / a - 1)
        return float(np.trapezoid(cs / (a * H), lna))

    def zstar(self) -> float:   # Hu & Sugiyama 1996
        wb, wm = self.omega_b, self.omega_m_early + OMEGA_NU
        g1 = 0.0783 * wb ** -0.238 / (1 + 39.5 * wb ** 0.763)
        g2 = 0.560 / (1 + 21.1 * wb ** 1.81)
        return 1048 * (1 + 0.00124 * wb ** -0.738) * (1 + g1 * wm ** g2)

    def zdrag(self) -> float:   # Eisenstein & Hu 1998
        wb, wm = self.omega_b, self.omega_m_early + OMEGA_NU
        b1 = 0.313 * wm ** -0.419 * (1 + 0.607 * wm ** 0.674)
        b2 = 0.238 * wm ** 0.223
        return 1291 * wm ** 0.251 / (1 + 0.659 * wm ** 0.828) * (1 + b1 * wb ** b2)

    def rdrag(self) -> float:
        """Drag-epoch sound horizon. Direct integration to the EH98 z_drag, rescaled by one fixed constant so
        that it reproduces the Aubourg+2015 CAMB-calibrated fit at the Planck 2018 cosmology (the fitting formula
        for z_drag is ~2% off in absolute terms; the constant is the same for every model)."""
        return self.rs(self.zdrag()) * RD_CALIBRATION

    # ---------------------------------------------------------------- CMB distance priors
    def cmb_vector(self) -> np.ndarray:
        """(R, l_A, omega_b) computed exactly as prescribed by Chen, Huang & Wang 2019 (arXiv:1808.05724), whose
        priors we use: radiation from z_eq = 2.5e4 omega_m (T/2.7)^-4, 3/(4 omega_gamma) = 31500 (T/2.7)^-4, and their
        printed z_* fit (Hu & Sugiyama with g1 coefficient 0.0738). The model enters through its late-time E(z):
        our own radiation/neutrino terms are swapped for theirs. With this recipe the Planck 2018 best fit gives
        chi^2 ~ 1.7 against the priors; with textbook coefficients it gives ~19, so recipe consistency matters."""
        T = (2.7255 / 2.7) ** -4
        wb = self.omega_b
        wm = self.omega_m_early + OMEGA_NU
        g1 = 0.0738 * wb ** -0.238 / (1 + 39.5 * wb ** 0.763)
        g2 = 0.560 / (1 + 21.1 * wb ** 1.81)
        zs = 1048 * (1 + 0.00124 * wb ** -0.738) * (1 + g1 * wm ** g2)
        h2 = self.h ** 2
        orad = (wm / h2) / (1 + 2.5e4 * wm * T)

        def Ec(a):
            rho = self.omega_b * a ** -3 + OMEGA_NU * a ** -3 + self.dark(a)
            return np.sqrt(np.maximum(rho / h2 + orad * a ** -4 + self.omega_k * a ** -2, 1e-30))
        lna = np.linspace(np.log(1e-9), np.log(1 / (1 + zs)), 6000)
        a = np.exp(lna)
        rs = C_KMS / (100 * self.h) * np.trapezoid(1 / (a * Ec(a) * np.sqrt(3 * (1 + 31500 * wb * T * a))), lna)
        x = np.linspace(0, np.log(1 + zs), 6000)
        zz = np.expm1(x)
        chi = C_KMS / (100 * self.h) * np.trapezoid((1 + zz) / Ec(1 / (1 + zz)), x)
        if abs(self.omega_k) > 1e-8:
            sk = np.sqrt(abs(self.omega_k)) * 100 * self.h / C_KMS
            chi = np.sinh(sk * chi) / sk if self.omega_k > 0 else np.sin(sk * chi) / sk
        R = np.sqrt(wm / h2) * 100 * self.h * chi / C_KMS
        return np.array([R, np.pi * chi / rs, wb])


def _aubourg_rd(wb, wc, wnu=OMEGA_NU):
    return 55.154 * np.exp(-72.3 * (wnu + 0.0006) ** 2) / ((wb + wc + wnu) ** 0.25351 * wb ** 0.12807)


def _calibrate():
    wb, wc, h = 0.02236, 0.1200, 0.6736
    b = Background(h=h, omega_b=wb, dark=lambda a: wc * a ** -3 + (h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc), omega_m_early=wb + wc)
    return _aubourg_rd(wb, wc) / b.rs(b.zdrag())


RD_CALIBRATION = 1.0
RD_CALIBRATION = _calibrate()


# ============================================================================ likelihoods
def chi2_bao(bg: Background, bao, rd: Optional[float] = None) -> float:
    rd = bg.rdrag() if rd is None else rd
    th = []
    for z, k in zip(bao.z, bao.kind):
        if k.startswith("DV"):
            th.append(bg.DV(z) / rd)
        elif k.startswith("DM"):
            th.append(bg.DM(z) / rd)
        elif k.startswith("DH"):
            th.append(bg.DH(z) / rd)
        else:
            raise ValueError(k)
    d = bao.value - np.array(th)
    return float(d @ bao.icov @ d)


def chi2_sn(bg: Background, sn) -> float:
    """Pantheon+ with the absolute magnitude (and hence H0) analytically marginalised."""
    dl = (1 + sn.zhel) * bg.DM(sn.z)
    mu = 5 * np.log10(np.maximum(dl, 1e-10)) + 25
    d = sn.mb - mu
    Cd = sn.icov @ d
    A = float(d @ Cd)
    B = float(Cd.sum())
    Csum = float(sn.icov.sum())
    return A - B * B / Csum


def chi2_cmb(bg: Background, cmb) -> float:
    d = bg.cmb_vector() - cmb.mean
    return float(d @ cmb.icov @ d)


# ============================================================================ growth
def growth_smooth(bg: Background, omega_clustering: Callable[[np.ndarray], np.ndarray], z_out: np.ndarray):
    """Linear growth for a model whose clustering component(s) have zero pressure and whose dark energy is
    smooth. Returns (D(z_out)/D(0), f(z_out)). omega_clustering(a): physical density of clustering matter."""
    def rhs(lna, y):
        a = np.exp(lna)
        z = 1 / a - 1
        E = bg.E(z)
        eps = 1e-4
        dlnE = (np.log(bg.E(1 / (a * np.exp(eps)) - 1)) - np.log(bg.E(1 / (a * np.exp(-eps)) - 1))) / (2 * eps)
        Om = omega_clustering(a) / (bg.h ** 2 * E ** 2)
        d, dp = y
        return [dp, -(2 + dlnE) * dp + 1.5 * Om * d]
    a0 = 1e-3
    sol = solve_ivp(rhs, [np.log(a0), 0.0], [a0, a0], dense_output=True, rtol=1e-6, atol=1e-10)
    lna = np.log(1 / (1 + np.asarray(z_out)))
    d, dp = sol.sol(lna)
    d0 = sol.sol(0.0)[0]
    return d / d0, dp / d


def growth_unified_fluid(bg: Background, w_fn, cs2_fn, omega_fluid_fn, z_out, k_hmpc: float = 0.1):
    """Linear growth of baryons + one dark fluid with equation of state w(a) and sound speed c_s^2(a),
    sub-horizon neo-Newtonian equations (Reis 2003, PRD 67, 087301; Lima, Zanchin & Brandenberger 1997):
        d' = -3(cs2 - w) d - (1+w) T
        T' = -(2 + dlnH) T - 1.5 sum_i Om_i d_i (1 + 3 cs2_i) + cs2 (k/aH)^2 d / (1+w)
    with ' = d/dln a. Baryons have w = cs2 = 0. Returns baryon growth D_b(z)/D_b(0) and f_b = dlnD_b/dlna,
    the quantity that redshift-space distortions of galaxies (which live in the baryon wells) measure."""
    k = k_hmpc * bg.h  # 1/Mpc

    def rhs(lna, y):
        a = np.exp(lna)
        z = 1 / a - 1
        E = bg.E(z)
        H = 100 * bg.h * E / C_KMS  # 1/Mpc
        eps = 1e-4
        dlnE = (np.log(bg.E(1 / (a * np.exp(eps)) - 1)) - np.log(bg.E(1 / (a * np.exp(-eps)) - 1))) / (2 * eps)
        h2E2 = bg.h ** 2 * E ** 2
        Ob = (bg.omega_b * a ** -3 + omega_nu(a)) / h2E2
        Of = omega_fluid_fn(a) / h2E2
        w = w_fn(a)
        c2 = cs2_fn(a)
        db, Tb, df, Tf = y
        src = 1.5 * (Ob * db + Of * df * (1 + 3 * c2))
        ddb = -Tb
        dTb = -(2 + dlnE) * Tb - src
        ddf = -3 * (c2 - w) * df - (1 + w) * Tf
        dTf = -(2 + dlnE) * Tf - src + c2 * (k / (a * H)) ** 2 * df / max(1 + w, 1e-6)
        return [ddb, dTb, ddf, dTf]
    a0 = 1e-3
    y0 = [a0, -a0, a0, -a0]
    sol = solve_ivp(rhs, [np.log(a0), 0.0], y0, method="LSODA", dense_output=True, rtol=1e-6, atol=1e-12)
    if not sol.success:
        return None, None
    lna = np.log(1 / (1 + np.asarray(z_out)))
    db, Tb, _, _ = sol.sol(lna)
    d0 = sol.sol(0.0)[0]
    return db / d0, -Tb / db


def chi2_fsigma8(bg: Background, growth: tuple, sigma8_0: float, gd) -> float:
    """Gold-2017 chi^2 with the Alcock-Paczynski fiducial-cosmology correction of Nesseris+2017 eq. (2.3)."""
    D, f = growth
    model = f * sigma8_0 * D
    ratio = np.empty_like(gd.z)
    for i, (z, om) in enumerate(zip(gd.z, gd.om_fid)):
        ef = np.sqrt(om * (1 + z) ** 3 + 1 - om)
        zz = np.linspace(0, z, 200)
        daf = np.trapezoid(1 / np.sqrt(om * (1 + zz) ** 3 + 1 - om), zz)
        H0 = 100 * bg.h
        ratio[i] = (bg.E(z) * bg.DM(z) * H0 / C_KMS) / (ef * daf)
    v = gd.fs8 - ratio * model
    return float(v @ gd.icov @ v)


def best_sigma8(bg, growth, gd) -> tuple[float, float]:
    """sigma8_0 enters linearly: minimise analytically."""
    D, f = growth
    base = f * D
    ratio = np.empty_like(gd.z)
    for i, (z, om) in enumerate(zip(gd.z, gd.om_fid)):
        ef = np.sqrt(om * (1 + z) ** 3 + 1 - om)
        zz = np.linspace(0, z, 200)
        daf = np.trapezoid(1 / np.sqrt(om * (1 + zz) ** 3 + 1 - om), zz)
        ratio[i] = (bg.E(z) * bg.DM(z) * 100 * bg.h / C_KMS) / (ef * daf)
    t = ratio * base
    s8 = float((t @ gd.icov @ gd.fs8) / (t @ gd.icov @ t))
    return s8, chi2_fsigma8(bg, growth, s8, gd)


def growth_smooth_fast(bg: Background, omega_clustering: Callable[[np.ndarray], np.ndarray], z_out, n: int = 600):
    """Same equation as growth_smooth, fixed-step RK4 on a ln(a) grid (fast enough for MCMC). Agrees with the
    adaptive solver to <1e-4."""
    lna = np.linspace(np.log(1e-3), 0.0, 2 * n + 1)
    a = np.exp(lna)
    E = bg.E(1 / a - 1)
    dlnE = np.gradient(np.log(E), lna)
    Om = omega_clustering(a) / (bg.h ** 2 * E ** 2)
    dstep = lna[2] - lna[0]
    d, dp = a[0], a[0]
    D = np.empty(n + 1)
    F = np.empty(n + 1)
    D[0], F[0] = d, 1.0

    def f(i, d, dp):
        return dp, -(2 + dlnE[i]) * dp + 1.5 * Om[i] * d
    for k in range(n):
        i = 2 * k
        k1 = f(i, d, dp)
        k2 = f(i + 1, d + 0.5 * dstep * k1[0], dp + 0.5 * dstep * k1[1])
        k3 = f(i + 1, d + 0.5 * dstep * k2[0], dp + 0.5 * dstep * k2[1])
        k4 = f(i + 2, d + dstep * k3[0], dp + dstep * k3[1])
        d, dp = d + dstep / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]), dp + dstep / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        D[k + 1], F[k + 1] = d, dp / d
    lg = lna[::2]
    lz = np.log(1 / (1 + np.asarray(z_out)))
    return np.interp(lz, lg, D) / D[-1], np.interp(lz, lg, F)

"""Hypothesis 4 (Clayten, lead): a short-range, speed-dependent dark force.

Dark matter particles (mass m_chi) exchange a light mediator (mass m_phi, coupling alpha_D): Yukawa potential.
Range ~ 1/m_phi; the momentum-transfer cross-section falls with collision speed (physics/yukawa.py).

Predictions:
  v(r) SPARC        : each galaxy's CDM (NFW) halo evolved for its age with the parametric gravothermal SIDM
                      model (physics/sidm.py) at the halo's effective cross-section sigma_eff(nu = 0.64 Vmax).
                      Cores form at small tau = t/t_c; halos approaching tau ~ 1 core-collapse (denser).
  dwarf rho(150 pc) : same model for the Read+2019 dwarfs (pre-infall M200 quoted there). Dense dwarfs can be
                      matched either by low sigma (still cuspy) or by very high sigma (collapsed): both branches
                      are in the model.
  clusters          : merger lag beta = 1 - exp(-sigma_T(v)/sigma*) (Harvey+2015); halo-averaged
                      <sigma v>/<v> against the cluster/group strong-lensing limits.
  H(z), CMB         : elastic scattering does not change the expansion history -> Lambda-CDM background.
                      The cosmology block therefore inherits the Lambda-CDM fit (stated, not hidden).
The 2610.26877 reproduction lives in hypotheses/h4_check_2610_26877.py.
"""
from __future__ import annotations

import numpy as np

from fit.galaxies import fit_one, halo_c_prior, starts_halo, baryon_v2
from physics import yukawa
from physics.halos import nfw_from_m200, v_cored, c200_dutton_maccio, C_SCATTER_DEX, rho_cored
from physics.sidm import sidm_profile, nu_eff, formation_lookback_gyr

ID = "H4"
NAME = "Short-range speed-dependent dark force (Yukawa SIDM)"

# grid of effective cross-sections (cm^2/g) on which every galaxy and dwarf is profiled
SIGMA_GRID = np.array([0.0, 0.1, 0.3, 0.6, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 30.0, 50.0, 80.0, 120.0, 200.0, 350.0])
HALO_BOUNDS = [(6.0, 14.5), (0.0, np.log10(60.0))]


# ------------------------------------------------------------------ SPARC
def _total_v2_factory(sigma):
    def total_v2(g, yd, yb, hp):
        M = 10 ** hp[0]
        rhos0, rs0, _ = nfw_from_m200(M, 10 ** hp[1])
        rhos, rs, rc, _ = sidm_profile(rhos0, rs0, M, sigma)
        return baryon_v2(g, yd, yb) + v_cored(g.r, rhos, rs, rc) ** 2
    return total_v2


def _prior(g, hp):
    return halo_c_prior(hp[0], hp[1])


def galaxy_worker(g):
    """Profile the galaxy's chi^2 over SIGMA_GRID. Returns per-grid chi2 and the halo's nu_eff."""
    rows = []
    starts = starts_halo(g)
    for s in SIGMA_GRID:
        f = fit_one(g, _total_v2_factory(s), starts, HALO_BOUNDS, _prior, ["logM200", "logc"])
        M = 10 ** f.params["logM200"]
        rhos0, rs0, _ = nfw_from_m200(M, 10 ** f.params["logc"])
        _, _, rc, tau = sidm_profile(rhos0, rs0, M, s)
        rows.append(dict(sigma=float(s), chi2_data=f.chi2_data, chi2_prior=f.chi2_prior, nu=float(nu_eff(rhos0, rs0)),
                         rc=float(rc), tau=tau, params=f.params))
        starts = [(f.params["logM200"], f.params["logc"])] + starts[:2]
    return dict(name=g.name, npts=len(g.r), nparams=rows[0]["params"].__len__(), grid=rows)


def galaxy_chi2_given_sigma_fn(res, sigma_of_nu):
    """chi^2 (data + prior) for one galaxy when the cross-section law is sigma_eff(nu)."""
    chi = np.array([r["chi2_data"] + r["chi2_prior"] for r in res["grid"]])
    nu = res["grid"][0]["nu"]
    s = float(sigma_of_nu(nu))
    x = np.log10(SIGMA_GRID + 0.03)
    return float(np.interp(np.log10(min(max(s, 0.0), SIGMA_GRID[-1]) + 0.03), x, chi)), s


# ------------------------------------------------------------------ dwarfs
def dwarf_log_rho150_grid(d, rng, n=300):
    """For each sigma on the grid: distribution (mean, sd) of log10 rho(150 pc), marginalising M200 error,
    concentration scatter (0.11 dex) and formation-time scatter (0.16 dex, Yang+2023). Returns arrays and the
    dwarf's median nu_eff."""
    M = np.clip(rng.normal(d.M200, d.eM200, n), 0.1 * d.M200, None)
    c = 10 ** (np.log10(c200_dutton_maccio(M)) + rng.normal(0, C_SCATTER_DEX, n))
    tage = formation_lookback_gyr(M) * 10 ** rng.normal(0, 0.16, n)
    tage = np.minimum(tage, 13.6)
    rhos0, rs0, _ = nfw_from_m200(M, c)
    mu, sd = [], []
    for s in SIGMA_GRID:
        vals = np.empty(n)
        for i in range(n):
            rhos, rs, rc, _ = sidm_profile(rhos0[i], rs0[i], M[i], s, tage[i])
            vals[i] = np.log10(rho_cored(0.15, rhos, rs, rc))
        mu.append(vals.mean())
        sd.append(vals.std())
    return np.array(mu), np.array(sd), float(np.median(nu_eff(rhos0, rs0)))


def dwarf_chi2(d, grid, sigma):
    mu, sd, _ = grid
    x = np.log10(SIGMA_GRID + 0.03)
    xs = np.log10(min(max(sigma, 0), SIGMA_GRID[-1]) + 0.03)
    m, s = np.interp(xs, x, mu), np.interp(xs, x, sd)
    return obs_chi2_log(d, m, s)


def obs_chi2_log(d, m, s):
    lo = np.log10(d.rho150) - np.log10(d.rho150 - d.erho_lo)
    hi = np.log10(d.rho150 + d.erho_hi) - np.log10(d.rho150)
    e = hi if m > np.log10(d.rho150) else lo
    return float((m - np.log10(d.rho150)) ** 2 / (e ** 2 + s ** 2))


# ------------------------------------------------------------------ clusters
def cluster_chi2(sig_of_v_point, sig_of_v_mean, constraints, rng_seed=0):
    """Total chi^2 of the cluster/group block for given cross-section laws, plus per-constraint pieces."""
    parts = {}
    for c in constraints:
        if c["kind"] == "beta":
            s = float(sig_of_v_point(c["v"]))
            ss = np.linspace(0.5, 15, 60)
            w = np.exp(-0.5 * ((ss - c["sigma_star"]) / c["esigma_star"]) ** 2)
            beta = 1 - np.exp(-s / ss)
            like = np.sum(w * np.exp(-0.5 * ((beta - c["beta"]) / c["ebeta"]) ** 2)) / np.sum(w)
            parts[c["key"]] = float(-2 * np.log(max(like, 1e-300)))
        elif c["kind"] == "ul68":
            s = float(sig_of_v_point(c["v"]))
            parts[c["key"]] = float((s / c["ul"]) ** 2)
        elif c["kind"] == "ul95":
            s = float(sig_of_v_mean(c["v"]))
            parts[c["key"]] = float((s / (c["ul"] / 1.96)) ** 2)
    return float(sum(parts.values())), parts


# ------------------------------------------------------------------ particle-physics scan
THERMAL_ALPHA_PER_GEV = 2.45e-5   # alpha giving <sigma v> = pi alpha^2 / m^2 = 2.2e-26 cm^3/s (symmetric thermal relic)


def yukawa_laws(m_chi, m_phi, alpha, attractive=True):
    """Return (sigma_eff(nu), sigma_T(v), <sigma>(vmean)) as fast interpolating functions."""
    nus = np.logspace(0, np.log10(3000), 36)
    se = yukawa.sigma_eff_over_m(nus, m_chi, m_phi, alpha, attractive)
    vs = np.logspace(1, np.log10(6000), 36)
    st = yukawa.sigma_T_over_m(vs, m_chi, m_phi, alpha, attractive)
    sm = yukawa.sigma_mean_over_m(vs, m_chi, m_phi, alpha, attractive)
    lse, lst, lsm = (np.log10(np.maximum(a, 1e-30)) for a in (se, st, sm))
    f_eff = lambda nu: 10 ** np.interp(np.log10(nu), np.log10(nus), lse)
    f_T = lambda v: 10 ** np.interp(np.log10(v), np.log10(vs), lst)
    f_m = lambda v: 10 ** np.interp(np.log10(v), np.log10(vs), lsm)
    return f_eff, f_T, f_m


# ------------------------------------------------------------------ forecasts for the mediator
def dark_photon_lifetime_s(m_phi_gev, eps):
    """Lifetime if the mediator is a kinetically-mixed dark photon decaying to e+e- (m_phi > 1.022 MeV)."""
    me = 0.000511
    if m_phi_gev <= 2 * me:
        return np.inf
    alpha_em = 1 / 137.036
    r = (me / m_phi_gev) ** 2
    gamma = alpha_em * eps ** 2 * m_phi_gev / 3 * np.sqrt(1 - 4 * r) * (1 + 2 * r)
    return 6.582e-25 / gamma


def eps_bbn_floor(m_phi_gev, tau_max_s=1.0):
    """Smallest kinetic mixing for which the mediator decays before BBN (lifetime < 1 s)."""
    return float(np.sqrt(dark_photon_lifetime_s(m_phi_gev, 1.0) / tau_max_s))

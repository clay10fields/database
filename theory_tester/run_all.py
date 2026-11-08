"""One command: python run_all.py

Downloads and checksums every input, fits all seven hypotheses on every dataset that applies, logs every result
with the exact configuration that produced it under results/<run_id>/ (never overwritten), and writes
report/REPORT.md.

Options:
  --quick          small settings for a smoke test (subset of galaxies, short chains); report is marked QUICK
  --workers N      parallel processes (default: all cores)
  --mcmc-steps N   emcee steps per cosmology chain (default 2000; burn-in = 1/3)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

# one BLAS thread per worker process: parallelism comes from the process pool
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from data import download, loaders, literature  # noqa: E402
from fit import cosmo_fit  # noqa: E402
from fit.galaxies import fit_many, summarize  # noqa: E402
from score import scores  # noqa: E402

COSMO_SETS = {
    "combined": ["DESI DR2", "Planck", "Pantheon+", "fsigma8"],
    "combined_DR1": ["DESI DR1", "Planck", "Pantheon+", "fsigma8"],
}
SINGLES = ["DESI DR2", "Planck", "Pantheon+", "fsigma8"]


# ============================================================================ logging
class Log:
    def __init__(self, cfg):
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = os.path.join(HERE, "results", stamp + ("-quick" if cfg["quick"] else ""))
        path, i = base, 1
        while os.path.exists(path):          # never overwrite a previous run
            path, i = f"{base}-{i}", i + 1
        os.makedirs(path)
        self.dir = path
        self.cfg = cfg
        self.t0 = time.time()
        self.save("config", cfg)

    def save(self, name, obj):
        p = os.path.join(self.dir, name + ".json")
        if os.path.exists(p):
            raise FileExistsError(p)
        with open(p, "w") as f:
            json.dump(dict(config_ref="config.json", step=name, result=obj), f, indent=1, default=_jsonable)

    def say(self, msg):
        print(f"[{time.time() - self.t0:7.0f}s] {msg}", flush=True)


def _jsonable(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def git_commit():
    try:
        return subprocess.check_output(["git", "-C", HERE, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


# ============================================================================ cosmology
def _cosmo_models():
    from hypotheses import h1_lcdm, h2_mond, h3_w0wa, h5_push_pull as h5
    from hypotheses import h4_check_2610_26877 as chk
    return {
        "H1": h1_lcdm.cosmo_model(),
        "H2": h2_mond.cosmo_model(),
        "H3": h3_w0wa.cosmo_model(),
        "H5a": h5.gcg_model(),
        "H5b": h5.farnes_model(False),
        "H5b-free": h5.farnes_model(True),
        "H5c": h5.env_model(),
        "2610-SIDM2+Planck": chk.wcdm_with_planck(),
    }


def _cosmo_job(args):
    key, sets, cfg = args
    data = cosmo_fit.Data(loaders)
    model = _cosmo_models()[key]
    out = {}
    for label, ds in sets.items():
        out[label] = cosmo_fit.best_fit(model, data, ds, maxiter=cfg["de_maxiter"], popsize=cfg["de_popsize"])
        out[label]["datasets"] = ds
        out[label]["npts"] = {d: data.npts(d) for d in ds}
    return key, model.params, out


def _mcmc_job(args):
    key, p0, cfg = args
    data = cosmo_fit.Data(loaders)
    model = _cosmo_models()[key]
    summ, chain = cosmo_fit.run_mcmc(model, data, COSMO_SETS["combined"], p0, nsteps=cfg["mcmc_steps"],
                                     burn=cfg["mcmc_steps"] // 3, seed=cfg["seed"])
    extra = {}
    if key == "H3":
        w0, wa = chain[:, 3], chain[:, 4]
        # posterior distance of LCDM point (w0,wa)=(-1,0) in Gaussian-sigma units via Mahalanobis distance
        mu = np.array([w0.mean(), wa.mean()])
        cov = np.cov(np.vstack([w0, wa]))
        d = np.array([-1.0, 0.0]) - mu
        extra["lcdm_mahalanobis_chi2"] = float(d @ np.linalg.solve(cov, d))
    if key == "H5a":
        a = chain[:, 3]
        extra["alpha_abs_95"] = float(np.percentile(np.abs(a), 95))
    return key, summ, extra


def run_cosmology(log, cfg):
    models = _cosmo_models()
    sets = dict(COSMO_SETS)
    for s in SINGLES:
        sets["only:" + s] = [s]
    jobs = [(k, sets if k in ("H1", "H3", "H5a", "H5c", "H2", "H5b") else {"combined": COSMO_SETS["combined"]}, cfg)
            for k in models]
    res = {}
    with ProcessPoolExecutor(max_workers=cfg["workers"]) as ex:
        for key, params, out in ex.map(_cosmo_job, jobs):
            res[key] = dict(params=params, fits=out, name=models[key].name)
            c = out["combined"]
            log.say(f"cosmology {key:18s} chi2={c['chi2']:.2f}  p={np.round(c['p'], 4).tolist()}")
    # posteriors
    mc_keys = ["H1", "H3", "H5a", "H5c"]
    with ProcessPoolExecutor(max_workers=cfg["workers"]) as ex:
        for key, summ, extra in ex.map(_mcmc_job, [(k, res[k]["fits"]["combined"]["p"], cfg) for k in mc_keys]):
            res[key]["mcmc"] = summ
            res[key]["mcmc_extra"] = extra
            log.say(f"mcmc {key}: " + ", ".join(f"{n}={v['mean']:.4g}±{v['sd']:.2g}" for n, v in summ["summary"].items()))
    # explicit check of the Chaplygin-gas weak spot: alpha = 0 must reproduce LCDM exactly; small |alpha| vs growth
    from physics.cosmology import OMEGA_R, omega_nu
    data = cosmo_fit.Data(loaders)
    h, wb, wc = res["H1"]["fits"]["combined"]["p"]
    wg = h ** 2 - OMEGA_R - wb - omega_nu(1.0) - wc
    As = 1 - wc / (h ** 2 - OMEGA_R - wb - omega_nu(1.0))
    gm = models["H5a"]
    chk = {}
    for al in (0.0, 1e-4, -1e-4, 1e-3, -1e-3, 1e-2):
        chk[str(al)] = cosmo_fit.chi2_parts(gm, [h, wb, As, al], data, COSMO_SETS["combined"])
    chk["lcdm"] = res["H1"]["fits"]["combined"]["parts"]
    res["H5a"]["alpha_scan_at_lcdm_point"] = chk
    log.save("cosmology", res)
    return res


def run_2610_check(log, cfg):
    from hypotheses import h4_check_2610_26877 as chk
    data = cosmo_fit.Data(loaders)
    ds = ["DESI DR2", "Pantheon+"]
    out = {}
    for k in ["LCDM", "SIDM1", "SIDM2", "SIDM3"]:
        m = chk.model(k)
        out[k] = cosmo_fit.best_fit(m, data, ds, maxiter=cfg["de_maxiter"], popsize=cfg["de_popsize"])
        out[k]["params"] = m.params
        out[k]["desi_only"] = cosmo_fit.best_fit(m, data, ["DESI DR2"], maxiter=cfg["de_maxiter"] // 2,
                                                 popsize=cfg["de_popsize"])
        log.say(f"2610 check {k}: chi2={out[k]['chi2']:.2f} p={np.round(out[k]['p'], 3).tolist()}")
    summ, _ = cosmo_fit.run_mcmc(chk.model("SIDM2"), data, ds, out["SIDM2"]["p"], nsteps=cfg["mcmc_steps"],
                                 burn=cfg["mcmc_steps"] // 3, seed=cfg["seed"])
    out["SIDM2"]["mcmc"] = summ
    out["paper"] = chk.PAPER
    log.save("check_2610_26877", out)
    return out


# ============================================================================ galaxies
def run_sparc(log, cfg):
    from hypotheses import h1_lcdm, h2_mond, h4_yukawa_sidm as h4, h5_push_pull as h5, h6_dark_atoms as h6, h7_black_holes as h7
    gals = loaders.load_sparc()
    if cfg["quick"]:
        gals = gals[::12]
    os.environ["TT_WORKERS"] = str(cfg["workers"])
    out = {"galaxies": [g.name for g in gals]}

    f = fit_many(gals, h1_lcdm.galaxy_worker)
    out["H1"] = dict(summary=summarize(f), per_galaxy=[x.__dict__ for x in f])
    log.say(f"SPARC LCDM/NFW: {out['H1']['summary']}")

    a0s = cfg["mond_a0_grid"]
    prof = []
    for a0 in a0s:
        fm = fit_many(gals, h2_mond.galaxy_worker, a0)
        s = summarize(fm)
        prof.append(dict(a0=a0, chi2=s["chi2_data"] + s["chi2_prior"], summary=s, fits=fm))
    best = min(prof, key=lambda r: r["chi2"])
    out["H2"] = dict(a0_profile=[dict(a0=r["a0"], chi2=r["chi2"]) for r in prof], a0_best=best["a0"],
                     summary=best["summary"], per_galaxy=[x.__dict__ for x in best["fits"]])
    log.say(f"SPARC MOND: best a0={best['a0']:.3g}  {best['summary']}")

    with ProcessPoolExecutor(max_workers=cfg["workers"]) as ex:
        out["H4"] = list(ex.map(h4.galaxy_worker, gals))
    log.say("SPARC SIDM grid done")

    f = fit_many(gals, h5.farnes_galaxy_worker)
    out["H5b"] = dict(summary=summarize(f), per_galaxy=[x.__dict__ for x in f])
    log.say(f"SPARC Farnes negative-mass halo: {out['H5b']['summary']}")

    with ProcessPoolExecutor(max_workers=cfg["workers"]) as ex:
        out["H6"] = list(ex.map(h6.galaxy_worker, gals))
    log.say("SPARC dark-disc grid done")

    f = fit_many(gals, h7.galaxy_worker)
    out["H7"] = dict(summary=summarize(f), per_galaxy=[x.__dict__ for x in f])
    log.say(f"SPARC NFW + central black hole: {out['H7']['summary']}")
    log.save("sparc", out)
    return out


# ============================================================================ dwarfs
def run_dwarfs(log, cfg, a0_best):
    from hypotheses import h1_lcdm, h2_mond, h4_yukawa_sidm as h4, h5_push_pull as h5
    rng = np.random.default_rng(cfg["seed"])
    dw = loaders.load_dwarfs()
    out = {"dwarfs": [d.__dict__ for d in dw], "H1": [], "H2": [], "H4_grid": [], "H5b": []}
    for d in dw:
        l = h1_lcdm.dwarf_log_rho150(d, rng)
        out["H1"].append(dict(name=d.name, mu=float(l.mean()), sd=float(l.std()), chi2=h4.obs_chi2_log(d, l.mean(), l.std())))
        m = h2_mond.dwarf_log_rho150(d, rng, a0_best, n=200)
        out["H2"].append(dict(name=d.name, mu=float(m.mean()), sd=float(m.std()), chi2=h4.obs_chi2_log(d, m.mean(), m.std())))
        mu, sd, nu = h4.dwarf_log_rho150_grid(d, rng)
        out["H4_grid"].append(dict(name=d.name, mu=mu.tolist(), sd=sd.tolist(), nu=nu,
                                   chi2=[h4.obs_chi2_log(d, a, b) for a, b in zip(mu, sd)]))
        out["H5b"].append(dict(name=d.name, chi2=h5.farnes_dwarf_chi2(d)))
    out["sigma_grid"] = h4.SIGMA_GRID.tolist()
    log.say("dwarfs: LCDM chi2=%.1f  MOND chi2=%.1f  Farnes chi2=%.1f" % (
        sum(x["chi2"] for x in out["H1"]), sum(x["chi2"] for x in out["H2"]), sum(x["chi2"] for x in out["H5b"])))
    log.save("dwarfs", out)
    return out


# ============================================================================ H4 Yukawa scan
def _scan_chunk(args):
    from hypotheses import h4_yukawa_sidm as h4
    m_chi, mphis, alphas, attractive, G_CHI, G_NU, D_CHI, D_NU, cons = args
    xg = np.log10(h4.SIGMA_GRID + 0.03)
    rows = []
    for mp in mphis:
        for al in alphas:
            f_eff, f_T, f_m = h4.yukawa_laws(m_chi, mp, al, attractive)
            sg = np.minimum(f_eff(G_NU), h4.SIGMA_GRID[-1])
            xs = np.log10(sg + 0.03)
            cg = float(sum(np.interp(x, xg, row) for x, row in zip(xs, G_CHI)))
            sd = np.minimum(f_eff(D_NU), h4.SIGMA_GRID[-1])
            xd = np.log10(sd + 0.03)
            cd = float(sum(np.interp(x, xg, row) for x, row in zip(xd, D_CHI)))
            cc, _ = h4.cluster_chi2(f_T, f_m, cons)
            rows.append((m_chi, mp, al, int(attractive), cg, cd, cc,
                         float(f_T(30.0)), float(f_eff(np.array([20.0]))[0]), float(f_m(1000.0)), float(f_T(1500.0)),
                         float(f_m(1458.0))))
    return rows


def run_h4(log, cfg, sparc, dwarfs):
    from hypotheses import h4_yukawa_sidm as h4
    G_CHI = np.array([[r["chi2_data"] + r["chi2_prior"] for r in g["grid"]] for g in sparc["H4"]])
    G_NU = np.array([g["grid"][0]["nu"] for g in sparc["H4"]])
    D_CHI = np.array([d["chi2"] for d in dwarfs["H4_grid"]])
    D_NU = np.array([d["nu"] for d in dwarfs["H4_grid"]])
    cons = literature.SIGMA_CONSTRAINTS
    out = {}
    # empirical: each galaxy / dwarf's own best constant cross-section
    emp = []
    for g, chi, nu in zip(sparc["H4"], G_CHI, G_NU):
        j = int(np.argmin(chi))
        emp.append(dict(name=g["name"], nu=float(nu), sigma_best=float(h4.SIGMA_GRID[j]), dchi2_vs_cdm=float(chi[0] - chi[j])))
    for d, chi, nu in zip(dwarfs["H4_grid"], D_CHI, D_NU):
        j = int(np.argmin(chi))
        emp.append(dict(name=d["name"], nu=float(nu), sigma_best=float(h4.SIGMA_GRID[j]), dchi2_vs_cdm=float(chi[0] - chi[j]),
                        dwarf=True))
    out["empirical"] = emp
    # constant (velocity-independent) cross-section for comparison
    const = []
    for j, s in enumerate(h4.SIGMA_GRID):
        cc, parts = h4.cluster_chi2(lambda v: s, lambda v: s, cons)
        const.append(dict(sigma=float(s), sparc=float(G_CHI[:, j].sum()), dwarfs=float(D_CHI[:, j].sum()), clusters=cc))
    out["constant_sigma"] = const
    cdm_cl, cdm_parts = h4.cluster_chi2(lambda v: 0.0, lambda v: 0.0, cons)
    out["cdm"] = dict(sparc=float(G_CHI[:, 0].sum()), dwarfs=float(D_CHI[:, 0].sum()), clusters=cdm_cl, cluster_parts=cdm_parts)

    mchis = np.logspace(0, 3.5, cfg["scan_n"])
    mphis = np.logspace(-4, np.log10(0.05), cfg["scan_n"])
    alphas = np.logspace(-6, -0.5, int(cfg["scan_n"] * 1.5))
    jobs = [(m, mphis, alphas, att, G_CHI, G_NU, D_CHI, D_NU, cons) for m in mchis for att in (True, False)]
    rows = []
    with ProcessPoolExecutor(max_workers=cfg["workers"]) as ex:
        for r in ex.map(_scan_chunk, jobs):
            rows.extend(r)
    A = np.array(rows)
    tot = np.nan_to_num(A[:, 4] + A[:, 5] + A[:, 6], nan=1e12)
    ib = int(np.argmin(tot))
    best = A[ib]
    cols = ["m_chi_GeV", "m_phi_GeV", "alpha", "attractive", "chi2_sparc", "chi2_dwarfs", "chi2_clusters",
            "sigmaT_30", "sigma_eff_nu20", "sigma_mean_1000", "sigmaT_1500", "sigma_mean_1458"]
    out["scan_columns"] = cols
    out["best"] = dict(zip(cols, best.tolist()))
    out["best"]["chi2_total"] = float(tot[ib])
    win = tot - tot[ib] < 7.815   # 95% for 3 parameters
    W = A[win]
    out["window_n"] = int(win.sum())
    out["n_scanned"] = int(len(A))
    out["window"] = {c: [float(W[:, i].min()), float(W[:, i].max())] for i, c in enumerate(cols) if i not in (3,)}
    out["window_attractive_fraction"] = float(W[:, 3].mean()) if len(W) else 0.0
    # how many window points sit near the thermal-relic coupling
    th = h4.THERMAL_ALPHA_PER_GEV * W[:, 0]
    out["window_thermal_relic_points"] = int(np.sum(np.abs(np.log10(W[:, 2] / th)) < 0.3))
    # per-block best (tension between scales)
    out["best_sparc_only"] = dict(zip(cols, A[int(np.argmin(A[:, 4]))].tolist()))
    out["best_dwarfs_only"] = dict(zip(cols, A[int(np.argmin(A[:, 5]))].tolist()))
    # brief targets
    tgt = (A[:, 7] >= 30) & (A[:, 7] <= 100) & (A[:, 10] <= 1.0)
    out["target_points_total"] = int(tgt.sum())
    out["target_points_in_window"] = int((tgt & win).sum())
    if tgt.any():
        it = np.where(tgt)[0][int(np.argmin(tot[tgt]))]
        out["best_on_target"] = dict(zip(cols, A[it].tolist()), chi2_total=float(tot[it]))
    # mediator forecasts
    mp_lo, mp_hi = out["window"]["m_phi_GeV"] if len(W) else (np.nan, np.nan)
    out["bbn_eps_floor"] = {f"{m * 1e3:.2f} MeV": h4.eps_bbn_floor(m) for m in sorted(set([mp_lo, mp_hi, 0.002, 0.005, 0.01, 0.02]))
                            if np.isfinite(m) and m > 0.00103}
    # store a thinned table (window + a sample of the rest) for the report
    keep = np.where(win)[0]
    out["window_points"] = A[keep][np.argsort(tot[keep])][:400].tolist()
    cdm_tot = out["cdm"]["sparc"] + out["cdm"]["dwarfs"] + out["cdm"]["clusters"]
    log.say(f"H4 scan: {len(A)} points, best chi2={tot[ib]:.1f} vs collisionless {cdm_tot:.1f}; best {out['best']}")
    log.save("h4_scan", out)
    return out


# ============================================================================ H6 dark atoms
def run_h6(log, cfg, sparc, dwarfs):
    from hypotheses import h6_dark_atoms as h6
    from hypotheses import h4_yukawa_sidm as h4
    dw = loaders.load_dwarfs()
    grid = []
    base_dw = sum(x["chi2"] for x in dwarfs["H1"])
    for f in h6.F_GRID:
        for lam in h6.LAMBDA_GRID:
            sp = 0.0
            for g in sparc["H6"]:
                e = [x for x in g["grid"] if x["f"] == f and x["lam"] == lam][0]
                sp += e["chi2_data"] + e["chi2_prior"]
            dchi = 0.0
            for d, r in zip(dw, dwarfs["H1"]):
                dchi += h4.obs_chi2_log(d, r["mu"] + np.log10(1 - f), r["sd"])
            beta, _ = h6.cluster_beta(f)
            cl = float(((beta - (-0.04)) / 0.07) ** 2)
            gaia_thin = h6.gaia_chi2(f, lam, 20.0)
            # thinnest disc allowed by Gaia at 95%
            hs = np.logspace(0, 3.5, 300)
            ok = [h for h in hs if h6.sigma_dd_sun(f, lam) <= h6.gaia_sigma_max(h)]
            grid.append(dict(f=float(f), lam=float(lam), sparc=sp, dwarfs=dchi, clusters=cl, gaia_thin20pc=gaia_thin,
                             planck=h6.planck_chi2(f), sigma_sun=float(h6.sigma_dd_sun(f, lam)),
                             h_min_pc=float(ok[0]) if ok else None))
    for r in grid:
        r["total"] = r["sparc"] + r["dwarfs"] + r["clusters"] + r["gaia_thin20pc"] + r["planck"]
    best = min(grid, key=lambda r: r["total"])
    win = [r for r in grid if r["total"] - best["total"] < 5.99]
    out = dict(grid=grid, best=best, window=win, base_dwarfs=base_dw)
    log.say(f"H6: best f_disc={best['f']} lambda={best['lam']} total={best['total']:.1f}")
    log.save("h6_dark_atoms", out)
    return out


# ============================================================================ H7 PBH windows
def run_h7(log, cfg):
    from hypotheses import h7_black_holes as h7
    L = h7.load_limits()
    M = np.logspace(-20, 6, 521)
    fm, who = h7.fmax_monochromatic(M, L)
    mono = [dict(M_msun=float(m), M_g=float(m * h7.MSUN_G), fmax=(float(f) if np.isfinite(f) else None), by=str(w))
            for m, f, w in zip(M, fm, who)]

    def window(th):
        ok = fm >= th
        if not ok.any():
            return []
        segs, start = [], None
        for i, o in enumerate(ok):
            if o and start is None:
                start = i
            if (not o or i == len(ok) - 1) and start is not None:
                end = i if o else i - 1
                segs.append([float(M[start] * h7.MSUN_G), float(M[end] * h7.MSUN_G)])
                start = None
        return segs
    # only report windows that are bracketed by constraints on both sides (outside the digitised range is
    # 'no data', not 'allowed')
    lo_edge = min(m.min() for m, _ in L.values())
    hi_edge = max(m.max() for m, _ in L.values())
    win_all = [s for s in window(1.0) if s[0] > lo_edge * h7.MSUN_G * 1.01 and s[1] < hi_edge * h7.MSUN_G * 0.99]
    win_most = [s for s in window(0.5) if s[0] > lo_edge * h7.MSUN_G * 1.01 and s[1] < hi_edge * h7.MSUN_G * 0.99]
    ln = []
    for sig in cfg["pbh_sigmas"]:
        for mc in np.logspace(-17, -9, 33):
            f, w = h7.fmax_lognormal(mc, sig, L)
            ln.append(dict(sigma=float(sig), Mc_msun=float(mc), Mc_g=float(mc * h7.MSUN_G),
                           fmax=(float(f) if np.isfinite(f) else None), by=w))
    out = dict(limits={k: v for k, v in h7.PBH_LIMITS.items()}, monochromatic=mono, window_all_dm_g=win_all,
               window_most_dm_g=win_most, lognormal=ln, digitised_range_msun=[float(lo_edge), float(hi_edge)])
    log.say(f"H7 PBH: f=1 window {win_all} g; f>=0.5 window {win_most} g")
    log.save("h7_pbh", out)
    return out


# ============================================================================ clusters
def run_clusters(log, cfg, h6res):
    from hypotheses import h4_yukawa_sidm as h4
    from baselines import mond
    from hypotheses import h6_dark_atoms as h6
    hv = [c for c in literature.SIGMA_CONSTRAINTS if c["kind"] == "beta"][0]

    def beta_chi2(b, eb):
        return float((b - hv["beta"]) ** 2 / (hv["ebeta"] ** 2 + eb ** 2))
    cdm, parts = h4.cluster_chi2(lambda v: 0.0, lambda v: 0.0, literature.SIGMA_CONSTRAINTS)
    b, eb = mond.cluster_beta()
    out = dict(
        H1=dict(chi2=cdm, parts=parts, beta=0.0),
        H2=dict(chi2=beta_chi2(b, eb) + cdm - parts["harvey15_offsets"], beta=b,
                note="lensing follows baryons; other cluster limits are on a cross-section MOND does not have, scored as zero"),
        H5b=dict(chi2=beta_chi2(b, eb) + cdm - parts["harvey15_offsets"], beta=b),
        H6=dict(chi2=h6res["best"]["clusters"] + cdm - parts["harvey15_offsets"], beta=h6res["best"]["f"]),
        face_value_detections=dict(
            note="Andrade+22 and Sagunski+21 report mild non-zero cross-sections; scored here as upper limits",
            cdm_penalty_if_taken_as_measurements=float((0.082 / 0.024) ** 2 + (0.5 / 0.2) ** 2 + (0.19 / 0.09) ** 2)),
    )
    log.save("clusters", out)
    return out


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--mcmc-steps", type=int, default=None)
    a = ap.parse_args()
    cfg = dict(
        quick=a.quick, workers=a.workers, seed=20261027,
        mcmc_steps=a.mcmc_steps or (300 if a.quick else 2000),
        de_maxiter=25 if a.quick else 120, de_popsize=8 if a.quick else 12,
        scan_n=8 if a.quick else 22,
        mond_a0_grid=[1.2e-10] if a.quick else [0.8e-10, 0.9e-10, 1.0e-10, 1.1e-10, 1.2e-10, 1.3e-10, 1.4e-10, 1.6e-10],
        pbh_sigmas=[0.25, 0.5, 1.0, 1.5, 2.0],
        git_commit=git_commit(), python=sys.version, platform=platform.platform(),
        packages={m: __import__(m).__version__ for m in ("numpy", "scipy", "emcee")},
        started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    )
    log = Log(cfg)
    log.say(f"run directory: {log.dir}")
    log.say("data: download / verify checksums")
    log.save("data_status", download.fetch_all(verbose=False))
    log.save("literature_check", literature.check_all())
    log.say("literature numbers verified against their sources")

    cosmo = run_cosmology(log, cfg)
    chk = run_2610_check(log, cfg)
    sparc = run_sparc(log, cfg)
    dwarfs = run_dwarfs(log, cfg, sparc["H2"]["a0_best"])
    h4res = run_h4(log, cfg, sparc, dwarfs)
    h6res = run_h6(log, cfg, sparc, dwarfs)
    h7res = run_h7(log, cfg)
    clusters = run_clusters(log, cfg, h6res)

    from report.make_report import write_report
    path = write_report(log.dir, dict(cfg=cfg, cosmo=cosmo, chk=chk, sparc=sparc, dwarfs=dwarfs, h4=h4res, h6=h6res,
                                      h7=h7res, clusters=clusters))
    log.say(f"report written: {path}")


if __name__ == "__main__":
    main()

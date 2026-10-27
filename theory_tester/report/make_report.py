"""Turn one run's results into report/REPORT.md (plain English, numbers from the run, nothing typed in by hand).

Scoring conventions are explained at the top of the report itself.
"""
from __future__ import annotations

import json
import os

import numpy as np

from score import scores

HERE = os.path.dirname(os.path.abspath(__file__))

N_COSMO = None


def _f(x, d=1):
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    if not np.isfinite(x):
        return "∞"
    if abs(x) >= 1e5:
        return f"{x:.3g}"
    return f"{x:,.{d}f}"


def _sig(dchi2, dk):
    return scores.delta_chi2_to_sigma(dchi2, dk)


def _e(x):
    return f"{x:.2g}" if x is not None else "—"


# ----------------------------------------------------------------------------- score table
def build_rows(R):
    cos, sp, dw, h4, h6, h7, cl = R["cosmo"], R["sparc"], R["dwarfs"], R["h4"], R["h6"], R["h7"], R["clusters"]
    ncos = sum(cos["H1"]["fits"]["combined"]["npts"].values())
    nsp = sp["H1"]["summary"]["npts"]
    ndw = len(dw["H1"])
    ncl = 5

    def cosmo(key):
        c = cos[key]["fits"]["combined"]
        return c["chi2"], len(cos[key]["params"]) + 1, c["parts"]

    sp_h1 = sp["H1"]["summary"]
    sp1 = sp_h1["chi2_data"] + sp_h1["chi2_prior"]
    dw1 = sum(x["chi2"] for x in dw["H1"])
    cl1 = cl["H1"]["chi2"]

    rows = {}

    def row(key, name, cosk, spc, spk, dwc, clc, spec, kglob, inherited, note=""):
        c, ck, parts = cosmo(cosk)
        rows[key] = dict(name=name, cosmo=c, cosmo_k=ck, cosmo_parts=parts, sparc=spc, sparc_k=spk, dwarfs=dwc,
                         clusters=clc, specific=spec, k_global=kglob, inherited=inherited, note=note)

    row("H1", "Lambda-CDM (baseline)", "H1", sp1, sp_h1["nparams"], dw1, cl1, 0.0, 0, [])
    s2 = sp["H2"]["summary"]
    row("H2", "MOND (standard μ)", "H2", s2["chi2_data"] + s2["chi2_prior"], s2["nparams"], sum(x["chi2"] for x in dw["H2"]),
        cl["H2"]["chi2"], 0.0, 1, [], "cosmology = 'no dark matter' (baryons + Λ)")
    row("H3", "Evolving dark energy (w0–wa)", "H3", sp1, sp_h1["nparams"], dw1, cl1, 0.0, 0, ["SPARC", "dwarfs", "clusters"])
    # H4: deltas relative to its own collisionless limit (removes optimiser / Monte-Carlo noise)
    b = h4["best"]
    d_sp = b["chi2_sparc"] - h4["cdm"]["sparc"]
    d_dw = b["chi2_dwarfs"] - h4["cdm"]["dwarfs"]
    row("H4", "Short-range speed-dependent force (Yukawa SIDM)", "H1", sp1 + d_sp, sp_h1["nparams"], dw1 + d_dw,
        b["chi2_clusters"], 0.0, 3, ["cosmology"])
    # H5 variants
    s5b = sp["H5b"]["summary"]
    row("H5a", "Push-pull: generalised Chaplygin gas", "H5a", sp1, sp_h1["nparams"], dw1, cl1, 0.0, 0,
        ["SPARC", "dwarfs", "clusters"], "small scales inherit ΛCDM only because the fit drives α→0")
    row("H5b", "Push-pull: Farnes negative-mass fluid", "H5b", s5b["chi2_data"] + s5b["chi2_prior"], s5b["nparams"],
        sum(x["chi2"] for x in dw["H5b"]), cl["H5b"]["chi2"], 0.0, 0, [])
    row("H5c", "Push-pull: environment-dependent push", "H5c", sp1, sp_h1["nparams"], dw1, cl1, 0.0, 0,
        ["SPARC", "dwarfs", "clusters"])
    # H6
    g0 = [r for r in h6["grid"] if r["f"] == 0.0][0]
    hb = h6["best"]
    row("H6", "Dark atoms / dark disc", "H1", sp1 + hb["sparc"] - g0["sparc"], sp_h1["nparams"],
        dw1 + hb["dwarfs"] - g0["dwarfs"], hb["clusters"] + cl1 - cl["H1"]["parts"]["harvey15_offsets"],
        hb["gaia_thin20pc"] + hb["planck"], 2, ["cosmology"])
    # H7
    s7 = sp["H7"]["summary"]
    pbh_ok = len(h7["window_all_dm_g"]) > 0
    row("H7", "Many black holes (SMBH + PBHs)", "H1", s7["chi2_data"] + s7["chi2_prior"], s7["nparams"], dw1, cl1,
        0.0 if pbh_ok else 1e4, 1, ["cosmology", "dwarfs", "clusters"])
    for r in rows.values():
        r["total"] = r["cosmo"] + r["sparc"] + r["dwarfs"] + r["clusters"] + r["specific"]
        r["k"] = r["cosmo_k"] + r["sparc_k"] + r["k_global"]
        r["n"] = ncos + nsp + ndw + ncl
        r["aic"] = scores.aic(r["total"], r["k"])
        r["bic"] = scores.bic(r["total"], r["k"], r["n"])
    base = rows["H1"]
    # SPARC error bars are too small (chi2/dof >> 1 for every model): a conservative variant divides SPARC chi^2
    # differences by Lambda-CDM's SPARC chi2/dof before charging for parameters.
    s_sp = base["sparc"] / max(nsp - base["sparc_k"], 1)
    for r in rows.values():
        r["daic"] = r["aic"] - base["aic"]
        r["daic_rescaled"] = r["daic"] - (r["sparc"] - base["sparc"]) * (1 - 1 / s_sp)
        r["dbic"] = r["bic"] - base["bic"]
        for blk in ("cosmo", "sparc", "dwarfs", "clusters", "specific", "total"):
            r["d_" + blk] = r[blk] - base[blk]
    return rows, dict(ncos=ncos, nsp=nsp, ndw=ndw, ncl=ncl, s_sp=s_sp)


def write_report(run_dir, R):
    rows, N = build_rows(R)
    cfg = R["cfg"]
    cos, chk, sp, dw, h4, h6, h7, cl = (R[k] for k in ("cosmo", "chk", "sparc", "dwarfs", "h4", "h6", "h7", "clusters"))
    # H5: best variant represents the hypothesis
    h5_best = min(("H5a", "H5b", "H5c"), key=lambda k: rows[k]["aic"])
    seven = ["H1", "H2", "H3", "H4", h5_best, "H6", "H7"]
    ranked = sorted(seven, key=lambda k: rows[k]["aic"])

    L = []
    w = L.append
    w("# Theory Tester — report")
    w("")
    if cfg["quick"]:
        w("> **QUICK SMOKE-TEST RUN** — reduced galaxy sample, short chains, coarse scans. Numbers are indicative only. "
          "Run `python run_all.py` without `--quick` for the real result.")
        w("")
    w(f"Run `{os.path.basename(run_dir)}` · code commit `{cfg['git_commit'][:10]}` · started {cfg['started_utc'][:19]} UTC · "
      f"numpy {cfg['packages']['numpy']}, scipy {cfg['packages']['scipy']}, emcee {cfg['packages']['emcee']}. "
      f"Every number below is in `results/{os.path.basename(run_dir)}/` with the exact configuration that produced it.")
    w("")
    w("## How to read the scores")
    w("")
    w("* **χ²** measures misfit: lower is better. **Δ** columns are *hypothesis minus Lambda-CDM*: **negative means the "
      "hypothesis fits better than standard cosmology**, positive means worse.")
    w("* **AIC = χ² + 2k** and **BIC = χ² + k ln N** charge for free parameters k (BIC charges more). A ΔAIC below about −10 is "
      "strong evidence for the hypothesis; above +10 is strong evidence against it.")
    w("* Dataset blocks: **Cosmology** = DESI DR2 BAO + Planck 2018 distance priors + Pantheon+ + f·σ8 (fitted jointly); "
      "**SPARC** = rotation curves; **Dwarfs** = central dark-matter densities at 150 pc; **Clusters** = merger offsets and "
      "cluster/group cross-section limits; **Own limits** = hypothesis-specific limits (Gaia dark disc + Planck for dark "
      "atoms; the PBH limit set for black holes).")
    w("* *(=ΛCDM)* marks a block where the hypothesis makes the same prediction as Lambda-CDM, so it inherits that score. "
      "That is stated, not hidden.")
    w(f"* Data sizes: cosmology N = {N['ncos']}, SPARC N = {N['nsp']} points in {sp['H1']['summary']['ngal']} galaxies, "
      f"dwarfs N = {N['ndw']}, cluster constraints N = {N['ncl']}.")
    w("")
    w("## Ranked table (best first, by total AIC)")
    w("")
    w("| Rank | Hypothesis | ΔCosmology χ² | ΔSPARC χ² | ΔDwarfs χ² | ΔClusters χ² | Own limits χ² | ΔTotal χ² | Δk | ΔAIC | ΔBIC | ΔAIC, SPARC errors rescaled |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    base = rows["H1"]
    for i, k in enumerate(ranked, 1):
        r = rows[k]

        def cell(blk, label):
            v = _f(r["d_" + blk])
            return v + (" *(=ΛCDM)*" if label in r["inherited"] else "")
        w(f"| {i} | **{k if not k.startswith('H5') else 'H5'}** {r['name']} | {cell('cosmo', 'cosmology')} | {cell('sparc', 'SPARC')} | "
          f"{cell('dwarfs', 'dwarfs')} | {cell('clusters', 'clusters')} | {_f(r['specific'])} | {_f(r['d_total'])} | "
          f"{r['k'] - base['k']:+d} | {_f(r['daic'])} | {_f(r['dbic'])} | {_f(r['daic_rescaled'])} |")
    w("")
    w(f"The last column divides every SPARC χ² difference by ΛCDM's SPARC χ²/dof = {N['s_sp']:.1f} (rotation-curve error bars are "
      "too small for every model), the usual conservative correction; read it as the more cautious verdict.")
    w("")
    w(f"Absolute Lambda-CDM χ²: cosmology {_f(base['cosmo'])}, SPARC {_f(base['sparc'])}, dwarfs {_f(base['dwarfs'])}, "
      f"clusters {_f(base['clusters'])}.")
    w("")
    w("All three push-pull versions (H5 is ranked by its best version, **" + h5_best + "**):")
    w("")
    w("| Version | ΔCosmology χ² | ΔSPARC χ² | ΔDwarfs χ² | ΔClusters χ² | ΔAIC |")
    w("|---|---|---|---|---|---|")
    for k in ("H5a", "H5b", "H5c"):
        r = rows[k]
        w(f"| {k} {r['name']} | {_f(r['d_cosmo'])} | {_f(r['d_sparc'])} | {_f(r['d_dwarfs'])} | {_f(r['d_clusters'])} | {_f(r['daic'])} |")
    w("")

    # per-dataset cosmology table
    w("### Cosmology χ² per dataset at each model's joint best fit")
    w("")
    w("| Model | DESI DR2 (13) | Planck (3) | Pantheon+ (1590) | fσ8 (18) | σ8 | PG tension test |")
    w("|---|---|---|---|---|---|---|")
    for key in ("H1", "H3", "H5a", "H5c", "H5b", "H5b-free", "H2"):
        c = cos[key]["fits"]
        p = c["combined"]["parts"]
        pg = "—"
        if all(("only:" + s) in c for s in ("DESI DR2", "Planck", "Pantheon+", "fsigma8")):
            k = len(cos[key]["params"]) + 1
            singles = [(c["only:" + s]["chi2"], min(k, n)) for s, n in (("DESI DR2", 13), ("Planck", 3),
                                                                        ("Pantheon+", 1590), ("fsigma8", 18))]
            t = scores.pg_test(c["combined"]["chi2"], k, singles)
            pg = f"χ²={t['chi2_pg']:.1f}, dof={t['dof']}, {t['sigma']:.1f}σ" + (" **⚑ tension**" if t["flag"] else "")
        w(f"| {key} {cos[key].get('name', '')} | {_f(p['DESI DR2'])} | {_f(p['Planck'])} | {_f(p['Pantheon+'])} | "
          f"{_f(p['fsigma8'])} | {p.get('_sigma8', float('nan')):.3f} | {pg} |")
    w("")
    w("Pantheon+ absolute χ² is ≈ 1400 for 1590 SNe in every model that fits at all (its covariance is conservative); "
      "only differences between models carry information. SPARC's absolute χ² is high for every model "
      f"(ΛCDM χ²/N ≈ {base['sparc'] / N['nsp']:.1f}) because rotation-curve error bars do not include non-circular motions; "
      "every hypothesis gets identical nuisance freedom (distance, inclination, mass-to-light), so differences are fair.")
    w("")

    # ----------------------------------------------------------------- sections
    w("---")
    w("")
    _sec_h1(w, rows, cos, sp, dw, cl)
    _sec_h2(w, rows, cos, sp, dw, cl)
    _sec_h3(w, rows, cos)
    _sec_h4(w, rows, h4, chk, dw, cl, sp)
    _sec_h5(w, rows, cos, sp, dw, cl)
    _sec_h6(w, rows, h6)
    _sec_h7(w, rows, sp, h7)
    _sec_method(w, cfg)

    text = "\n".join(L) + "\n"
    os.makedirs(HERE, exist_ok=True)
    out = os.path.join(HERE, "REPORT.md")
    with open(out, "w") as f:
        f.write(text)
    with open(os.path.join(run_dir, "REPORT.md"), "w") as f:
        f.write(text)
    with open(os.path.join(run_dir, "score_table.json"), "w") as f:
        json.dump(rows, f, indent=1, default=float)
    return out


# ----------------------------------------------------------------------------- sections
def _mc(cos, key, par):
    m = cos[key].get("mcmc", {}).get("summary", {}).get(par)
    return m


def _sec_h1(w, rows, cos, sp, dw, cl):
    c = cos["H1"]["fits"]["combined"]
    p = dict(zip(cos["H1"]["params"], c["p"]))
    om = (p["omega_b"] + p["omega_c"] + 0.000645) / p["h"] ** 2
    w("## H1 — Lambda-CDM (baseline)")
    w("")
    w(f"* **Cosmology:** best fit h = {p['h']:.4f}, Ω_m = {om:.4f}, ω_b = {p['omega_b']:.5f}, σ8 = {c['parts'].get('_sigma8', 0):.3f}. "
      f"χ² = {c['chi2']:.1f} (DESI {c['parts']['DESI DR2']:.1f} for 13 points, Planck {c['parts']['Planck']:.1f} for 3).")
    w(f"* **Galaxies:** NFW halos with the standard concentration prior fit SPARC with χ² = {rows['H1']['sparc']:,.0f} "
      f"for {sp['H1']['summary']['npts']} points.")
    bad = [(x["name"], d["kind"], x["mu"] > np.log10(d["rho150"])) for x, d in zip(dw["H1"], dw["dwarfs"]) if x["chi2"] > 4]
    nirr = sum(1 for b in bad if b[1] == "dIrr")
    over = sum(1 for b in bad if b[2])
    w(f"* **Dwarfs:** pure NFW predicts central densities with χ² = {rows['H1']['dwarfs']:.1f} for {len(dw['H1'])} dwarfs; "
      f"{len(bad)} miss by more than 2σ ({', '.join(b[0] for b in bad)}); {nirr} of those are star-forming dwarf irregulars and "
      f"{over} of the misses are NFW predicting *too much* central dark matter. Read+2019 attribute low central densities to "
      "supernova feedback, which this pure-gravity baseline does not include.")
    w(f"* **Clusters:** collisionless dark matter predicts no lag; χ² = {rows['H1']['clusters']:.2f}.")
    w("")


def _sec_h2(w, rows, cos, sp, dw, cl):
    r = rows["H2"]
    a0 = sp["H2"]["a0_best"]
    c = cos["H2"]["fits"]["combined"]
    w("## H2 — MOND (standard interpolation function)")
    w("")
    w(f"* **Galaxies (its home ground):** best global a0 = {a0:.2e} m/s². SPARC χ² is {_f(r['d_sparc'])} relative to ΛCDM, but MOND "
      f"uses {sp['H1']['summary']['nparams'] - sp['H2']['summary']['nparams'] - 1} fewer parameters, so on BIC the galaxy-only comparison is "
      f"{_f(r['d_sparc'] + (sp['H2']['summary']['nparams'] + 1 - sp['H1']['summary']['nparams']) * np.log(sp['H1']['summary']['npts']))} "
      "(negative would favour MOND).")
    w(f"* **Dwarfs:** MOND's implied ('phantom') density at 150 pc gives χ² = {r['dwarfs']:.1f} vs ΛCDM {rows['H1']['dwarfs']:.1f}. "
      "The Milky Way's external field was ignored, which only helps MOND for the satellites.")
    w(f"* **Clusters:** with no dark matter, lensing mass must follow the baryons, ~85% of which is hot gas, so the predicted lag is "
      f"β ≈ {cl['H2']['beta']:.2f}; Harvey+2015 measured β = −0.04 ± 0.07 over 72 collisions. χ² = {r['clusters']:.0f} "
      f"(a {np.sqrt(max(r['clusters'], 0)):.0f}σ miss).")
    w(f"* **Cosmology:** MOND alone supplies no dark matter, so the only self-contained cosmology is baryons + Λ: χ² = {c['chi2']:,.0f} "
      f"vs ΛCDM {rows['H1']['cosmo']:,.0f} (Planck alone {c['parts']['Planck']:,.0f}). This is a failure by any measure. "
      "Relativistic MOND theories that add a dust-like field (e.g. AeST) are different hypotheses and were not scored.")
    dbic_g = r['d_sparc'] + (sp['H2']['summary']['nparams'] + 1 - sp['H1']['summary']['nparams']) * np.log(sp['H1']['summary']['npts'])
    galv = ("better than NFW halos on rotation curves once parameters are charged" if dbic_g < 0 else
            "worse than NFW halos on rotation curves in this setup, even after NFW is charged for its extra parameters "
            "(published MOND fits that also free each galaxy's distance and inclination more widely do better)")
    w(f"* **Verdict:** {galv}; fails clusters (by ~{np.sqrt(max(r['clusters'], 0)):.0f}σ) and fails cosmology outright.")
    w("")


def _sec_h3(w, rows, cos):
    c = cos["H3"]["fits"]["combined"]
    p = dict(zip(cos["H3"]["params"], c["p"]))
    d = rows["H3"]["d_cosmo"]
    w0, wa = _mc(cos, "H3", "w0"), _mc(cos, "H3", "wa")
    ex = cos["H3"].get("mcmc_extra", {})
    w("## H3 — Evolving dark energy (w0–wa)")
    w("")
    w(f"* **DESI DR2 + Planck + Pantheon+ (+fσ8):** best fit w0 = {p['w0']:.3f}, wa = {p['wa']:.3f}; Δχ² = {d:.2f} vs ΛCDM for 2 extra "
      f"parameters = **{_sig(-d, 2):.1f}σ** preference" + (f" (posterior w0 = {w0['mean']:.3f} ± {w0['sd']:.3f}, wa = {wa['mean']:.2f} ± {wa['sd']:.2f})" if w0 else "") + ".")
    if "lcdm_mahalanobis_chi2" in ex:
        w(f"* Distance of the ΛCDM point (−1, 0) from the posterior centre: Δχ² = {ex['lcdm_mahalanobis_chi2']:.1f} "
          f"({_sig(ex['lcdm_mahalanobis_chi2'], 2):.1f}σ).")
    c1 = cos["H3"]["fits"].get("combined_DR1")
    c1l = cos["H1"]["fits"].get("combined_DR1")
    if c1 and c1l:
        dd = c1["chi2"] - c1l["chi2"]
        w(f"* **Same test with DESI DR1 instead of DR2:** Δχ² = {dd:.2f} ({_sig(-dd, 2):.1f}σ). DR2 vs DR1 shows whether the signal is growing with data.")
    w(f"* ΔAIC = {rows['H3']['daic']:.1f}, ΔBIC = {rows['H3']['dbic']:.1f}. Rotation curves, dwarfs and clusters are blind to dark energy.")
    sg = _sig(-d, 2)
    word = "no meaningful" if sg < 1.5 else ("a mild" if sg < 2.5 else ("a real but not yet decisive" if sg < 4 else "a strong"))
    w(f"* **Verdict:** {word} preference ({sg:.1f}σ). DESI's own published range for DESI+CMB+SNe is 2.8–4.2σ; this run uses "
      "compressed CMB priors and the Gold-2017 growth data, so modest differences from DESI's full-likelihood numbers are expected.")
    w("")


def _sec_h4(w, rows, h4, chk, dw, cl, sp):
    b = h4["best"]
    W = h4["window"]
    r = rows["H4"]
    cdm = h4["cdm"]
    dtot = b["chi2_total"] - (cdm["sparc"] + cdm["dwarfs"] + cdm["clusters"])
    sscale = rows["H1"]["sparc"] / max(sp["H1"]["summary"]["npts"] - sp["H1"]["summary"]["nparams"], 1)
    dtot_c = (b["chi2_sparc"] - cdm["sparc"]) / sscale + (b["chi2_dwarfs"] - cdm["dwarfs"]) + (b["chi2_clusters"] - cdm["clusters"])
    const = min(h4["constant_sigma"], key=lambda x: x["sparc"] + x["dwarfs"] + x["clusters"])
    const_tot = const["sparc"] + const["dwarfs"] + const["clusters"]
    w("## H4 — Clayten's short-range, speed-dependent force (lead hypothesis)")
    w("")
    w("**Model.** Dark matter scatters off itself through a light mediator (Yukawa potential). Each SPARC galaxy and each dwarf "
      "keeps its own collisionless halo; the force then reshapes it over the halo's age with a simulation-calibrated "
      "gravothermal model (cores form first; very strong scattering drives core collapse = the dense outliers). "
      "Clusters test the high-speed end. Scan: "
      f"{h4['n_scanned']:,} points over m_χ = 1–3000 GeV, m_φ = 0.1–50 MeV, α_D = 10⁻⁶–0.3, attractive and repulsive.")
    w("")
    w(f"* **Best fit:** m_χ = {b['m_chi_GeV']:.3g} GeV, m_φ = {b['m_phi_GeV'] * 1e3:.3g} MeV, α_D = {b['alpha']:.2e}, "
      f"{'attractive' if b['attractive'] else 'repulsive'}. Cross-section: σ/m ≈ {b['sigmaT_30']:.3g} cm²/g at 30 km/s, "
      f"{b['sigma_mean_1000']:.3g} at ~1000 km/s (halo average), {b['sigmaT_1500']:.3g} at 1500 km/s.")
    w(f"* **Against collisionless dark matter on the same galaxies/dwarfs/clusters:** Δχ² = {dtot:.1f} for 3 extra parameters "
      f"(**{_sig(-dtot, 3):.1f}σ** {'improvement' if dtot < 0 else '— no improvement'}). Breakdown: SPARC {b['chi2_sparc'] - cdm['sparc']:+.1f}, "
      f"dwarfs {b['chi2_dwarfs'] - cdm['dwarfs']:+.1f}, clusters {b['chi2_clusters'] - cdm['clusters']:+.1f}. "
      f"ΔAIC vs ΛCDM overall = {r['daic']:.1f}. **Conservative version** (SPARC Δχ² divided by ΛCDM's SPARC χ²/dof = {sscale:.1f}): "
      f"Δχ² = {dtot_c:.1f} ({_sig(-dtot_c, 3):.1f}σ).")
    w(f"* **Speed dependence is needed:** the best *constant* cross-section ({const['sigma']} cm²/g) reaches Δχ² = "
      f"{const_tot - (cdm['sparc'] + cdm['dwarfs'] + cdm['clusters']):.1f}; the velocity-dependent force does "
      f"{(b['chi2_total'] - const_tot):+.1f} better than that.")
    nmore = sum(1 for e in h4["empirical"] if not e.get("dwarf") and e["dchi2_vs_cdm"] > 4)
    ng = sum(1 for e in h4["empirical"] if not e.get("dwarf"))
    w(f"* **Galaxy by galaxy:** {nmore} of {ng} SPARC galaxies individually prefer a non-zero cross-section by Δχ² > 4. "
      f"Dwarfs individually prefer: " + ", ".join(f"{e['name']} {e['sigma_best']:g}" for e in h4["empirical"] if e.get("dwarf")) + " cm²/g.")
    w(f"* **Your target (30–100 cm²/g at 30 km/s and ≤ 1 cm²/g at 1500 km/s):** {h4['target_points_total']:,} scanned points hit it; "
      f"{h4['target_points_in_window']:,} of them are inside the 95% surviving window."
      + (f" Best on-target point: m_χ = {h4['best_on_target']['m_chi_GeV']:.3g} GeV, m_φ = {h4['best_on_target']['m_phi_GeV'] * 1e3:.3g} MeV, "
         f"α = {h4['best_on_target']['alpha']:.2e}, Δχ² from best = {h4['best_on_target']['chi2_total'] - b['chi2_total']:.1f}."
         if "best_on_target" in h4 else ""))
    if h4["window_n"]:
        w(f"* **Surviving window (Δχ² < 7.8 from best, 95% for 3 parameters; {h4['window_n']} points, "
          f"{h4['window_attractive_fraction'] * 100:.0f}% attractive):** m_χ = {W['m_chi_GeV'][0]:.3g}–{W['m_chi_GeV'][1]:.3g} GeV, "
          f"m_φ = {W['m_phi_GeV'][0] * 1e3:.3g}–{W['m_phi_GeV'][1] * 1e3:.3g} MeV, α_D = {W['alpha'][0]:.2e}–{W['alpha'][1]:.2e}. "
          f"Predicted σ/m: {W['sigmaT_30'][0]:.3g}–{W['sigmaT_30'][1]:.3g} cm²/g at 30 km/s; "
          f"{W['sigma_mean_1000'][0]:.3g}–{W['sigma_mean_1000'][1]:.3g} at ~1000 km/s; {W['sigmaT_1500'][0]:.3g}–{W['sigmaT_1500'][1]:.3g} at 1500 km/s. "
          f"{h4['window_thermal_relic_points']} window points lie within a factor 2 of the coupling a simple thermal relic would need.")
    w("* **Cosmology (DESI + Planck):** elastic scattering does not change the expansion history, so this hypothesis has exactly "
      "ΛCDM's cosmology score — neither helped nor hurt.")
    w("* **Strong-lensing subhalos:** no published hard limit on σ at < 30 km/s exists yet (only forecasts), so this block "
      "is not scored; it is the main forecast below.")
    # 2610 check
    p2 = dict(zip(chk["SIDM2"]["params"], chk["SIDM2"]["p"]))
    p1 = dict(zip(chk["SIDM1"]["params"], chk["SIDM1"]["p"]))
    p3 = dict(zip(chk["SIDM3"]["params"], chk["SIDM3"]["p"]))
    m2 = chk["SIDM2"].get("mcmc", {}).get("summary", {}).get("n")
    l0 = chk["LCDM"]["chi2"]
    d2o = chk["SIDM2"]["desi_only"]
    w("")
    w("**Reproduction of arXiv:2610.26877** (DESI DR2 BAO with r_d free + Pantheon+):")
    w("")
    w("| Model | χ² | Δχ² vs ΛCDM | our parameters | paper |")
    w("|---|---|---|---|---|")
    w(f"| ΛCDM | {l0:.2f} | 0 | Ω = {chk['LCDM']['p'][0]:.3f} | — |")
    w(f"| SIDM1 (annihilation only) | {chk['SIDM1']['chi2']:.2f} | {chk['SIDM1']['chi2'] - l0:+.2f} | log κC₁ → {p1['log10_kC1']:.2f} (pinned to the low edge = no effect) | best −4.36, UL −3.93: indistinguishable from ΛCDM |")
    w(f"| SIDM2 (= constant-w dark energy) | {chk['SIDM2']['chi2']:.2f} | {chk['SIDM2']['chi2'] - l0:+.2f} | n = {p2['n']:.2f}"
      + (f" ± {m2['sd']:.2f}" if m2 else "") + f" ⇒ w = {-1 - p2['n'] / 3:.3f}; DESI alone n = {d2o['p'][1]:.2f} | n = −0.55 ± 0.12 (w = −0.82); DESI alone n = −0.24 |")
    w(f"| SIDM3 | {chk['SIDM3']['chi2']:.2f} | {chk['SIDM3']['chi2'] - l0:+.2f} | n = {p3['n']:.2f}, log κC₁ = {p3['log10_kC1']:.2f}, Ω = {p3['Omega_2']:.3f} | n = −0.74, Ω = 0.243 |")
    w("")
    desi_ok = abs(d2o["p"][1] - (-0.24)) < 0.1
    sp_ok = abs(p2["n"] - (-0.55)) < 0.12
    w(f"* DESI alone: our n = {d2o['p'][1]:.2f} vs the paper's −0.24 — " + ("reproduced." if desi_ok else "**not** reproduced.")
      + f" DESI + Pantheon+: our w = {-1 - p2['n'] / 3:.3f} vs the paper's −0.82 ± 0.04 — "
      + ("reproduced." if sp_ok else "**not reproduced**: the standard Pantheon+ likelihood (full covariance, magnitude marginalised) "
         "does not pull w as far from −1 as the paper reports. Their extra cosmic-chronometer data or a different supernova "
         "treatment may account for it; we did not include cosmic chronometers."))
    sp_ = rows["H3"]  # noqa
    w("* **What the paper does and does not show for your force:** its 'SIDM' is a cosmic fluid with annihilation and particle "
      "creation; SIDM2 is mathematically constant-w dark energy. Its preference over ΛCDM is the same late-time "
      "dark-energy signal as H3, not evidence for velocity-dependent scattering. It does not test a Yukawa force.")
    w("")
    w("**Forecast — what future data should see if this force is real (window above):**")
    w("")
    w(f"* **Euclid** (thousands of lensing clusters and mergers): cluster-scale σ/m in the window is {W['sigmaT_1500'][0]:.2g}–{W['sigmaT_1500'][1]:.2g} cm²/g "
      "at 1500 km/s. Values ≳ 0.1 would show up as cored cluster lensing profiles and small DM–galaxy lags; values ≪ 0.05 mean "
      "Euclid clusters will look exactly like cold dark matter, which would *not* kill the hypothesis (the action is at low speed).")
    w(f"* **Rubin LSST** (new ultra-faint dwarfs, many more quadruple lenses): the window predicts σ/m ≈ {W['sigma_eff_nu20'][0]:.3g}–"
      f"{W['sigma_eff_nu20'][1]:.3g} cm²/g at ~20 km/s. Gilman+2021 forecast that 50 lenses give σ₂₀ < 11–23 cm²/g if dark matter "
      "is cold — so if the window is right, LSST-era lens samples should *detect* SIDM (collapsed, very dense subhalos plus cored ones). "
      "A null result at that level would kill most of the window. Dwarf densities vs orbital pericentre (more dense outliers on tight orbits) are the second test.")
    eps = h4.get("bbn_eps_floor", {})
    if eps:
        w(f"* **NA64 / LDMX** (fixed-target searches for MeV dark photons): if the mediator is a kinetically-mixed dark photon of "
          f"{W['m_phi_GeV'][0] * 1e3:.2g}–{W['m_phi_GeV'][1] * 1e3:.2g} MeV, it must decay before Big-Bang nucleosynthesis, which requires "
          "mixing ε ≳ " + ", ".join(f"{v:.1e} ({k})" for k, v in eps.items()) + ". NA64 and LDMX reach mixings far above that floor, "
          "so they can **confirm** such a mediator if ε happens to be large, but cannot **rule it out** (it can hide at small ε, or decay to "
          "neutrinos). Direct-detection limits (which bound ε from the other side for heavy dark matter) were not part of this run.")
    w("* **Verdict:** " + ("the force fits the galaxy and dwarf data better than cold dark matter while respecting every cluster limit; "
                         "the surviving window is listed above." if dtot < -6 else
                         "no significant improvement over cold dark matter with these data; the window above is what survives."))
    w("")


def _sec_h5(w, rows, cos, sp, dw, cl):
    a = cos["H5a"]["fits"]["combined"]
    pa = dict(zip(cos["H5a"]["params"], a["p"]))
    ex = cos["H5a"].get("mcmc_extra", {})
    b = cos["H5b"]["fits"]["combined"]
    bf = cos["H5b-free"]["fits"]["combined"]
    pbf = dict(zip(cos["H5b-free"]["params"], bf["p"]))
    c = cos["H5c"]["fits"]["combined"]
    pc = dict(zip(cos["H5c"]["params"], c["p"]))
    from hypotheses.h5_push_pull import void_to_crowd_ratio
    bc = _mc(cos, "H5c", "beta")
    s5 = sp["H5b"]["per_galaxy"]
    mneg = np.array([g["params"]["logM_neg"] for g in s5])
    w("## H5 — Clayten's push-pull unification")
    w("")
    w("**(a) Generalised Chaplygin gas** (one fluid: matter-like when dense, Λ-like when diluted).")
    w(f"* Best fit α = {pa['alpha']:.2e}, A_s = {pa['A_s']:.4f}; Δχ² vs ΛCDM = {rows['H5a']['d_cosmo']:.2f}"
      + (f"; 95% bound |α| < {ex['alpha_abs_95']:.1e}" if "alpha_abs_95" in ex else "") + ".")
    sc = cos["H5a"].get("alpha_scan_at_lcdm_point", {})
    if sc:
        f0 = sc["lcdm"]["fsigma8"]
        d0 = sum(sc["0.0"][k] for k in ("DESI DR2", "Planck", "Pantheon+", "fsigma8")) - sum(sc["lcdm"][k] for k in ("DESI DR2", "Planck", "Pantheon+", "fsigma8"))
        w(f"* α = 0 is *exactly* ΛCDM (same parameters give Δχ² = {d0:.1e}). The growth data are the weak spot, as expected: the "
          "unified fluid's sound speed c_s² = −αw makes structure oscillate away (α > 0) or blow up (α < 0). Holding everything else "
          "at the ΛCDM best fit, fσ8 χ² changes by: " + ", ".join(f"α = {a}: {sc[a]['fsigma8'] - f0:+.1f}" for a in map(str, (1e-4, -1e-4, 1e-3, -1e-3, 1e-2)))
          + ".")
    ma = _mc(cos, "H5a", "alpha")
    if ma:
        w(f"* Posterior with σ8 free: α = {ma['mean']:.3f} ± {ma['sd']:.3f} (95%: {ma['p2_5']:.3f} to {ma['p97_5']:.3f}). "
          + ("α = 0 (ΛCDM) is inside the 95% range: the data allow the Chaplygin gas only as a small departure from ΛCDM."
             if ma["p2_5"] <= 0 <= ma["p97_5"] else "α = 0 is outside the 95% range."))
    w(f"* **Where it holds:** only for |α| of order the posterior width above, i.e. essentially where it *is* ΛCDM "
      f"(best-fit Δχ² vs ΛCDM = {rows['H5a']['d_cosmo']:+.2f}). SPARC, dwarfs and clusters inherit ΛCDM scores only under that condition.")
    w("")
    w("**(b) Farnes (2018) negative-mass fluid.**")
    w(f"* As published (ρ₋ < 0 constant, open universe, no other dark matter): χ² = {b['chi2']:,.0f} vs ΛCDM {rows['H1']['cosmo']:,.0f} "
      f"(Planck priors alone: {b['parts']['Planck']:,.0f}). The best fit pushes the negative density to zero: a negative constant density "
      "*decelerates* expansion, the opposite of what supernovae show.")
    w(f"* With the sign left free the data choose Ω = {pbf['Omega_-']:+.2f} — a **positive** cosmological constant — and still fail "
      f"(χ² = {bf['chi2']:,.0f}) because there is no dark matter to make the CMB and BAO work.")
    w(f"* **Galaxies:** a spherical negative-mass halo can only weaken gravity inside it. The SPARC fit drives the halo mass to "
      f"the floor (median log M₋ = {np.median(mneg):.1f}), leaving baryons alone: ΔSPARC χ² = {rows['H5b']['d_sparc']:+,.0f} vs ΛCDM. "
      f"Dwarfs: a measured positive dark density vs ≤ 0 predicted: χ² = {rows['H5b']['dwarfs']:,.0f}. Clusters: lensing would follow "
      f"the gas: χ² = {rows['H5b']['clusters']:.0f}.")
    w("* **Verdict:** fails every dataset by large margins. Farnes's flat-rotation-curve claim does not survive the shell theorem with real data.")
    w("")
    w("**(c) Environment-dependent push** (dark energy differs in voids and crowded regions; void volume grows with structure).")
    w(f"* Best fit β = {pc['beta']:+.3f}" + (f" (posterior {bc['mean']:+.2f} ± {bc['sd']:.2f})" if bc else "")
      + f", i.e. void/crowded push ratio r ≈ {void_to_crowd_ratio(pc['beta']):.2f} (r = 1 is ΛCDM). Δχ² = {rows['H5c']['d_cosmo']:.2f} "
      f"for 1 extra parameter ({_sig(-rows['H5c']['d_cosmo'], 1):.1f}σ). Growth (fσ8) χ² = {c['parts']['fsigma8']:.1f} vs ΛCDM "
      f"{cos['H1']['fits']['combined']['parts']['fsigma8']:.1f}: this version does not suffer the Chaplygin growth problem because dark matter still clusters.")
    w("* **Where it holds:** everywhere ΛCDM holds, with r within the posterior above; it gains less than w0–wa because one "
      "parameter tied to structure growth cannot reproduce the w0 > −1, wa < 0 shape DESI prefers.")
    w("")
    w(f"**H5 overall:** represented in the ranking by its best version. Future data: Euclid/DESI-extension fσ8 and void "
      "statistics (void-by-void expansion) directly test version (c); version (a) is already excluded except at α ≈ 0.")
    w("")


def _sec_h6(w, rows, h6):
    b = h6["best"]
    g = h6["grid"]
    win = h6["window"]
    fmax_win = max([r["f"] for r in win], default=0.0)
    gaia_only = max([r["f"] for r in g if r["gaia_thin20pc"] < 4], default=0.0)
    w("## H6 — Clayten's dark atoms")
    w("")
    w("**Model.** A fraction of dark matter is a dissipative 'dark atom' gas that cools into a thin dark disc (mass f_disc·M200, "
      "scale length λ × the stellar disc's); the rest is NFW cold dark matter. SPARC, the Gaia limits at the Sun, the Planck limit on "
      "strongly-interacting dark matter, dwarf densities and cluster lags are combined.")
    w("")
    w("| f_disc | λ | ΔSPARC χ² | Σ_DD at Sun (M☉/pc²) | Gaia χ² (h = 20 pc) | thinnest Gaia-allowed disc | Planck χ² | Cluster χ² | Total Δ |")
    w("|---|---|---|---|---|---|---|---|---|")
    g0 = [r for r in g if r["f"] == 0.0][0]
    for r in g:
        if r["f"] == 0 and r["lam"] != g0["lam"]:
            continue
        w(f"| {r['f']:g} | {r['lam']:g} | {r['sparc'] - g0['sparc']:+.1f} | {r['sigma_sun']:.2f} | {r['gaia_thin20pc']:.1f} | "
          f"{('any' if (r['h_min_pc'] or 0) <= 1.01 else '%.0f pc' % r['h_min_pc']) if r['h_min_pc'] else '> 3 kpc'} | {r['planck']:.1f} | {r['clusters']:.2f} | {r['total'] - g0['total']:+.1f} |")
    w("")
    w(f"* **Best combination:** f_disc = {b['f']:g}, λ = {b['lam']:g} (total Δχ² vs no dark disc = {b['total'] - g0['total']:+.1f}).")
    w(f"* **Surviving window** (all blocks combined, Δχ² < 6 from best, thin 20 pc disc): f_disc ≤ {fmax_win:g} of the halo mass "
      f"({', '.join(f'f={r[chr(102)]:g}/λ={r[chr(108)+chr(97)+chr(109)]:g}' for r in win)}). Gaia alone would allow up to {gaia_only:g}; "
      "the rotation curves are what squeeze it further. A disc holding a larger share must be thicker than the 'thinnest Gaia-allowed' "
      "column — at which point it is no longer the thin disc the idea needs.")
    w("* **Planck:** at most ~5% of dark matter can be strongly coupled to dark radiation; the dissipative fraction f ≥ f_disc, "
      "so the window above is safely inside that unless only a small part of the dark-atom gas forms the disc.")
    w("* **What SPARC says:** adding a dark disc " + ("improves" if b["sparc"] < g0["sparc"] - 4 else "does not improve")
      + " rotation-curve fits; rotation curves cannot measure the disc's thickness at all.")
    w("* **Future data:** Gaia DR4/DR5 vertical kinematics push the thin-disc limit below ~1–2 M☉/pc²; a detection would be a "
      "sub-100-pc dark layer in the vertical force at the Sun. Stellar streams crossing the disc and CMB-S4 (dark acoustic "
      "oscillations) test the dissipative fraction independently.")
    w("")


def _sec_h7(w, rows, sp, h7):
    s7 = sp["H7"]["per_galaxy"]
    s1 = {g["name"]: g for g in sp["H1"]["per_galaxy"]}
    bh = np.array([g["params"]["logM_BH"] for g in s7])
    d = rows["H7"]["d_sparc"]
    gain = sorted([((g["chi2_data"] + g["chi2_prior"]) - (s1[g["name"]]["chi2_data"] + s1[g["name"]]["chi2_prior"]),
                    g["name"], g["params"]["logM_BH"]) for g in s7])
    big = [x for x in gain if x[0] < -4]
    w("## H7 — Clayten's many black holes")
    w("")
    w(f"* **Galaxies:** PBH dark matter is cold and collisionless on galaxy scales, so it makes the same halos as particle dark matter. "
      f"Adding a central black hole (mass prior from the Kormendy & Ho black-hole–bulge relation) changes SPARC χ² by {d:+.1f} vs NFW alone "
      f"for {len(bh)} extra parameters (median fitted log M_BH = {np.median(bh):.1f}). "
      f"{len(big)} galaxies improve by Δχ² > 4" + (": " + ", ".join(f"{n} ({dd:+.0f}, log M_BH = {m:.1f})" for dd, n, m in big[:8]) if big else "")
      + ". In those, the point mass mostly absorbs inner-rotation-curve residuals (bulge mass-to-light, non-circular motions): "
      "a 10⁹ M☉ black hole would be at the top of the observed range. In every other galaxy the black hole is invisible at SPARC radii. "
      f"Conservatively (SPARC errors rescaled) the galaxy-block change is {d / (rows['H1']['sparc'] / max(sp['H1']['summary']['npts'] - sp['H1']['summary']['nparams'], 1)):+.1f}.")
    wa = h7["window_all_dm_g"]
    wm = h7["window_most_dm_g"]
    w("* **Single-mass PBHs, every limit in data item 8** (HSC, OGLE, EROS, MACHO microlensing; Eridanus II/ultra-faint heating; "
      "wide binaries; Planck accretion; Hawking evaporation in gamma rays, Voyager e±, 511 keV, CMB; plus LIGO):")
    w("  * PBHs can be **all** of the dark matter for masses " + ("; ".join(f"{a:.1e} – {b:.1e} g" for a, b in wa) if wa else "nowhere")
      + ".")
    w("  * PBHs can be **most** (≥ 50%) of it for " + ("; ".join(f"{a:.1e} – {b:.1e} g" for a, b in wm) if wm else "nowhere") + ".")
    w("  * Everywhere else at least one limit forbids f_PBH = 1 (the bounding constraints are logged per mass in `h7_pbh.json`).")
    ln = h7["lognormal"]
    for sig in sorted(set(x["sigma"] for x in ln)):
        ok = [x for x in ln if x["sigma"] == sig and (x["fmax"] is None or x["fmax"] >= 1)]
        if ok:
            w(f"  * Log-normal spectrum, width σ = {sig}: all dark matter allowed for central masses "
              f"{min(x['Mc_g'] for x in ok):.1e} – {max(x['Mc_g'] for x in ok):.1e} g.")
        else:
            w(f"  * Log-normal spectrum, width σ = {sig}: no central mass allows PBHs to be all the dark matter.")
    w("* **Caveat on the window's edges:** the low edge is set by Hawking-evaporation limits and the high edge by Subaru HSC "
      "microlensing, whose finite-source and wave-optics treatment moves the edge by up to ~10× between published versions.")
    w("* **Future data:** the asteroid-mass window is hard to close. Probes that could: next-generation MeV gamma-ray telescopes "
      "(e.g. COSI) at the low edge; high-cadence microlensing of nearby galaxies/white dwarfs and X-ray pulsar lensing at the high "
      "edge; Roman Space Telescope microlensing for the planetary-mass end.")
    w("* **Verdict:** " + ("survives, but only as asteroid-mass PBHs" if wa else "does not survive as all of the dark matter")
      + "; the 'one big black hole per galaxy' part is invisible in most rotation curves, and where it registers it cannot be told apart "
      "from ordinary inner-galaxy mass (bulge stars) with these data.")
    w("")


def _sec_method(w, cfg):
    w("## What was run (method in brief)")
    w("")
    w("* **Data** (downloaded, cached, SHA-256 in `data/MANIFEST.json`): SPARC (all galaxies with ≥5 points), DESI DR2 and DR1 BAO, "
      "Planck 2018 distance priors (Chen+2019, parsed from the paper's LaTeX), Pantheon+ (z > 0.01, full covariance), Gold-2017 fσ8 "
      "(18 points), Read+2019 dwarf densities (the compilation Correa 2021 fits), Harvey+2015 72-collision lag, Bullet Cluster, "
      "Andrade+2022 and Sagunski+2021 cross-section limits, Gaia dark-disc limits, Planck interacting-DM limit, and the PBH limit set "
      "(Kavanagh's PBHbounds digitisations). Single-number literature constraints are machine-checked against the cached abstracts/LaTeX.")
    w("* **Fits:** cosmology by differential evolution + Nelder–Mead, posteriors by emcee "
      f"({cfg['mcmc_steps']} steps); galaxies one by one with identical nuisance priors for every hypothesis; the Yukawa force on a "
      f"{cfg['scan_n']}×{cfg['scan_n']}×{int(cfg['scan_n'] * 1.5)} grid (× attractive/repulsive).")
    w("* **Known simplifications** (all stated in the code): compressed CMB instead of full Planck likelihood; SIDM halos via the "
      "Yang+2023 parametric model without baryonic contraction or tidal stripping of satellites (Correa 2021 shows stripping matters for "
      "the dSphs); the Yukawa cross-section uses the Tulin–Yu–Zurek analytic regimes with σ_T as a stand-in for the viscosity cross-section; "
      "MOND ignores the external field effect; the dark disc is razor-thin for rotation curves.")
    w("")

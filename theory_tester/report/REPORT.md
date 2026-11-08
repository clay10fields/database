# Theory Tester — report

> **QUICK SMOKE-TEST RUN** — reduced galaxy sample, short chains, coarse scans. Numbers are indicative only. Run `python run_all.py` without `--quick` for the real result.

Run `20261027T024921Z-quick` · code commit `ed35048d32` · started 2026-10-27T02:49:21 UTC · numpy 2.5.3, scipy 1.18.1, emcee 3.1.6. Every number below is in `results/20261027T024921Z-quick/` with the exact configuration that produced it.

## How to read the scores

* **χ²** measures misfit: lower is better. **Δ** columns are *hypothesis minus Lambda-CDM*: **negative means the hypothesis fits better than standard cosmology**, positive means worse.
* **AIC = χ² + 2k** and **BIC = χ² + k ln N** charge for free parameters k (BIC charges more). A ΔAIC below about −10 is strong evidence for the hypothesis; above +10 is strong evidence against it.
* Dataset blocks: **Cosmology** = DESI DR2 BAO + Planck 2018 distance priors + Pantheon+ + f·σ8 (fitted jointly); **SPARC** = rotation curves; **Dwarfs** = central dark-matter densities at 150 pc; **Clusters** = merger offsets and cluster/group cross-section limits; **Own limits** = hypothesis-specific limits (Gaia dark disc + Planck for dark atoms; the PBH limit set for black holes).
* *(=ΛCDM)* marks a block where the hypothesis makes the same prediction as Lambda-CDM, so it inherits that score. That is stated, not hidden.
* Data sizes: cosmology N = 1624, SPARC N = 275 points in 15 galaxies, dwarfs N = 16, cluster constraints N = 5.

## Ranked table (best first, by total AIC)

| Rank | Hypothesis | ΔCosmology χ² | ΔSPARC χ² | ΔDwarfs χ² | ΔClusters χ² | Own limits χ² | ΔTotal χ² | Δk | ΔAIC | ΔBIC | ΔAIC, SPARC errors rescaled |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **H4** Short-range speed-dependent force (Yukawa SIDM) | 0.0 *(=ΛCDM)* | -102.6 | -137.0 | 2.6 | 0.0 | -237.0 | +3 | -231.0 | -214.3 | -140.7 |
| 2 | **H3** Evolving dark energy (w0–wa) | -7.7 | 0.0 *(=ΛCDM)* | 0.0 *(=ΛCDM)* | 0.0 *(=ΛCDM)* | 0.0 | -7.7 | +2 | -3.7 | 7.4 | -3.7 |
| 3 | **H1** Lambda-CDM (baseline) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | +0 | 0.0 | 0.0 | 0.0 |
| 4 | **H5** Push-pull: environment-dependent push | -1.2 | 0.0 *(=ΛCDM)* | 0.0 *(=ΛCDM)* | 0.0 *(=ΛCDM)* | 0.0 | -1.2 | +1 | 0.8 | 6.4 | 0.8 |
| 5 | **H6** Dark atoms / dark disc | 0.0 *(=ΛCDM)* | 0.0 | 0.0 | -0.0 | 0.0 | 0.0 | +2 | 4.0 | 15.1 | 4.0 |
| 6 | **H7** Many black holes (SMBH + PBHs) | 0.0 *(=ΛCDM)* | -27.9 | 0.0 *(=ΛCDM)* | 0.0 *(=ΛCDM)* | 0.0 | -27.9 | +16 | 4.1 | 93.0 | 28.7 |
| 7 | **H2** MOND (standard μ) | 8.23e+05 | 748.8 | 277.3 | 106.7 | 0.0 | 8.25e+05 | -30 | 8.24e+05 | 8.24e+05 | 8.24e+05 |

The last column divides every SPARC χ² difference by ΛCDM's SPARC χ²/dof = 8.4 (rotation-curve error bars are too small for every model), the usual conservative correction; read it as the more cautious verdict.

Absolute Lambda-CDM χ²: cosmology 1,434.8, SPARC 1,631.1, dwarfs 139.6, clusters 0.3.

All three push-pull versions (H5 is ranked by its best version, **H5c**):

| Version | ΔCosmology χ² | ΔSPARC χ² | ΔDwarfs χ² | ΔClusters χ² | ΔAIC |
|---|---|---|---|---|---|
| H5a Push-pull: generalised Chaplygin gas | 5.0 | 0.0 | 0.0 | 0.0 | 7.0 |
| H5b Push-pull: Farnes negative-mass fluid | 2.88e+07 | 12,745.1 | 368.9 | 106.7 | 2.88e+07 |
| H5c Push-pull: environment-dependent push | -1.2 | 0.0 | 0.0 | 0.0 | 0.8 |

### Cosmology χ² per dataset at each model's joint best fit

| Model | DESI DR2 (13) | Planck (3) | Pantheon+ (1590) | fσ8 (18) | σ8 | PG tension test |
|---|---|---|---|---|---|---|
| H1 Lambda-CDM | 12.4 | 3.7 | 1,405.9 | 12.7 | 0.758 | χ²=9.9, dof=11, 0.6σ |
| H3 Evolving dark energy (w0-wa) | 10.0 | 1.3 | 1,403.0 | 12.9 | 0.755 | χ²=7.7, dof=15, 0.1σ |
| H5a Generalised Chaplygin gas | 12.8 | 3.2 | 1,406.5 | 17.4 | 1.585 | χ²=16.4, dof=13, 1.2σ |
| H5c Environment-dependent push (void vs crowded) | 11.7 | 5.5 | 1,403.5 | 12.8 | 0.756 | χ²=10.6, dof=13, 0.5σ |
| H5b Farnes negative-mass fluid (rho_- < 0, as published) | 24,284.9 | 2.88e+07 | 1,598.1 | 0.0 | nan | χ²=24184.8, dof=11, 37.1σ **⚑ tension** |
| H5b-free Farnes negative-mass fluid (sign left free) | 4,138.3 | 21,117.9 | 1,829.1 | 18.7 | 1.498 | — |
| H2 MOND cosmology (baryons + Lambda, no DM) | 3,523.8 | 8.2e+05 | 1,759.4 | 0.0 | nan | χ²=1667.9, dof=9, 37.1σ **⚑ tension** |

Pantheon+ absolute χ² is ≈ 1400 for 1590 SNe in every model that fits at all (its covariance is conservative); only differences between models carry information. SPARC's absolute χ² is high for every model (ΛCDM χ²/N ≈ 5.9) because rotation-curve error bars do not include non-circular motions; every hypothesis gets identical nuisance freedom (distance, inclination, mass-to-light), so differences are fair.

---

## H1 — Lambda-CDM (baseline)

* **Cosmology:** best fit h = 0.6849, Ω_m = 0.3005, ω_b = 0.02253, σ8 = 0.758. χ² = 1434.8 (DESI 12.4 for 13 points, Planck 3.7 for 3).
* **Galaxies:** NFW halos with the standard concentration prior fit SPARC with χ² = 1,631 for 275 points.
* **Dwarfs:** pure NFW predicts central densities with χ² = 139.6 for 16 dwarfs; 8 miss by more than 2σ (Fornax, WLM, DDO 52, DDO 87, DDO 154, NGC 2366, CVnIdwA, DDO 168); 7 of those are star-forming dwarf irregulars and 8 of the misses are NFW predicting *too much* central dark matter. Read+2019 attribute low central densities to supernova feedback, which this pure-gravity baseline does not include.
* **Clusters:** collisionless dark matter predicts no lag; χ² = 0.33.

## H2 — MOND (standard interpolation function)

* **Galaxies (its home ground):** best global a0 = 1.20e-10 m/s². SPARC χ² is 748.8 relative to ΛCDM, but MOND uses 29 fewer parameters, so on BIC the galaxy-only comparison is 585.9 (negative would favour MOND).
* **Dwarfs:** MOND's implied ('phantom') density at 150 pc gives χ² = 416.8 vs ΛCDM 139.6. The Milky Way's external field was ignored, which only helps MOND for the satellites.
* **Clusters:** with no dark matter, lensing mass must follow the baryons, ~85% of which is hot gas, so the predicted lag is β ≈ 0.85; Harvey+2015 measured β = −0.04 ± 0.07 over 72 collisions. χ² = 107 (a 10σ miss).
* **Cosmology:** MOND alone supplies no dark matter, so the only self-contained cosmology is baryons + Λ: χ² = 824,854 vs ΛCDM 1,435 (Planck alone 819,571). This is a failure by any measure. Relativistic MOND theories that add a dust-like field (e.g. AeST) are different hypotheses and were not scored.
* **Verdict:** worse than NFW halos on rotation curves in this setup, even after NFW is charged for its extra parameters (published MOND fits that also free each galaxy's distance and inclination more widely do better); fails clusters (by ~10σ) and fails cosmology outright.

## H3 — Evolving dark energy (w0–wa)

* **DESI DR2 + Planck + Pantheon+ (+fσ8):** best fit w0 = -0.852, wa = -0.522; Δχ² = -7.70 vs ΛCDM for 2 extra parameters = **2.3σ** preference (posterior w0 = -0.844 ± 0.051, wa = -0.54 ± 0.19).
* Distance of the ΛCDM point (−1, 0) from the posterior centre: Δχ² = 9.5 (2.6σ).
* **Same test with DESI DR1 instead of DR2:** Δχ² = -6.58 (2.1σ). DR2 vs DR1 shows whether the signal is growing with data.
* ΔAIC = -3.7, ΔBIC = 7.4. Rotation curves, dwarfs and clusters are blind to dark energy.
* **Verdict:** a mild preference (2.3σ). DESI's own published range for DESI+CMB+SNe is 2.8–4.2σ; this run uses compressed CMB priors and the Gold-2017 growth data, so modest differences from DESI's full-likelihood numbers are expected.

## H4 — Clayten's short-range, speed-dependent force (lead hypothesis)

**Model.** Dark matter scatters off itself through a light mediator (Yukawa potential). Each SPARC galaxy and each dwarf keeps its own collisionless halo; the force then reshapes it over the halo's age with a simulation-calibrated gravothermal model (cores form first; very strong scattering drives core collapse = the dense outliers). Clusters test the high-speed end. Scan: 1,536 points over m_χ = 1–3000 GeV, m_φ = 0.1–50 MeV, α_D = 10⁻⁶–0.3, attractive and repulsive.

* **Best fit:** m_χ = 316 GeV, m_φ = 0.243 MeV, α_D = 1.00e-01, repulsive. Cross-section: σ/m ≈ 177 cm²/g at 30 km/s, 0.324 at ~1000 km/s (halo average), 0.0282 at 1500 km/s.
* **Against collisionless dark matter on the same galaxies/dwarfs/clusters:** Δχ² = -237.0 for 3 extra parameters (**15.0σ** improvement). Breakdown: SPARC -102.6, dwarfs -137.0, clusters +2.6. ΔAIC vs ΛCDM overall = -231.0. **Conservative version** (SPARC Δχ² divided by ΛCDM's SPARC χ²/dof = 8.4): Δχ² = -146.7 (11.7σ).
* **Speed dependence is needed:** the best *constant* cross-section (0.3 cm²/g) reaches Δχ² = -170.0; the velocity-dependent force does -67.0 better than that.
* **Galaxy by galaxy:** 8 of 15 SPARC galaxies individually prefer a non-zero cross-section by Δχ² > 4. Dwarfs individually prefer: UMi 120, Draco 200, Sculptor 120, Sextans 120, Leo I 200, Leo II 120, Carina 80, Fornax 80, WLM 2, DDO 52 5, DDO 87 12, DDO 154 2, Aquarius 20, NGC 2366 20, CVnIdwA 20, DDO 168 5 cm²/g.
* **Your target (30–100 cm²/g at 30 km/s and ≤ 1 cm²/g at 1500 km/s):** 58 scanned points hit it; 3 of them are inside the 95% surviving window. Best on-target point: m_χ = 10 GeV, m_φ = 3.49 MeV, α = 1.00e-03, Δχ² from best = 2.8.
* **Surviving window (Δχ² < 7.8 from best, 95% for 3 parameters; 12 points, 58% attractive):** m_χ = 10–1e+03 GeV, m_φ = 0.1–8.47 MeV, α_D = 3.16e-04–3.16e-01. Predicted σ/m: 49.3–251 cm²/g at 30 km/s; 0.12–0.578 at ~1000 km/s; 0.00893–0.0631 at 1500 km/s. 1 window points lie within a factor 2 of the coupling a simple thermal relic would need.
* **Cosmology (DESI + Planck):** elastic scattering does not change the expansion history, so this hypothesis has exactly ΛCDM's cosmology score — neither helped nor hurt.
* **Strong-lensing subhalos:** no published hard limit on σ at < 30 km/s exists yet (only forecasts), so this block is not scored; it is the main forecast below.

**Reproduction of arXiv:2610.26877** (DESI DR2 BAO with r_d free + Pantheon+):

| Model | χ² | Δχ² vs ΛCDM | our parameters | paper |
|---|---|---|---|---|
| ΛCDM | 1416.14 | 0 | Ω = 0.304 | — |
| SIDM1 (annihilation only) | 1416.14 | +0.00 | log κC₁ → -7.00 (pinned to the low edge = no effect) | best −4.36, UL −3.93: indistinguishable from ΛCDM |
| SIDM2 (= constant-w dark energy) | 1411.53 | -4.61 | n = -0.26 ± 0.12 ⇒ w = -0.913; DESI alone n = -0.26 | n = −0.55 ± 0.12 (w = −0.82); DESI alone n = −0.24 |
| SIDM3 | 1410.66 | -5.48 | n = -0.53, log κC₁ = -2.50, Ω = 0.242 | n = −0.74, Ω = 0.243 |

* DESI alone: our n = -0.26 vs the paper's −0.24 — reproduced. DESI + Pantheon+: our w = -0.913 vs the paper's −0.82 ± 0.04 — **not reproduced**: the standard Pantheon+ likelihood (full covariance, magnitude marginalised) does not pull w as far from −1 as the paper reports. Their extra cosmic-chronometer data or a different supernova treatment may account for it; we did not include cosmic chronometers.
* **What the paper does and does not show for your force:** its 'SIDM' is a cosmic fluid with annihilation and particle creation; SIDM2 is mathematically constant-w dark energy. Its preference over ΛCDM is the same late-time dark-energy signal as H3, not evidence for velocity-dependent scattering. It does not test a Yukawa force.

**Forecast — what future data should see if this force is real (window above):**

* **Euclid** (thousands of lensing clusters and mergers): cluster-scale σ/m in the window is 0.0089–0.063 cm²/g at 1500 km/s. Values ≳ 0.1 would show up as cored cluster lensing profiles and small DM–galaxy lags; values ≪ 0.05 mean Euclid clusters will look exactly like cold dark matter, which would *not* kill the hypothesis (the action is at low speed).
* **Rubin LSST** (new ultra-faint dwarfs, many more quadruple lenses): the window predicts σ/m ≈ 34.4–115 cm²/g at ~20 km/s. Gilman+2021 forecast that 50 lenses give σ₂₀ < 11–23 cm²/g if dark matter is cold — so if the window is right, LSST-era lens samples should *detect* SIDM (collapsed, very dense subhalos plus cored ones). A null result at that level would kill most of the window. Dwarf densities vs orbital pericentre (more dense outliers on tight orbits) are the second test.
* **NA64 / LDMX** (fixed-target searches for MeV dark photons): if the mediator is a kinetically-mixed dark photon of 0.1–8.5 MeV, it must decay before Big-Bang nucleosynthesis, which requires mixing ε ≳ 3.7e-10 (2.00 MeV), 2.3e-10 (5.00 MeV), 1.8e-10 (8.47 MeV), 1.6e-10 (10.00 MeV), 1.2e-10 (20.00 MeV). NA64 and LDMX reach mixings far above that floor, so they can **confirm** such a mediator if ε happens to be large, but cannot **rule it out** (it can hide at small ε, or decay to neutrinos). Direct-detection limits (which bound ε from the other side for heavy dark matter) were not part of this run.
* **Verdict:** the force fits the galaxy and dwarf data better than cold dark matter while respecting every cluster limit; the surviving window is listed above.

## H5 — Clayten's push-pull unification

**(a) Generalised Chaplygin gas** (one fluid: matter-like when dense, Λ-like when diluted).
* Best fit α = 8.70e-03, A_s = 0.7392; Δχ² vs ΛCDM = 5.03; 95% bound |α| < 6.9e-02.
* α = 0 is *exactly* ΛCDM (same parameters give Δχ² = -1.1e-04). The growth data are the weak spot, as expected: the unified fluid's sound speed c_s² = −αw makes structure oscillate away (α > 0) or blow up (α < 0). Holding everything else at the ΛCDM best fit, fσ8 χ² changes by: α = 0.0001: -0.2, α = -0.0001: +6.7, α = 0.001: +11.1, α = -0.001: +280.9, α = 0.01: +4.7.
* Posterior with σ8 free: α = 0.028 ± 0.022 (95%: 0.000 to 0.086). α = 0 is outside the 95% range.
* **Where it holds:** only for |α| of order the posterior width above, i.e. essentially where it *is* ΛCDM (best-fit Δχ² vs ΛCDM = +5.03). SPARC, dwarfs and clusters inherit ΛCDM scores only under that condition.

**(b) Farnes (2018) negative-mass fluid.**
* As published (ρ₋ < 0 constant, open universe, no other dark matter): χ² = 28,785,512 vs ΛCDM 1,435 (Planck priors alone: 28,759,629). The best fit pushes the negative density to zero: a negative constant density *decelerates* expansion, the opposite of what supernovae show.
* With the sign left free the data choose Ω = +0.99 — a **positive** cosmological constant — and still fail (χ² = 27,104) because there is no dark matter to make the CMB and BAO work.
* **Galaxies:** a spherical negative-mass halo can only weaken gravity inside it. The SPARC fit drives the halo mass to the floor (median log M₋ = 0.0), leaving baryons alone: ΔSPARC χ² = +12,745 vs ΛCDM. Dwarfs: a measured positive dark density vs ≤ 0 predicted: χ² = 508. Clusters: lensing would follow the gas: χ² = 107.
* **Verdict:** fails every dataset by large margins. Farnes's flat-rotation-curve claim does not survive the shell theorem with real data.

**(c) Environment-dependent push** (dark energy differs in voids and crowded regions; void volume grows with structure).
* Best fit β = -0.151 (posterior -0.15 ± 0.14), i.e. void/crowded push ratio r ≈ 0.78 (r = 1 is ΛCDM). Δχ² = -1.20 for 1 extra parameter (1.1σ). Growth (fσ8) χ² = 12.8 vs ΛCDM 12.7: this version does not suffer the Chaplygin growth problem because dark matter still clusters.
* **Where it holds:** everywhere ΛCDM holds, with r within the posterior above; it gains less than w0–wa because one parameter tied to structure growth cannot reproduce the w0 > −1, wa < 0 shape DESI prefers.

**H5 overall:** represented in the ranking by its best version. Future data: Euclid/DESI-extension fσ8 and void statistics (void-by-void expansion) directly test version (c); version (a) is already excluded except at α ≈ 0.

## H6 — Clayten's dark atoms

**Model.** A fraction of dark matter is a dissipative 'dark atom' gas that cools into a thin dark disc (mass f_disc·M200, scale length λ × the stellar disc's); the rest is NFW cold dark matter. SPARC, the Gaia limits at the Sun, the Planck limit on strongly-interacting dark matter, dwarf densities and cluster lags are combined.

| f_disc | λ | ΔSPARC χ² | Σ_DD at Sun (M☉/pc²) | Gaia χ² (h = 20 pc) | thinnest Gaia-allowed disc | Planck χ² | Cluster χ² | Total Δ |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.5 | +0.0 | 0.00 | 0.0 | any | 0.0 | 0.33 | +0.0 |
| 0.001 | 0.5 | +20.4 | 0.19 | 0.0 | any | 0.0 | 0.34 | +20.3 |
| 0.001 | 1 | +2.7 | 1.11 | 0.2 | any | 0.0 | 0.34 | +2.7 |
| 0.001 | 2 | +8.4 | 1.34 | 0.3 | any | 0.0 | 0.34 | +8.6 |
| 0.003 | 0.5 | +32.8 | 0.57 | 0.1 | any | 0.0 | 0.38 | +32.5 |
| 0.003 | 1 | +21.7 | 3.32 | 1.8 | any | 0.0 | 0.38 | +23.1 |
| 0.003 | 2 | +23.6 | 4.01 | 2.6 | any | 0.0 | 0.38 | +25.8 |
| 0.01 | 0.5 | +229.7 | 1.89 | 0.6 | any | 0.2 | 0.51 | +229.2 |
| 0.01 | 1 | +133.4 | 11.06 | 19.6 | 93 pc | 0.2 | 0.51 | +151.8 |
| 0.01 | 2 | +66.6 | 13.38 | 28.6 | 100 pc | 0.2 | 0.51 | +94.1 |
| 0.02 | 0.5 | +511.6 | 3.78 | 2.3 | any | 0.6 | 0.73 | +512.1 |
| 0.02 | 1 | +282.8 | 22.11 | 78.2 | 155 pc | 0.6 | 0.73 | +359.2 |
| 0.02 | 2 | +115.2 | 26.75 | 114.5 | 187 pc | 0.6 | 0.73 | +228.0 |
| 0.05 | 0.5 | +2002.4 | 9.44 | 14.3 | 79 pc | 4.0 | 1.65 | +2014.9 |
| 0.05 | 1 | +690.2 | 55.28 | 488.9 | 386 pc | 4.0 | 1.65 | +1177.3 |
| 0.05 | 2 | +226.0 | 66.88 | 715.8 | 467 pc | 4.0 | 1.65 | +940.0 |
| 0.1 | 0.5 | +5147.7 | 18.88 | 57.0 | 131 pc | 16.0 | 4.00 | +5210.3 |
| 0.1 | 1 | +1274.4 | 110.55 | 1955.5 | 779 pc | 16.0 | 4.00 | +3235.5 |
| 0.1 | 2 | +354.6 | 133.77 | 2863.1 | 940 pc | 16.0 | 4.00 | +3223.2 |

* **Best combination:** f_disc = 0, λ = 0.5 (total Δχ² vs no dark disc = +0.0).
* **Surviving window** (all blocks combined, Δχ² < 6 from best, thin 20 pc disc): f_disc ≤ 0.001 of the halo mass (f=0/λ=0.5, f=0/λ=1, f=0/λ=2, f=0.001/λ=1). Gaia alone would allow up to 0.02; the rotation curves are what squeeze it further. A disc holding a larger share must be thicker than the 'thinnest Gaia-allowed' column — at which point it is no longer the thin disc the idea needs.
* **Planck:** at most ~5% of dark matter can be strongly coupled to dark radiation; the dissipative fraction f ≥ f_disc, so the window above is safely inside that unless only a small part of the dark-atom gas forms the disc.
* **What SPARC says:** adding a dark disc does not improve rotation-curve fits; rotation curves cannot measure the disc's thickness at all.
* **Future data:** Gaia DR4/DR5 vertical kinematics push the thin-disc limit below ~1–2 M☉/pc²; a detection would be a sub-100-pc dark layer in the vertical force at the Sun. Stellar streams crossing the disc and CMB-S4 (dark acoustic oscillations) test the dissipative fraction independently.

## H7 — Clayten's many black holes

* **Galaxies:** PBH dark matter is cold and collisionless on galaxy scales, so it makes the same halos as particle dark matter. Adding a central black hole (mass prior from the Kormendy & Ho black-hole–bulge relation) changes SPARC χ² by -27.9 vs NFW alone for 15 extra parameters (median fitted log M_BH = 5.5). 2 galaxies improve by Δχ² > 4: NGC2955 (-20, log M_BH = 9.1), UGC06787 (-10, log M_BH = 9.4). In those, the point mass mostly absorbs inner-rotation-curve residuals (bulge mass-to-light, non-circular motions): a 10⁹ M☉ black hole would be at the top of the observed range. In every other galaxy the black hole is invisible at SPARC radii. Conservatively (SPARC errors rescaled) the galaxy-block change is -3.3.
* **Single-mass PBHs, every limit in data item 8** (HSC, OGLE, EROS, MACHO microlensing; Eridanus II/ultra-faint heating; wide binaries; Planck accretion; Hawking evaporation in gamma rays, Voyager e±, 511 keV, CMB; plus LIGO):
  * PBHs can be **all** of the dark matter for masses 1.0e+17 – 8.9e+21 g.
  * PBHs can be **most** (≥ 50%) of it for 7.9e+16 – 1.6e+22 g.
  * Everywhere else at least one limit forbids f_PBH = 1 (the bounding constraints are logged per mass in `h7_pbh.json`).
  * Log-normal spectrum, width σ = 0.25: all dark matter allowed for central masses 1.1e+17 – 6.3e+21 g.
  * Log-normal spectrum, width σ = 0.5: all dark matter allowed for central masses 2.0e+17 – 6.3e+21 g.
  * Log-normal spectrum, width σ = 1.0: all dark matter allowed for central masses 6.3e+17 – 3.5e+21 g.
  * Log-normal spectrum, width σ = 1.5: all dark matter allowed for central masses 3.5e+18 – 2.0e+21 g.
  * Log-normal spectrum, width σ = 2.0: all dark matter allowed for central masses 3.5e+19 – 6.3e+20 g.
* **Caveat on the window's edges:** the low edge is set by Hawking-evaporation limits and the high edge by Subaru HSC microlensing, whose finite-source and wave-optics treatment moves the edge by up to ~10× between published versions.
* **Future data:** the asteroid-mass window is hard to close. Probes that could: next-generation MeV gamma-ray telescopes (e.g. COSI) at the low edge; high-cadence microlensing of nearby galaxies/white dwarfs and X-ray pulsar lensing at the high edge; Roman Space Telescope microlensing for the planetary-mass end.
* **Verdict:** survives, but only as asteroid-mass PBHs; the 'one big black hole per galaxy' part is untestable with rotation curves.

## What was run (method in brief)

* **Data** (downloaded, cached, SHA-256 in `data/MANIFEST.json`): SPARC (all galaxies with ≥5 points), DESI DR2 and DR1 BAO, Planck 2018 distance priors (Chen+2019, parsed from the paper's LaTeX), Pantheon+ (z > 0.01, full covariance), Gold-2017 fσ8 (18 points), Read+2019 dwarf densities (the compilation Correa 2021 fits), Harvey+2015 72-collision lag, Bullet Cluster, Andrade+2022 and Sagunski+2021 cross-section limits, Gaia dark-disc limits, Planck interacting-DM limit, and the PBH limit set (Kavanagh's PBHbounds digitisations). Single-number literature constraints are machine-checked against the cached abstracts/LaTeX.
* **Fits:** cosmology by differential evolution + Nelder–Mead, posteriors by emcee (300 steps); galaxies one by one with identical nuisance priors for every hypothesis; the Yukawa force on a 8×8×12 grid (× attractive/repulsive).
* **Known simplifications** (all stated in the code): compressed CMB instead of full Planck likelihood; SIDM halos via the Yang+2023 parametric model without baryonic contraction or tidal stripping of satellites (Correa 2021 shows stripping matters for the dSphs); the Yukawa cross-section uses the Tulin–Yu–Zurek analytic regimes with σ_T as a stand-in for the viscosity cross-section; MOND ignores the external field effect; the dark disc is razor-thin for rotation curves.


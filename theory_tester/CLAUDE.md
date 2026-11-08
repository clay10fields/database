# CLAUDE.md — Theory Tester (complete brief, nothing to fill in)

You are Claude Code. This is the entire job. Every hypothesis is already written below. Do not ask Clayten for hypotheses, inputs or approval. Build the tool, run everything, and hand back one plain-English report. Keep working until the Done section is met. Save this text as CLAUDE.md in the project root first.

## What you are building
A local Python instrument on Clayten's Mac (M4 Pro, 48 GB, no GPU needed) that fits each physics hypothesis below to public data, scores it against standard cosmology (Lambda-CDM), and reports where it holds and where it breaks.

## Data (download, cache, checksum)
1. SPARC: rotation curves for 175 galaxies (astroweb.cwru.edu/SPARC).
2. DESI BAO: DR1 and DR2 public expansion-history results.
3. Planck 2018: compressed CMB distance priors.
4. Pantheon+ supernovae.
5. Growth-rate data (f sigma8) from published compilations.
6. Milky Way dwarf spheroidal central densities (Read et al. compilations; MNRAS 503, 920).
7. Cluster merger dark matter vs galaxy offsets (Bullet Cluster; Harvey et al. 2015 sample).
8. Primordial black hole limits: microlensing (Subaru HSC, OGLE, EROS), Eridanus II cluster heating, Gaia wide binaries, Planck accretion, Hawking evaporation.

## Repo layout
data/ (downloaders + cache), hypotheses/ (one file per hypothesis: parameters, priors, predictions for v(r), H(z), CMB distances), baselines/ (Lambda-CDM, MOND), fit/ (scipy then emcee), score/ (chi-squared, AIC, BIC per dataset and combined, plus tension flags), results/ (every run logged with full config, never overwritten), report/ (plain English).

## Hypotheses to run (all of them, on every dataset that applies)
1. Lambda-CDM (baseline).
2. MOND with a standard interpolation function.
3. Evolving dark energy (w0-wa) on DESI + Planck + Pantheon+.
4. CLAYTEN'S SHORT-RANGE, SPEED-DEPENDENT FORCE (LEAD HYPOTHESIS). Dark matter has its own force that only acts up close and weakens as particles move faster. Target: roughly 30-100 cm^2/g at dwarf speeds (~30 km/s), at most 0.1-1 cm^2/g at cluster speeds (~1,500 km/s). Implement a Yukawa-mediator cross-section. Scan dark matter mass, mediator mass (start ~1-10 MeV) and coupling. Fit SPARC cores, dwarf densities (dense outliers = gravothermal collapse), cluster offsets and strong-lensing subhalo constraints together with DESI + Planck. Reproduce arXiv 2610.26877 (Oct 2026, DESI DR2, velocity-dependent SIDM favoured over Lambda-CDM) as a check. Report the surviving window and forecast what Euclid, Rubin LSST, NA64 and LDMX should see.
5. CLAYTEN'S PUSH-PULL UNIFICATION. Dark matter and dark energy are one substance: pulls where dense, pushes where spread out. Implement generalised Chaplygin gas and a Farnes-style (2018) negative-mass fluid. Fit SPARC, DESI, Planck, then test growth (f sigma8), its known weak spot. Also test an environment-dependent version where the push differs in voids vs crowded regions.
6. CLAYTEN'S DARK ATOMS. A fraction f of dark matter is atoms of hidden charged particles with their own dark photon; they cool into a thin dark disc, the rest is cold dark matter (Fan, Katz, Randall & Reece 2013; Cyr-Racine & Sigurdson). Fit f, disc thickness and density to SPARC and Gaia vertical-force limits, with Planck limits on early interaction.
7. CLAYTEN'S MANY BLACK HOLES. One big central black hole per galaxy plus countless small primordial black holes making up some or all of dark matter. Single-mass and log-normal spectra. Fit SPARC, then run every limit in data item 8. Map the window where they can still be most of dark matter (main open gap ~1e17-1e22 grams).

## Rules
- Never skip a hypothesis or dataset.
- Log every result with the exact configuration that produced it.
- For hypotheses 4-7 (Clayten's own), work to find the conditions where each holds before judging it, then report the numbers straight.
- Don't stop between steps to ask. Fix your own errors and keep going.

## Done
One command (python run_all.py) runs everything and writes report/REPORT.md: a ranked table of all seven hypotheses with scores per dataset, then a short plain-English section per hypothesis saying what passed, what failed, by how much, and, for Clayten's four, the surviving parameter window and what future data would confirm or kill it.

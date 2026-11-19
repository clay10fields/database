# Theory Tester

Fits seven dark-matter / dark-energy hypotheses to public data, scores each against Lambda-CDM, and writes a
plain-English report. The brief is in `CLAUDE.md`.

## Run it (Mac or Linux, Python 3.10+)

```bash
cd theory_tester
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_all.py            # full run: downloads data (~60 MB), fits everything, writes report/REPORT.md
python run_all.py --quick    # ~10-minute smoke test on a galaxy subset with short chains
```

On an M4 Pro (14 cores) the full run takes roughly 30–60 minutes; it uses every core by default (`--workers N` to
limit). Nothing needs a GPU.

## Where things are

| Folder | What it holds |
|---|---|
| `data/` | `download.py` (fetch + cache + SHA-256 manifest), `loaders.py` (parsers; paper tables are read from the papers' own LaTeX), `literature.py` (single-number limits, each machine-checked against its source) |
| `physics/` | expansion history, distances, sound horizon, CMB priors, growth; halo profiles; Yukawa cross-sections; the gravothermal SIDM model |
| `baselines/` | Lambda-CDM and MOND |
| `hypotheses/` | one file per hypothesis (H1–H7) plus the arXiv:2610.26877 reproduction |
| `fit/` | cosmology fitter (scipy differential evolution, then emcee) and the per-galaxy rotation-curve fitter |
| `score/` | chi-squared, AIC, BIC, goodness-of-fit and parameter-goodness-of-fit tension tests |
| `results/<run_id>/` | every step's JSON with the full config (`config.json`); a new directory per run, never overwritten |
| `report/REPORT.md` | the latest report (a copy also sits in each run directory) |

`data/cache/` is not committed; `data/MANIFEST.json` is, so a fresh download is checked against the hashes of the
files these results were computed from.

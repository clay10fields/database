# database — read this first

This repo is the permanent record. Rules, none waived:

* `raw/` is append-only. Never rewrite, reorder, or "fix" a raw file. A bad row is documented in
  `raw/*/meta/`, not edited away.
* `derived/` is disposable. It is rebuilt from `raw/` by `collectors/resample.py`. Never hand-edit it.
* Read-only public endpoints. The only credentials are read-only market-data keys stored as
  GitHub secrets (`COINALYZE_API_KEY`, `COINGECKO_API_KEY`; see `collectors/SECRETS.md`), read
  from the environment by the recorders. No exchange keys. Never commit a key.
* No orders. Not in any mode, not behind any flag. This repo has no trading code and will not.
* Never write a zero that was not measured. Failed fetches go in meta as failures.

Layout: `raw/` recorded truth · `derived/panel/<interval>/<COIN>.csv` what calculators read ·
`research/` studies, each dated, with the code that produced them · `collectors/` the recorder
and the resampler. Sister repo: `clay10fields/crypto-research-machine` (the OKX whole-market
recorder lives there; its output is mirrored under `raw/okx_recorder/`).

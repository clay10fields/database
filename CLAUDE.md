# READ EVERY FILE. OPEN EVERY RESULT TABLE. HE TELLS YOU THIS PERSONALLY. DO IT.

# database — read this first

**READ THE FILES. OPEN EVERY RESULT TABLE. DO NOT SKIM THE INDEX AND START WRITING.** Clayten says this to every session in person. The verdicts are in `research/steward/WHAT-THE-FILES-SAY.md`. The tables are in each study's `results/` folder. Open them. A note that cites a number without the table is not done. Do not ask him to explain the job again.

The job, already decided. Find an edge on the coins he can trade, Kraken and Kalshi. Paper only. No orders. This repo, main, no other repo. Regime before the trade: Stress, trend up, trend down, calm. Compression is stand-down. Do not short a bull leg unless that cell already paid. One idea at a time. A close miss stays. A failure is written with the reason, and that reason is the next hypothesis. Do not add to the current book from a backtest.

The book is the crowd short and the flush long in `research/book/CURRENT-BOOK-2026-10-01.md`, with its two caveats. Already settled: do not short a funding spike, a liquidation spike, a break, or catch-up on the 16. The paper spec is the wide washout on the 16 only. ZEC, NEAR, ALGO, WLD, RENDER have no liquidation history in `raw/coinalyze_daily/` yet. Do not rerun that spec on them and call it done.

Rules, none waived:

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
and the resampler. Do not open another repo. The copy under `raw/okx_recorder/` is already here.

Branches: `main` is the only live branch. The 15 `chatgpt-*` branches and `claude-review-2026-10-01` were merged
into `main` on 2026-10-01 (PR #1) and are **superseded** — every file on them is contained in `main`, verified
file-by-file. Do not branch from them, cherry-pick from them, or treat them as unmerged work; they are pending
deletion only because ref deletion is blocked from the agent sandbox. The 13 `chatgpt-*.yml` workflows they carried
were dropped deliberately: each was pinned to its own branch and could never fire again.

Research detail after the verdicts file: `research/README.md`.

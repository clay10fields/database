# GitHub Actions secrets

Exactly two secrets exist for this repo, both read-only market-data keys:

- `COINALYZE_API_KEY` — the free, read-only Coinalyze data key (hourly + daily recorders).
- `COINGECKO_API_KEY` — the free CoinGecko demo key (record-coingecko: daily price, volume,
  market cap; demo keys only serve the last 365 days).

That is the whole list. Per `CLAUDE.md`: read-only public endpoints, no exchange keys of any
kind, ever. Kraken, Coinbase, Binance US and Kalshi collectors use only unauthenticated public
endpoints; if an endpoint requires a key it is not recorded, and the failure is logged in meta.
Data-only keys like these are fine. Do not add KRAKEN_*, COINBASE_*, BINANCE_*, or KALSHI_* secrets. (A list of those was here
briefly on 2026-10-01 and was removed; the Kalshi signing code was removed with it.)

Repo → Settings → Secrets and variables → Actions. After changing a secret: Actions →
the matching workflow (record-hourly, record-coingecko) → Run workflow.

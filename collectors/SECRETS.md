# GitHub Actions secrets

Exactly one secret exists for this repo:

- `COINALYZE_API_KEY` — the free, read-only Coinalyze data key.

That is the whole list. Per `CLAUDE.md`: read-only public endpoints, no exchange keys of any
kind, ever. Kraken, Coinbase, Binance US and Kalshi collectors use only unauthenticated public
endpoints; if an endpoint requires a key it is not recorded, and the failure is logged in meta.
Do not add KRAKEN_*, COINBASE_*, BINANCE_*, or KALSHI_* secrets. (A list of those was here
briefly on 2026-10-01 and was removed; the Kalshi signing code was removed with it.)

Repo → Settings → Secrets and variables → Actions. After changing a secret: Actions →
record-hourly → Run workflow.

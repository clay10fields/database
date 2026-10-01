# GitHub Actions secrets for the hourly recorder

Repo → Settings → Secrets and variables → Actions → New repository secret.

Do not put any of these in a file in the repo.

Required for Coinalyze (already in use):

- COINALYZE_API_KEY

Optional. Public market data still records without them.

- KRAKEN_API_KEY
- KRAKEN_API_SECRET
- COINBASE_API_KEY
- COINBASE_API_SECRET
- BINANCE_US_API_KEY
- BINANCE_US_API_SECRET

Needed if Kalshi estimate calls start returning 401:

- KALSHI_KEY_ID
- KALSHI_PRIVATE_KEY   (full PEM, including BEGIN/END lines)

After saving a secret, run Actions → record-hourly → Run workflow.

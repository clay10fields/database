# Binance UM backfill, Dec 2021 – Aug 2026

Source: data.binance.vision daily metrics (5-min OI, taker long/short, top-trader long/short) resampled to 4h, joined to monthly 4h klines. Eight playbook coins. Single venue, not Coinalyze aggregate. Raw daily zips not committed.

Same rule as the playbook cell: first 4h close above prior UTC day high, OI +4% from bar before break to bar after, short, 36h, 0.1% fee.

ALL n=1098 mean -0.08% win 55% t -0.42

2021 n=17 +0.98
2022 n=317 +0.18
2023 n=309 -0.27
2024 n=199 -1.48 t -2.45
2025 n=179 +0.47
2026 n=77 +1.69 t 3.62

2026 matches the Coinalyze year. 2022–2024 do not. Taker-ratio filter did not repair it.

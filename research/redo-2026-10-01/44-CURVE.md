# 44. Equity curve and exits — 2026-10-01 19:48 ET

Computed on `raw/coinalyze_daily/`. Not a book add. Not a Kraken result. The five missing coins are not in this file.

## Curve
Washout spec, skip AAVE and SHIB. Hold 7 days. Fee 0.10%. $5,000 start. 10% of equity per trade. Max 5 open. No second position in the same coin. Marked only when a trade closes, so the drop is understated.

111 trades taken, from 2020-11-25 to 2026-09-15. End $10,547. Worst marked drop −5.69%. Win 64.9%.

Years, mean of the trades that got in. 2020 +9.28% on 3. 2021 +2.82% on 8. 2022 +5.03% on 16. 2023 +2.65% on 35. 2024 +21.66% on 17. 2025 +4.95% on 20. 2026 +6.30% on 12. Every year in this cut is positive. 2020 is three trades.

The curve is positive. It is not the book. The book is a different engine and a larger number. This is one long, 10% at a time, on 16 coins.

## What was changed
Vol target, size = 4% divided by the prior 20-day daily vol, capped at 1.5. Mean fell from +7.10% to +6.20%. t rose from 3.12 to 3.36. Worst trade went from −29.8% to −36.2%. Sizing did not clean the tail.

An 8% stop checked on daily closes: +5.91%, t 2.65. It cuts the tail and cuts the edge. Not used.

A 5% target: +4.11%, t 4.34. Higher t, less money. It sells the bounce. Not used.

Hold 10 days: +10.88%, t 2.58. More money, weaker t, 2021 red. The 7-day hold stays.

Skip AAVE and SHIB is the curve above. That skip was already in the paper spec. It is the version that keeps every year positive in this run.

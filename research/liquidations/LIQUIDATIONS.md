# Liquidation spikes: what we know

Status: **full treatment 2026-10-01. The plain version is real across 7 years but violent, and it has been losing since Dec 2025. The version worth running is the filtered one (market-wide spike in a high-volatility tape), small. Never short a short squeeze.**
Coinalyze daily liquidations, OI and price for 16 Binance perps, Sep 2019 to Oct 2026. This is the one dataset here that covers the
previous cycle. Liquidations ranked against the coin's own trailing 90 days. Enter at the day's close, hold N days, 0.10% fee.

## Results (results/deep_results.csv)
| rule | side | hold | n | per trade | edge | t | 2019–21 / 2022–23 / 2024–26 edge | years + |
|---|---|---|---|---|---|---|---|---|
| **long liquidations ≥ 95th pct** | long | 3d | 1716 | **+2.07%** | +1.65 | **3.1** | +2.2 / +0.8 / +2.0 | 6 of 7 |
| same + OI down (H15) | long | 3d | 1272 | +2.12% | +1.63 | 2.8 | +2.2 / +0.7 / +2.0 | 5 of 7 |
| long liqs ÷ OI ≥ 95th + OI down | long | 3d | 1222 | +2.31% | +1.79 | 2.9 | +2.6 / +1.0 / +1.9 | 5 of 7 |
| long liqs ≥ 99th pct | long | 3d | 419 | +2.15% | +1.77 | 1.6 | +4.1 / −0.1 / +2.0 | 5 of 7 |
| same, 7-day hold | long | 7d | 1334 | +2.53% | +1.34 | 1.7 | worst trade −62% | 4 of 7 |
| **short liquidations ≥ 95th pct** | **short** | 3d | 1567 | **−2.51%** | −1.93 | **−4.0** | −4.0 / −0.7 / −1.9 | 0 of 7 |
| short liqs + close in top 10% of 20-day range (H16) | short | 3d | 471 | −2.47% | −1.58 | −1.9 | — | 1 of 7 |
| short liqs + OI still rising | short | 3d | 998 | −2.39% | −1.80 | −3.6 | — | 1 of 7 |
| short liqs + top of range: ride it long | long | 3d | 471 | +2.27% | +1.58 | 1.9 | +4.1 / +1.3 / +0.4 | 6 of 7 |
| placebo: OI down > 5% alone | long | 3d | 3753 | +1.12% | +0.49 | 1.7 | — | — |
| placebo: price down > 5% alone | long | 3d | 2909 | +1.14% | +0.57 | 1.2 | — | — |
| placebo: random | long | 3d | 1716 | +0.27% | −0.20 | −0.8 | — | — |

## What it means
* **A long-liquidation spike is a buy, for 3 days.** It beats a plain big down day or a plain OI drop by about +1% per trade, and it worked
  in 2019–21, 2022–23 and 2024–26. This is the daily cousin of the flush long (OI flush + crowd un-crowded): forced selling that ends.
* **Never short a short-squeeze.** A short-liquidation spike means price keeps going up for days: shorting it lost −2.5% per 3 days,
  negative in all 7 years, worst trades past −100%. Riding it long is positive (+2.3%) but noisy. Same lesson as the funding study.
* Measuring liquidations as a share of OI is slightly better than raw liquidations. 7-day holds earn more but blow up more.
* 2022–23 is the weak stretch for the long: in a bear market the flush keeps flushing. Consistent with the flush long's 2022.


## Every cut (deep2.py, results/deep2_results.csv)
* **Dose-response holds**: liqs ≥ 80th pct +1.11%, ≥ 90th +1.49%, ≥ 95th +2.07%, ≥ 98th **+3.09%** (62% win, median +2.0%). At the 99th the sample thins and it drops.
* Liquidations as a share of OI is a touch better than raw contracts (≥ 95th: +2.30%).
* **Hold 2–3 days.** Day 1 earns +0.74%, day 2 +1.54%, day 3 +2.07%; after that the median goes to zero and the worst trades blow up. 2 days gives up 0.3% and cuts the worst trade from −64% to −27%.
* Conditions that held in all three periods (2019–21, 2022–23, 2024–26): **market-wide spike (5+ coins)** +2.41%, 7/7 years; **high volatility tape** (20-day vol in its top fifth) +3.47%, 7/7;
  **coin already down >15% over 7 days** +2.65%, 66% win, 7/7; BTC up over 30 days +2.94%, 7/7; coin within 20% of its 1-year high +4.30%.
* What hurts: a single-coin spike (1–2 coins) +1.00%, only 2/7 years; BTC flat or up on the day (the liqs were a wick) +0.95%, 46% win; low-volatility tape +0.99%.
* Funding, OI direction, first-vs-second day: don't matter much here.
* By coin: DOGE +4.6%, XLM +3.9%, DOT +3.2%, SOL +2.7%, ADA +2.4%, SHIB +2.5%. Weak: AAVE +0.6%, ETH +1.0%, XRP +1.1%, BTC +1.2%.
* By year: 2020 +4.0%, 2021 +3.8%, **2022 −0.6%**, 2023 +1.7%, 2024 +3.7%, 2025 +2.6%, **2026 −0.4%** (226 trades; May–June 2026 lost on 107 trades).

## Stacked versions (combo.py)
| version | n | per year | per trade | win | t | 2022 | 2026 | years + |
|---|---|---|---|---|---|---|---|---|
| A base: liqs ≥ 95th, 3d | 1716 | 245 | +2.07% | 57% | 3.1 | −0.6% | −0.4% | 6 of 7 |
| B liqs ≥ 98th | 791 | 113 | +3.09% | 62% | 3.3 | −1.1% | −0.7% | 5 of 7 |
| C base + market-wide | 1186 | 169 | +2.41% | 61% | 2.7 | −0.8% | +0.3% | **7 of 7** |
| D base + high-vol tape | 599 | 86 | +3.47% | 60% | 3.6 | −0.6% | +0.8% | **7 of 7** |
| **F base + market-wide + high-vol** | 381 | 54 | **+4.20%** | **66%** | 3.2 | −0.3% | **+2.4%** | **7 of 7** |
| H base + coin down >15% over 7d | 393 | 56 | +2.65% | 66% | 2.0 | +0.1% | +2.3% | 7 of 7 |

## The path and how to react (account.py)
* Day by day (base): +0.81% after day 1, +1.89% after day 2, +2.17% after day 3. 43% of trades are under water after day 1.
  The deepest dip inside the trade: median −4.8%, **one in ten dips more than −17%**. This is a wilder trade than the 4h flush long.
* **Don't cut day-1 losers.** A trade down more than 5% after day 1 (20% of them win) still has **+2.9% left in it** on average: the second-leg bounce.
  On the filtered version F it's +8.0% left. Cutting them costs money.
* Winners show on day 1: up more than 3% after day 1 → 84% win, +8.9% average.
* **Stops gut it.** An 8% intraday stop: +2.07% → +0.89%. A 12% stop: +1.39%. A 6% target: +0.99%. The one free rule is "exit after day 2 if not positive" (+2.17%, worst −27% instead of −64%).
* Damage control = size. Size so a −20% trade is survivable.

## $5K account (account.py, results/account_results.csv; Kraken US costs, SHIB/XTZ out, max 5 open)
| version | per trade size | per year | worst drop | Sharpe | worst month | 2022 | 2026 |
|---|---|---|---|---|---|---|---|
| A base | 15% | +42% | **−30%** | 1.3 | −14% | −$867 | **−$5,605** |
| A base | 25% | +76% | −51% | 1.3 | −24% | −$4,477 | −$47,595 |
| D + high-vol | 15% | +27% | −18% | 1.3 | −9% | −$986 | +$587 |
| **F + market-wide + high-vol** | **15%** | **+18%** | **−19%** | 1.1 | **−7%** | −$558 | **+$1,538** |
| F | 25% | +39% | −36% | 1.2 | −13% | −$1,370 | +$7,193 |
* **The base version is not tradeable as a book.** It took −51% in Dec 2021–May 2022, −39% at FTX, −37% in Apr–Aug 2024, and has been in a −43% hole since Dec 2025 that hasn't recovered. Every one of those is a bear leg where the flush kept flushing.
* No pause rule fixes the base version (skipping when BTC is 20% off its high still leaves −36% drawdowns). **The filter is the fix**: wait for the market-wide spike in a high-volatility tape. Version F is positive in every year including 2026, at the cost of ~54 trades a year instead of 245.
* Stops make the account worse (A with a 12% stop: Sharpe 1.3 → 1.0). Max 8 open makes it worse (−63%). Max 3 is a touch safer, not much.


## Symptoms before the move (symptoms.py, results/symptoms_*.csv)
What the 3–30 days before the spike looked like, and how the 3-day buy went. Base version; version F in brackets.
| the lead-up | n | per trade | win |
|---|---|---|---|
| **funding ran hot the week before** | 597 | **+3.42%** [+6.17%, 69% win] | 58% |
| funding was cold the week before | 338 | +1.96% | 55% |
| **price had run up >30% in the month before the drop** | 357 | **+3.64%** [+5.60%, 71% win] | 60% |
| price was already falling the month before | 412 | **+1.08%** [+3.18%, t 1.0] | 56% |
| OI had built >15% in the 14 days before (leverage piled in) | 458 | +3.28% | 53% |
| crowd was still long (daily L/S ≥ 70th pct) | 727 | **+1.41%**, t 1.2 | 55% |
| crowd was already short (≤ 30th pct) | 445 | +2.86% | 57% |
| crowd leaving (ratio down >10% in 7 days) | 467 | +2.57% | 55% |
| 4–5 of the last 5 days down (a long slide) | 562 | +1.56% | 58% |
| 1–2 of the last 5 days down (a sudden hit) | 609 | +2.89% | 55% |
| liquidations 5×+ the 30-day average (true cascade) | 481 | +2.48% | 57% |
* **The bounce is biggest when the spike ends a euphoric run**: hot funding, a 30%+ run-up, leverage piled in, then a sudden hit. That's a crowded
  bull move getting flushed, and the buyers come back.
* **The bounce is weakest when the spike is one more leg of a slide**: price already falling for a month, 4–5 red days in a row, and the crowd
  still long (more left to flush). That is 2022 and May–June 2026.
* So the symptom to watch before buying: was this a sudden liquidation out of strength, or the latest hit in an ongoing bleed with longs still trapped?

## Current read
* Run **version F only**: long liquidations ≥ 95th pct on 5+ coins the same day, with the coin's 20-day vol in its top fifth. Buy the close, hold 3 days, no stop,
  exit after day 2 if not positive. 15% per trade, max 5 open. Expect ~1 trade a week and −20% drawdowns.
* It's the same mechanism as the flush long (forced selling that ends), so on the book it may not add much diversification. Test it on the combined book before adding.
* The hourly recorder has liquidations, so a 4h version can be built once there's history; the daily version can go in a daily watcher now.

## Earlier read (first pass)
* Add long-liquidation spikes to the flush-long family. The hourly recorder has liquidations (Coinalyze liq table), so an hourly/4h
  version can be tested once there's history (the 4h archive has no liquidations; the daily one does).
* Hard rule for the toolkit: short liquidations spiking = do not short, whatever the Grid cell says.

Files: code/deep.py (first pass), deep2.py (every cut), combo.py (stacked), account.py (path, rules, account, drawdowns); results/*.csv. Run from this folder.

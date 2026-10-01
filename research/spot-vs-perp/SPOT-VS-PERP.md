# Spot vs perp flow: what we know

Status: **full treatment 2026-10-01. On its own: nothing. On the trades: a real quality signal, best used as a size rule, not a gate. Not yet in the watcher.**
Binance spot 4h klines (taker-buy volume) for 15 coins (no XTZ spot), Aug 2020 on; joined to the 16-coin perp panel, Dec 2021 to Aug 2026.
spot_net = 2 × taker-buy ÷ volume − 1 (positive = aggressive buyers), averaged over 24h, ranked against the coin's own 90 days.

## On its own (H09, H10, H11): nothing
| rule | side | hold | n | per trade | t |
|---|---|---|---|---|---|
| rally > 3%, spot not buying | short | 24h / 72h | 1583 / 1336 | −0.05% / +0.04% | 0.2 |
| rally > 3%, spot buying | long | 24h / 72h | 3758 / 2778 | +0.02% / +0.41% | 0.8 / 1.7 |
| perp taker ratio at its extreme (H11) | short | any | ~1900 | ~0 | < 0.5 |
| perp-led rally (futures ÷ spot volume high) | short | any | ~1300 | −0.2% | −0.9 |
| spot-led rally | long | any | ~1700 | ~0 | < 0.9 |
| "hollow move" (OI up, spot volume low, price up) | short | any | ~750 | ~0 | < 0.7 |
A rally is a rally whoever is buying it. The futures-vs-spot ratio says nothing about the next 3 days.

## As a filter on the trades that work: strong
| trade | with spot flow | n | per trade | win | t | every year? |
|---|---|---|---|---|---|---|
| crowd short (base), 72h | spot NOT buying (≤ 30th pct) | 500 | **+1.23%** | 59% | **4.3** | yes |
| crowd short (base), 72h | spot buying (≥ 70th pct) | 676 | +0.22% | 52% | 1.2 | 4 of 5 |
| crowd short (base), 24h | spot not buying | 644 | +0.52% | 56% | 3.8 | yes |
| flush long B, 72h | spot buying (≥ 70th pct) | 355 | **+2.62%** | 56% | 3.4 | 4 of 5 |
| flush long B, 72h | spot selling (≤ 30th pct) | 314 | +0.16% | 47% | 0.6 | — |
| drop > 3% in 24h, spot buying | long, 72h | 1049 | +1.03% | 50% | 3.0 | yes |
* The crowd short works when the crowd is long on the perps and **spot isn't confirming**. When spot is buying too, the rally is real and the short is dead.
* The flush long works when **spot is buying the flush**. A flush that spot is also selling keeps going.
* This is the same picture as the OI-jump study: leverage without spot behind it fades; leverage with spot behind it continues.
* Both filters use data the hourly recorder already collects (Coinalyze spot_ohlcv, bv). They can go into the watcher now.


## Full treatment (code/account.py, code/book.py; results/filter_results.csv, book_results.csv, book_sized_results.csv)
### Dose-response on each trade
| spot condition | crowd short 72h | crowd short 24h | flush long B |
|---|---|---|---|
| no condition | +1.44%, 59% win (265) | +0.46% (1239) | +1.86% (771) |
| short: spot_pct ≤ 0.6 · long: ≥ 0.4 | +1.94%, 63% (155), t 3.9 | +0.59% (691) | +2.59%, 55% (484), **5/5 years** |
| short: ≤ 0.5 · long: ≥ 0.5 | +1.73% (126) | +0.57% (588) | **+2.84%, 56% (408), train +1.6 / test +4.3, 5/5** |
| short: ≤ 0.3 · long: ≥ 0.7 | **+2.26%, 67% (69)** | **+0.81%, 56% (330), t 3.8** | +3.01% (256), worst −19% |
| extreme: ≤ 0.1 · ≥ 0.9 | +0.88% (20) | +0.34% | +2.25% (83) |
| the opposite (spot agreeing with the crowd) | +0.87%, 2/5 years | +0.24% | +0.98%, 49% win |
| perp-led move (futures ÷ spot volume ≥ 80th pct) | **+2.95%, 74% win (38)**, both halves | +0.65% | **+0.45%**, t 1.1 |
| spot-led move (≤ 20th pct) | +1.23% | +0.55% | **+2.80%, 61% win** |
| 3-day spot flow instead of 24h | +1.62% | +0.52% | +3.37%, 5/5 years |
* Clean dose-response on the flush long: the more spot is buying the flush, the bigger the bounce, up to the 80th pct (the top decile is thin and 2024-heavy).
* On the crowd short the sweet spot is "spot not buying" (≤ 0.3–0.6); the extreme (≤ 0.1) is too thin. **A perp-led rally** (futures volume swamping spot) is the single best short set-up here: +2.95%, 74% win, in both halves, but only 38 trades.
* **A perp-led flush doesn't bounce** (+0.45%): if spot isn't involved in the flush, the leverage is just being moved around. A spot-led flush bounces (+2.80%).
* The crowd short's 72h version is thin (265 trades) and the halves disagree on the tight thresholds. Treat the crowd-short numbers as leads; the flush-long ones as a pass.

### On the account: gate vs size
| plan ($5K, Feb 2023–Aug 2026, Kraken costs) | per year | worst drop | Sharpe | worst month |
|---|---|---|---|---|
| crowd short 72h 50%, no spot gate | +46% | −21% | 1.7 | −10% |
| same, only spot ≤ 0.6 | +23% | −10% | 1.4 | −6% |
| flush long 15%, no gate | +36% | −14% | 1.8 | −5% |
| same, only spot ≥ 0.5 | +30% | −13% | 1.9 | −5% |
| **book, no spot gates** | **+110%** | −24% | 2.6 | −11% |
| book, both gated (CS ≤ 0.6, FL ≥ 0.5) | +72% | **−15%** | 2.5 | **−5%** |
| **book, spot as size: CS 50% / 35%, FL 25% / 10%** | **+153%** | −27% | **2.7** | −11% |
| book, spot as size: CS 50/35, FL 20/15 | +132% | −22% | 2.7 | −10% |
* **As a hard gate, spot flow halves the trade count and the return, and the Sharpe doesn't improve.** The trades it removes were still positive on average (+0.9% to +1.0%); throwing them away costs more than the risk it saves. Gating is the conservative version: half the return, half the drawdown.
* **As a size rule it adds.** Full size when spot agrees, reduced when it doesn't: Sharpe 2.6 → 2.7, return up by a third, drawdown roughly unchanged. The 20/15 version keeps the drawdown at −22%.
* Live: the hourly recorder has spot taker-buy volume (panel columns sv, sbv), so spot_pct can be computed in the watcher exactly as here (2 × sbv ÷ sv − 1, 24h mean, own 90-day rank).

## Current read (replaces the earlier one)
Don't gate on spot flow; size on it. Crowd short: 50% when spot_pct ≤ 0.6, 35% otherwise. Flush long: 20–25% when spot_pct ≥ 0.5, 10–15% otherwise.
Log spot_pct on every watcher signal so the live record can confirm the split. The perp-led-rally short (+2.95%, 74%) is a lead to watch, not a rule.

## Earlier read (first pass)
Add to both trades as a condition, pending a check on the account (it cuts trade counts by ~40%): crowd short needs spot_net_pct ≤ 0.3;
flush long needs spot_net_pct ≥ 0.7. Test on the $5K account next, then into the watcher as CROWD_24H_S / FLUSH_B_S.

Files: code/deep.py (first pass), account.py (dose-response), book.py (account and book); results/*.csv. Run from this folder.

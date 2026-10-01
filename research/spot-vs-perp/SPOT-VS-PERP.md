# Spot vs perp flow: what we know

Status: **tested 2026-10-01. On its own: nothing. As a filter on the two working trades: strong. Not yet in the watcher.**
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

## Current read
Add to both trades as a condition, pending a check on the account (it cuts trade counts by ~40%): crowd short needs spot_net_pct ≤ 0.3;
flush long needs spot_net_pct ≥ 0.7. Test on the $5K account next, then into the watcher as CROWD_24H_S / FLUSH_B_S.

Files: code/deep.py, results/deep_results.csv. Run from this folder.

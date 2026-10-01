# Redo 2026-10-01 — killed ideas walked again

Written in this repo only. Not in crypto-research-machine. Not in hype-pressure-kit.
Read this before trusting a "dead, do not retest" line from 2026-10-01.

Rule used: one idea, every cut, find where it holds. A loss on one setting is a result, not a ban.
Fee 0.10% round trip. t is clustered by entry day. No orders.

## 1. Level-break fade — finished, not a trade
Data: derived/panel/4h_backfill, 14 coins, 2025-10-31 to 2026-09-30. ETH and SOL files are not in that folder.
First 4h close above the prior UTC day high, open interest up, short.
OI jump over 4% in 8h, hold 36h: 118 trades, -0.91%, 52% win, t -1.16.
Bigger OI jump is worse (over 6%: -2.40% on 58). Break with OI flat or down: +0.14% on 961.
Holds in chop / compressed / normal vol (about 0). Loses in expanded vol (-5.11% on 22) and trend (-3.97% on 26).
8h cover if price is +1% and OI still rising only moves it to -0.77%.
The fade is flat in quiet tape and a loss in a trend. Not a strategy.

## 2. Laggards and weekends — finished, not trades
Same 4h backfill.
BTC +2% in 4h, coin up 0.5% or less, long: 35 trades, +1.77% at 24h (t 0.76), +0.74% at 72h (t 0.18).
Only pocket: trend, +5.02% on 14 trades, t 0.56. Chop -2.11% on 21. Too few.
Short a coin that held up in a BTC -2% drop: -0.78% at 24h on 60. Not a trade.
Short the leader (coin already +4%): +0.30% on 134, t 0.30. Nothing.
Weekend long Sat 00:00 UTC to Mon 00:00: 672 trades, -0.73%, t -1.49. Every coin flat or red.
Only pocket: compressed vol +0.77% on 168, t 0.90. Weekend short +0.53%, t 1.08. A lean, not a rule.

## 3. Level-break chase — taken the whole way. Lead, not added to the book.
Same break, OI up more than 4% over 8h, BUY the close. Do not fade it.
Hold 24h: 118 trades, +0.73%, 50% win, t 1.20, worst -13.8%.
12h +0.45%. 36h +0.71%. 48h +0.95% but win rate 44% and worst -22%. 24h is the hold.
OI is doing the work. OI up 2% or less: -0.15% on 321. OI over 6%: +1.28% on 58, t 1.19. OI over 8%: dead (28 trades).
Break with OI flat or down: -0.10% on 962.
Where it holds: expanded vol +2.80% on 24 (t 1.65); trend +2.70% on 26 (t 1.66); trend or expanded +2.05% on 37.
Chop +0.17%. Normal vol flat. 2026 +0.93% on 95. 2025 flat (23).
Coins that carry it: BCH +3.03% (19), XLM +3.85% (9), DOGE +1.33% (11).
Coins that do not: AAVE -1.47%, AVAX -0.98%, XTZ -1.01%.
Enter at the close. Wait 1 bar: +0.39%. Wait 2 bars: +0.30%.
Path: +0.52% in the first 4h, then a grind. About half the trades are underwater at every bar.
Cut if red at 8h: +0.66% and win rate 35%. Worse than sitting the 24h.
Account, $5k, 15% slot, max 5, no second position in the same coin: 117 trades, ends $5,469, max drop -8%.
Fails the pass bar (t 1.2 not 3, n 118 not 200, gain is mostly 2026). Lead only.
Paper spec, not a book add: buy the first close through the prior-day high only when OI is up 4-8% and BTC is trending or vol is expanded. Enter that close. Hold 24h. No stop from this sample. Skip AAVE, AVAX, XTZ until they have more trades.

## 4. Extreme funding — short is finished and it loses. Low-funding long taken the whole way. Lead, not a book add.
Data: raw/coinalyze_daily/funding.csv joined to perp_ohlcv.csv. 16 coins, 2020-01-21 to 2026-10-01. Own 90-day percentile.
Short when funding is at its 90-day top (95th percentile or higher):
1 day: 1654 trades, -1.04%, t -4.50, 1 year positive.
3 days: -2.43%, t -5.65, worst -150%.
7 days: -4.94%, t -7.39.
Loses in compressed, normal, and expanded vol. Loses in chop and trend. Loses if price is already up and if price is already down.
The only green year is 2022: +3.60% on 33 trades. That is the bear year, not a rule.
Placebo (middle funding, short) also loses, but the extreme short loses more. High funding is momentum, not a top. Do not short it.

Long when funding is at its 90-day bottom (5th percentile or lower), hold 3 days:
1810 trades, +0.75%, 51% win, t 2.20, worst -32.6%, 5 of 7 years positive on the 1-day and 3-day holds.
7 days: +1.32%, t 2.61.
Path keeps rising: day 1 +0.27%, day 3 +0.86%, day 7 +1.42%. About half are underwater. Cutting if red on day 1 drops the 3-day average from +0.76% to +0.21%. Sit.
Where it holds: BTC +1.02% (t 2.34), DOT +1.83%, XTZ +2.10%, HBAR +2.48%, XLM +1.36%. Those four best coins together +1.82% on 473.
Where it does not: 2025 flat, 2026 -1.26% on 175. AAVE, AVAX, LINK, XRP flat or red.
Account, $5k, 10% slot, max 5, 3-day hold: 1058 trades, ends $7,815, max drop -27%.
Fails the pass bar (t 2.2 not 3, and the last two years do not pay). Lead only.
Paper spec: long the daily close when a coin's funding is at its own 90-day 5th percentile or lower. Hold 3 days, no day-1 stop. Prefer BTC, DOT, XTZ, HBAR. Do not size it like the crowd short. 2025-26 did not pay.

# Redo 2026-10-01 — handoff for the next session

Read this file before trusting any "dead, do not retest" line written on 2026-10-01.
This file is the record of a re-walk. Clayten will not reread it. A later model will. Write any follow-up in this folder, on `main`, in this repo only.

Do not open or edit `crypto-research-machine`. Do not open or edit `hype-pressure-kit`. Those are older repos. They are not this program.

## How to use this file

1. Read the legend. The words below are used with those meanings only.
2. Read the data section before quoting a number. Two different files were used. They are not the same sample.
3. A verdict of "not a trade" means the versions listed were run and lost. It does not mean the idea is banned. A new alteration needs a new row, not a citation of this file as a ban.
4. Do not add anything here to `book/CURRENT-BOOK-2026-10-01.md`. Nothing in this file cleared the pass bar.
5. Do not place orders. Research is paper only.

## Legend

| Word | Meaning in this file |
|---|---|
| Trade | One coin, one entry, one exit. Coins that fire on the same day are not sixteen independent bets. |
| n | Number of those trades. |
| Mean | Average trade result after a 0.10% round-trip fee. A positive number is the trade made money. |
| t | How far that average is from zero, after coins on the same day are collapsed into one day. t of 2 is a hint. t of 3 is the pass line used in this repo. A plain per-trade t would look stronger and is not used. |
| Win | Share of trades with a result above zero after the fee. |
| Lead | Sign is right, but t is under 3, or n is under 200, or a recent year fails. Not a book add. |
| Not a trade | The versions tested lost. Not a ban on a different version. |
| Book | The live paper spec in `book/CURRENT-BOOK-2026-10-01.md`: crowd short CS72 plus flush long Flush-B. This file does not change it. |
| Pass bar | Mean above 0, t at least 3, both halves of the sample positive, at least 3 of 5 years positive, n at least 200. From `batch1-2026-10-01/PREREG.md`. |
| Own percentile | The coin compared with its own trailing 90 days, not with other coins. 95th means this reading is higher than 95% of that coin's last 90 days. |
| Compressed / normal / expanded | Bitcoin's 20-bar realized volatility versus its own trailing median. Compressed is below 0.85 times that median. Expanded is above 1.30 times it. |
| Chop / trend | Bitcoin's 30-day efficiency ratio. Trend means the net move is more than 35% of the sum of absolute daily moves. Otherwise chop. |
| Fake account | A ranking tool. $5,000 start, a fixed percent of equity per trade, max 5 open, no second position in the same coin. It is not a forecast. See the last section. |
| Funding | The perp funding rate the longs pay the shorts, or the reverse. It is not in the fake-account dollars. |

## Data used

Two files. Do not mix their dates.

| Name | Path | What it is | Coins | Span |
|---|---|---|---|---|
| 4h backfill | `derived/panel/4h_backfill/` | 4-hour close and open interest. Some coins also have spot volume. ETH and SOL files are missing from this folder. | 14 | 2025-10-31 to 2026-09-30 |
| Daily archive | `raw/coinalyze_daily/` | Daily perp price, funding, open interest, long/short ratio, liquidations, spot volume. | 16: AAVE ADA AVAX BCH BTC DOGE DOT ETH HBAR LINK LTC SHIB SOL XLM XRP XTZ | Prices and liquidations from 2019-09-12. Funding from 2020-01-21. Through 2026-10-01. |

Fee on every trade in this file: 0.10% round trip, taken once. No exchange funding in the trade result unless a sentence says so.

## 1. Level-break fade — not a trade

Idea. Price breaks the prior UTC day's high and open interest jumps, so the break is a squeeze and should be shorted.

Rule tested. First 4-hour close above the prior day's high. Open interest up more than 4% over the last 8 hours. Short. Hold 36 hours. Data: 4h backfill.

Result. 118 trades, mean -0.91%, win 52%, t -1.16, worst about -33%.

What was changed. A bigger open-interest jump was worse, not better. Over 6%: -2.40% on 58 trades. A break with open interest flat or down: +0.14% on 961 trades, so the jump was the part that lost. Quiet tape was flat: compressed +0.06% on 42, normal +0.04% on 54, chop about 0 on 92. Expanded volatility -5.11% on 22. Trend -3.97% on 26. Covering at 8 hours if price was up 1% and open interest still rising only moved it to -0.77%.

Verdict. The fade is flat in quiet tape and a loss in a trend. Not a strategy on this sample. A later session may test a different break definition. It may not cite this file as proof the idea is impossible.

## 2. Laggards and weekends — not trades

Laggard. Bitcoin up 2% in 4 hours, the coin up 0.5% or less, buy the coin. 4h backfill. 35 trades. +1.77% at 24 hours, t 0.76. +0.74% at 72 hours, t 0.18. The only pocket is trend: +5.02% on 14 trades, t 0.56. Chop is -2.11% on 21. Too few to be a rule.

The reverse, shorting a coin that held up while Bitcoin dropped 2%, is -0.78% at 24 hours on 60 trades. Shorting a coin already up 4% with Bitcoin is +0.30% on 134, t 0.30. Relative strength does not snap back inside a day on this sample, and it does not pay to chase it either.

Weekend. Long from Saturday 00:00 UTC to Monday 00:00 UTC. 672 trades, -0.73%, win 42%, t -1.49. Every coin flat or red. Compressed volatility only: +0.77% on 168, t 0.90. Shorting the weekend: +0.53%, t 1.08. A lean, not a rule.

## 3. Level-break chase — lead, not a book add

This is the other side of section 1. Same break, same open-interest jump, buy it.

Rule. First 4-hour close above the prior day's high, open interest up more than 4% over 8 hours, buy that close, hold 24 hours. 4h backfill.

Result. 118 trades, +0.73%, win 50%, t 1.20, worst -13.8%.

What was changed. Hold 12 hours +0.45%. Hold 36 hours +0.71%. Hold 48 hours +0.95% but win rate 44% and worst -22%. Open interest up 2% or less loses (-0.15% on 321). Over 6% is +1.28% on 58, t 1.19. Over 8% dies (28 trades). A break with open interest flat or down loses (-0.10% on 962). Expanded volatility +2.80% on 24, t 1.65. Trend +2.70% on 26, t 1.66. Chop +0.17%. 2026 +0.93% on 95. 2025 flat on 23. BCH +3.03% on 19, XLM +3.85% on 9, DOGE +1.33% on 11. AAVE -1.47%, AVAX -0.98%, XTZ -1.01%. Waiting one bar cuts it to +0.39%. Waiting two bars cuts it to +0.30%. Cutting if red at 8 hours drops the average to +0.66% and the win rate to 35%. Sitting 24 hours is better.

Fake account, for rank only. $5,000, 15% of equity, max 5, 24-hour hold: 117 trades, ends $5,469, worst drop -8%. About +9% over 11 months on this sample.

Verdict. Lead. Fails t of 3 and n of 200. Almost all of the gain is 2026. If paper-watched: buy the first close through the prior-day high only when open interest is up 4% to 8% and Bitcoin is trending or volatility is expanded. Enter that close. Hold 24 hours. No stop from this sample. Skip AAVE, AVAX, XTZ until they have more trades. Do not add it to the book.

## 4. Extreme funding

Data. Daily archive, funding joined to perp price. 16 coins, 2020-01-21 to 2026-10-01.

Short the top. Funding at its own 90-day 95th percentile or higher, short, hold 3 days. 1654 trades, -2.43%, t -5.65, worst about -150%. 1 day -1.04%, t -4.50. 7 days -4.94%, t -7.39. Loses in compressed, normal, and expanded volatility. Loses in chop and trend. Loses if price is already up and if price is already down. The only green year is 2022: +3.60% on 33 trades. That is the bear year, not a rule. A middle-funding short also loses, but the extreme short loses more. High funding is momentum, not a top. Do not short it.

Long the bottom. Funding at its own 90-day 5th percentile or lower, long, hold 3 days. 1810 trades, +0.75%, win 51%, t 2.20, worst -32.6%. 7 days +1.32%, t 2.61. The path rises: day 1 +0.27%, day 3 +0.86%, day 7 +1.42%. About half the trades are underwater. Cutting a red day 1 drops the 3-day average from +0.76% to +0.21%. Sit. Holds on BTC +1.02% (t 2.34), DOT +1.83%, XTZ +2.10%, HBAR +2.48%. Does not hold in 2025 (flat) or 2026 (-1.26% on 175). AAVE, AVAX, LINK, XRP flat or red.

Two alterations that failed. Subtracting Bitcoin's return from this long cuts it from +0.75% to +0.15%. Doubling the stake after a loss wipes a fake account. Flat size is the version that survives.

Verdict. The short is not a trade. The long is a lead. Paper spec if watched: long the daily close when funding is at that coin's own 90-day 5th percentile or lower. Hold 3 days. No day-1 stop. Prefer BTC, DOT, XTZ, HBAR. Do not size it like the crowd short.

## 5. Alterations of rules that lost on the first wording

Same daily archive, 16 coins, 2019-09-12 to 2026-10-01. Each change was one knob: delay the entry, restrict the regime, add a second condition, or flip the side.

Short a short-liquidation spike. Short the day short-liquidations are at their own 90-day 95th percentile, hold 3 days. 2246 trades, -2.54%, t -6.51. Wait one day, then short: -2.03%, t -5.73. Short only if the next day is still up: -2.24%. Chop only: -1.14%. Compressed only: -1.80%. Funding below its 80th: -2.07%. Established coins only (BTC ETH SOL XRP ADA LINK LTC BCH DOGE): -2.07%. After a week already up 15%: -4.09%, worse. No short version flipped positive.

The other side of that spike. Buy it, hold 3 days: 2246 trades, +2.34%, t 6.00, 5 years positive. Hold 1 day +0.95%, t 3.79. Hold 7 days +4.24%, t 7.05. Expanded volatility only +3.29%, t 3.02. Spot already buying +2.42%, t 4.62. Years: 2020 +4.15, 2021 +6.24, 2022 -0.44, 2023 +1.84, 2024 +5.01, 2025 +1.44, 2026 -0.22. This is the same mechanism as the long-liquidation buy, on the other side of the tape. Not a new book.

Crowd at its high, short. Long/short ratio at its own 90-day 90th, short 3 days. 5301 trades, -0.59%, t -2.94. Price already up a week: -1.57%. Funding already extreme: -0.88%. Chop only: -0.28%. Wait a day: -0.56%. Spot not buying: -0.47%. All still red.

The one flip. Compressed volatility only: 2055 trades, +0.33%, t 1.19. Add funding below its 70th: +0.60%, t 2.00, 1187 trades. That flip is 2020 (+2.82) and 2022 (+2.30, t 3.78). 2024 is -2.38%, t -3.30. 2021, 2023, 2025 are flat. ADA +1.31, XLM +1.05. BTC and ETH flat. Lead only, and not outside a quiet bear.

Perp-led rally short. Price up 3% on the day and perp taker-buy share ahead of spot taker-buy share. Short 3 days: 164 trades, -2.35%, t -2.36. Funding already hot: -2.14% on 32. After a +15% week: -5.80% on 29. Chop only: -1.62%. Wait a day: -1.87%. No short version paid. Buying that same bar: +2.15%, t 2.16.

Spot-led rally long, left as worded. Price up 3% and spot taker-buy share ahead of perp. 969 trades, +1.34%, t 3.01. Restricting it to expanded volatility dropped it to +0.84%. Restricting it to a down week made it -0.95%. Leave the base wording. It is continuation, not a fade. Years are mixed: 2021 +3.95, 2022 -0.35, 2024 +1.11, 2025 -0.53, 2026 +1.54.

## 6. Pairs

Question asked. Do the rules that pay fire on the same day, and is the combination better than either alone?

Same coin, same day, daily archive, 3-day hold.

| Pair | n | Mean | t | What it means |
|---|---:|---:|---:|---|
| Long-liquidation spike alone | 2263 | +2.03% | 4.29 | Buy the day long liquidations are at the coin's 90-day 95th. |
| Short-liquidation spike, bought | 2246 | +2.34% | 6.00 | Buy the day short liquidations are at the 95th. |
| Crowd already low, long | 4648 | +0.87% | 3.23 | Long/short ratio at its own 90-day 10th or lower. |
| Funding already low, long | 1810 | +0.75% | 2.20 | Funding at its own 90-day 5th or lower. |
| Spot-led rally, long | 916 | +1.36% | 2.94 | Price up 3% and spot takers ahead of perp takers. |
| Long-liq spike AND crowd already low | 304 | +4.32% | 3.38 | The pair. Crowd short is the condition. Liquidation is the trigger. |
| Both liquidation sides same day | 549 | +4.36% | 3.71 | Longs and shorts both flushed. Same mechanism, not a second idea. |
| Crowd-low AND funding-low | 291 | +1.62% | 1.92 | Better than either alone. Not enough to add. |
| Spot-led AND crowd-low | 114 | +1.17% | 0.74 | Worse. Do not stack. |

Overlap. Only 13% of long-liquidation days also have the crowd already low. Only 2% of spot-led days are also long-liquidation days. Spot-led is a different day. Leave it alone.

Side by side, not the same trade. The quiet-tape crowd short (section 5) does not fire with the liquidation buy. Putting it next to the buy does not deepen the hole. Putting crowd-low next to the short-liquidation long makes a bigger fake-account ending and a deeper drop, because both are longs on the same kind of day.

## What the fake-account dollars are

A later session will see endings like $65,268 and $107,448. Those are not a forecast and not a claim about Clayten's account.

What was done. Start at $5,000. Each signal takes 10% of current equity (15% on the 4-hour chase). Hold 3 days, or 24 hours for the chase. Up to 5 positions. No second position in the same coin. Exit on the daily close. No funding charged. No intraday path.

What it is for. Rank one pairing against another on the same history. A higher ending means that pairing made more on this sample. It does not mean a live account will reach that number. The daily close skips the move inside the day. Funding on a 3-day long can eat the edge. Five open at once is more heat than the book uses.

Numbers from that rank, so they are not lost. Short-liq long alone: end $65,268, worst drop -24.7%. Add crowd-low beside it: end $107,448, drop -33.9%. Both liquidation sides: end $101,582, drop -30.7%. Long-liq buy plus quiet crowd short: end $41,749, drop -25.0%. Crowd-low alone: drop -34.1%.

Use the per-trade mean and t. Use the fake account only to see which pair dug a deeper hole.

## What a later session may do

May. Test a new alteration of a "not a trade" and write the new row here. Paper-watch a lead, labeled as a lead. Re-run these numbers from the two data paths above.

May not. Add any rule in this file to the current book. Treat a loss on one setting as a ban. Write this note into another repo. Place an order. Quote a fake-account ending as expected profit.

Still not run. ETF-flow days. No ETF series is in the daily archive. Grid cell scores as a signal. Coin-group rotation was only a weekly glance, not a full walk.

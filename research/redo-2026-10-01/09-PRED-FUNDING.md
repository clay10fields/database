# 9. Predicted funding — short is not a trade, gap is a lead

Read `REDO.md` for the legend. ETF-flow days were checked first. No ETF file is in this repo. This is the next series that is on disk.

Idea. Predicted funding is the rate the market is quoting for the next window. Extreme predicted funding should be faded. A gap between predicted and realized should also mean something.

Rule. `raw/coinalyze_daily/pred_funding.csv` joined to funding and perp price. 16 coins, 2020-10-23 to 2026-10-01. Own 90-day percentile. Hold 3 days. Fee 0.10%.

Short the predicted 95th. 1391 trades, -2.50%, t -5.56. Same result as shorting realized funding. Predicted being above realized, top 10% of the gap, short: 3437 trades, -1.11%, t -4.14. Do not short either.

Long the predicted 5th. 1728 trades, +0.75%, t 2.04. Same size as the realized-funding long in REDO.md section 4. 2022 loses. 2025 is flat. Lead, not a new idea.

The gap. Predicted funding below realized funding, bottom 10% of the gap (cut about -1.3 percentage points on the file's units). Long 3 days: 3438 trades, +1.39%, t 4.81. Years: 2021 +3.49 (t 4.49), 2022 -1.04 (t -2.13), 2023 +1.11, 2024 +0.86, 2025 -0.05, 2026 +0.71. Coins that carry it: DOGE +4.75, SOL +2.84, BCH +2.51, ADA +2.16. HBAR and SHIB are flat to red.

Verdict. Shorting predicted funding is not a trade. The long at the 5th is the same lead as section 4. The gap long clears t of 3 and n of 200, and it fails 2022 and is flat in 2025, so it does not clear the pass bar. Lead. Paper spec if watched: long the daily close when predicted funding is below realized by at least that coin's own bottom 10% gap. Hold 3 days. Do not add it to the book. Do not treat 2021 as the rule.

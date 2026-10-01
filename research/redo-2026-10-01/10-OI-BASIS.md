# 10. Daily open-interest drop and perp-spot basis

Read `REDO.md` for the legend.

Open interest. Idea: a 5% drop in open interest is a flush, so buy it. Data: `raw/coinalyze_daily/oi.csv` joined to perp price. 16 coins, 2020-01-21 to 2026-10-01. Hold 3 days. Fee 0.10%.

Long the day open interest falls 5% or more: 4970 trades, +1.07%, t 4.44. A 10% drop: 1635 trades, +1.77%, t 3.60. Shorting the same day: -1.27%, t -5.26. Do not short a flush.

Years, the 5% long. 2020 +1.39. 2021 +2.81. 2022 -0.86. 2023 +1.62. 2024 +2.10. 2025 -0.40. 2026 -1.18. It is the same mechanism as Flush-B, on daily bars. It fails the bear year and the last two years. Not a new book entry. The book already trades the 4-hour version.

Basis. Perp price minus spot price, own 90-day percentile. The spot join only lands on 2446 rows, so this is not the 16-coin panel. Long the 5th percentile: 130 trades, +2.96%, t 3.17. Short that cheap basis: -3.16%. A rich basis (95th) is 159 trades and does not pay either way. Years are 10 to 26 trades. Too thin to be a rule. Do not add it. A later session needs a real spot-price panel before retesting basis.

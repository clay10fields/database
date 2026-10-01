# 8. Grid cell score — not a separate trade

Read `REDO.md` for the legend. This is the walk that file had left open.

Idea. A regime cell has a past average. Trade the cell when that average is good, and short it when the average is bad.

Rule. Cell is Bitcoin volatility (compressed, normal, expanded) crossed with Bitcoin direction (chop, trend). Definitions are in the REDO.md legend. The score is the cell's own past 3-day forward return, expanding, lagged one day so today is not in the score. Minimum 40 prior days in the cell. Long when that past mean is above 0.5%. Short when it is below -0.2%. Fee 0.10%. Data: `raw/coinalyze_daily/perp_ohlcv.csv`, 16 coins, 2019-09-12 to 2026-10-01.

Result. Long the good cell: 16485 trades, +1.33%, t 5.67. Short the bad cell: 4698 trades, -0.08%, t -0.20. The short does not pay.

What the long actually is. Every-day long, no cell: +0.44%, t 3.19. That is the drift. The cells: compressed-chop -0.19%, normal-chop -0.21%, expanded-chop +0.70% (t 1.67). Compressed-trend +1.69% (t 2.96). Expanded-trend +2.34% (t 3.23). Normal-trend +2.72% (t 6.31). The score is selecting the trend cells. It is not a new signal on top of "Bitcoin is trending."

Years, long the good cell. 2020 +2.26. 2021 +2.06. 2022 -0.33. 2023 +1.72. 2024 +2.79. 2025 +0.34. 2026 -0.66. The bear year and the current year do not pay.

Verdict. Not a separate trade. The short side of a bad cell is flat. The long side is the trend cell, which the book already uses as a season, not as its own entry. Do not add a grid score. Do not short a cell because its past average was red.

Still not run. ETF-flow days. No ETF series is in the daily archive.

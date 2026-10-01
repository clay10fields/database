# 41. Washout rerun on the file that is here — 2026-10-01 19:34 ET

Ran on `raw/coinalyze_daily/` in this repo. Not a book add. Does not replace the 141 in `22-WASHOUT-SPEC.md`.

Symbols in `liq.csv`: the original 16 only. ZEC, NEAR, ALGO, WLD, RENDER are not in the file. No washout row for them.

Rule. Prior 90 days, today not included in the window. Long-liquidation at or above the 95th. Long/short ratio at or below the 10th. At least four coins with a liquidation spike that day. Hold 7 days. Fee 0.10%.

153 trades, +7.10%, day-collapsed t 3.12, 86 days.

Years. 2020 +9.51% on 5. 2021 −0.78% on 10. 2022 +5.14% on 18. 2023 +1.87% on 52. 2024 +25.52% on 26. 2025 +5.27% on 26. 2026 +3.49% on 16.

The 141-trade spec used a different percentile construction. This run is the same sign and the same size. It is not a new rule.

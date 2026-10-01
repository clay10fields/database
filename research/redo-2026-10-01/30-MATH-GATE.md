# 30. Math gate on the wide washout — 2026-10-01 evening ET

Read `22-WASHOUT-SPEC.md` for the spec. This file does not replace its 141. A later session may not quote the count below as the spec.

## How to use this file

May. Use the beta and the residual t as the reason the washout stays a paper watch. Re-run the script idea on `raw/coinalyze_daily/` after ZEC, NEAR, ALGO, WLD, RENDER are actually in `liq.csv`.

May not. Add this to `book/CURRENT-BOOK-2026-10-01.md`. Treat the 165 as a correction of the 141. Call the five coins filled. Write this note in another repo.

## Legend

Same words as `REDO.md`. t collapses same-day coins into one day. Beta is the slope of the trade's price return on Bitcoin's 7-day return. Residual is that return minus beta times Bitcoin, then minus the 0.10% fee. A fake account was not run.

## Data

`raw/coinalyze_daily/liq.csv`, `ls_ratio.csv`, `perp_ohlcv.csv`. Symbols present after record-daily run 36932292038 (success, 2026-10-01 22:07 UTC): the original 16 only. ZEC, NEAR, ALGO, WLD, RENDER are in `collectors/coinalyze_daily.py` and in `raw/binance_vision/fundingRate/` zips from that run. They are not in `liq.csv`. Do not call them filled.

## What was run

Rule as worded in `22-WASHOUT-SPEC.md`. Own 90-day percentile, shifted one day, at least 60 days of history. That shift is the difference from the 141. Fee 0.10%. Hold 7 days.

Result of this wording. 165 trades, mean +6.94%, win 61%, worst -29.8%, 92 days, t 3.04. Years: 2020 +9.5% on 5, 2021 -0.8% on 10, 2022 +4.4% on 20, 2023 +1.9% on 55, 2024 +25.4% on 28, 2025 +5.9% on 27, 2026 +2.0% on 20. Skip AAVE and SHIB: 146 trades, +8.12%, t 3.39, worst -24.2%.

Math gate. Beta to Bitcoin's 7-day return is 1.38. Residual mean +4.22%, residual t 1.63. About 40% of the gross return is the Bitcoin move. After that hedge the t is under 3. Hill alpha was not fit; the worst trade is -29.8%, so a Sharpe on this row understates the tail. e-process was not re-run. The toolkit's e-process has cleared only CS72 held 48 hours.

Verdict. Lead, paper watch, not a book add. The base wording is positive. The beta formula was run and the residual does not clear t of 3. n is under 200 on both wordings. The five coins the rule was never built on are still missing, so the out-of-sample coin test is not done.

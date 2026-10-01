# 26. Double check of the six hypotheses

Recomputed on `raw/coinalyze_daily/`, 16 coins, fee 0.10%, same-day coins collapsed. H4 and H5 cannot be recomputed here: the rotation test was weekly groups, and the spot join is 2,446 rows.

H1. Confirmed. Washout spec, 7-day hold: 141 trades, +7.00%, t 3.00, 2026 +4.20% on 15. Same number as `22-WASHOUT-SPEC.md`.

H2. The daily version is stronger than the 4-hour chase. Long a close above the prior 20-day high, hold 1 day: 1,893 trades, +0.69%, t 2.67, 2026 +0.66%. Add open interest up 2%: 1,144 trades, +0.85%, t 3.00, 2026 +0.08%. The short of the same break: -0.89%, t -3.44. The fade is still wrong. The long is the hypothesis. It is small per day.

H3. The short is confirmed dead: funding at the 95th, short 3 days, -2.42%, t -5.65. The plain long at the 5th is +0.75%, t 2.20, 2026 -1.26%. The week-up filter does not help. It drops the long to +0.44%, t 0.70, and 2026 stays red. The week-down version is the better of the two, +0.87%, t 2.50, and 2026 is still -1.49%. Kill the week-up version of H3. The funding long stays a lead, not a repaired rule.

H6. The loose version, predicted funding below the realized close, is weaker than the percentile gap in `09-PRED-FUNDING.md`. 12,746 trades, +0.53%, t 3.08. 2022 is -1.03% on 2,423. Adding the crowd-low filter does not repair 2022: -0.24% on 346. The kill test failed. Do not carry H6 as a repaired hypothesis. The percentile version in file 09 remains the lead, and it still fails 2022.

H4 and H5. Not re-run. Leave them as written in file 25 until the weekly panel and a real spot file are the source.

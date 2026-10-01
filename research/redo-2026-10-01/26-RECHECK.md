# 26. Recheck of the six hypotheses

Rerun on `raw/coinalyze_daily/`, 16 coins, fee 0.10%, same-day coins collapsed. This corrects `25-NEXT-HYPOTHESES.md`.

H1 holds. Wide washout, 7-day hold: 141 trades, +7.00%, t 3.00. Same number as `22-WASHOUT-SPEC.md`.

H3 short holds. Funding at its own 95th, short, 3 days: 1,659 trades, -2.42%, t -5.65. Do not short a funding spike.

H3 long is weaker than the note implied. Funding at its own 5th, long: 1,810 trades, +0.75%, t 2.20. The week-up filter, which `25` said to try, makes it worse: 465 trades, +0.44%, t 0.70. Drop that filter. The hypothesis that survives is only "do not short the spike." The long stays a lead, not a rule.

H6 direction holds, the old count does not. Predicted below realized, long: 12,746 trades, +0.53%, t 3.08. The short of predicted above realized: -0.62%, t -3.24. The earlier +1.39% on 3,438 was a tighter cut. Do not quote that count for this definition. The short is still the wrong side.

H4 does not separate. A major already up, next 7 days: 2,661 trades, +1.24%, t 5.09. A major already down, next 7 days: 2,364 trades, +0.98%, t 3.93. Both are positive. That is Bitcoin drift, not proof that leaders beat laggards. The catch-up short stays dead. The "buy only the leader" rule is not shown here.

H2 and H5 were not rerun. The break continuation was a 4-hour result, t 1.20 on 118. The spot-led long used a join of 2,446 rows. Neither is confirmed on this file.

What still stands: do not fade the break, do not short a funding spike, do not short a liquidation spike, do not trade the catch-up. The one long spec that rechecked is the wide washout.

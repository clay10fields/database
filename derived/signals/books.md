# Paper books — no orders placed

Six candidate books on the same signal stream. $5,000 start, max 5 open, short priority over long, then the SNIPER.md slot tie-break. A-D differ only in which Flush signals are admitted; E is the book the 2026-10-01 strict walk-forward picked; F is E with the Flush leg gated on a hot run instead of the volatility stand-down.

- **A_curated_nocap** (current spec: curated seven, no Flush cap): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **B_dynamic_cap2** (rule-based universe, max 2 concurrent Flush): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **C_dynamic_calm1** (rule-based, max 1 Flush in Calm else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **D_dynamic_volcap** (rule-based, max 1 Flush when BTC vol pct < 0.40 else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **E_experiments_final** (CS 48h + CS24 established + Flush stand-down (vol<0.50) + liq buy, season-sized): $5,028.29 (+0.57%), worst drawdown 0.00%, 2 admitted / 14 rejected, 2 closed, avg +2.79% win 100%
- **F_hot_gate** (book E with the Flush leg gated on a HOT run instead of the vol stand-down): $5,028.29 (+0.57%), worst drawdown 0.00%, 2 admitted / 14 rejected, 2 closed, avg +2.79% win 100%

The live record decides between them; nothing here changes a rule. A vs D settles the Flush universe (research/universe-refresh/FLUSH-VOL-CAP-2026-10-01.md); E vs F settles which Flush filter is real (research/daily-gate-2026-10-01/FLUSH-FILTER.md). F is retired if its next 30 closed flush trades trail E's over the same window.

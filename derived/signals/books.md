# Paper books — no orders placed

Five candidate books on the same signal stream. $5,000 start, max 5 open, short priority over long. A-D differ only in which Flush signals are admitted; E is the book the 2026-10-01 strict walk-forward picked (research/experiments-2026-10-01/NOTES.md).

- **A_curated_nocap** (current spec: curated seven, no Flush cap): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **B_dynamic_cap2** (rule-based universe, max 2 concurrent Flush): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **C_dynamic_calm1** (rule-based, max 1 Flush in Calm else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **D_dynamic_volcap** (rule-based, max 1 Flush when BTC vol pct < 0.40 else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **E_experiments_final** (CS 48h + CS24 established + Flush stand-down (vol<0.50) + liq buy, season-sized): $5,000.00 (+0.00%), worst drawdown 0.00%, 3 admitted / 3 rejected, 0 closed

The live record decides between them; nothing here changes a rule. See research/universe-refresh/FLUSH-VOL-CAP-2026-10-01.md for why D is the leading candidate.

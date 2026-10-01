# Paper books — no orders placed

Four candidate books on the same signal stream. $5,000 start, max 5 open, CS72 priority over Flush. They differ only in which Flush signals are admitted.

- **A_curated_nocap** (current spec: curated seven, no Flush cap): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **B_dynamic_cap2** (rule-based universe, max 2 concurrent Flush): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **C_dynamic_calm1** (rule-based, max 1 Flush in Calm else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed
- **D_dynamic_volcap** (rule-based, max 1 Flush when BTC vol pct < 0.40 else 2): $5,000.00 (+0.00%), worst drawdown 0.00%, 0 admitted / 0 rejected, 0 closed

The live record decides between them; nothing here changes a rule. See research/universe-refresh/FLUSH-VOL-CAP-2026-10-01.md for why D is the leading candidate.

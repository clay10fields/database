# 38. The three jobs, done

Spec not changed. Book not changed. Count here is 146, not the 141 in `22-WASHOUT-SPEC.md`, because the percentile is shifted one day and AAVE and SHIB are skipped. The 141 remains the paper spec.

## Exits

Time exit at 7 days: 146 trades, +8.12%, t 3.39, worst -24.2%.

A hard stop at 5%, 8%, or 12% cuts the mean to +4.9% or +6.4% and drops t under 3. A 5% or 8% target raises t to 4.57 and 5.04 and cuts the mean to +2.41% and +3.63%. The stop is the wrong exit. The time exit is the one that keeps the spec.

## Account

$5,000, 10% of equity, max 5 open, no second position in the same coin, 7-day time exit, 0.10% fee. End $10,748. The marked drawdown was -5.3%, and that number is low because the account was only marked on signal days, not every day. Not a Kraken result. Not a book add.

## Five tests

N1, regime. Stress: 117 trades, +6.28%, t 3.12. Up: 21 trades, +20.29%, t 1.67. Calm 6. Down 2. A washout day is already a wide-range day, so the calm slice has no sample. Kill. Not a filter.

N2, six-month trend. Up: 61 trades, +11.42%, t 2.81. Down: 80 trades, +5.37%, t 2.26. The down coins still pay. Kill as a drop rule. Not adopted.

N3, compressed range. One trade. A washout day is not a compressed day. Nothing to filter.

N4, leftover volume-climax days, no liquidation spike, four or more coins, crowd at the 10th, 3-day hold. 59 trades, +8.90%, t 2.81. The liquidation spike on the same hold is +2.01%, t 3.67, on 2,367. The leftover mean is higher and the t is under 3. Kill. Not a second signal.

N5, funding long at the 5th in 2022. 612 trades, -2.18%, t -2.24. The other years are +1.74%, t 5.12. The bear year is red. Kill.

Nothing in this file enters `book/CURRENT-BOOK-2026-10-01.md`. The paper spec is still the 141-trade row. The 30 closed paper trades are not in the file yet, because they have not happened.

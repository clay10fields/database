---
name: hypothesis-exhaust
description: "Exhaust one trading hypothesis before the next. Use when testing a rule, a killed idea, a book change, or a pair of signals in clay10fields/database. Not for orders, not for other repos."
type: workflow
lifecycle: active
---

# Hypothesis exhaust

One idea. Find where it holds. A loss on one setting is a row, not a ban.

Read `research/FULL-TREATMENT.md` and `research/redo-2026-10-01/REDO.md` before a new test. Do not add a result to `book/CURRENT-BOOK-2026-10-01.md` unless it clears the pass bar.

## Order

1. State the idea in one sentence and the exact rule: entry, side, hold, fee.
2. Name the file and the date span. Do not mix the 4h backfill (2025-10-31 to 2026-09-30) with the daily archive (2019-09-12 to 2026-10-01).
3. Run the base rule. Report n, mean after 0.10% round trip, win rate, day-clustered t, worst trade, years positive.
4. Change one knob at a time: dose, hold, entry delay, regime (compressed / normal / expanded, chop / trend), coin list, a second condition, the other side.
5. If the single side pays, test pairs on the same coin and day, and side by side. Report overlap. A pair that fires on the same day and deepens the drop is not diversification.
6. Stop. Write the handoff. Do not start a second idea in the same write.

## Verdicts

| Verdict | Rule |
|---|---|
| Book add | Mean > 0, t >= 3, n >= 200, both halves positive, at least 3 of 5 years positive. Still paper only. |
| Lead | Sign is right, but t < 3, or n < 200, or a recent year fails. |
| Not a trade | The versions run lost. Say which versions. Do not write "do not retest." |

Fee is 0.10% round trip unless the sentence says otherwise. t collapses same-day coins into one day. A fake account is a rank only: say the stake, the max open, and that funding was not charged.

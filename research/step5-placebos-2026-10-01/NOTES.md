# Step 5 — placebos and power (HANDOFF-2026-09-30)

step5.py; surface_CZ.csv and surface_BN.csv hold every cell (OI 0/3/4/5/6%, read 4h/8h,
hold 8–48h, exit none/4/8/12h). t is cluster-robust by entry day.

## OI-jump fade vs placebos, read8, hold 36h, +8h exit
| data | all breaks | OI falling | OI ≥4% (A_fade) | OI ≥6% |
|---|---|---|---|---|
| Coinalyze 2025-11..2026-09, 14 coins | −0.15% (n 2017) | −0.27% | +0.57%, t 1.1 (n 172) | +0.02% |
| Binance 2021-12..2026-08, 16 coins | −0.16% (n 12801) | −0.28% | −0.17%, t −1.0 (n 2058) | −0.30% |

* Coinalyze year: OI ≥4% beats the placebos by ~0.7%, but bootstrap 95% CI −0.46..+1.56%,
  and no dose-response (≥6% is worse than ≥4%). Inside regime A: +0.88% vs all-breaks −0.20%.
* Binance 5 years: OI jump does not beat a random break. 0 of 34 surface cells positive.
* Verdict: the OI-jump fade is not established. At most a regime-A, 2026-only effect. Do not trade it.

## Crowding rules pass their placebos — see crowding-2026-10-01/NOTES.md

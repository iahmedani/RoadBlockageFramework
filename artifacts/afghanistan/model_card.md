# Model card -- C2RB road-blockage model: **afghanistan**

- **Trained:** 2026-09-26
- **Data:** `data/ACLED Data_classified.csv` -- 69,655 events
- **Calibration target:** `is_road_blocked` (607 blocked, 0.87% of events)
- **Estimator:** per-`sub_event_type` Beta-Binomial empirical-Bayes shrinkage (prior_strength=50) toward the global rate

## Validation (5-fold cross-validated logistic regression)

- **AUC** = 0.732  (discrimination; 0.5 = random)
- **PR-AUC** = 0.0423  (prevalence 0.0087)
- **Brier** = 0.00846  vs no-skill baseline 0.00864  -> **PASS**

Validation cross-validates the same classifier that is then refit on all rows and persisted as `model.joblib` (the event-level model used by predict.py).

## Calibrated P0 (peak blockage propensity, highest first)

| sub_event_type | n | blocked | raw | **P0 (shrunk)** | 95% CrI |
|---|--:|--:|--:|--:|---|
| Violent demonstration | 44 | 8 | 0.1818 | **0.0897** | [0.0410, 0.1549] |
| Change to group/activity | 318 | 30 | 0.0943 | **0.0827** | [0.0568, 0.1129] |
| Non-violent transfer of territory | 130 | 14 | 0.1077 | **0.0802** | [0.0453, 0.1239] |
| Non-state actor overtakes territory | 905 | 57 | 0.0630 | **0.0601** | [0.0460, 0.0761] |
| Peaceful protest | 1454 | 89 | 0.0612 | **0.0595** | [0.0481, 0.0720] |
| Government regains territory | 507 | 25 | 0.0493 | **0.0457** | [0.0299, 0.0645] |
| Protest with intervention | 81 | 5 | 0.0617 | **0.0415** | [0.0145, 0.0816] |
| Excessive force against protesters | 43 | 3 | 0.0698 | **0.0369** | [0.0089, 0.0834] |
| Other | 753 | 23 | 0.0305 | **0.0292** | [0.0187, 0.0419] |
| Looting/property destruction | 360 | 10 | 0.0278 | **0.0255** | [0.0125, 0.0427] |
| Abduction/forced disappearance | 663 | 8 | 0.0121 | **0.0118** | [0.0053, 0.0210] |
| Mob violence | 184 | 2 | 0.0109 | **0.0104** | [0.0017, 0.0268] |
| Armed clash | 39974 | 269 | 0.0067 | **0.0067** | [0.0060, 0.0076] |
| Headquarters or base established | 17 | 0 | 0.0000 | **0.0065** | [0.0000, 0.0346] |
| Grenade | 176 | 1 | 0.0057 | **0.0064** | [0.0004, 0.0201] |
| Attack | 4623 | 26 | 0.0056 | **0.0057** | [0.0037, 0.0080] |
| Remote explosive/landmine/IED | 8545 | 28 | 0.0033 | **0.0033** | [0.0022, 0.0046] |
| Sexual violence | 83 | 0 | 0.0000 | **0.0033** | [0.0000, 0.0175] |
| Shelling/artillery/missile attack | 2540 | 5 | 0.0020 | **0.0021** | [0.0007, 0.0042] |
| Agreement | 204 | 0 | 0.0000 | **0.0017** | [0.0000, 0.0092] |
| Suicide bomb | 289 | 0 | 0.0000 | **0.0013** | [0.0000, 0.0069] |
| Arrests | 306 | 0 | 0.0000 | **0.0012** | [0.0000, 0.0065] |
| Air/drone strike | 6249 | 4 | 0.0006 | **0.0007** | [0.0002, 0.0015] |
| Disrupted weapons use | 1207 | 0 | 0.0000 | **0.0003** | [0.0000, 0.0019] |

_Fallback `default_p0` for unseen types = 0.0087._

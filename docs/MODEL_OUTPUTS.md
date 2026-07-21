# What the trained model outputs — a reference

This document answers one question: **"what predictions does the trained model actually
produce?"** All numbers below are real, taken from the current Afghanistan artifacts
(`artifacts/afghanistan/`, trained 2026-06-29; spatial scores for the 90-day window ending
2026-06-01).

## The trained model is a pair, not one file

Running `python train.py --config countries/afghanistan.yaml` is the training step. It fits
**two things** on the same ground-truth `is_road_blocked` labels (the "two models, two
questions" design):

| Trained object | Where it is saved | Question it answers |
|---|---|---|
| **Calibrated `P0` table** (parametric model) | `countries/afghanistan.yaml` + `artifacts/<country>/model_card.md` | How likely is each *event type* to block a road? |
| **Logistic-regression classifier** | `artifacts/<country>/model.joblib` | Will *this specific event* block a road? |

`score.py` and `predict.py` do **not** train anything — they apply these trained objects.
The distance kernels and radii in `params.base.yaml` are literature-seeded constants, not
learned; only the probabilities that anchor them (`P0`, the classifier weights) come from
data. The spatial rankings are therefore a hybrid: **trained `P0` × fixed physics**.

## Output 1 — Calibrated `P0` per event type

The model's core learned output: a peak blockage probability for each of the 24
`sub_event_type`s, estimated with Beta–Binomial empirical-Bayes shrinkage (see
`STATISTICAL_METHODS.md` §1). Highest and lowest, from the model card:

| Event type | n | blocked | P0 (shrunk) | Reading |
|---|--:|--:|--:|---|
| Violent demonstration | 44 | 8 | **0.0897** | ~9% chance of blocking — the highest |
| Change to group/activity | 318 | 30 | 0.0827 | territorial-control events close roads deliberately |
| Non-violent transfer of territory | 130 | 14 | 0.0802 | checkpoints, handovers |
| Peaceful protest | 1,454 | 89 | 0.0595 | sit-ins physically occupy roads |
| Armed clash | 39,974 | 269 | 0.0067 | fighting rarely closes a road outright |
| Remote explosive/landmine/IED | 8,545 | 28 | 0.0033 | *affects* roads constantly, *blocks* them almost never |
| Air/drone strike | 6,249 | 4 | **0.0007** | ~130× less likely to block than a demonstration |

Full 24-row table with raw rates and 95% credible intervals:
`artifacts/afghanistan/model_card.md`. Unseen types fall back to `default_p0 = 0.0087`
(the global rate).

**The headline pattern:** blockage is driven by *deliberate, sustained* closures (protests,
territorial control), not by explosive violence.

## Output 2 — Event-level probability (`predict.py`)

The saved classifier takes one event's attributes and returns a single calibrated
probability:

```
$ python predict.py --config countries/afghanistan.yaml \
    --sub-event-type "Peaceful protest" --geo-precision 1 --fatalities 0

event: Peaceful protest | geo_precision=1 | fatalities=0 | civilian_targeting=False
P(road blocked by this event) = 0.0649
```

The same command with `"Armed clash"` gives ≈ 0.007. Features used: event type (one-hot),
geo-precision, log-fatalities, civilian-targeting flag. Batch mode: pass `--input <csv>` to
score many events at once.

## Output 3 — Spatial road rankings (`score.py`)

For a date window, `score.py` combines **all** events (buffer → kernel decay → `P0·K(d)` →
temporal fade → noisy-OR) across the 27,991 ~1 km road segments and writes three files to
`artifacts/<country>/`:

- **`road_rankings.csv`** — one row per named road (553 roads), ranked:

  | Road | max P(blocked) | mean P | segments |
  |---|--:|--:|--:|
  | Kabul to Maydan Shahr | 0.498 | 0.321 | 38 |
  | Kabul to Surobi | 0.497 | 0.165 | 67 |
  | Kabul to Bagrami | 0.497 | 0.467 | 11 |
  | Kabul Airport Road | 0.489 | 0.469 | 5 |

- **`segment_scores.csv`** — per-segment `p_block` for every one of the 27,991 segments
  (road name, class, admin1/admin2, probability).
- **`p_block_map.png`** — the road network drawn as a heat map of blockage probability.

Two readings of the same road: **max_p** finds hot spots ("Kabul to Surobi" peaks at 0.50
but most of its 67 km is quiet, mean 0.16), while **mean_p** finds uniformly risky roads
("Kabul Airport Road": 0.47 across all 5 segments).

**Why spatial probabilities (~0.50) exceed any single P0 (~0.09):** noisy-OR accumulation.
No single event is likely to block a road, but dozens of overlapping events each contribute
a little, and `1 − ∏(1 − pᵢ)` compounds them. Caveat: overlapping ACLED events may be
duplicate reports of one incident, so noisy-OR can over-count in dense areas — the
motivation for the proposed Voronoi de-duplication (see `methodology.md` limitations).

## Diagnostics (not predictions — how much to trust them)

| File | Contents |
|---|---|
| `metrics.json` / `model_card.md` | AUC **0.732**, PR-AUC 0.0423 (≈5× the 0.0087 prevalence), Brier **0.00846** vs no-skill baseline 0.00864 → PASS |
| `calibration_curve.png` | predicted vs observed probability, cross-validated |
| `p0_calibration.png` | shrunk P0 per type with Beta posterior credible intervals |

How to read these under 0.87% class imbalance: `06_evaluation.md`.

## Interactive access

`streamlit run app.py` (or `make app`) is a front end over outputs 2 and 3: pick an event
type to see its probability ranked against every other type, or click the map to drop a
hypothetical event and watch nearby segments light up.

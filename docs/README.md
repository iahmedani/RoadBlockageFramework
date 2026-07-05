# C2RB documentation

This folder documents every stage of the Conflict → Road-Blockage (C2RB) pipeline, from raw
data to a deployed model. Read in order if you're new; jump to the stage you need otherwise.

```
 01 data ─▶ 02 labels ─▶ 03 roads ─▶ 04 config ─▶ 05 train ─▶ 06 evaluate ─▶ 07 score/predict ─▶ 08 deploy
                                                                                  │
                                                              09 troubleshooting ◀┘ (when anything breaks)
```

| Doc | Answers |
|---|---|
| [01_data_acquisition.md](01_data_acquisition.md) | Where does the ACLED data come from, what columns must it have? |
| [02_labeling_protocol.md](02_labeling_protocol.md) | How do I create the ground-truth `is_road_blocked` labels? |
| [03_road_network.md](03_road_network.md) | Where do I get a road network, and how do I segment it? |
| [04_configuration.md](04_configuration.md) | What does every parameter mean, and how do the YAML layers merge? |
| [05_training.md](05_training.md) | What does `train.py` actually produce, and how? |
| [06_evaluation.md](06_evaluation.md) | How do I read the metrics — and when should I *not* trust the model? |
| [07_scoring_and_prediction.md](07_scoring_and_prediction.md) | How do I rank roads (`score.py`) and score single events (`predict.py`)? |
| [08_deployment.md](08_deployment.md) | How do I run the interactive Streamlit app? |
| [09_troubleshooting.md](09_troubleshooting.md) | Common errors and their fixes. |

Three documents sit above the stage docs:

- **[COUNTRY_GUIDE.md](COUNTRY_GUIDE.md)** — the end-to-end walkthrough for building the model
  for a **new country**, linking into the stage docs at each step. If your goal is "make this
  work for Somalia/Mali/Myanmar", start there.
- **[methodology.md](methodology.md)** (also `.tex` / `.pdf`) — the formal write-up: formulas,
  statistical justification, validation results, and limitations.
- **[STATISTICAL_METHODS.md](STATISTICAL_METHODS.md)** — the educational companion: every
  statistical technique (empirical-Bayes shrinkage, credible vs. Wilson intervals, quadrature,
  kernels, noisy-OR, cross-validation, imbalance metrics) explained with intuition and worked
  examples from the real Afghanistan numbers.

Reference: [AcledCodebook.md](AcledCodebook.md) — ACLED's field definitions (event types,
geo-precision codes, etc.).

## The model in one paragraph

Each conflict event gets an **effective impact radius** `R_eff = √(R_phys² + R_geo²) · M_sev`
(physical reach of the event type, locational uncertainty, severity stretch), a **distance-decay
kernel** `K(d)` shaped by the event type's physics, and a **peak blockage propensity** `P0`
calibrated per `sub_event_type` on ground-truth `is_road_blocked` labels. A road segment's
blockage probability is `P0·K(d)` per event, faded by temporal decay and combined across events
with **noisy-OR**. A separate logistic-regression classifier (persisted in `model.joblib`)
answers the event-level question "will *this* event block a road?". Neither model forecasts
where future events occur — this is impact modeling of *given* events.

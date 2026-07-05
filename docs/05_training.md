# 05 — Training (calibration)

```bash
python train.py --config countries/<name>.yaml
```

"Training" here produces **two models for two questions**:

1. **The parametric `P0(sub_event_type)`** — `P(is_road_blocked | type)`, estimated with
   Beta-Binomial empirical-Bayes shrinkage and **written back into the country YAML**. This
   drives the *spatial* scorer (`score.py`: which roads are blocked) and stays the
   interpretable core of the framework.
2. **A logistic-regression classifier** — cross-validated for the metrics, then refit on all
   rows and persisted into `artifacts/<name>/model.joblib`. This answers the *event-level*
   question (`predict.py`, `app.py`: will this event block a road?).

## What happens, step by step

1. **Gatekeeper** (`check_inputs`): hard-fails with a clear message on missing required columns
   or zero positive labels; warns below 30 positives (`MIN_POSITIVES_WARN`) — calibration then
   leans heavily on the prior and should be treated as provisional.
2. **Event prep** (`c2rb.prepare_events`): parses dates, coerces fatalities to int, derives
   `civ_flag`.
3. **Labels** (`c2rb.load_labels`): yes/no → 0/1. (The parsed columns are *assigned back* onto
   the frame — never `pd.concat`, which would duplicate columns.)
4. **Calibration** (`c2rb.empirical_bayes_p0`): per-type shrunk rates. With `k_s` blocked of
   `n_s` events of type `s` and global rate `p̄`:
   `P̂0(s) = (k_s + a0)/(n_s + a0 + b0)` where `a0 = p̄·m`, `b0 = (1−p̄)·m`, `m` = prior
   strength (default 50). Intuition: the prior acts as `m` pseudo-events at the global rate —
   a type with 40 events is pulled strongly toward `p̄`; a type with 40,000 keeps its raw rate.
   Beta posterior 95% credible intervals come along for plotting.
5. **Validation** (`c2rb.validate_signal`, skip with `--no-validate`): 5-fold cross-validation
   of the classifier → AUC, PR-AUC, Brier vs. baseline, calibration-by-decile. See
   [06_evaluation.md](06_evaluation.md) for how to read these.
6. **Persistence**: rewrites the country YAML (`p0`/`default_p0`; other keys preserved — see
   [04_configuration.md](04_configuration.md)), saves `model.joblib`, `metrics.json`,
   `model_card.md`, and the two plots.

## Flags

| Flag | Effect |
|---|---|
| `--prior-strength N` | Shrinkage pseudo-count (default 50). Higher = more shrinkage toward the global rate; raise it when positives are scarce. |
| `--no-write-p0` | Compute but don't touch the country YAML (useful for experiments). |
| `--no-validate` | Skip the cross-validation (faster; you lose the metrics). |
| `--no-save-model` | Skip persisting `model.joblib`. |
| `--out DIR` | Artifact directory (default `artifacts/<config-stem>/`). |
| `--seed N` | CV fold seed. |

## Artifacts produced

| File | Contents |
|---|---|
| `artifacts/<name>/model.joblib` | The deployable bundle (`format: c2rb-model-v1`): fitted sklearn `classifier`, `p0` dict, `default_p0`, feature spec, CV `metrics`, provenance (country, date, config path). |
| `artifacts/<name>/metrics.json` | Everything machine-readable: event counts, prevalence, validation block, per-decile calibration, the full `p0` map. |
| `artifacts/<name>/model_card.md` | The human-readable summary — validation PASS/CHECK verdict and the full P0 table with credible intervals. |
| `artifacts/<name>/p0_calibration.png` | P0 by type with Beta posterior 95% credible intervals. |
| `artifacts/<name>/calibration_curve.png` | Predicted vs. observed by decile (5-fold CV). |
| `countries/<name>.yaml` (rewritten) | The calibrated `p0` / `default_p0` block. |

## Classifier spec (fixed in `c2rb/classifier.py`)

`is_road_blocked ~ OneHot(sub_event_type, geo_precision) + civ_flag + log(1+fatalities)`,
`LogisticRegression(max_iter=1000)`. One definition (`_make_classifier`) is shared by
validation, training, and prediction so they can never drift apart.

Next: [06_evaluation.md](06_evaluation.md).

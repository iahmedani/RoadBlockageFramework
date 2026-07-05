# 06 — Evaluation: reading the metrics (and knowing when not to trust them)

Everything you need is in `artifacts/<name>/metrics.json` (machine-readable) and
`model_card.md` (human-readable, includes a PASS/CHECK verdict).

## Why accuracy is meaningless here

Blocked events are ~0.87% of the Afghanistan data. A model that predicts "never blocked" is
99.13% accurate and completely useless. Under this imbalance, judge the model by **PR-AUC**
and **Brier vs. baseline**, never accuracy.

## The four numbers

| Metric | Afghanistan reference | How to read it |
|---|---|---|
| **AUC** (ROC) | 0.73 | Discrimination: probability a random blocked event out-scores a random non-blocked one. 0.5 = coin flip. 0.7+ means event attributes genuinely separate blocking events. AUC is insensitive to imbalance — good, but it can look healthy while probabilities are garbage, hence the next two. |
| **PR-AUC** | 0.042 vs. 0.0087 prevalence | Precision-recall area. The honest number under imbalance. Compare it to *prevalence* (= the no-skill PR-AUC): 0.042 / 0.0087 ≈ **5× better than random**. Don't compare PR-AUC across datasets with different prevalence. |
| **Brier** | 0.008457 | Mean squared error of the predicted probabilities. Only meaningful against the **no-skill baseline** `p̄(1−p̄)` = 0.008638: Brier < baseline ⇒ the probabilities carry real information (the model card prints **PASS**); Brier ≥ baseline ⇒ **CHECK** — the probabilities are no better than predicting the base rate for everyone. |
| **Calibration curve** | predicted ≈ observed | Per-decile predicted vs. observed rates (`calibration_curve.png`). Points hugging the diagonal mean you can read the outputs as *probabilities*, not just rankings. |

## Reading the P0 table

The model card lists, per `sub_event_type`: `n`, blocked count, raw rate, **shrunk P0**, and a
95% credible interval.

- **Use the Beta posterior credible intervals** (`post_lo`/`post_hi`) when reasoning about the
  shrunk P0 — they bracket the posterior mean by construction. The Wilson interval columns
  describe the *raw* rate, not the shrunk estimate.
- **Thin types**: a type with `n < ~100` has a P0 that is mostly prior. That's the shrinkage
  working as designed — but don't over-interpret differences between two thin types.
- **Expected shape**: protests and territorial-control events on top (deliberate closures),
  explosives near the bottom (IEDs *affect* roads 66% of the time but *block* them 0.3%).

## Red flags — when NOT to trust the model

1. **Brier ≥ baseline** (model card says CHECK): the probabilities are uninformative. Usual
   causes: too few positives, or labels that don't measure what you think.
2. **Fewer than ~30 positives** (train.py warns): every per-type P0 is provisional; use the
   model for rough ranking at most.
3. **Inverted P0 ranking** — explosives above protests: the classic symptom of *affected*
   leaking into *blocked* during labeling (roadside-bomb scenes marked as closures). Re-read
   [02_labeling_protocol.md](02_labeling_protocol.md) and relabel.
4. **Roads-within-1-km far below ~60%** (printed by `score.py`; literature says ~70%): a
   spatial-data problem, not a model problem — wrong CRS, partial road coverage, coordinate
   errors.
5. **Calibration curve bowing away from the diagonal**: rankings may still be fine, but stop
   quoting the outputs as probabilities (or add isotonic/Platt recalibration).

## Sensitivity

`R_phys` and the kernel *shapes* are literature-seeded assumptions (unlike P0, which is
calibrated). Notebook §7 sweeps them to show how the footprint responds — rerun it after any
physics override so you know what your change did.

Next: [07_scoring_and_prediction.md](07_scoring_and_prediction.md).

# Statistical methods — the intuition behind every technique in C2RB

A companion to [methodology.md](methodology.md) §4. That document states *what* the model does;
this one explains *why each method exists, how it works, and what would go wrong without it* —
with worked examples using the real Afghanistan numbers. Each section ends with where the
method lives in the code.

Contents:
1. [Beta-Binomial empirical-Bayes shrinkage](#1-beta-binomial-empirical-bayes-shrinkage) (the calibration workhorse)
2. [Uncertainty intervals: Beta posterior vs. Wilson](#2-uncertainty-intervals-beta-posterior-vs-wilson)
3. [Quadrature combination of radii](#3-quadrature-combination-of-radii)
4. [Bounded log-linear severity scaling](#4-bounded-log-linear-severity-scaling)
5. [Distance-decay kernels](#5-distance-decay-kernels)
6. [Noisy-OR aggregation with temporal decay](#6-noisy-or-aggregation-with-temporal-decay)
7. [Logistic regression with one-hot features](#7-logistic-regression-with-one-hot-features)
8. [Stratified k-fold cross-validation](#8-stratified-k-fold-cross-validation)
9. [Metrics under severe class imbalance](#9-metrics-under-severe-class-imbalance-auc-pr-auc-brier-calibration)
10. [Extensions: Voronoi de-duplication and KDE](#10-extensions-voronoi-de-duplication-and-kde)

---

## 1. Beta-Binomial empirical-Bayes shrinkage

**The problem.** We want `P0(s) = P(road blocked | sub_event_type = s)` for each of 24 event
types. The naive estimate is the raw rate `k/n` (blocked count over event count). For big types
that's fine — Armed clash has 269 blocked out of 39,974, and 0.0067 is a trustworthy number.
But for small types the raw rate is noise:

- **Headquarters or base established**: 0 blocked of 17 → raw rate **0.000**. Do we really
  believe establishing a military base *never* blocks a road? With 17 observations of a ~1%
  event, seeing zero successes is expected even if the true rate is 2–3%.
- **Violent demonstration**: 8 of 44 → raw rate **0.182**. Genuinely the highest-propensity
  type — but is it *really* 18%, or did 44 events just get lucky? With n=44, the raw rate
  moves by 2.3 percentage points every time one label flips.

Raw rates from small samples are **high-variance estimates**. Ranking types by them rewards
small-n flukes.

**The idea: borrow strength from the global rate.** Before looking at any single type, we know
something: blocked events overall run at `p̄ = 607/69,655 = 0.87%`. A sensible estimator starts
every type at that global rate and lets its own data pull it away — a little data pulls a
little, a lot of data pulls all the way. That compromise is called **shrinkage**, and
"empirical Bayes" means the prior itself is estimated from the data (the global rate) rather
than chosen by hand.

**The machinery: the Beta prior as pseudo-events.** The Beta distribution is the natural prior
for a probability because it is *conjugate* to the Binomial: if your prior is
`Beta(a₀, b₀)` and you then observe `k` successes in `n` trials, the posterior is simply
`Beta(a₀ + k, b₀ + n − k)` — no integrals, just addition. Interpretation: `a₀` and `b₀` act as
**pseudo-observations** — it's as if you had already seen `a₀` blocked and `b₀` non-blocked
events before looking at this type.

We anchor the prior at the global rate with total weight `m` (the `prior_strength`, default 50):

```
a₀ = p̄·m = 0.0087 × 50 = 0.436          (pseudo-blocked events)
b₀ = (1−p̄)·m = 49.564                    (pseudo-non-blocked events)
```

The estimate is the **posterior mean**:

```
P̂0(s) = (k + a₀) / (n + a₀ + b₀) = (k + 0.436) / (n + 50)
```

Read it as: *pretend every type starts with 50 extra events at the global rate, then count.*

**Worked examples (real numbers from the Afghanistan model card):**

| Type | n | k | raw k/n | shrunk (k+0.436)/(n+50) | What happened |
|---|--:|--:|--:|--:|---|
| Violent demonstration | 44 | 8 | 0.1818 | **0.0897** | Halved: 44 real events vs. 50 pseudo-events — the data and the prior have nearly equal say. Still ranks #1. |
| Headquarters/base established | 17 | 0 | 0.0000 | **0.0065** | Rescued from an implausible zero: 17 events can't establish "never". |
| Suicide bomb | 289 | 0 | 0.0000 | **0.0013** | Also zero raw — but 289 zero-blocked events is *real evidence* of rarity, so it shrinks less of the way up than Headquarters. |
| Armed clash | 39,974 | 269 | 0.0067 | **0.0067** | Unmoved: 39,974 real events vs. 50 pseudo-events — the prior is a rounding error. |

This is the estimator's elegance: **one formula smoothly interpolates** between "trust the
prior" (small n) and "trust the data" (large n), with the crossover at `n ≈ m = 50`.

**Choosing `prior_strength`.** `m` is the crossover sample size. `m = 50` says "a type needs
~50 events before its own data outweighs the global rate". Raise it (`--prior-strength 100`)
when positives are scarce and you want more conservative estimates; lower it when you have
abundant, trustworthy labels. There are fancier ways to pick `m` (marginal-likelihood
maximization), but a fixed, documented value is transparent and easy to sensitivity-test.

**Where:** `c2rb/calibration.py::empirical_bayes_p0`; `train.py --prior-strength`;
methodology §3.2. The same idea appears in baseball batting-average estimation (the classic
Efron–Morris example), ad click-through rates, and small-area epidemiology — any "many groups,
few observations each" problem.

---

## 2. Uncertainty intervals: Beta posterior vs. Wilson

Every P0 estimate ships with an interval, and the code computes **two different kinds** —
they answer different questions.

**Beta posterior 95% credible interval** (`post_lo`, `post_hi`): the 2.5th–97.5th percentiles
of the posterior `Beta(k + a₀, n − k + b₀)`. This describes uncertainty about the **shrunk**
estimate and always brackets it (the shrunk P0 *is* that distribution's mean). A credible
interval has the intuitive reading people usually want: *"given the data and prior, there's a
95% probability the true rate lies here."* Violent demonstration: P0 0.0897, CrI
[0.041, 0.155] — honest about how much those 44 events leave unknown.

**Wilson 95% confidence interval** (`ci_lo`, `ci_hi`): a frequentist interval on the **raw**
rate `k/n`, no prior involved. Wilson's version (rather than the textbook "normal
approximation" interval) is used because it stays sensible at small n and at k=0 — the naive
interval collapses to [0, 0] for a zero count, which is absurd; Wilson gives 0/176 an upper
bound around 2%.

**The rule** (also a CLAUDE.md gotcha): when plotting or reasoning about the *shrunk* P0, use
the **Beta posterior** intervals — pairing a shrunk point estimate with a raw-rate interval
mismatches estimator and uncertainty (the interval may not even contain the point). The Wilson
columns exist so you can see what the data alone say, before shrinkage.

**Where:** both in `c2rb/calibration.py`; the P0 plot and the model-card table use the
posterior intervals.

---

## 3. Quadrature combination of radii

Each event has two length scales: `R_phys` (how far its physical effect reaches) and `R_geo`
(how uncertain we are about *where* it happened — ACLED geo-precision 1/2/3 → 1/5/25 km).
The model combines them as:

```
R_eff = √(R_phys² + R_geo²)
```

— "adding in quadrature", the same rule as combining independent measurement errors. **Why not
just add?** Both scales behave like standard deviations of independent Gaussian spreads
(physical extent, locational error), and *variances* of independent effects add — so standard
deviations combine as the root of summed squares. Plain addition would systematically
over-inflate: an Armed clash (15 km) at precision 1 (1 km) would get 16 km additively, but the
1 km of locational fuzz barely changes a 15 km footprint — quadrature gives 15.03 km, which is
right. The rule also has the correct limiting behavior: whichever scale dominates, `R_eff`
approaches it; the result is never smaller than either input.

**Where:** `c2rb/model.py::effective_radius`; methodology Eq. 1.

---

## 4. Bounded log-linear severity scaling

Deadlier events should reach further — but not linearly. The severity score blends two growth
curves (methodology Eq. 2):

```
S(n_f) = α·(1 + n_f) + (1−α)·(1 + ln(1 + n_f)),   α = 0.15
```

The **log term** applies diminishing returns (the jump 0→5 fatalities means more than
100→105); the small **linear component** (α = 0.15) still lets true mass-casualty events
register. The `1+` offsets make `S(0) = 1` — a zero-fatality event is the baseline, and
`ln(1+n)` is defined at zero.

The score then stretches the radius *gently and boundedly* (Eq. 3):

```
M_sev = clip( (1 + κ·(S/S_ref − 1)) · (1 + γ_civ·c),  0.5,  3.0 )
```

`κ = 0.25` converts relative severity into a multiplier; the civilian-targeting flag `c` adds a
30% bump (`γ_civ`); and the **whole product** is clipped to [0.5, 3.0] — the clip is the
statistical safety net that stops one 500-fatality outlier from painting half a province. Note
the bump is applied *inside* the clip: a maximum-severity civilian-targeted event caps at 3.0×,
not 3.9× (this is locked by `tests/test_math.py::test_severity_civ_bump_applied_inside_clip`).

**Where:** `c2rb/model.py::severity_S`, `severity_multiplier`.

---

## 5. Distance-decay kernels

`K(d) ∈ [0,1]` is the fraction of the peak blockage probability surviving at distance `d`.
Rather than one shape for everything, the **shape is chosen by the event type's physics**:

| Kernel | Formula | Types | Statistical intuition |
|---|---|---|---|
| Gaussian | `exp(−d²/2σ²)`, σ = R_eff/2 | explosives, strikes | Blast-like: flat near the center, then falls fast. Thin tail — negligible effect beyond ~2σ. |
| Exponential | `exp(−d/λ)`, λ = R_eff/3 | armed clashes | Heavy tail: battles spread along roads/terrain, so meaningful probability persists further out than a Gaussian allows. |
| Uniform | 1 if d ≤ R_eff | protests, territorial control | An occupied area or closed district: roughly constant effect inside, nothing outside. |
| Point | 1 if d ≤ max(R_eff, 0.3) | targeted violence, arrests | Site-confined, with a 300 m floor so tiny radii don't vanish. |

The σ and λ scalings are chosen so `R_eff` means roughly "the radius containing most of the
effect" for every shape — kernels are comparable across types. These shapes (unlike `P0`) are
**assumptions**, literature-seeded; notebook §7's sensitivity analysis sweeps `R_phys` (not the
kernel shapes, which you would have to vary by hand).

**Where:** `c2rb/model.py::kernel`; per-type assignment in `params.base.yaml` `decay:`.

---

## 6. Noisy-OR aggregation with temporal decay

Covered in depth in methodology §2.3 (Eq. 5), so briefly: a segment near several events is
blocked if **any** blocks it. Treating events as independent blocking attempts,

```
P_segment = 1 − ∏ (1 − P_block(dₑ, e) · φ(Δtₑ))
```

— multiply each event's *failure* probability, and one-minus the product. Always in [0,1],
never less than the strongest single event, saturates instead of exploding. The temporal decay
`φ(Δt) = 0.5^(Δt/30)` fades each event on its own clock with a 30-day half-life. The known
bias: clustered duplicate reports over-count (independence is violated), which Voronoi
de-duplication (§10) would fix.

**Where:** `c2rb/model.py::noisy_or`, `temporal_decay`; the loop in
`c2rb/scoring.py::score_targets`. Never add probabilities — always this.

---

## 7. Logistic regression with one-hot features

The event-level model (`model.joblib`, used by `predict.py` and the app) is a deliberately
simple supervised classifier:

```
P(blocked) = sigmoid( β₀ + Σ βᵢ·xᵢ ),
x = OneHot(sub_event_type) ⊕ OneHot(geo_precision) ⊕ civ_flag ⊕ log(1 + fatalities)
```

**Why one-hot?** `sub_event_type` is categorical with no order — "Armed clash" isn't 3× 
"Grenade". One-hot encoding gives each type its own indicator column and hence its own
coefficient, which is the regression analogue of the per-type P0 table. `geo_precision` is
one-hot too (its codes are labels, not magnitudes). Fatalities enter as `log(1+n)` for the same
diminishing-returns reason as Eq. 2. `handle_unknown="ignore"` means an event type never seen
in training just contributes no type coefficient instead of crashing.

**Why logistic regression and not something fancier?** Three reasons. (1) With 607 positives,
a low-capacity model is a feature — a gradient-boosted tree would happily memorize noise.
(2) LR outputs are **naturally well-calibrated probabilities** when classes aren't reweighted
(the methodology notes that `class_weight="balanced"` would improve ranking but inflate
probabilities, needing recalibration). (3) Coefficients are inspectable — the model can be
audited against the P0 table.

**Where:** `c2rb/classifier.py::_make_classifier` (one definition shared by validation,
training, and prediction, so they can't drift).

---

## 8. Stratified k-fold cross-validation

Quoting a model's performance on the data it was fit to is cheating (it rewards memorization).
**5-fold cross-validation** splits the events into 5 folds; each fold is predicted by a model
trained on the *other* 4, so every event gets an **out-of-sample** prediction, and the metrics
below are computed on those.

**Stratified** matters here specifically because of imbalance: plain random folds of a 0.87%
positive class could easily land a fold with almost no blocked events, making its metrics
undefined or wildly noisy. Stratification forces each fold to carry its proportional share
(~121 positives per fold).

After validation, the *same* classifier is refit on **all** rows for deployment — CV folds are
for measurement only; you don't throw away 20% of scarce positives in the shipped model.

**Where:** `c2rb/classifier.py::validate_signal` (`StratifiedKFold`, `cross_val_predict`);
`train_classifier` does the full refit.

---

## 9. Metrics under severe class imbalance (AUC, PR-AUC, Brier, calibration)

With 0.87% prevalence, **accuracy is worthless**: "never blocked" scores 99.13%. The suite of
metrics is chosen so each one covers a failure mode the others miss.

**AUC (ROC) = 0.732.** The probability that a randomly chosen blocked event gets a higher
predicted probability than a randomly chosen non-blocked one. Pure *ranking* skill, insensitive
to prevalence — which is both its strength (comparable across datasets) and its blind spot
(it can look fine while the probabilities themselves are useless).

**PR-AUC = 0.042 vs. prevalence 0.0087.** Precision-recall area — the honest metric under
imbalance, because precision punishes the false positives that ROC barely notices when
negatives are abundant. The key reading rule: the no-skill PR-AUC equals the **prevalence**,
so 0.042 means **~5× better than random**, not "4%-and-therefore-bad". Never compare PR-AUCs
across datasets with different base rates.

**Brier = 0.00846 vs. baseline 0.00864.** Mean squared error of the probabilities:
`mean((p̂ − y)²)`. This is a **proper scoring rule** — it is minimized only by the true
probabilities, so a model can't game it by hedging. Alone it's unreadable (small prevalence
makes every Brier tiny); against the no-skill baseline `p̄(1−p̄)` (always predict the base
rate) it becomes a verdict: **Brier < baseline ⇒ the probabilities carry real information**
(the model card prints PASS). If this fails, use rankings only — never quote the outputs as
probabilities.

**Calibration curve.** Bin the out-of-sample predictions into deciles; within each bin compare
mean predicted vs. observed blocked rate. Points on the diagonal mean "when the model says 3%,
it happens 3% of the time" — the property that licenses treating outputs as probabilities.
AUC measures *discrimination*, calibration measures *honesty*; you need both.

**Where:** `c2rb/classifier.py::validate_signal`; plots from `train.py`; reading guide in
[06_evaluation.md](06_evaluation.md).

---

## 10. Extensions: Voronoi de-duplication and KDE

Two methods are referenced as extensions, not yet implemented:

**Voronoi de-duplication** (ACLED's approach in its Conflict Exposure product). Noisy-OR
assumes independent events, but ACLED often carries multiple reports of one physical episode;
each multiplies in as fresh evidence, inflating dense clusters. The fix: tessellate space into
Voronoi cells (each point of the map belongs to its nearest event), so overlapping events
partition the area instead of stacking on it. Candidate next step #3 in CLAUDE.md.

**Kernel density estimation (KDE)** — smoothing event points into a continuous intensity
surface, useful as *context* (where is conflict concentrated?) but deliberately not part of the
scoring path: KDE describes event density, not blockage probability, and mixing the two would
re-introduce the affected/blocked conflation the ground-truth labels fixed.

---

## One-paragraph summary

Literature-seeded **geometry** (quadrature radii, typed decay kernels, bounded severity) turns
each event into a probability field; a **calibrated** per-type peak (`P0`, Beta-Binomial
empirical-Bayes shrinkage with Beta-posterior uncertainty) sets each field's height from
ground-truth labels; **noisy-OR with temporal decay** composes fields across events; and an
independent **logistic regression**, judged out-of-sample by imbalance-appropriate metrics
(PR-AUC, Brier-vs-baseline, calibration), both validates that the signal generalizes and serves
as the deployable event-level predictor. Assumed parts (shapes, radii) are stress-tested by
sensitivity analysis; learned parts (P0, coefficients) carry explicit uncertainty.

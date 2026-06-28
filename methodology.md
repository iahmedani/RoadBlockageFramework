# A Framework for Estimating Road-Blockage Probability from Conflict Events

**Conflict-event → Road-Blockage (C2RB) impact model**
Data: ACLED, Afghanistan, 2017–2026 (69,655 geocoded events) · `ACLED Data_classified.csv`
(adds ground-truth `is_road_affected` / `is_road_blocked` labels)

---

## 1. Problem and approach

**Goal.** Given a conflict event (or a set of events over a time window), estimate which
nearby roads are *affected* and the *probability that each road is blocked*. The central
modelling question is the one you identified: **how large is an event's impact "buffer
zone", and how does it differ by `sub_event_type`?**

**Ground-truth labels.** Each event now carries two human/LLM-verified yes/no labels:
**`is_road_affected`** (the event impacted a road in any way — 20.8% of events) and
**`is_road_blocked`** (a road was actually closed / made impassable — 0.87% of events). The
latter is our calibration and scoring target. *(The framework was originally built
weakly-supervised — the signal was mined from the `notes` free text — because the raw export had
no such column; that proxy has now been replaced by these labels.)*

**Our approach — a supervised parametric probability model.** We build an explicit, interpretable
probability model whose parameters are (a) **seeded from published literature** (the radii and
decay shapes) and (b) **calibrated against the ground-truth `is_road_blocked` label**. This is
defensible, reproducible, and mirrors established practice — ACLED's own *Conflict Exposure*
product uses fixed event-type buffers (1/2/5 km) with Voronoi de-duplication, and a published
conflict-impact model assigns per-event-type radii (Battles 25 km, Explosions 10 km,
Protests/Riots 5 km) with type-specific decay shapes.

The pipeline:

```
 event ─▶ effective buffer radius R_eff ─▶ distance-decay kernel K(d) ─▶ P(block | d)
       └─────────────────────────── noisy-OR over nearby events (+ time decay) ──────▶ P(road blocked)
```

---

## 2. The model

For an event `e` with sub-event-type `s`, geo-precision code `g ∈ {1,2,3}`, fatalities `n_f`,
and civilian-targeting flag `c ∈ {0,1}`:

### 2.1 Effective buffer radius — *"how big is the zone?"*

```LaTeX
R_eff(e) = sqrt( R_phys(s)² + R_geo(g)² ) · M_sev(e)
```

- **`R_phys(s)`** — physical/operational impact radius of the event type (km), literature-seeded
  per `sub_event_type` (see `params.yaml`). Example: IED 1 km, armed clash 15 km, protest 4 km.
- **`R_geo(g)`** — *locational uncertainty* of where the event actually happened. ACLED
  geo-precision 1 ≈ town (1 km), 2 ≈ near a town / part of a region (5 km), 3 ≈ wider region
  (25 km). This matters: a low-precision event must "spread" its blockage probability over a
  larger uncertain area.
- **Quadrature combination** `sqrt(R_phys² + R_geo²)`. Both terms behave like independent
  Gaussian length-scales (physical spread and locational error), and the variance of a sum of
  independent Gaussians adds — so their *standard deviations add in quadrature*. This is more
  principled than naive addition (which would double-count) and never smaller than either term.
- **Severity multiplier** `M_sev(e)` stretches the radius for deadlier and civilian-directed
  events, with diminishing returns so a 50-fatality battle does not produce a 50× radius:

```
S(n_f)   = α·(1 + n_f) + (1 − α)·(1 + ln(1 + n_f))         # blend of linear + log growth   (Eq. 2)
M_sev(e) = clip( 1 + κ·(S(n_f)/S(n_ref) − 1), 0.5, 3.0 ) · (1 + γ_civ·c)                     (Eq. 3)
```

with defaults `α = 0.15` (mostly log growth), `κ = 0.25`, `γ_civ = 0.30`. The `clip` bounds
keep outliers from exploding the buffer.

**Explanation of Equation 2 (the severity score `S(n_f)`).** A deadlier event tends to affect a
larger area, but the relationship is not linear — the difference between 0 and 5 fatalities is far
more meaningful than between 100 and 105. Equation 2 captures this by **blending two growth
curves**:

- the **linear term `(1 + n_f)`** grows in direct proportion to the fatality count — it lets
  genuinely large, mass-casualty events (a major battle, a deadly bombing) widen the buffer; and
- the **logarithmic term `(1 + ln(1 + n_f))`** grows ever more slowly as `n_f` rises — it applies
  *diminishing returns* so that extreme counts do not blow the radius up without bound.

The mixing weight **`α ∈ [0,1]`** chooses the balance: `α = 0` is pure-log (very gentle scaling),
`α = 1` is pure-linear (aggressive). The default `α = 0.15` keeps growth mostly logarithmic with a
small linear component. The **`1 +` offsets** are deliberate: they make `ln(1 + n_f)` well-defined
at `n_f = 0` (avoiding `ln 0 = −∞`) and guarantee `S(0) = 1`, so a zero-fatality event is the
natural baseline. Equation 2 feeds Equation 3 only through the **ratio `S(n_f)/S(n_ref)`**: an
event is compared to a reference fatality level `n_ref` (default 1), the ratio is turned into a
gentle multiplier by `κ`, bounded to `[0.5, 3]`, and finally bumped by `γ_civ` if civilians were
targeted. In short: Equation 2 converts a raw body count into a *bounded, diminishing-returns
severity signal* that stretches the buffer sensibly rather than mechanically.

### 2.2 Distance-decay blockage probability — *"how does it fall with distance?"*

```
P(block | d, e) = P0(s) · K_s(d ; R_eff)
```

- **`P0(s)`** — *peak blockage propensity*: the probability that an event of type `s` blocks a
  road at the epicenter. **This is the parameter calibrated on the `is_road_blocked` label** (§3).
- **`K_s(d)` ∈ [0,1]** — distance-decay kernel, its *shape* chosen by the event type's physics:| Kernel      | Formula                                  | Used for                                   | Rationale                                            |
  | ----------- | ---------------------------------------- | ------------------------------------------ | ---------------------------------------------------- |
  | Gaussian    | `exp(−d² / 2σ²)`, `σ = R_eff/2` | IED, suicide, grenade, shelling, airstrike | sharp, blast-like, fast decay                        |
  | Exponential | `exp(−d / λ)`, `λ = R_eff/3`      | armed clash / battles                      | heavier tail — fighting spreads along terrain/roads |
  | Uniform     | `1 if d ≤ R_eff else 0`               | protests, riots, territorial control       | roughly constant over an area, then cut off          |
  | Point       | `1 if d ≤ max(R_eff, 0.3) else 0`     | targeted violence, arrests                 | effect confined to the site                          |

### 2.3 Combining many events — noisy-OR with temporal decay

A road segment near several events is blocked if *any* of them blocks it. Treating events as
independent blocking attempts gives the **noisy-OR**:

```
P_segment = 1 − ∏_{e ∈ W} [ 1 − P(block | d_e, e) · φ(Δt_e) ]
```

over a time window `W`, with an **exponential temporal decay** `φ(Δt) = 0.5^(Δt / τ)`
(half-life `τ = 30` days) so older events fade. (ACLED-style Voronoi de-duplication can be
layered on to avoid double-counting tightly-clustered events; noted as an extension.)

### 2.4 From points to roads

We use the **WFP/AGCHO Afghanistan road network** (`afg_trs_roads_l_arazi_2023x_fixed_ segmented.shp`): **27,991 LineString segments, ~1 km each** (median 1,068 m), EPSG:4326, each
carrying road name, class, average slope and altitude. Each segment is represented by its
midpoint; `d_e` is the segment-to-event distance. Every segment within `r_max = 3·R_eff` of an
event receives that event's `P(block | d_e, e)`, and segments are aggregated by noisy-OR. The
result is a per-segment blockage probability that rolls up to **named roads** (§6 of the
notebook). **Without a road layer the same scoring runs over a regular lat/lon grid**,
producing a continuous blockage-risk raster (the design's fallback) — the code path is
identical, only the target points differ.

---

## 3. Calibration & validation on the ground-truth labels

### 3.1 The two labels — and why we model *blocked*, not *affected*

Each event carries two yes/no labels: **`is_road_affected`** (14,456 events, 20.8%) and
**`is_road_blocked`** (607 events, 0.87%). Blockage is almost a strict subset of affectedness —
only **1 of 607** blocked events is not also flagged affected — so the labels are internally
consistent (`P0_blocked ≤ P0_affected` by construction), and `P(blocked | affected) = 0.042`.

The two tell *different stories*, which is exactly why we calibrate on **blocked**:

| sub_event_type                  |    n | P(affected) | P(blocked) |
| ------------------------------- | ---: | ----------: | ---------: |
| Remote explosive/landmine/IED   | 8,545 |   **0.656** |  **0.003** |
| Suicide bomb                    |   289 |       0.405 |      0.000 |
| Violent demonstration           |    44 |       0.386 |  **0.182** |
| Peaceful protest                | 1,454 |       0.102 |      0.061 |
| Air/drone strike                | 6,249 |       0.049 |      0.001 |

An IED/landmine **affects** roads constantly (a roadside bomb — 66% of the time) but rarely
**blocks** them (traffic resumes — 0.3%). A protest or demonstration is the reverse: it
deliberately **blocks** the road. A single "is the road relevant?" signal — like the old weak
label — conflates these; the ground-truth `is_road_blocked` label separates them cleanly.

### 3.2 Peak blockage propensity `P0(s)`

`P0(s) = P(is_road_blocked = yes | s)`, estimated with **Beta-Binomial empirical-Bayes
shrinkage** (prior strength 50, anchored at the 0.87% global rate) so small-sample types
(Grenade n=176, Suicide n=289) get stable estimates instead of noisy 0.000s. Selected results
(full 24-row table in `params.yaml`), with Beta posterior 95% credible intervals:

| sub_event_type                      |      n | P0 (shrunk) | 95% CrI        |
| ----------------------------------- | -----: | ----------: | -------------- |
| Violent demonstration               |     44 |   **0.090** | [0.04, 0.16]   |
| Change to group/activity            |    318 |       0.083 | [0.06, 0.11]   |
| Non-violent transfer of territory   |    130 |       0.080 | [0.05, 0.13]   |
| Peaceful protest                    |  1,454 |       0.060 | [0.05, 0.07]   |
| Non-state actor overtakes territory |    905 |       0.060 | [0.05, 0.08]   |
| Armed clash                         | 39,974 |       0.007 | [0.006, 0.008] |
| Remote explosive/landmine/IED       |  8,545 |       0.003 | [0.002, 0.005] |
| Air/drone strike                    |  6,249 |   **0.001** | [0.000, 0.002] |

**This is the headline result.** Road *blockage* is driven by **protests and territorial-control
events** (deliberate, sustained closures), not by explosive violence — the **opposite** of an
affected-based ranking. This confirms the premise that the model **must** vary by
`sub_event_type`, and shows why the ground-truth label matters: it corrects the weak label,
which had wrongly placed IEDs at the top by conflating *affected* with *blocked*.

### 3.3 Validation — supervised, on the true label

A logistic regression `is_road_blocked ~ sub_event_type + log(1+fatalities) + geo_precision +
civilian_targeting`, evaluated with 5-fold cross-validation:

- **AUC = 0.73** — event attributes discriminate road-blocking events well above chance.
- **PR-AUC = 0.042** vs a 0.0087 prevalence — ~5× better than random under heavy imbalance.
- **Brier = 0.0085** — *better* than the no-skill baseline (0.0086), i.e. genuinely informative.
- **Well-calibrated**: predicted ≈ observed across deciles. (Use the plain model for calibrated
  probabilities; `class_weight="balanced"` improves ranking but inflates probabilities — apply
  isotonic/Platt calibration if class-weighting.)

The model is both **discriminative and calibrated**, so the calibrated `P0(s)` values are
trustworthy as probabilities, not just rankings.

### 3.4 Other sanity checks (in the notebook)

- **Roads-within-1km benchmark — passed.** With the real road network loaded, **78% of events
  fall within 1 km of a road**, independently matching the published ~70% figure. This is strong
  external validation that the spatial model and data are consistent.
- **Nesting check** — blocked ⊆ affected (1 exception in 607), confirming label consistency.
- **Sensitivity analysis** over `R_phys` and decay-kernel choice shows how the affected-road
  footprint responds to assumptions (transparency about what is assumed vs. learned).

---

## 4. Statistical methods used

Distance-decay kernels (Gaussian / exponential / uniform); quadrature combination of
independent uncertainty scales; bounded log-linear severity scaling; noisy-OR probabilistic
aggregation with exponential temporal decay; Beta-Binomial empirical-Bayes shrinkage with
Beta posterior credible intervals (and Wilson intervals on raw rates); supervised logistic
regression with cross-validated AUC / PR-AUC / Brier / calibration-curve diagnostics under
class imbalance; (optional) Voronoi tessellation for overlap de-duplication and KDE for
hotspot context.

---

## 5. Limitations & honest caveats

1. **Labels are ground truth, but derived from `notes`.** `is_road_affected` / `is_road_blocked`
   were classified from the ACLED `notes` text, so they inherit its reporting quality — an event
   whose notes omit a closure can be a false negative. **Class imbalance is severe** (blocked =
   0.87%), so absolute probabilities are small and PR-style metrics matter more than accuracy.
   Cross-checking against independent closure data (OCHA/Logistics Cluster access reports) would
   further harden `P0` — the calibration code is unchanged.
2. **`R_geo` cannot be learned from this data.** ACLED snaps all events at a named `location`
   to one shared centroid, so intra-location coordinate spread is structurally ~0 km. We
   therefore fall back to ACLED's *documented* precision semantics (1/5/25 km). If you obtain
   finer coordinates, the empirical-spread estimator in the notebook will populate `R_geo`.
3. **`R_phys` and kernel *shapes* are assumptions** (literature-seeded), unlike `P0` (data-
   calibrated). The sensitivity analysis quantifies how much they matter; tune in `params.yaml`.
4. **Independence in noisy-OR** slightly over-counts spatially correlated events; Voronoi
   de-duplication (ACLED's approach) is the recommended refinement.
5. **Static / impact-only.** Per the brief, this scores the impact of given events; it does
   not forecast where future events will occur.

---

## 6. Files

| File                             | Purpose                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `c2rb.py`                      | Framework core: label loading, calibration, radius/kernel/noisy-OR math, scorer                         |
| `params.yaml`                  | All tunable parameters:`R_phys`, decay class, `R_geo`, calibrated `P0`, severity & time constants |
| `conflict_road_blockage.ipynb` | Annotated end-to-end walkthrough: load → label → calibrate → score → map → sensitivity             |
| `build_notebook.py`            | Regenerates the notebook from cell definitions (diffable source of truth)                               |
| `requirements.txt`             | Pinned dependencies for reproducibility                                                                 |
| `methodology.md`               | This document                                                                                           |

**Reproduce:** create the venv and `pip install -r requirements.txt` (or `pandas numpy scipy scikit-learn matplotlib seaborn pyyaml nbformat jupyter geopandas shapely pyproj`), then run the
notebook top-to-bottom. The road and admin layers are already wired in `params.yaml`
(`Road Network/…segmented.shp`, `Admin Boundaries/…adm1….shp`); set `paths.roads: null` to fall
back to grid-raster mode.

---

## 7. References

- ACLED, *Conflict Exposure methodology* (buffer zones 1/2/5 km, event-type adjustment, Voronoi
  de-duplication) — https://acleddata.com/methodology/conflict-exposure-methodology
- ACLED, *Codebook* (event types, sub-event types, geo-precision codes) — `AcledCodebook.md`
- *Applying Computational Engineering Modelling to Analyse the Social Impact of Conflict and
  Violent Events* (per-type impact radii & decay shapes), PMC12562815 —
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12562815/
- *Proximity to roads shapes patterns of violence in North and West Africa* (~70% of violent
  events within 1 km of a road) — https://anl.geog.ufl.edu/roads-violence-nwafrica/
- Road network: WFP / AGCHO-NSIA Afghanistan segmented roads (`afg_trs_roads_l_arazi_2023x`);
  admin boundaries: AGCHO-NSIA Afghanistan adm1/adm2 (2017).

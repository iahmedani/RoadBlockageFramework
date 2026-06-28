# A Framework for Estimating Road-Blockage Probability from Conflict Events

**Conflict-event → Road-Blockage (C2RB) impact model**
Data: ACLED, Afghanistan, 2017–2026 (69,655 geocoded events) · `ACLED Data_2026-06-17.csv`

---

## 1. Problem and approach

**Goal.** Given a conflict event (or a set of events over a time window), estimate which
nearby roads are *affected* and the *probability that each road is blocked*. The central
modelling question is the one you identified: **how large is an event's impact "buffer
zone", and how does it differ by `sub_event_type`?**

**The core difficulty — no ground truth.** The ACLED export has no column that says "a road
was blocked." A fully supervised classifier therefore cannot be trained directly. Two naive
alternatives are both unsatisfying:

- *Pure assumption* (pick buffer radii by hand): not defensible, not reproducible.
- *Pure ML* (train a closure classifier): impossible without labels.

**Our approach — a weakly-supervised parametric probability model.** We build an explicit,
interpretable probability model whose parameters are (a) **seeded from published literature**
and (b) **calibrated against weak labels mined from the ACLED `notes` free text**. This is
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
S(n_f)   = α·(1 + n_f) + (1 − α)·(1 + ln(1 + n_f))         # blend of linear + log growth
M_sev(e) = clip( 1 + κ·(S(n_f)/S(n_ref) − 1), 0.5, 3.0 ) · (1 + γ_civ·c)
```

with defaults `α = 0.15` (mostly log growth), `κ = 0.25`, `γ_civ = 0.30`. The `clip` bounds
keep outliers from exploding the buffer.

### 2.2 Distance-decay blockage probability — *"how does it fall with distance?"*

```
P(block | d, e) = P0(s) · K_s(d ; R_eff)
```

- **`P0(s)`** — *peak blockage propensity*: the probability that an event of type `s` blocks a
  road at the epicenter. **This is the parameter calibrated from `notes`** (§3).
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

## 3. Calibration & validation from `notes` (weak supervision)

### 3.1 Building a weak "road-disruption" label

Reading the `notes` text revealed **three distinct mechanisms** by which an event disrupts a
road. Each is captured by its own regular expression (see `c2rb.weak_label`); the label is
their union, `road_disruption = block ∨ hazard ∨ denial`:

| Mechanism          | Signal in notes                                                               | Coverage                       | Typical type     |
| ------------------ | ----------------------------------------------------------------------------- | ------------------------------ | ---------------- |
| **Blockage** | "blocked/closed the highway", "cut off the road", "under siege", "impassable" | 0.14%                          | protests, sieges |
| **Hazard**   | "roadside bomb", "IED/landmine on the road", "bridge destroyed"               | 2.36%                          | IED / landmine   |
| **Denial**   | "convoy ambushed", "set up checkpoint", "seized control of the road"          | 1.89%                          | armed clashes    |
| **Union**    | any of the above                                                              | **4.35%** (3,032 events) | —               |

Crucially the label is **derived only from text, never from `sub_event_type`** (only ~18% of
IEDs are "roadside"), so the per-type rates below are genuine signal, not a relabeling of the
type. This three-mechanism distinction is itself a finding: *road hazard* (a mined road) and
*deliberate blockage* (protesters on a highway) are different phenomena that a single "road
blocked?" keyword would have missed.

### 3.2 Peak blockage propensity `P0(s)`

`P0(s) = P(road_disruption | s)`, estimated with **Beta-Binomial empirical-Bayes shrinkage**
(prior strength 50, anchored at the 4.35% global rate) so small-sample types (Grenade n=176,
Suicide n=289) get stable estimates instead of noisy 0.000s. Selected results (full table in
`params.yaml`), with Wilson 95% CIs:

| sub_event_type                |      n |     P0 (shrunk) | 95% CI         |
| ----------------------------- | -----: | --------------: | -------------- |
| Remote explosive/landmine/IED |  8,545 | **0.181** | [0.174, 0.190] |
| Suicide bomb                  |    289 |           0.098 | [0.077, 0.148] |
| Armed clash                   | 39,974 |           0.031 | [0.029, 0.032] |
| Peaceful protest              |  1,454 |           0.019 | [0.012, 0.026] |
| Shelling/artillery/missile    |  2,540 |           0.010 | [0.007, 0.014] |
| Air/drone strike              |  6,249 | **0.002** | [0.001, 0.003] |

**This is the headline result.** Blockage propensity spans ~90× across types: IEDs and
landmines — deliberately placed *on roads* to deny movement — dominate, while air/drone
strikes (which target buildings and people) almost never produce road-disruption language.
This empirically confirms the premise that the buffer/blockage model **must** vary by
`sub_event_type`.

### 3.3 Validation — does the signal generalise?

A logistic regression `road_disruption ~ sub_event_type + log(1+fatalities) + geo_precision + civilian_targeting`, evaluated with 5-fold cross-validation:

- **AUC = 0.79** — event attributes alone discriminate road-disrupting events well above chance.
- **Brier = 0.039** — *better* than the no-skill baseline (0.042), i.e. genuinely informative.
- **Well-calibrated**: predicted ≈ observed across all deciles (e.g. top decile predicts 0.19,
  observes 0.17). (Calibration requires the plain model; `class_weight="balanced"` improves
  ranking but inflates probabilities — use isotonic/Platt calibration if class-weighting.)

The model is both **discriminative and calibrated**, so the calibrated `P0(s)` values are
trustworthy as probabilities, not just rankings.

### 3.4 Other sanity checks (in the notebook)

- **Roads-within-1km benchmark — passed.** With the real road network loaded, **78% of events
  fall within 1 km of a road**, independently matching the published ~70% figure. This is strong
  external validation that the spatial model and data are consistent.
- **Sensitivity analysis** over `R_phys` and decay-kernel choice shows how the affected-road
  footprint responds to assumptions (transparency about what is assumed vs. learned).
- **Severity & geo-precision** move the weak label in sensible directions.

---

## 4. Statistical methods used

Distance-decay kernels (Gaussian / exponential / uniform); quadrature combination of
independent uncertainty scales; bounded log-linear severity scaling; noisy-OR probabilistic
aggregation with exponential temporal decay; weak supervision via regex labelling of free
text; Beta-Binomial empirical-Bayes shrinkage with Wilson confidence intervals; logistic
regression with cross-validated AUC / Brier / calibration-curve diagnostics; (optional)
Voronoi tessellation for overlap de-duplication and KDE for hotspot context.

---

## 5. Limitations & honest caveats

1. **Weak labels are a proxy, not ground truth.** `road_disruption` measures *reported*
   road-relevant language in `notes`, not verified physical closures. Reporting bias (some
   events get richer notes) propagates into `P0`. Replace with real closure data
   (OCHA/Logistics Cluster access reports) when available — the calibration code is unchanged.
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
| `c2rb.py`                      | Framework core: weak-label regexes, calibration, radius/kernel/noisy-OR math, scorer                    |
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

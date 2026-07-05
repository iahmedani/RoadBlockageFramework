# Localizing C2RB to another country

The framework separates **universal physics** from **country-local data**, so adapting it to a
new country is mostly configuration plus one calibration run — no changes to `c2rb.py`.

```
params.base.yaml          UNIVERSAL  — R_phys, decay kernels, R_geo, severity, temporal
countries/<name>.yaml     LOCAL      — data paths, metric CRS, calibrated P0  (you create this)
```

`c2rb.load_config("countries/<name>.yaml")` merges the country file on top of the base.

## What changes vs. what stays

| Parameter | Tier | New country? |
|---|---|---|
| `R_phys` (impact radius by type) | literature-seeded | **keep** (override only with local evidence) |
| `decay` (kernel shape by type) | conflict-science | **keep** |
| `r_geo` (1/5/25 km by geo_precision) | ACLED semantics | **keep** |
| severity (`alpha`, `kappa`, `civ_bump`, …), `tau_days` | universal mechanics | **keep** |
| `paths` (CSV, roads, admin, label cols) | local | **change** |
| `crs_metric` (UTM zone) | local | **change** |
| `p0`, `default_p0` | calibrated on local labels | **recalibrate** (`train.py` writes these) |

## Prerequisites

1. **An ACLED export for the country** with the standard ACLED columns
   (`sub_event_type`, `latitude`, `longitude`, `geo_precision`, `event_date`, `fatalities`,
   `civilian_targeting`, `location`) **plus a ground-truth `is_road_blocked` label**
   (`yes`/`no`), and optionally `is_road_affected`. The label is what makes calibration
   meaningful; classify it from event notes against closure data (OCHA, Logistics Cluster,
   local reporting). Aim for at least a few dozen positive (blocked) examples.
2. **A road network shapefile** (`EPSG:4326`) with a road-name column. If its lines are long,
   cut them into ~1 km segments first:
   ```bash
   python tools/segment_roads.py --in roads_raw.shp --out roads_segmented.shp --seg-km 1.0
   ```
3. *(Optional)* an admin-boundary shapefile for nicer maps.

## Steps

**1. Create the country config.** Copy the reference and edit the `paths` + `crs_metric`:

```bash
cp countries/afghanistan.yaml countries/somalia.yaml
```

```yaml
# countries/somalia.yaml
paths:
  acled_csv: "data/somalia_classified.csv"
  label_blocked_col: "is_road_blocked"
  label_affected_col: "is_road_affected"
  roads: "data/somalia_roads_segmented.shp"
  roads_name_col: "road_name"      # whatever your shapefile calls it
  admin: "data/somalia_adm1.shp"   # optional
crs_metric: "EPSG:32638"           # a metre-based UTM zone covering the country
# (leave the p0 block as-is for now — train.py overwrites it)
```

**Picking `crs_metric`.** Use the UTM zone for the country's central longitude:
`zone = floor((lon + 180) / 6) + 1`, then `EPSG = 32600 + zone` (northern hemisphere) or
`32700 + zone` (southern). E.g. Somalia (~46°E, north) → zone 38 → `EPSG:32638`.
`tools/segment_roads.py` will auto-pick this if you omit `--metric-crs`.

**2. Train (calibrate the model).**

```bash
python train.py --config countries/somalia.yaml
```

This calibrates `P0` per `sub_event_type` (Beta-Binomial empirical-Bayes shrinkage), **writes
it back into `countries/somalia.yaml`**, and emits to `artifacts/somalia/`:

- `model.joblib` — the deployable trained model (event-level classifier + parametric P0)
- `metrics.json` — validation (AUC, PR-AUC, Brier vs. baseline) + the calibrated P0 table
- `model_card.md` — human-readable summary of the trained model
- `p0_calibration.png`, `calibration_curve.png`

`train.py` fails fast if required columns are missing or there are zero blocked labels, and
warns (but proceeds) if there are very few positives — in that case P0 leans on the prior and
should be treated as provisional.

**3. Score roads for a window.**

```bash
python score.py --config countries/somalia.yaml --as-of 2024-12-31 --window-days 90
```

Outputs to `artifacts/somalia/`:

- `road_rankings.csv` — named roads ranked by blockage risk (`--rank-by max|mean`)
- `segment_scores.csv` — every segment's `p_block`
- `p_block_map.png` — risk map (falls back to a grid heatmap if no road layer is set)

**4. (Optional) Predict per event.** For the event-level question — "will *this* event block a
road?" — use the saved classifier:

```bash
python predict.py --config countries/somalia.yaml \
    --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3
# or batch-score a CSV of events:
python predict.py --config countries/somalia.yaml --events new_events.csv --out scored.csv
```

`score.py` answers *which roads* are blocked (spatial); `predict.py` answers *will this event*
block a road (event-level). Both come from the same `train.py` run.

## Reading the results

- **Trust the model** when `Brier < no-skill baseline` and `AUC` is comfortably above 0.5 in
  `metrics.json` / `model_card.md`. Under heavy class imbalance, judge by **PR-AUC and Brier**,
  not accuracy.
- **Expect protests / territorial-control events to dominate** the P0 ranking and explosives to
  sit low — if your country inverts this, check the labels (are roadside-bomb events being
  marked *blocked* when they only *affected* the road?).
- **`R_phys` and kernel shapes are assumptions.** Re-run the notebook's sensitivity analysis
  (Section 7) or sweep them if local reach differs from the literature defaults.

See `methodology.md` for the formulas and `CLAUDE.md` for repo conventions.

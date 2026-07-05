# Building a C2RB model for another country

The framework separates **universal physics** from **country-local data**, so adapting it to a
new country is data preparation plus one calibration run — no changes to the `c2rb` package.
This guide is the end-to-end walkthrough; each step links to the stage doc with full detail.

```
params.base.yaml          UNIVERSAL  — R_phys, decay kernels, R_geo, severity, temporal
countries/<name>.yaml     LOCAL      — data paths, calibrated P0  (you create this)
```

`c2rb.load_config("countries/<name>.yaml")` merges the country file on top of the base.

## What changes vs. what stays

| Parameter | Tier | New country? |
|---|---|---|
| `R_phys` (impact radius by type) | literature-seeded | **keep** (override only with local evidence — put the override in the country file; `train.py` preserves it) |
| `decay` (kernel shape by type) | conflict-science | **keep** |
| `r_geo` (1/5/25 km by geo_precision) | ACLED semantics | **keep** |
| severity (`alpha`, `kappa`, `civ_bump`, …), `tau_days` | universal mechanics | **keep** |
| `paths` (CSV, roads, admin, label cols) | local | **change** |
| `crs_metric` (UTM-zone hint for GIS preprocessing) | local | **change** |
| `p0`, `default_p0` | calibrated on local labels | **recalibrate** (`train.py` writes these) |

## Prerequisites checklist

- [ ] ACLED export for the country, all event types, as long a window as available
- [ ] Ground-truth `is_road_blocked` labels on that export (the real work — budget time for it)
- [ ] A road network shapefile with a name column, segmented to ~1 km
- [ ] *(Optional)* admin-boundary shapefile for map context
- [ ] The repo venv set up (`python3 -m venv .venv && pip install -r requirements.txt`)

## Step 0 — Get the data ([full detail: 01](01_data_acquisition.md))

Export from ACLED (registration required; note the attribution requirements). Required columns:
`sub_event_type, latitude, longitude, geo_precision, event_date, fatalities` plus (recommended)
`civilian_targeting, location, notes`. Keep the raw export unchanged in `data/` for provenance;
your labeled copy is a second file.

## Step 1 — Label the ground truth ([full detail: 02](02_labeling_protocol.md))

Add `is_road_blocked` (`yes`/`no`) — and ideally `is_road_affected` — to each event. **This is
what makes calibration meaningful**, and it's where localizations fail, so follow the protocol:

- *Blocked* means **closed / impassable** (barricade, sit-in, checkpoint denial, destroyed
  bridge, territorial closure) — not "happened on a road". A roadside IED is *affected*, not
  *blocked*, unless the notes say the road was closed.
- Classify from the `notes` text, cross-checked against OCHA / Logistics Cluster access
  reports where you have them. When ambiguous, label **no**.
- QA before training: blocked ⊆ affected (near-zero exceptions), prevalence in the ~0.5–2%
  band, **at least a few dozen positives** (train.py warns below 30), and a second-opinion
  spot-check on 100–200 events.

## Step 2 — Prepare the road network ([full detail: 03](03_road_network.md))

Source a LineString network (HDX / OSM / national authority) with a road-name attribute, then
cut it into ~1 km segments:

```bash
python tools/segment_roads.py --in roads_raw.shp --out "data/<name>_roads_segmented.shp" --seg-km 1.0
```

Omit `--metric-crs` and the tool auto-picks the UTM zone; or compute it yourself:
`zone = floor((lon + 180)/6) + 1`, `EPSG = 32600 + zone` (north) / `32700 + zone` (south).
E.g. Somalia (~46°E, north) → zone 38 → `EPSG:32638`. Record it as `crs_metric` in the config —
it's a hint for GIS work, not read by the model.

## Step 3 — Create the country config ([full detail: 04](04_configuration.md))

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
crs_metric: "EPSG:32638"
# (leave the p0 block as-is for now — train.py overwrites it)
```

Paths are relative to the repo root; run all commands from there. If you have local evidence
for a physics override (say, clashes reach only 10 km in your context), add it as a top-level
key here — `train.py` preserves such overrides when it rewrites the file.

## Step 4 — Train ([full detail: 05](05_training.md))

```bash
python train.py --config countries/somalia.yaml
```

This calibrates `P0` per `sub_event_type` (Beta-Binomial empirical-Bayes shrinkage), **writes it
back into `countries/somalia.yaml`**, and emits to `artifacts/somalia/`:

- `model.joblib` — the deployable trained model (event-level classifier + parametric P0)
- `metrics.json` / `model_card.md` — validation (AUC, PR-AUC, Brier vs. baseline) + the P0 table
- `p0_calibration.png`, `calibration_curve.png`

It fails fast on missing columns or zero positives, and warns (but proceeds) below 30 positives —
in that case P0 leans on the prior and is provisional.

## Step 5 — Evaluate before you trust it ([full detail: 06](06_evaluation.md))

Open `artifacts/somalia/model_card.md` and check, in order:

1. **Brier < baseline** (the card prints PASS/CHECK) — if CHECK, stop and fix labels/data.
2. **PR-AUC vs. prevalence** — you want a healthy multiple of the base rate (Afghanistan: ~5×).
3. **P0 ranking shape** — protests/territorial control on top, explosives near the bottom.
   An inverted ranking almost always means *affected* leaked into *blocked* during labeling.
4. **Roads-within-1-km** (printed by score.py in the next step) — expect ~70%.

## Step 6 — Score and predict ([full detail: 07](07_scoring_and_prediction.md))

```bash
# WHICH roads are likely blocked (spatial):
python score.py --config countries/somalia.yaml --as-of 2024-12-31 --window-days 90
# → road_rankings.csv, segment_scores.csv, p_block_map.png in artifacts/somalia/

# Will THIS event block a road (event-level):
python predict.py --config countries/somalia.yaml \
    --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3
# or batch:
python predict.py --config countries/somalia.yaml --events new_events.csv --out scored.csv
```

Both come from the same `train.py` run: `score.py` uses the parametric P0 spatially;
`predict.py` uses the persisted classifier per event.

## Step 7 — Deploy the app ([full detail: 08](08_deployment.md))

```bash
streamlit run app.py
```

The app auto-discovers every country with a trained `model.joblib` — your new country appears
in the selector as soon as Step 4 has run. Tab 1 predicts single events interactively; Tab 2
lets you click the map and watch nearby roads recolor by risk.

## When something breaks

[09_troubleshooting.md](09_troubleshooting.md) maps the common failure messages (missing
columns, zero positives, model-not-found, CRS problems, grid-mode fallbacks) to fixes.

## Reading the results

- **Trust the model** when `Brier < no-skill baseline` and AUC is comfortably above 0.5 in
  `metrics.json` / `model_card.md`. Under heavy class imbalance, judge by **PR-AUC and Brier**,
  not accuracy.
- **Expect protests / territorial-control events to dominate** the P0 ranking and explosives to
  sit low — if your country inverts this, check the labels (are roadside-bomb events being
  marked *blocked* when they only *affected* the road?).
- **`R_phys` and kernel shapes are assumptions.** Re-run the notebook's sensitivity analysis
  (Section 7) or sweep them if local reach differs from the literature defaults.

See [methodology.md](methodology.md) for the formulas and `CLAUDE.md` for repo conventions.

# Road Blockage Framework (C2RB)

Estimating the **probability that roads are blocked** by armed-conflict events, from
[ACLED](https://acleddata.com) data for Afghanistan (2017–2026, 69,655 events).

Given conflict events, the model assigns each ~1 km road segment a blockage probability by
combining a per-event **impact buffer** (whose size varies by event type, location precision,
and severity), a **distance-decay** of probability away from the event, and a **noisy-OR**
aggregation of all nearby events over a time window. It is an *impact* model — it scores given
events; it does not forecast future ones.

## Headline result

Road **blockage** is driven by **protests and territorial-control events** (deliberate, sustained
closures), not by explosive violence. IEDs *affect* roads constantly (66%) but rarely *block*
them (0.3% — a roadside bomb, then traffic resumes). The model is calibrated on ground-truth
`is_road_blocked` labels and validated at **AUC 0.73 / Brier 0.0085** (better than baseline), with
**78% of events within 1 km of a road** (matching the published ~70% benchmark).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Pipeline (CLI)

Two scripts run the whole process headless, against a per-country config:

```bash
# 1) TRAIN — calibrate per-type blockage propensity P0 on the ground-truth labels.
#    Writes P0 back into the country config and emits artifacts/<country>/.
python train.py --config countries/afghanistan.yaml

# 2) SCORE — rank the roads most likely blocked in a date window (spatial).
#    Writes road_rankings.csv + p_block_map.png to artifacts/<country>/.
python score.py --config countries/afghanistan.yaml --as-of 2026-06-01 --window-days 90

# 3) PREDICT — given a single event's attributes, P(this event blocks a road).
#    Uses the saved artifacts/<country>/model.joblib from step 1.
python predict.py --config countries/afghanistan.yaml \
    --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3
```

**Two prediction questions, two tools:** `score.py` answers *which roads* are blocked (spatial,
parametric) for a window of events; `predict.py` answers *will this event* block a road
(event-level, a saved classifier). `train.py` produces both.

### Interactive app

```bash
streamlit run app.py     # opens http://localhost:8501
```

A point-and-click test bench: pick an event type to see its blockage probability ranked against
every other type, or **click anywhere on the map** to drop a hypothetical event and watch the
nearby road network light up by risk. Auto-discovers any country that has a trained model.

**Localize to another country** by copying `countries/afghanistan.yaml`, pointing it at that
country's ACLED export + road network, and running the same two commands — see
**[`LOCALIZATION.md`](LOCALIZATION.md)**. Universal physics (`R_phys`, decay kernels, `R_geo`,
severity) lives in `params.base.yaml` and is shared by every country.

### Notebook (narrated walkthrough)

```bash
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 conflict_road_blockage.ipynb
# ...or open it interactively:
jupyter notebook conflict_road_blockage.ipynb
```

## What's here

| File | Purpose |
|---|---|
| `methodology.pdf` / `.md` / `.tex` | **Start here** — the full method, formulas, results, limitations |
| `LOCALIZATION.md` | How to build a model for another country |
| `app.py` | Interactive Streamlit app — click-to-test event predictions + a live road-risk map |
| `train.py` / `score.py` / `predict.py` | CLI pipeline — train the model / road rankings + maps (spatial) / event-level P(blocked) |
| `artifacts/<name>/model.joblib` | Deployable trained model (event-level classifier + parametric P0) |
| `c2rb.py` | Reusable framework core (import this) |
| `params.base.yaml` | Universal parameters (`R_phys`, decay, `R_geo`, severity) — shared by all countries |
| `countries/<name>.yaml` | Per-country config: data paths, metric CRS, calibrated `P0` |
| `artifacts/<name>/` | Generated outputs: `metrics.json`, `model_card.md`, rankings, plots |
| `tools/segment_roads.py` | Utility — cut a raw road network into ~1 km segments |
| `conflict_road_blockage.ipynb` | Annotated end-to-end walkthrough (load → calibrate → score → map) |
| `build_notebook.py` | Regenerates the notebook (the notebook is generated, not hand-edited) |
| `ACLED Data_classified.csv` | Dataset with ground-truth `is_road_affected` / `is_road_blocked` |
| `Road Network/`, `Admin Boundaries/` | Road segments + province polygons (GIS layers) |
| `CLAUDE.md` | Working notes & conventions for continued development |

## How it works (one screen)

```
event ─▶ R_eff = √(R_phys² + R_geo²)·severity   ─▶  K(d) decay  ─▶  P0·K(d)  ─▶  noisy-OR  ─▶  P(blocked)
```

- **R_phys** — physical impact radius per `sub_event_type` (literature-seeded).
- **R_geo** — locational uncertainty from ACLED `geo_precision` (1/5/25 km).
- **severity** — bounded, diminishing-returns scaler in fatalities (see Eq. 2 in the methodology).
- **P0** — peak blockage probability per `sub_event_type`, **calibrated on the labels**.
- **K(d)** — Gaussian / exponential / uniform / point, chosen per event type.

## Requirements

Python 3.14, packages in `requirements.txt`. The PDF is built with
[Tectonic](https://tectonic-typesetting.github.io/) (`tectonic methodology.tex`).

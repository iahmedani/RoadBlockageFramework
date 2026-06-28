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

# run the full analysis end-to-end (writes outputs back into the notebook)
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 conflict_road_blockage.ipynb
# ...or open it interactively:
jupyter notebook conflict_road_blockage.ipynb
```

Tune the model by editing `params.yaml` (no code changes needed).

## What's here

| File | Purpose |
|---|---|
| `methodology.pdf` / `.md` / `.tex` | **Start here** — the full method, formulas, results, limitations |
| `conflict_road_blockage.ipynb` | Annotated end-to-end walkthrough (load → calibrate → score → map) |
| `c2rb.py` | Reusable framework core (import this) |
| `params.yaml` | All tunable parameters + calibrated per-type probabilities |
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

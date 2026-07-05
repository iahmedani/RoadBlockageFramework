# CLAUDE.md — Conflict → Road-Blockage Framework (C2RB)

Guidance for working in this repo. Read this first.

## What this project is

A **supervised, parametric probability model** that turns ACLED conflict events (Afghanistan,
2017–2026, 69,655 events) into **per-road-segment road-blockage probabilities**. Impact modeling
only — it scores the impact of *given* events; it does **not** forecast where future events occur.

Pipeline:

```
event ─▶ effective buffer radius  R_eff = √(R_phys² + R_geo²)·M_sev
      ─▶ distance-decay kernel    K(d)            (shape per sub_event_type)
      ─▶ P(block | d)             = P0(sub_event_type) · K(d)
      ─▶ noisy-OR over nearby events (+ temporal decay)  ─▶  P(road blocked)
```

`P0` is **calibrated on the ground-truth `is_road_blocked` label**; `R_phys` and kernel shapes
are literature-seeded; `R_geo` follows ACLED's documented geo-precision semantics.

## Repository map

| Path | Role |
|---|---|
| `c2rb/` | **Framework core package** — import `c2rb`; the full public API is re-exported from `__init__.py`. Submodules: `geometry` (projection, haversine), `calibration` (`load_labels`, `wilson_ci`, `empirical_bayes_p0`), `config` (kernel constants, `C2RBConfig`, `config_from_yaml`, `load_config`), `model` (severity, `effective_radius`, `kernel`, `temporal_decay`, `noisy_or`), `scoring` (`score_targets`), `classifier` (`prepare_events`, `validate_signal`, `train_classifier`, `predict_blockage`). Don't reinvent; don't import submodules directly outside the package. |
| `train.py` / `score.py` / `predict.py` | **CLI pipeline.** `train.py` calibrates `P0` + validates + saves `model.joblib`; `score.py` ranks roads for a window (spatial); `predict.py` gives event-level P(blocked) from `model.joblib`. All take `--config countries/<name>.yaml`. |
| `app.py` | **Streamlit app** (`streamlit run app.py`). Tab 1: event-type → P(blocked) + ranked comparison (uses `model.joblib`). Tab 2: click-to-place event on a folium map → spatial road scoring (`score_targets`). Auto-discovers countries with a trained model. |
| `params.base.yaml` | **Universal parameters** — per-type `R_phys`, decay class, `R_geo`, severity & temporal constants. Shared by every country; no paths or `P0`. |
| `countries/<name>.yaml` | **Per-country config** — CSV/label/road paths, calibrated `P0`/`default_p0` (**written by `train.py`**), optional `crs_metric` hint. Non-templated top-level keys (physics overrides like `r_phys`, `tau_days`) are **preserved** by the rewriter. Merged onto the base by `c2rb.load_config`. |
| `docs/` | **All documentation.** `README.md` (index) → stage docs `01_data_acquisition` … `09_troubleshooting`, `COUNTRY_GUIDE.md` (end-to-end new-country walkthrough), `methodology.md`/`.tex`/`.pdf` (the write-up; `.md` and `.tex` maintained in parallel, `.pdf` compiled from `.tex`), `AcledCodebook.md`. |
| `data/` | ACLED CSVs and GIS layers. `ACLED Data_classified.csv` = **active dataset** (ground-truth `is_road_affected`/`is_road_blocked`); `ACLED Data_2026-06-17.csv` = original unlabeled export (provenance); `Road Network/…segmented.shp` = 27,991 ~1 km segments (EPSG:4326); `Admin Boundaries/…adm1/adm2…shp`. |
| `tools/segment_roads.py` | Utility — cut a raw road network into ~1 km segments. |
| `artifacts/<name>/` | Generated: `model.joblib` (deployable model), `metrics.json`, `model_card.md`, calibration plots, road rankings. |
| `tests/` | Pytest smoke suite: core math (noisy-OR, kernels, radius, shrinkage, severity clip), config merge + YAML-rewriter round-trip, label parsing, import surface. `make test`. |
| `Makefile` | `make help` — targets for train/score/predict/notebook/pdf/test/app. Enforces repo-root CWD. |
| `build_notebook.py` | **Source of truth for the notebook.** Cells defined via `md()`/`code()` helpers. |
| `conflict_road_blockage.ipynb` | **Generated** by `build_notebook.py` — do not hand-edit. |
| `requirements.txt` | Pinned deps. |

## Environment & commands

Always work inside the venv.

```bash
source .venv/bin/activate                      # Python 3.14 venv
# (first-time setup: python3 -m venv .venv && pip install -r requirements.txt)

make test                                       # pytest smoke suite
python train.py --config countries/afghanistan.yaml             # calibrate P0 + validate + artifacts
python score.py --config countries/afghanistan.yaml \
    --as-of 2026-06-01 --window-days 90                         # rank roads + map for a window (spatial)
python predict.py --config countries/afghanistan.yaml \
    --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3   # event-level P(blocked)

make notebook                                   # regenerate .ipynb from build_notebook.py AND execute it
# (equivalently: python build_notebook.py && jupyter nbconvert --to notebook --execute \
#     --inplace --ExecutePreprocessor.timeout=900 conflict_road_blockage.ipynb)

make pdf                                        # recompile docs/methodology.pdf
# (equivalently: cd docs && export PATH="/opt/homebrew/bin:$PATH" && tectonic methodology.tex)
```

## Conventions (important)

- **Never edit `conflict_road_blockage.ipynb` directly** — edit `build_notebook.py` and
  regenerate, then re-execute. Otherwise changes are lost on the next build.
- **Layered config.** Universal physics is in `params.base.yaml`; country-local settings (paths,
  calibrated `P0`, overrides) are in `countries/<name>.yaml`. `c2rb.load_config(country, base)`
  deep-merges them. The notebook and all CLI scripts load via `load_config`, never a single flat file.
- **Keep things in sync** when results change: the country config's `P0` (regenerated by
  `train.py`), `docs/methodology.md` AND `docs/methodology.tex` (prose/tables), then recompile
  the PDF (`make pdf`). The `.md` and `.tex` carry the same content in two formats.
- **`P0` lives in `countries/<name>.yaml`**, not in code, and is **written by `train.py`** (which
  calls `c2rb.empirical_bayes_p0` on `is_road_blocked`). Don't hand-edit it; rerun `train.py`.
  Validation (`c2rb.validate_signal`) is shared by `train.py` and the notebook — edit it in one place.
- **`import c2rb` is the contract.** The package `__init__.py` re-exports the public API; scripts
  and the notebook use `c2rb.X`, never `c2rb.model.X`. If you add a public function to a
  submodule, re-export it in `__init__.py` (+ `__all__`) and cover it in `tests/test_cli_imports.py`.
- All probabilities are in `[0,1]`; combine multiple events with `c2rb.noisy_or`, never by adding.
- All paths (configs, data, artifacts) are **CWD-relative to the repo root** — run commands from
  there (the Makefile does).

## Design decisions (locked unless the user changes them)

- **Blocked-only output.** `is_road_affected` is a consistency check, not a second output.
- **Two models, two questions** (changed 2026-06-29): the **parametric `P0`** drives the *spatial*
  scorer (`score.py`: which roads are blocked) and stays the interpretable core; a **persisted
  `LogisticRegression`** (`model.joblib`, via `c2rb.train_classifier`) answers the *event-level*
  question (`predict.py`: will this event block a road?). The classifier is now a sanctioned
  output, not validation-only. Both are built in `train.py`; `validate_signal` cross-validates the
  same classifier for metrics.
- **Weak labels removed** — no notes-regex code remains.
- **No forecasting** — both models score the impact of *given* events; neither predicts where
  future events occur.
- **Eq. 3 semantics**: the civilian-targeting bump is applied **inside** the `[0.5, 3.0]` severity
  clip (`severity_multiplier` in `c2rb/model.py`); the methodology states the same (fixed 2026-07-05).

## Gotchas

- The classified CSV **already has** `is_road_affected`/`is_road_blocked`; `load_labels` returns
  int columns with the same names. **Assign** them back (`df[col] = labels[col].values`) — don't
  `pd.concat`, which makes duplicate columns and breaks `df["is_road_blocked"]`.
- **`R_geo` is not learnable here**: ACLED snaps same-`location` events to one centroid, so
  coordinate spread is ~0. Use the documented 1/5/25 km values.
- **Class imbalance is severe** (blocked = 0.87%). Judge models by PR-AUC and Brier-vs-baseline,
  not accuracy. Use Beta posterior credible intervals (in `empirical_bayes_p0`), not Wilson on the
  raw rate, when plotting uncertainty on the *shrunk* P0.
- **affected ≠ blocked**: IEDs *affect* roads (0.66) but rarely *block* them (0.003); protests
  *block* them. Calibrate on the label that matches the question.
- **`crs_metric` is a hint, not a model input** — it documents the metric CRS for
  `tools/segment_roads.py --metric-crs`; training/scoring use a local equirectangular frame.
- **The country-YAML rewriter preserves unknown top-level keys** (physics overrides) but **not
  comments** — the file is regenerated from a template on every `train.py` run.

## Current state & open work

Done: supervised migration complete; country-localizable CLI pipeline (layered config, train/
score/predict) + Streamlit app; **2026-07-05 review pass**: 7 code defects fixed (YAML rewriter
preserved-overrides, input-check ordering, stale two-model docstrings, notebook Wilson→Beta
prose, guards/annotations), 5 methodology errors fixed (Eq. 3 civ-bump-inside-clip, three-scripts,
two-model wording, shrinkage equation added to the .md, filename typo); repo restructured
(`c2rb/` package with re-exported API, `data/` for datasets, `docs/` with stage docs 01–09 +
`COUNTRY_GUIDE.md`); Makefile + pytest smoke suite added. Notebook executes with 0 errors
(AUC 0.73, Brier 0.0085 < baseline); PDF compiles from `docs/`. The Afghanistan retrain
reproduces the original `P0` exactly (sanity-checked).

Candidate next steps (not yet done):
1. Optional parallel **`P(road affected)`** surface (calibration code already handles any label).
2. Cross-check `P0` against **independent closure data** (OCHA / Logistics Cluster) to harden it.
3. **Voronoi de-duplication** for overlapping events (ACLED-style) to reduce noisy-OR over-count.
4. Per-event severity features beyond type (use road `CLASSES`, `Avg_Slope`, `Avg_Alt`).

See `docs/methodology.md` for the full formulas, justification, and limitations.

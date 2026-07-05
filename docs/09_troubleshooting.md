# 09 — Troubleshooting

Symptoms → causes → fixes, roughly in pipeline order. All commands assume the repo root and an
activated venv (`source .venv/bin/activate`).

## Training

**`ERROR: input CSV is missing required column(s): [...]`**
The gatekeeper (`check_inputs`) — your export lacks one of `sub_event_type, geo_precision,
latitude, longitude, event_date, fatalities` or the blocked-label column. Fix the export
(see [01_data_acquisition.md](01_data_acquisition.md)) or point `paths.label_blocked_col`
at your actual label header.

**`ERROR: no positive 'is_road_blocked' labels found`**
Every label parsed as "no". Two usual causes: the column holds values other than yes/no
(e.g. `TRUE`/`1` — anything that isn't literally "yes", case-insensitive, parses as no), or you
pointed at the raw unlabeled export instead of the classified CSV.

**`WARNING: only N blocked events (< 30)`**
Not fatal, but every per-type P0 leans on the prior. Label more positives before trusting the
calibration ([02_labeling_protocol.md](02_labeling_protocol.md)).

**`KeyError: 'is_road_blocked'` deep in pandas** (rather than a friendly message)
Classic cause: label columns were attached with `pd.concat`, creating duplicate column names.
Assign them back instead: `df[col] = labels[col].values`. The shipped scripts do this
correctly — this bites custom notebooks.

## Spatial scoring

**`--mode road but roads file not found`** / silently falls back to grid mode
`paths.roads` doesn't exist relative to the **repo root**. Check the path in the country YAML
(data now lives under `data/`); remember you must run commands from the repo root.

**Events-within-1-km far below ~60%** (score.py prints it)
Wrong CRS on the road layer (must be reprojectable — check `roads.crs`), a network covering only
part of the country, or lat/lon swapped in the CSV. Plot both layers together to see the
mismatch immediately.

**`Input has no CRS` from segment_roads.py**
The source shapefile lacks a `.prj`. Set one first: `gdf.set_crs(4326).to_file(...)` (only if
you *know* the coordinates are lon/lat).

**`No events in the window`**
`--as-of` minus `--window-days` misses your data's date range. Omit `--as-of` to default to the
latest event date.

## Prediction / app

**`ERROR: model not found: artifacts/<name>/model.joblib`**
Train first: `python train.py --config countries/<name>.yaml`. The app only lists countries
that have this file.

**App shows no countries**
Same cause — no `model.joblib` — or you launched Streamlit from a different working directory.
`streamlit run app.py` from the repo root.

## Build / environment

**`ModuleNotFoundError: c2rb`** (or stale behavior after pulling the restructure)
Run from the repo root so `c2rb/` is importable, and clear compiled leftovers from the old
single-file layout: `find . -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +`.

**Notebook execution times out**
`jupyter nbconvert ... --ExecutePreprocessor.timeout=900` — raise the timeout; the spatial
cells score 28k segments and are the slow ones. Never hand-edit the `.ipynb`; edit
`build_notebook.py` and regenerate (`make notebook`).

**`tectonic: command not found`**
Tectonic is installed via Homebrew outside the default PATH here:
`export PATH="/opt/homebrew/bin:$PATH"` first, or use `make pdf`.

**Shapefile loads fail with fiona/pyogrio errors**
Ensure the full sidecar set moved together (`.shp` + `.shx` + `.dbf` + `.prj`); a lone `.shp`
is unreadable.

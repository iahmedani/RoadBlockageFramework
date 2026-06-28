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
| `c2rb.py` | **Framework core** — geometry, `load_labels`, `empirical_bayes_p0`, `C2RBConfig`, kernels, `effective_radius`, `score_targets`. Import this; don't reinvent. |
| `params.yaml` | **All tunable parameters** — CSV/label/road paths, per-type `R_phys`, decay class, `R_geo`, calibrated `P0`, severity & temporal constants. |
| `build_notebook.py` | **Source of truth for the notebook.** Cells defined via `md()`/`code()` helpers. |
| `conflict_road_blockage.ipynb` | **Generated** by `build_notebook.py` — do not hand-edit. |
| `methodology.md` / `.tex` / `.pdf` | The write-up. `.md` and `.tex` are maintained in parallel; `.pdf` is compiled from `.tex`. |
| `requirements.txt` | Pinned deps. |
| `ACLED Data_classified.csv` | **Active dataset** — ACLED + ground-truth `is_road_affected` / `is_road_blocked`. |
| `ACLED Data_2026-06-17.csv` | Original unlabeled export (superseded; kept for provenance). |
| `Road Network/…segmented.shp` | 27,991 ~1 km road segments (EPSG:4326). |
| `Admin Boundaries/…adm1/adm2…shp` | Province/district polygons (for maps). |
| `AcledCodebook.md` | ACLED field definitions. |

## Environment & commands

Always work inside the venv.

```bash
source .venv/bin/activate                      # Python 3.14 venv
# (first-time setup: python3 -m venv .venv && pip install -r requirements.txt)

python build_notebook.py                        # regenerate the .ipynb from build_notebook.py
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 conflict_road_blockage.ipynb   # run end-to-end

export PATH="/opt/homebrew/bin:$PATH" && tectonic methodology.tex    # recompile the PDF
```

## Conventions (important)

- **Never edit `conflict_road_blockage.ipynb` directly** — edit `build_notebook.py` and
  regenerate, then re-execute. Otherwise changes are lost on the next build.
- **Keep three things in sync** when results change: `params.yaml` (numbers), `methodology.md`
  AND `methodology.tex` (prose/tables), then recompile `methodology.pdf`. The `.md` and `.tex`
  carry the same content in two formats.
- **`P0` lives in `params.yaml`**, not in code. To recalibrate, re-run notebook Sections 2–3
  (`c2rb.empirical_bayes_p0` on `is_road_blocked`) and paste the shrunk values back.
- All probabilities are in `[0,1]`; combine multiple events with `c2rb.noisy_or`, never by adding.

## Design decisions (locked unless the user changes them)

- **Blocked-only output.** `is_road_affected` is a consistency check, not a second output.
- **Per-type calibrated `P0`** kept for interpretability; a supervised classifier is for
  *validation* (AUC/Brier), not the scoring path.
- **Weak labels removed** — no notes-regex code remains.
- **No forecasting.**

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

## Current state & open work

Done: supervised migration complete, notebook executes with 0 errors (AUC 0.73, Brier 0.0085 <
baseline), PDF compiles, methodology updated, Equation 2 explained.

Candidate next steps (not yet done):
1. Optional parallel **`P(road affected)`** surface (calibration code already handles any label).
2. Cross-check `P0` against **independent closure data** (OCHA / Logistics Cluster) to harden it.
3. **Voronoi de-duplication** for overlapping events (ACLED-style) to reduce noisy-OR over-count.
4. Per-event severity features beyond type (use road `CLASSES`, `Avg_Slope`, `Avg_Alt`).

See `methodology.md` for the full formulas, justification, and limitations.

# 07 — Scoring and prediction

Two questions, two tools, one `train.py` run behind both:

| Question | Tool | Model used |
|---|---|---|
| *Which roads* are likely blocked right now? | `score.py` | Parametric: calibrated `P0` + radius/kernel/noisy-OR (spatial) |
| *Will this event* block a road? | `predict.py` | The persisted classifier in `model.joblib` (event-level) |

## score.py — spatial road ranking

```bash
python score.py --config countries/<name>.yaml --as-of 2026-06-01 --window-days 90
```

Takes every event in `[as_of − window_days, as_of]` and scores every road-segment midpoint.
Per segment, each event contributes `P0(type) · K(distance) · φ(age)` — peak propensity, decayed
by distance through the type's kernel, faded by the 30-day-half-life temporal decay — and
contributions combine by **noisy-OR** (`1 − ∏(1−p)`). Events beyond `3 × R_eff` of a segment are
skipped for speed.

| Flag | Effect |
|---|---|
| `--as-of` | Window end (default: the latest event date in the CSV). |
| `--window-days` | Look-back length (default 90). |
| `--mode auto\|road\|grid` | `auto` uses the road layer if `paths.roads` exists, else a grid raster. `road` errors if the file is missing. |
| `--rank-by max\|mean` | Rank a named road by its worst segment (`max`, default — "is any part of this road blocked?") or its average (`mean` — "how bad is the whole road?"). |
| `--top N` | Rows printed to the console (default 25). |
| `--out DIR` | Output dir (default `artifacts/<name>/`). |

Outputs: `road_rankings.csv` (named-road rollup: `max_p`, `mean_p`, `segments`),
`segment_scores.csv` (every segment with useful attributes), `p_block_map.png`. It also prints
the events-within-1-km-of-a-road sanity statistic (~70% expected; see
[06_evaluation.md](06_evaluation.md)).

**Reading the numbers.** Segment probabilities are honest but small-ish in absolute terms —
a `p_block` of 0.5 near Kabul during an active window is very high. Compare *within* a run and
track *changes* between windows rather than fixating on absolute magnitudes; the calibration
(06) is what licenses the probabilistic reading.

## predict.py — event-level probability

```bash
# single event
python predict.py --config countries/<name>.yaml \
    --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3 [--civilian-targeting]

# batch: CSV in, same CSV + p_block column out
python predict.py --config countries/<name>.yaml --events new_events.csv --out scored.csv \
    [--threshold 0.05]
```

Loads `artifacts/<name>/model.joblib` (or `--model path`) and runs the persisted classifier on
`sub_event_type + geo_precision + civ_flag + log(1+fatalities)`. Batch mode needs
`sub_event_type` and `geo_precision` columns; `fatalities`/`civilian_targeting` are optional
(defaulted). `--threshold` additionally emits a 0/1 flag at your chosen cut-off — pick it from
the PR trade-off you care about, not 0.5 (at 0.9% prevalence, 0.5 flags almost nothing).

## Composing them

A typical operational loop: `predict.py --events` this week's raw feed to triage which incoming
events are likely blockers, then `score.py --as-of today --window-days 30` to turn the recent
event picture into a ranked road list for route planning.

Next: [08_deployment.md](08_deployment.md) — the same two questions, interactively.

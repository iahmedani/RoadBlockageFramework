# 01 — Data acquisition (ACLED export)

The framework is built on [ACLED](https://acleddata.com) (Armed Conflict Location & Event Data)
event data. This doc covers getting an export and what it must contain.

## Getting the data

1. Register at <https://acleddata.com/register/> (free for many use cases; check the current
   access tiers). Exports come from the **Data Export Tool** or the API.
2. Export **all event types** for your country and date range as CSV. Don't pre-filter to
   "violence only" — protests and territorial-control events are the *strongest* blockage
   signals (see [06_evaluation.md](06_evaluation.md)).
3. Prefer a long window. The Afghanistan reference model uses 2017–2026 (69,655 events);
   calibration needs enough events per `sub_event_type` to be meaningful, and blocked events
   are rare (~1%), so more history directly buys calibration quality.

**Licensing.** ACLED data is free for non-commercial use under ACLED's Terms of Use, with
required attribution ("Armed Conflict Location & Event Data Project (ACLED); acleddata.com").
Check the ToU before redistributing an export (this repo tracks its CSVs in `data/` — remove or
LFS them if you plan to publish a fork).

## Required columns

`train.py` fails fast (with a clear message) if any of these is missing:

| Column | Used for | Notes |
|---|---|---|
| `sub_event_type` | the core grouping — P0, radius, kernel are all per-type | ACLED's 20+ standard sub-event types |
| `latitude`, `longitude` | spatial scoring | decimal degrees, EPSG:4326 |
| `geo_precision` | locational-uncertainty radius `R_geo` | ACLED codes 1/2/3 (see AcledCodebook.md) |
| `event_date` | time-window filtering + temporal decay | parseable date |
| `fatalities` | severity multiplier + classifier feature | integer; blanks coerced to 0 |
| `is_road_blocked` | **the calibration target** | you add this — see [02_labeling_protocol.md](02_labeling_protocol.md) |

Also used when present:

| Column | Used for |
|---|---|
| `civilian_targeting` | severity bump + classifier feature (any non-blank value counts as "yes") |
| `is_road_affected` | consistency checks only (never a scoring target) |
| `location`, `notes` | labeling context (02) and provenance; not read by the model |

## Format contract

- **Encoding**: ACLED exports as UTF-8 with BOM; every reader in this repo uses
  `encoding="utf-8-sig"`, so a standard export just works.
- **One row per event.** Don't aggregate.
- Keep the **raw export unchanged** next to the labeled file, for provenance — the convention
  here is `data/ACLED Data_<export-date>.csv` (raw) and `data/ACLED Data_classified.csv`
  (raw + label columns). The country config points at the classified file.

## Field semantics

The full ACLED field reference is mirrored in [AcledCodebook.md](AcledCodebook.md). The two
fields people most often misread:

- **`geo_precision`**: 1 = the event happened in the named town (coords are the town),
  2 = near the town / part of a district, 3 = only the wider region is known. The model maps
  these to 1 / 5 / 25 km uncertainty radii — do not treat code 3 events as precisely located.
- **`fatalities`**: ACLED's best (often conservative) estimate; 0 is common and meaningful.

Next: [02_labeling_protocol.md](02_labeling_protocol.md) — adding the ground-truth labels.

# 04 — Configuration (layered YAML)

Configuration is split into **universal physics** (shared by every country) and a small
**per-country override**. `c2rb.load_config(country_path, base_path)` deep-merges the country
file **on top of** the base — any key present in both takes the country's value, nested dicts
merge key-by-key.

```
params.base.yaml          UNIVERSAL  — R_phys, decay kernels, r_geo, severity, temporal
countries/<name>.yaml     LOCAL      — paths, calibrated p0/default_p0, crs_metric hint
```

The merged dict is turned into a `C2RBConfig` dataclass by `c2rb.config_from_yaml(...)`;
`paths` stays a plain dict read directly by the CLI scripts.

## params.base.yaml — every key

| Key | Meaning | Default posture |
|---|---|---|
| `r_phys` | Physical impact radius (km) per `sub_event_type` — how far the event's *effect* reaches. Literature-seeded (battles 15–25 km, explosions 1–10 km, protests 4–5 km, targeted violence ~point). | Keep. Override per-country only with local evidence. |
| `decay` | Distance-decay kernel class per type: `gaussian` (blast-like), `exponential` (heavy tail — battles spread along terrain), `uniform` (constant then cut off — protests, territorial control), `point` (site-confined). | Keep. |
| `r_geo` | Locational uncertainty (km) per ACLED `geo_precision` code: `1: 1.0, 2: 5.0, 3: 25.0`. Follows ACLED's documented semantics — it **cannot** be learned from ACLED data (same-location events share one centroid, so coordinate spread is ~0). | Keep. |
| `alpha` | Severity blend: 0 = pure log growth in fatalities (gentle), 1 = pure linear. Default 0.15. | Keep. |
| `kappa` | How strongly severity stretches the radius. Default 0.25. | Keep. |
| `sev_ref_fatalities` | Fatality level that maps to multiplier 1.0. Default 1. | Keep. |
| `sev_clip` | Bounds on the severity multiplier, `[0.5, 3.0]`. The civilian bump is applied **inside** this clip (see methodology Eq. 3). | Keep. |
| `civ_bump` | Extra stretch when `civilian_targeting` is flagged. Default 0.30. | Keep. |
| `tau_days` | Temporal-decay half-life (days) in noisy-OR aggregation. Default 30. | Keep. |
| `r_max_factor` | Ignore an event beyond `r_max_factor × R_eff` (compute cutoff). Default 3. | Keep. |

## countries/<name>.yaml — every key

| Key | Meaning |
|---|---|
| `paths.acled_csv` | The labeled ACLED CSV (relative to the **repo root** — all commands run from there). |
| `paths.label_blocked_col` / `paths.label_affected_col` | Label column names (defaults `is_road_blocked` / `is_road_affected`). |
| `paths.roads` | Segmented road layer, or `null` to run in grid mode. |
| `paths.roads_name_col` | The road-name attribute for named rankings. |
| `paths.admin` | Optional admin-boundary layer for map context. |
| `crs_metric` | **Hint only** — the metre-based CRS to pass to `tools/segment_roads.py --metric-crs`. Not read by training or scoring (which use a local equirectangular frame). |
| `p0` / `default_p0` | The calibrated peak blockage propensity per type + fallback. **Written by `train.py` — never hand-edit; rerun training instead.** |

## The train.py rewrite contract

`train.py` (unless `--no-write-p0`) rewrites the country YAML with fresh `p0`/`default_p0`.
The rewriter serializes `paths`, `crs_metric`, the `p0` block — and **preserves every other
top-level key verbatim** under a "Country-level overrides" section. So this is safe and
retrain-proof:

```yaml
# countries/<name>.yaml — a country with evidence its clashes reach less far
paths: { ... }
crs_metric: "EPSG:32638"
r_phys:
  "Armed clash": 10.0     # local override of the base 15.0 — survives retraining
tau_days: 45              # slower-fading closures — survives retraining
p0: { ... }               # written by train.py
default_p0: 0.0087
```

Comments inside the file do **not** survive a rewrite (the file is regenerated from a template);
keep commentary in git history or here in docs.

## Rules of thumb

- All paths are **CWD-relative**: run every command from the repo root (the Makefile enforces
  this).
- Probabilities combine with `c2rb.noisy_or`, never by adding.
- If you override physics per-country, put the override in the **country file**, not in
  `params.base.yaml` — the base is shared by every country.

Next: [05_training.md](05_training.md).

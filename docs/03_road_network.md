# 03 — Road network sourcing and segmentation

The spatial scorer (`score.py`, the app's map tab, notebook §6) scores **road segment
midpoints**. Without a road layer everything still runs in grid mode (a risk raster), but the
per-road rankings — the concrete deliverable — need a segmented network.

## Requirements

- **LineString geometries** in a format geopandas reads (shapefile, GeoPackage, GeoJSON).
- Reprojectable to **EPSG:4326** (the loaders call `.to_crs(4326)`; any valid CRS works as input,
  but the file must *have* a CRS).
- A **road-name column** for the named-road rollup (`paths.roads_name_col` in the country
  config; Afghanistan's is `NAME_OF_RO`). Without one you still get per-segment scores, just no
  named rankings.
- Segments of **roughly 1 km** — long multi-kilometre lines make the map and rankings coarse,
  because each line is scored at a single representative point.

## Where to get one

- **HDX** (<https://data.humdata.org>) — search "<country> roads"; WFP/government layers are
  common for crisis-affected countries and usually carry usable name/class attributes.
  The Afghanistan reference layer is the WFP/AGCHO network.
- **OpenStreetMap** — via Geofabrik or HOT exports; filter `highway=` to the classes you care
  about (primary/secondary/tertiary). Name coverage varies by country.
- **National road authority / cadastre data** where accessible.

## Segmenting

```bash
python tools/segment_roads.py --in roads_raw.shp --out data/<country>_roads_segmented.shp \
    --seg-km 1.0 [--metric-crs EPSG:32642]
```

What it does: reprojects to a metre-based CRS, splits every LineString into ~equal pieces of
`--seg-km` km, copies all original attributes onto each piece, adds a `Segment_ID`, and writes
the result back in EPSG:4326.

**Picking `--metric-crs`**: use the UTM zone of the country's central longitude —
`zone = floor((lon + 180)/6) + 1`, `EPSG = 32600 + zone` (northern hemisphere) or `32700 + zone`
(southern). Omit the flag and the tool auto-picks the zone from the data centroid. Record the
value as `crs_metric` in the country YAML — it's a documentation hint for GIS work; the model
itself never reads it (scoring uses a local equirectangular frame).

## Reference numbers (Afghanistan)

- 27,991 segments from the WFP/AGCHO network, median length 1,068 m.
- Useful attributes carried per segment: road name, `CLASSES`, `Avg_Slope`, `Avg_Alt`.

## Sanity benchmark

The literature finds **~70% of violent events fall within 1 km of a road**. `score.py` prints
this statistic for every run (Afghanistan: ~78–83% depending on window). If your number is far
below ~60%, suspect a CRS problem, a road layer that covers only part of the country, or event
coordinates in the wrong hemisphere — see [09_troubleshooting.md](09_troubleshooting.md).

Next: [04_configuration.md](04_configuration.md).

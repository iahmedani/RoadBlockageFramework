#!/usr/bin/env python
"""
segment_roads.py -- Cut a raw road network into ~1 km segments for C2RB scoring.

The Afghanistan road layer shipped pre-segmented into ~1 km pieces. A new country's road
shapefile usually has long multi-kilometre LineStrings, which makes per-segment blockage
maps coarse. This utility splits every line into roughly equal-length segments (default
1 km), carrying all original attributes onto each piece, so score.py produces fine-grained
road rankings.

Usage
-----
    python tools/segment_roads.py --in roads_raw.shp --out roads_segmented.shp \
        [--seg-km 1.0] [--metric-crs EPSG:32642]

`--metric-crs` should be a metre-based projection appropriate to the country (a UTM zone).
Pick it from the country's central longitude: UTM zone = floor((lon + 180) / 6) + 1, then
EPSG = 32600 + zone (north) or 32700 + zone (south). See LOCALIZATION.md.
"""
from __future__ import annotations
import argparse

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import substring


def _segment_line(line, seg_m: float):
    """Yield ~seg_m-long sub-LineStrings covering `line` (metric CRS units = metres)."""
    geoms = line.geoms if isinstance(line, MultiLineString) else [line]
    for g in geoms:
        if not isinstance(g, LineString) or g.length == 0:
            continue
        n = max(1, int(round(g.length / seg_m)))
        step = g.length / n
        for i in range(n):
            piece = substring(g, i * step, (i + 1) * step)
            if isinstance(piece, LineString) and piece.length > 0:
                yield piece


def main() -> None:
    ap = argparse.ArgumentParser(description="Split a road network into ~1 km segments.")
    ap.add_argument("--in", dest="src", required=True, help="input road shapefile")
    ap.add_argument("--out", dest="dst", required=True, help="output segmented shapefile")
    ap.add_argument("--seg-km", type=float, default=1.0, help="target segment length (km)")
    ap.add_argument("--metric-crs", default=None,
                    help="metric CRS for length math (e.g. EPSG:32642). Defaults to an "
                         "auto UTM zone from the data centroid.")
    args = ap.parse_args()

    roads = gpd.read_file(args.src)
    if roads.crs is None:
        raise SystemExit("Input has no CRS; set one (usually EPSG:4326) before segmenting.")
    roads = roads.to_crs(4326)

    # Choose a metric CRS so segment lengths are in metres.
    if args.metric_crs:
        metric = args.metric_crs
    else:
        c = roads.geometry.union_all().centroid
        zone = int((c.x + 180) // 6) + 1
        metric = f"EPSG:{(32600 if c.y >= 0 else 32700) + zone}"
        print(f"auto metric CRS = {metric} (UTM zone {zone})")

    work = roads.to_crs(metric)
    seg_m = args.seg_km * 1000.0
    attr_cols = [c for c in work.columns if c != "geometry"]

    rows, geoms = [], []
    for _, row in work.iterrows():
        for piece in _segment_line(row.geometry, seg_m):
            rows.append({c: row[c] for c in attr_cols})
            geoms.append(piece)

    out = gpd.GeoDataFrame(rows, geometry=geoms, crs=metric).to_crs(4326)
    out["Segment_ID"] = [f"S{i+1}" for i in range(len(out))]  # stable per-segment id
    out.to_file(args.dst)
    print(f"wrote {len(out):,} segments (from {len(roads):,} input lines) -> {args.dst}")


if __name__ == "__main__":
    main()

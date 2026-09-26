#!/usr/bin/env python
"""
score.py -- Apply a trained C2RB model to produce road-blockage probabilities.

Given a country config (with calibrated P0 from train.py) and a date + look-back window,
this scores every road segment (or a grid, if no road layer is configured) against the
conflict events in that window via noisy-OR with temporal decay, then ranks the most
likely-blocked named roads.

Usage
-----
    python score.py --config countries/afghanistan.yaml --as-of 2026-06-01 --window-days 90
    python score.py --config countries/<name>.yaml [--mode road|grid|auto] \
        [--rank-by max|mean] [--top 25] [--out artifacts/<name>/]

Outputs (under --out, default artifacts/<config-stem>/)
    segment_scores.csv   per-segment p_block (road mode) or per-cell p_block (grid mode)
    road_rankings.csv    named-road rollup ranked by blockage risk (road mode only)
    p_block_map.png      risk map (segments coloured by p_block, or grid heatmap)
"""
from __future__ import annotations
import argparse
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

import c2rb


def load_events(cfg_raw: dict, as_of: pd.Timestamp,
                window_days: int) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Read the ACLED CSV; return (events inside [as_of - window, as_of], window start)."""
    df = pd.read_csv(cfg_raw["paths"]["acled_csv"], encoding="utf-8-sig", low_memory=False)
    df = c2rb.prepare_events(df)
    start = as_of - pd.Timedelta(days=window_days)
    win = df[(df["event_date"] >= start) & (df["event_date"] <= as_of)].copy()
    return win, start


def score_roads(events, cfg, cfg_raw, as_of, out, rank_by, top):
    """Road-layer mode: score each segment midpoint, write rankings + map."""
    import geopandas as gpd
    roads_path = cfg_raw["paths"]["roads"]
    name_col = cfg_raw["paths"].get("roads_name_col", "NAME_OF_RO")
    admin_path = cfg_raw["paths"].get("admin")

    roads = gpd.read_file(roads_path).to_crs(4326)
    mids = roads.geometry.representative_point()
    rt = pd.DataFrame({"latitude": mids.y.values, "longitude": mids.x.values})
    roads = roads.assign(p_block=c2rb.score_targets(events, rt, cfg, as_of_date=as_of))

    # Sanity check: share of events within 1 km of any road (~70% in the literature).
    lat0, lon0 = float(events.latitude.mean()), float(events.longitude.mean())
    ex, ey = c2rb.latlon_to_local_km(events.latitude, events.longitude, lat0, lon0)
    rx, ry = c2rb.latlon_to_local_km(rt.latitude, rt.longitude, lat0, lon0)
    near = [np.min(np.hypot(rx - ex[i], ry - ey[i])) <= 1.0 for i in range(len(events))]
    print(f"  scored {len(roads):,} segments | {100 * np.mean(near):.0f}% of events within 1 km of a road")

    # Per-segment scores (keep useful attributes for downstream filtering).
    keep_cols = [c for c in [name_col, "CLASSES", "admin1Name", "admin2Name", "p_block"]
                 if c in roads.columns]
    seg = roads[keep_cols].copy().sort_values("p_block", ascending=False)
    seg.to_csv(os.path.join(out, "segment_scores.csv"), index=False)

    # Named-road rollup, ranked by the chosen statistic (skipped if the layer has no name column).
    if name_col in roads.columns:
        rank_col = "max_p" if rank_by == "max" else "mean_p"
        rank = (roads[roads.p_block > 0]
                .groupby(name_col)
                .agg(max_p=("p_block", "max"), mean_p=("p_block", "mean"),
                     segments=("p_block", "size"))
                .sort_values(rank_col, ascending=False).round(4))
        rank.to_csv(os.path.join(out, "road_rankings.csv"))
        print(f"  top roads by {rank_col}:")
        print(rank.head(top).to_string())
    else:
        print(f"  no road-name column '{name_col}' (set paths.roads_name_col) -- "
              f"skipping named-road rankings; per-segment scores still written")
    print(f"  segments with P(block) > 0.25: {(roads.p_block > 0.25).sum()} of {len(roads):,}")

    # Map.
    fig, ax = plt.subplots(figsize=(10, 9))
    if admin_path and os.path.exists(admin_path):
        gpd.read_file(admin_path).to_crs(4326).boundary.plot(ax=ax, color="0.75", lw=0.5)
    roads.plot(column="p_block", cmap="inferno", legend=True, ax=ax, lw=0.7,
               legend_kwds={"label": "P(road blocked)"})
    ax.scatter(events.longitude, events.latitude, s=4, c="cyan", alpha=0.3)
    ax.set_title(f"Per-segment road-blockage probability — window ending {as_of.date()}")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    fig.tight_layout(); fig.savefig(os.path.join(out, "p_block_map.png"), dpi=110); plt.close(fig)


def score_grid(events, cfg, out, as_of, n=120):
    """Grid fallback: continuous risk surface when no road layer is configured."""
    lat = np.linspace(events.latitude.min(), events.latitude.max(), n)
    lon = np.linspace(events.longitude.min(), events.longitude.max(), n)
    grid = pd.DataFrame([(a, b) for a in lat for b in lon], columns=["latitude", "longitude"])
    grid["p_block"] = c2rb.score_targets(events, grid, cfg, as_of_date=as_of)
    grid.to_csv(os.path.join(out, "segment_scores.csv"), index=False)
    P = grid["p_block"].values.reshape(n, n)

    fig, ax = plt.subplots(figsize=(9, 8))
    m = ax.pcolormesh(lon, lat, P, shading="auto", cmap="inferno", vmin=0, vmax=min(1, P.max()))
    ax.scatter(events.longitude, events.latitude, s=3, c="cyan", alpha=0.25)
    fig.colorbar(m, ax=ax, label="P(road blocked)")
    ax.set_title(f"Road-blockage risk surface — window ending {as_of.date()} ({len(events)} events)")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    fig.tight_layout(); fig.savefig(os.path.join(out, "p_block_map.png"), dpi=110); plt.close(fig)
    print(f"  grid mode: P(block) mean={grid.p_block.mean():.3f} max={grid.p_block.max():.3f} "
          f"cells>0.5: {int((grid.p_block > 0.5).sum())}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Score road-blockage probabilities for one country.")
    ap.add_argument("--config", required=True, help="country config, e.g. countries/afghanistan.yaml")
    ap.add_argument("--base", default="params.base.yaml")
    ap.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default = latest event)")
    ap.add_argument("--window-days", type=int, default=90, help="look-back window length")
    ap.add_argument("--mode", choices=["auto", "road", "grid"], default="auto")
    ap.add_argument("--rank-by", choices=["max", "mean"], default="max",
                    help="rank named roads by their worst (max) or average (mean) segment")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.config))[0]
    out = args.out or os.path.join("artifacts", name)
    os.makedirs(out, exist_ok=True)

    cfg_raw = c2rb.load_config(args.config, args.base)
    cfg = c2rb.config_from_yaml(cfg_raw)

    # Default as-of to the latest event in the data.
    if args.as_of:
        as_of = pd.to_datetime(args.as_of)
    else:
        all_dates = pd.to_datetime(pd.read_csv(cfg_raw["paths"]["acled_csv"],
                                               usecols=["event_date"],
                                               encoding="utf-8-sig")["event_date"])
        as_of = all_dates.max()

    events, start = load_events(cfg_raw, as_of, args.window_days)
    print(f"[{name}] window {start.date()}…{as_of.date()} | {len(events):,} events")
    if events.empty:
        raise SystemExit("No events in the window -- widen --window-days or change --as-of.")

    roads_path = cfg_raw["paths"].get("roads")
    use_road = args.mode == "road" or (args.mode == "auto" and roads_path and os.path.exists(roads_path))
    if use_road:
        score_roads(events, cfg, cfg_raw, as_of, out, args.rank_by, args.top)
    else:
        if args.mode == "road":
            raise SystemExit(f"--mode road but roads file not found: {roads_path}")
        print("  no road layer configured — running grid mode")
        score_grid(events, cfg, out, as_of)
    print(f"[{name}] outputs -> {out}/")


if __name__ == "__main__":
    main()

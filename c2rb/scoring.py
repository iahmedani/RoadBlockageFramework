"""Spatial scorer: aggregate all events onto target points via noisy-OR."""
from __future__ import annotations
import numpy as np
import pandas as pd

from .config import C2RBConfig, GAUSS
from .geometry import latlon_to_local_km
from .model import effective_radius, kernel, temporal_decay


def score_targets(events: pd.DataFrame, targets: pd.DataFrame, cfg: C2RBConfig,
                  as_of_date=None, lat0=None, lon0=None) -> np.ndarray:
    """Blockage probability for each target point, aggregating all events via noisy-OR.

    events  : DataFrame with columns latitude, longitude, sub_event_type, geo_precision,
              fatalities, civ_flag (0/1), and (optional) event_date.
    targets : DataFrame with columns latitude, longitude.
    Returns : np.ndarray of length len(targets) with P(blocked) in [0,1].

    Vectorized over targets per event; loops over events (typically far fewer than targets
    after a spatial pre-filter). Uses a local equirectangular frame for fast planar distance.
    """
    if lat0 is None:
        lat0 = float(events["latitude"].mean())
    if lon0 is None:
        lon0 = float(events["longitude"].mean())
    tx, ty = latlon_to_local_km(targets["latitude"].values, targets["longitude"].values, lat0, lon0)
    ex, ey = latlon_to_local_km(events["latitude"].values, events["longitude"].values, lat0, lon0)

    r_eff = effective_radius(events["sub_event_type"].values, events["geo_precision"].values,
                             events["fatalities"].fillna(0).values,
                             events.get("civ_flag", pd.Series(0, index=events.index)).values, cfg)
    p0 = np.array([cfg.p0.get(s, cfg.default_p0) for s in events["sub_event_type"].values])
    kinds = events["sub_event_type"].map(lambda s: cfg.decay.get(s, GAUSS)).values

    if as_of_date is not None and "event_date" in events:
        dt = (pd.to_datetime(as_of_date) - pd.to_datetime(events["event_date"])).dt.days.clip(lower=0)
        phi = temporal_decay(dt.values, cfg)
    else:
        phi = np.ones(len(events))

    keep = np.ones(len(targets))  # accumulator for prod(1 - p_i)
    rmax = cfg.r_max_factor * r_eff
    for j in range(len(events)):
        d = np.hypot(tx - ex[j], ty - ey[j])
        within = d <= rmax[j]
        if not within.any():
            continue
        k = kernel(d[within], r_eff[j], kinds[j])
        p = np.clip(p0[j] * k * phi[j], 0, 1)
        keep[within] *= (1 - p)
    return 1 - keep

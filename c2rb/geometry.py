"""Geometry helpers -- metric distances without a GIS stack."""
from __future__ import annotations
import numpy as np

EARTH_R_KM = 6371.0088


def latlon_to_local_km(lat, lon, lat0, lon0):
    """Equirectangular projection to a local planar frame in km around (lat0, lon0).

    Accurate to ~0.1% over a country-sized extent -- more than enough for buffer math,
    and avoids a pyproj/geopandas dependency. Returns (x_km, y_km)."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    x = np.radians(lon - lon0) * np.cos(np.radians(lat0)) * EARTH_R_KM
    y = np.radians(lat - lat0) * EARTH_R_KM
    return x, y


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between scalar/array coordinate pairs."""
    lat1, lon1, lat2, lon2 = map(np.radians, (np.asarray(lat1, float), np.asarray(lon1, float),
                                              np.asarray(lat2, float), np.asarray(lon2, float)))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(a))

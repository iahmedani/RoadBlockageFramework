"""
c2rb -- Conflict-event to Road-Blockage probability framework (impact modeling).

A parametric, weakly-supervised probabilistic model that turns ACLED conflict events
into per-location road-blockage probabilities. The pipeline is:

    event -> effective buffer radius R_eff  (size of the impact zone)
          -> distance-decay kernel K        (how blockage probability falls with distance)
          -> P(block | distance)            (per point / road segment)
          -> noisy-OR over nearby events    (combine many events, with temporal decay)

Parameters are SEEDED from published literature and CALIBRATED against weak labels
mined from the ACLED `notes` free text (see weak_label / empirical_bayes_p0).

The module has no hard dependency on geopandas; geometry uses numpy + a local
equirectangular projection so it runs anywhere pandas/numpy are available.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# 0. Geometry helpers (metric distances without a GIS stack)
# --------------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------------
# 1. Weak-label mining from ACLED `notes`
# --------------------------------------------------------------------------------------
# Three mechanisms by which a conflict event disrupts a road, each its own regex so the
# methodology can report them separately. The combined label = OR of the three.

# (A) Explicit deliberate blockage / closure -- typical of protests and sieges.
RE_BLOCK = re.compile(
    r"block(?:ed|ing|s|ade)?\s+(?:the\s+|a\s+|off\s+)?(?:road|highway|route|traffic|pass|"
    r"subway|street|movement|access)"
    r"|(?:road|highway|route|street)\s+(?:was\s+|were\s+|is\s+|been\s+)?(?:block|clos)"
    r"|clos(?:e|ed|ure)\s+(?:of\s+)?(?:the\s+)?(?:road|highway|route)"
    r"|cut\s+off\s+(?:the\s+)?(?:road|highway|supply|access)"
    r"|seal(?:ed)?\s+off|impassable|under\s+siege|besieg",
    re.I)

# (B) Road hazard -- explosive ordnance on/along a road makes it dangerous/impassable.
RE_HAZARD = re.compile(
    r"roadside\s+(?:bomb|ied|mine|explos)"
    r"|(?:ied|mine|landmine|explosive)[^.]{0,30}\b(?:on|along|planted\s+(?:on|in|along)|"
    r"placed\s+(?:on|in|along))\b[^.]{0,20}(?:road|highway|route|street)"
    r"|(?:planted|placed)[^.]{0,25}(?:road|highway|route)"
    r"|(?:destroyed|blew\s+up|damaged|blown\s+up)\s+(?:the\s+|a\s+)?bridge",
    re.I)

# (C) Road denial -- ambush of a convoy / movement column on a route.
RE_DENIAL = re.compile(
    r"convoy"
    r"|ambush(?:ed)?[^.]{0,30}(?:road|highway|route|vehicle|truck|column)"
    r"|set\s+up\s+(?:a\s+)?(?:check\s?point|checkpost|check-post)"
    r"|seized\s+control\s+of[^.]{0,20}(?:road|highway|route|bridge)",
    re.I)


def weak_label(notes: pd.Series) -> pd.DataFrame:
    """Return a DataFrame of the three component weak labels and their union.

    Columns: lbl_block, lbl_hazard, lbl_denial, road_disruption (int 0/1).
    All derived purely from `notes` text -- never from sub_event_type -- so the
    per-type rates that come out are genuine signal, not a relabeling of the type.
    """
    s = notes.fillna("").astype(str)
    out = pd.DataFrame({
        "lbl_block": s.str.contains(RE_BLOCK).astype(int),
        "lbl_hazard": s.str.contains(RE_HAZARD).astype(int),
        "lbl_denial": s.str.contains(RE_DENIAL).astype(int),
    })
    out["road_disruption"] = (out.sum(axis=1) > 0).astype(int)
    return out


# --------------------------------------------------------------------------------------
# 2. Calibration: per-sub_event_type blockage propensity P0 with Empirical-Bayes shrinkage
# --------------------------------------------------------------------------------------
def wilson_ci(k, n, z=1.96):
    """Wilson score 95% interval for a binomial proportion (stable at small n / 0 counts)."""
    k = np.asarray(k, float); n = np.asarray(n, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, k / n, 0.0)
        den = 1 + z * z / n
        center = (p + z * z / (2 * n)) / den
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return np.clip(center - half, 0, 1), np.clip(center + half, 0, 1)


def empirical_bayes_p0(label: pd.Series, group: pd.Series, prior_strength: float = 50.0
                       ) -> pd.DataFrame:
    """Per-group blockage propensity P0 = P(road_disruption | group).

    Raw rates are unstable for small groups (e.g. Grenade n=176 -> 0.000). We shrink each
    group's rate toward the global mean with a Beta(a,b) conjugate prior whose total
    pseudo-count is `prior_strength`, anchored at the global positive rate. This is the
    standard Beta-Binomial empirical-Bayes estimator and gives every type a sane, smoothed
    P0 with honest uncertainty (Wilson CI on the raw rate is reported alongside).
    """
    g = pd.DataFrame({"y": label.values, "grp": group.values})
    glob = g["y"].mean()
    a0, b0 = glob * prior_strength, (1 - glob) * prior_strength
    agg = g.groupby("grp")["y"].agg(["sum", "count"]).rename(columns={"sum": "pos", "count": "n"})
    agg["p0_raw"] = agg["pos"] / agg["n"]
    agg["p0_shrunk"] = (agg["pos"] + a0) / (agg["n"] + a0 + b0)
    lo, hi = wilson_ci(agg["pos"].values, agg["n"].values)
    agg["ci_lo"], agg["ci_hi"] = lo, hi
    agg["global_rate"] = glob
    return agg.sort_values("p0_shrunk", ascending=False)


# --------------------------------------------------------------------------------------
# 3. Configuration: per-sub_event_type physical radius + decay kernel
# --------------------------------------------------------------------------------------
GAUSS, EXPON, UNIFORM, POINT = "gaussian", "exponential", "uniform", "point"


@dataclass
class C2RBConfig:
    """All tunable parameters. Defaults are literature-seeded; override from params.yaml."""
    # physical impact radius (km) by sub_event_type
    r_phys: dict = field(default_factory=lambda: {
        "Remote explosive/landmine/IED": 1.0, "Suicide bomb": 2.0, "Grenade": 1.0,
        "Shelling/artillery/missile attack": 7.0, "Air/drone strike": 3.0,
        "Armed clash": 15.0, "Non-state actor overtakes territory": 20.0,
        "Government regains territory": 20.0, "Non-violent transfer of territory": 20.0,
        "Attack": 0.5, "Abduction/forced disappearance": 0.5, "Sexual violence": 0.5,
        "Peaceful protest": 4.0, "Protest with intervention": 4.0,
        "Excessive force against protesters": 4.0, "Violent demonstration": 5.0,
        "Mob violence": 5.0, "Looting/property destruction": 3.0,
        "Disrupted weapons use": 1.0, "Arrests": 0.5, "Agreement": 2.0,
        "Change to group/activity": 2.0, "Headquarters or base established": 5.0,
        "Other": 2.0,
    })
    # decay kernel class by sub_event_type
    decay: dict = field(default_factory=lambda: {
        "Remote explosive/landmine/IED": GAUSS, "Suicide bomb": GAUSS, "Grenade": GAUSS,
        "Shelling/artillery/missile attack": GAUSS, "Air/drone strike": GAUSS,
        "Armed clash": EXPON, "Non-state actor overtakes territory": UNIFORM,
        "Government regains territory": UNIFORM, "Non-violent transfer of territory": UNIFORM,
        "Attack": POINT, "Abduction/forced disappearance": POINT, "Sexual violence": POINT,
        "Peaceful protest": UNIFORM, "Protest with intervention": UNIFORM,
        "Excessive force against protesters": UNIFORM, "Violent demonstration": UNIFORM,
        "Mob violence": UNIFORM, "Looting/property destruction": GAUSS,
        "Disrupted weapons use": GAUSS, "Arrests": POINT, "Agreement": UNIFORM,
        "Change to group/activity": UNIFORM, "Headquarters or base established": UNIFORM,
        "Other": GAUSS,
    })
    # locational uncertainty (km) by ACLED geo_precision code (1=town, 2=near town, 3=region)
    r_geo: dict = field(default_factory=lambda: {1: 1.0, 2: 5.0, 3: 25.0})
    # P0 peak blockage propensity by sub_event_type -- filled by calibration; falls back to default_p0
    p0: dict = field(default_factory=dict)
    default_p0: float = 0.05
    # severity scaler params:  S(n_f)=alpha*(1+n_f)+(1-alpha)*(1+ln(1+n_f))
    alpha: float = 0.15        # weight on the (explosive) linear term vs the log term
    kappa: float = 0.25        # how strongly severity stretches the radius
    sev_ref_fatalities: float = 1.0   # reference S() level -> multiplier 1.0
    sev_clip: tuple = (0.5, 3.0)      # bound the severity multiplier
    civ_bump: float = 0.30     # extra severity multiplier weight if civilian_targeting set
    # temporal decay half-life (days) for multi-event aggregation
    tau_days: float = 30.0
    # geometry / domain
    r_max_factor: float = 3.0  # consider an event out to r_max_factor * R_eff


# --------------------------------------------------------------------------------------
# 4. Effective radius and severity
# --------------------------------------------------------------------------------------
def severity_S(n_fatal, alpha):
    n = np.asarray(n_fatal, float)
    return alpha * (1 + n) + (1 - alpha) * (1 + np.log1p(n))


def severity_multiplier(n_fatal, civ_flag, cfg: C2RBConfig):
    """Bounded multiplier >=0.5, <=3 that stretches the radius for deadlier / civilian events."""
    S = severity_S(n_fatal, cfg.alpha)
    S_ref = severity_S(cfg.sev_ref_fatalities, cfg.alpha)
    m = 1 + cfg.kappa * (S / S_ref - 1)
    m = m * (1 + cfg.civ_bump * np.asarray(civ_flag, float))
    return np.clip(m, cfg.sev_clip[0], cfg.sev_clip[1])


def effective_radius(sub_type, geo_prec, n_fatal, civ_flag, cfg: C2RBConfig):
    """R_eff = sqrt(R_phys^2 + R_geo^2) * severity_multiplier  (quadrature of independent radii)."""
    rphys = np.array([cfg.r_phys.get(s, 2.0) for s in np.atleast_1d(sub_type)], float)
    rgeo = np.array([cfg.r_geo.get(int(g), 5.0) for g in np.atleast_1d(geo_prec)], float)
    base = np.sqrt(rphys ** 2 + rgeo ** 2)
    return base * severity_multiplier(n_fatal, civ_flag, cfg)


# --------------------------------------------------------------------------------------
# 5. Distance-decay kernels and per-event blockage probability
# --------------------------------------------------------------------------------------
def kernel(distance_km, r_eff, kind):
    """K(d) in [0,1]: fraction of peak blockage probability surviving at distance d."""
    d = np.asarray(distance_km, float)
    r = np.asarray(r_eff, float)
    if kind == GAUSS:
        sigma = r / 2.0
        return np.exp(-(d ** 2) / (2 * sigma ** 2))
    if kind == EXPON:
        lam = r / 3.0
        return np.exp(-d / lam)
    if kind == UNIFORM:
        return (d <= r).astype(float)
    if kind == POINT:
        return (d <= np.maximum(r, 0.3)).astype(float)
    raise ValueError(f"unknown kernel {kind!r}")


def p_block_at_distance(distance_km, sub_type, r_eff, cfg: C2RBConfig):
    """P(block | d) = P0(sub_type) * K(d). Scalar sub_type / r_eff."""
    p0 = cfg.p0.get(sub_type, cfg.default_p0)
    return p0 * kernel(distance_km, r_eff, cfg.decay.get(sub_type, GAUSS))


def temporal_decay(delta_days, cfg: C2RBConfig):
    """phi(dt) = 0.5 ** (dt / half_life) -- exponential fade of an event's relevance."""
    return 0.5 ** (np.asarray(delta_days, float) / cfg.tau_days)


def noisy_or(probs, axis=None):
    """Combine independent blockage probabilities: 1 - prod(1 - p)."""
    p = np.clip(np.asarray(probs, float), 0, 1)
    return 1 - np.prod(1 - p, axis=axis)


# --------------------------------------------------------------------------------------
# 6. Scoring a set of target points (road-segment midpoints or a grid) against events
# --------------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------------
# 7. Config (de)serialization
# --------------------------------------------------------------------------------------
def config_from_yaml(d: dict) -> C2RBConfig:
    """Build a C2RBConfig from a parsed params.yaml dict (only overrides provided keys)."""
    cfg = C2RBConfig()
    for key in ("r_phys", "decay", "p0", "default_p0", "alpha", "kappa",
                "sev_ref_fatalities", "civ_bump", "tau_days", "r_max_factor"):
        if key in d and d[key] is not None:
            setattr(cfg, key, d[key])
    if "r_geo" in d and d["r_geo"]:
        cfg.r_geo = {int(k): float(v) for k, v in d["r_geo"].items()}
    if "sev_clip" in d and d["sev_clip"]:
        cfg.sev_clip = tuple(d["sev_clip"])
    return cfg

"""
c2rb -- Conflict-event to Road-Blockage probability framework (impact modeling).

A parametric, supervised probabilistic model that turns ACLED conflict events
into per-location road-blockage probabilities. The pipeline is:

    event -> effective buffer radius R_eff  (size of the impact zone)
          -> distance-decay kernel K        (how blockage probability falls with distance)
          -> P(block | distance)            (per point / road segment)
          -> noisy-OR over nearby events    (combine many events, with temporal decay)

Radius/kernel shapes are SEEDED from published literature; the peak blockage propensity
P0 is CALIBRATED against the ground-truth `is_road_blocked` label (see load_labels /
empirical_bayes_p0). `is_road_affected` is loaded too, used only as a consistency check.

The module has no hard dependency on geopandas; geometry uses numpy + a local
equirectangular projection so it runs anywhere pandas/numpy are available.
"""
from __future__ import annotations
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
# 1. Ground-truth labels
# --------------------------------------------------------------------------------------
def _yesno_to_int(s: pd.Series) -> pd.Series:
    """Map a yes/no (case/whitespace-insensitive) Series to int 1/0; anything else -> 0."""
    return s.fillna("").astype(str).str.strip().str.lower().eq("yes").astype(int)


def load_labels(df: pd.DataFrame, blocked_col: str = "is_road_blocked",
                affected_col: str = "is_road_affected") -> pd.DataFrame:
    """Return the ground-truth road labels as int 0/1 columns.

    Always returns `is_road_blocked` (the calibration/scoring target). If `affected_col`
    is present it is also returned (`is_road_affected`) for consistency checks only --
    it is not used in scoring (the framework outputs blocked probability).
    """
    if blocked_col not in df:
        raise KeyError(f"label column {blocked_col!r} not found in dataframe")
    out = pd.DataFrame({"is_road_blocked": _yesno_to_int(df[blocked_col])})
    if affected_col in df:
        out["is_road_affected"] = _yesno_to_int(df[affected_col])
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
    """Per-group blockage propensity P0 = P(is_road_blocked | group).

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
    agg["ci_lo"], agg["ci_hi"] = lo, hi   # Wilson interval on the RAW rate
    # Beta posterior 95% credible interval -- consistent with the shrunk estimate (always
    # brackets p0_shrunk, the posterior mean), so it is the right interval to plot.
    from scipy.stats import beta as _beta
    agg["post_lo"] = _beta.ppf(0.025, agg["pos"] + a0, agg["n"] - agg["pos"] + b0)
    agg["post_hi"] = _beta.ppf(0.975, agg["pos"] + a0, agg["n"] - agg["pos"] + b0)
    agg["global_rate"] = glob
    return agg.sort_values("p0_shrunk", ascending=False)


# --------------------------------------------------------------------------------------
# 3. Configuration: per-sub_event_type physical radius + decay kernel
# --------------------------------------------------------------------------------------
GAUSS, EXPON, UNIFORM, POINT = "gaussian", "exponential", "uniform", "point"


@dataclass
class C2RBConfig:
    """All tunable parameters. Defaults are literature-seeded; override from params.base.yaml
    (universal) + countries/<name>.yaml (local) via load_config()."""
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
    """Build a C2RBConfig from a parsed params dict (only overrides provided keys)."""
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


# --------------------------------------------------------------------------------------
# 8. Layered configuration: universal base + per-country override (localization)
# --------------------------------------------------------------------------------------
def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge `override` onto `base` (override wins); returns a new dict."""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(country_path: str, base_path: str = "params.base.yaml") -> dict:
    """Load and merge the universal base params with a country override file.

    `base_path` (params.base.yaml) holds the country-INDEPENDENT physics -- r_phys,
    decay kernels, r_geo, severity and temporal constants. `country_path`
    (countries/<name>.yaml) holds only what is local: data `paths`, the metric
    `crs_metric`, and the calibrated `p0` / `default_p0`. The returned dict is the
    merged configuration; pass it to config_from_yaml() and read paths[...] from it.
    """
    import yaml
    with open(base_path, encoding="utf-8") as fh:
        base = yaml.safe_load(fh) or {}
    with open(country_path, encoding="utf-8") as fh:
        country = yaml.safe_load(fh) or {}
    return _deep_merge(base, country)


# --------------------------------------------------------------------------------------
# 9. Shared event preparation + supervised validation (reused by CLI + notebook)
# --------------------------------------------------------------------------------------
def prepare_events(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise the raw ACLED columns the calibrator/scorer need; returns the same df.

    Parses `event_date`, coerces `fatalities` to int, and derives `civ_flag` (1 when
    `civilian_targeting` is set). Safe to call on any ACLED export.
    """
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["fatalities"] = pd.to_numeric(df.get("fatalities"), errors="coerce").fillna(0).astype(int)
    civ = df.get("civilian_targeting", pd.Series("", index=df.index))
    df["civ_flag"] = (civ.fillna("").astype(str).str.strip() != "").astype(int)
    return df


# Event-level features the supervised model reads. Categorical cols are one-hot encoded;
# numeric cols pass through. Kept in one place so validation, training, and prediction agree.
CLF_CAT_FEATURES = ["sub_event_type", "geo_precision"]
CLF_NUM_FEATURES = ["civ_flag", "log_fat"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Assemble the event-level feature frame the classifier expects.

    Columns: sub_event_type, geo_precision, civ_flag, log_fat (= log1p(fatalities)).
    Run prepare_events first so `civ_flag` and `fatalities` exist.
    """
    feat = df[["sub_event_type", "geo_precision", "civ_flag"]].copy()
    feat["log_fat"] = np.log1p(df["fatalities"])
    return feat


def _make_classifier():
    """The one classifier definition: OneHot(categoricals) -> LogisticRegression."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    pre = ColumnTransformer([("oh", OneHotEncoder(handle_unknown="ignore"),
                              CLF_CAT_FEATURES)], remainder="passthrough")
    return Pipeline([("pre", pre), ("lr", LogisticRegression(max_iter=1000))])


def validate_signal(df: pd.DataFrame, label_col: str = "is_road_blocked",
                    n_splits: int = 5, seed: int = 0) -> dict:
    """Cross-validated supervised check that the per-type blockage signal generalises.

    Cross-validates the same classifier `train_classifier` persists, and returns AUC,
    PR-AUC, Brier (with the no-skill baseline = prevalence*(1-prevalence)) plus a
    per-decile calibration table. Requires `civ_flag` and `fatalities` (run
    prepare_events first) and an int `label_col`.
    """
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score

    y = np.asarray(df[label_col].values)
    proba = cross_val_predict(_make_classifier(), build_features(df), y,
                              cv=StratifiedKFold(n_splits, shuffle=True, random_state=seed),
                              method="predict_proba")[:, 1]
    prevalence = float(y.mean())
    dfc = pd.DataFrame({"p": proba, "y": y})
    dfc["bin"] = pd.qcut(dfc["p"], 10, duplicates="drop")
    cal = (dfc.groupby("bin", observed=True)
              .agg(pred=("p", "mean"), obs=("y", "mean")).reset_index(drop=True))
    return {
        "auc": float(roc_auc_score(y, proba)),
        "pr_auc": float(average_precision_score(y, proba)),
        "brier": float(brier_score_loss(y, proba)),
        "brier_baseline": float(prevalence * (1 - prevalence)),
        "prevalence": prevalence,
        "n": int(len(y)),
        "n_positive": int(y.sum()),
        "calibration": cal,   # DataFrame with columns pred, obs (one row per decile)
    }


def train_classifier(df: pd.DataFrame, label_col: str = "is_road_blocked"):
    """Fit the event-level classifier on ALL rows and return the fitted sklearn Pipeline.

    Unlike validate_signal (cross-validated, for metrics only), this refits on the full
    dataset to produce the deployable model that predict_blockage / predict.py consume.
    """
    clf = _make_classifier()
    clf.fit(build_features(df), np.asarray(df[label_col].values))
    return clf


def predict_blockage(classifier, events: pd.DataFrame) -> np.ndarray:
    """P(road blocked) for each event from a fitted classifier (run prepare_events first)."""
    return classifier.predict_proba(build_features(events))[:, 1]

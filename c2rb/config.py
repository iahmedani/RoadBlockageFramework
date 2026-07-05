"""Configuration: kernel classes, tunable parameters, and layered YAML loading."""
from __future__ import annotations
from dataclasses import dataclass, field

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
    (countries/<name>.yaml) holds only what is local: data `paths`, the calibrated
    `p0` / `default_p0`, and optionally a `crs_metric` hint (the metric CRS to pass to
    tools/segment_roads.py --metric-crs; NOT read by training or scoring, which use a
    local equirectangular frame). The returned dict is the merged configuration; pass
    it to config_from_yaml() and read paths[...] from it.
    """
    import yaml
    with open(base_path, encoding="utf-8") as fh:
        base = yaml.safe_load(fh) or {}
    with open(country_path, encoding="utf-8") as fh:
        country = yaml.safe_load(fh) or {}
    return _deep_merge(base, country)

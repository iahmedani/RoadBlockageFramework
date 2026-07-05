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

The core (`geometry`, `model`, `scoring`) has no hard dependency on geopandas; geometry
uses numpy + a local equirectangular projection so it runs anywhere pandas/numpy are
available.

Package layout (import `c2rb` and use the re-exported names below; the submodules are
an internal organization detail):

    geometry.py    local planar projection + haversine
    calibration.py ground-truth labels, Wilson CI, empirical-Bayes P0
    config.py      kernel classes, C2RBConfig, layered YAML loading
    model.py       severity, effective radius, decay kernels, noisy-OR
    scoring.py     score_targets -- spatial noisy-OR aggregation
    classifier.py  prepare_events + the supervised event-level classifier
"""
from .geometry import EARTH_R_KM, latlon_to_local_km, haversine_km
from .calibration import load_labels, wilson_ci, empirical_bayes_p0
from .config import (GAUSS, EXPON, UNIFORM, POINT, C2RBConfig,
                     config_from_yaml, load_config)
from .model import (severity_S, severity_multiplier, effective_radius, kernel,
                    p_block_at_distance, temporal_decay, noisy_or)
from .scoring import score_targets
from .classifier import (prepare_events, CLF_CAT_FEATURES, CLF_NUM_FEATURES,
                         build_features, validate_signal, train_classifier,
                         predict_blockage)

__all__ = [
    "EARTH_R_KM", "latlon_to_local_km", "haversine_km",
    "load_labels", "wilson_ci", "empirical_bayes_p0",
    "GAUSS", "EXPON", "UNIFORM", "POINT", "C2RBConfig",
    "config_from_yaml", "load_config",
    "severity_S", "severity_multiplier", "effective_radius", "kernel",
    "p_block_at_distance", "temporal_decay", "noisy_or",
    "score_targets",
    "prepare_events", "CLF_CAT_FEATURES", "CLF_NUM_FEATURES",
    "build_features", "validate_signal", "train_classifier", "predict_blockage",
]

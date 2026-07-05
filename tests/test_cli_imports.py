"""The import contract: the c2rb public API and the CLI modules stay importable."""
import importlib

import c2rb

PUBLIC_API = [
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


def test_import_c2rb_public_api():
    missing = [name for name in PUBLIC_API if not hasattr(c2rb, name)]
    assert not missing, f"c2rb no longer exports: {missing}"
    assert set(PUBLIC_API) == set(c2rb.__all__)


def test_import_cli_modules():
    # All three are __main__-guarded; importing must be side-effect free.
    # (app.py and build_notebook.py are deliberately excluded: streamlit runs at
    # module top level, and build_notebook writes the .ipynb on import.)
    for mod in ("train", "score", "predict"):
        importlib.import_module(mod)


def test_import_segment_roads():
    importlib.import_module("tools.segment_roads")

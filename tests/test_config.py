"""Layered config: deep-merge, YAML->dataclass coercions, and the train.py rewriter."""
import yaml
import pytest

import c2rb
from c2rb.config import _deep_merge
import train


def test_deep_merge_nested_override_wins():
    base = {"r_phys": {"Armed clash": 15.0, "Attack": 0.5}, "tau_days": 30}
    over = {"r_phys": {"Armed clash": 10.0}, "paths": {"acled_csv": "x.csv"}}
    out = _deep_merge(base, over)
    assert out["r_phys"]["Armed clash"] == 10.0   # overridden
    assert out["r_phys"]["Attack"] == 0.5         # inherited
    assert out["tau_days"] == 30
    assert out["paths"]["acled_csv"] == "x.csv"


def test_deep_merge_does_not_mutate_base():
    base = {"r_phys": {"Armed clash": 15.0}}
    _deep_merge(base, {"r_phys": {"Armed clash": 1.0}})
    assert base["r_phys"]["Armed clash"] == 15.0


def test_config_from_yaml_coercions():
    cfg = c2rb.config_from_yaml({"r_geo": {"1": "2.5"}, "sev_clip": [0.4, 2.0],
                                 "default_p0": 0.01})
    assert cfg.r_geo[1] == 2.5            # keys -> int, values -> float
    assert cfg.sev_clip == (0.4, 2.0)     # list -> tuple
    assert cfg.default_p0 == 0.01
    assert cfg.tau_days == 30.0           # untouched default


def test_load_config_layering(tmp_path):
    base = tmp_path / "base.yaml"
    country = tmp_path / "country.yaml"
    base.write_text("tau_days: 30\nr_phys:\n  A: 1.0\n  B: 2.0\n")
    country.write_text("tau_days: 45\nr_phys:\n  A: 9.0\npaths:\n  acled_csv: x.csv\n")
    merged = c2rb.load_config(str(country), str(base))
    assert merged["tau_days"] == 45
    assert merged["r_phys"] == {"A": 9.0, "B": 2.0}
    assert merged["paths"]["acled_csv"] == "x.csv"


COUNTRY = {
    "paths": {"acled_csv": "data/x.csv", "roads": "data/r.shp", "roads_name_col": "NAME"},
    "crs_metric": "EPSG:32642",
    "tau_days": 45,
    "r_phys": {"Armed clash": 10.0},
    "p0": {"Armed clash": 0.007, "Peaceful protest": 0.06},
    "default_p0": 0.0087,
}


def test_render_country_yaml_preserves_unknown_keys():
    out = train.render_country_yaml(dict(COUNTRY), "testland", 50.0)
    back = yaml.safe_load(out)
    # user physics overrides must survive the rewrite (the localization contract)
    assert back["tau_days"] == 45
    assert back["r_phys"] == {"Armed clash": 10.0}
    # and the templated keys are all present too
    assert back["crs_metric"] == "EPSG:32642"
    assert back["p0"]["Peaceful protest"] == pytest.approx(0.06)
    assert back["default_p0"] == pytest.approx(0.0087)


def test_render_country_yaml_roundtrip_paths_and_order():
    out = train.render_country_yaml(dict(COUNTRY), "testland", 50.0)
    back = yaml.safe_load(out)
    assert back["paths"] == COUNTRY["paths"]      # quoting/spaces survive
    # p0 is emitted highest-first
    p0_lines = [l for l in out.splitlines() if l.startswith('  "')]
    assert p0_lines[0].startswith('  "Peaceful protest"')


def test_render_country_yaml_no_extras_emits_no_override_block():
    country = {k: v for k, v in COUNTRY.items() if k not in ("tau_days", "r_phys")}
    out = train.render_country_yaml(country, "testland", 50.0)
    assert "Country-level overrides" not in out

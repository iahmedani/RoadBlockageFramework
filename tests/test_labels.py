"""Ground-truth label parsing and event preparation."""
import pandas as pd
import pytest

import c2rb


def test_load_labels_yes_no_case_whitespace():
    df = pd.DataFrame({"is_road_blocked": ["yes", " YES ", "no", "", None, "maybe"]})
    out = c2rb.load_labels(df)
    assert list(out["is_road_blocked"]) == [1, 1, 0, 0, 0, 0]


def test_load_labels_missing_blocked_col_raises():
    with pytest.raises(KeyError):
        c2rb.load_labels(pd.DataFrame({"other": ["yes"]}))


def test_load_labels_affected_optional():
    df = pd.DataFrame({"is_road_blocked": ["yes"], "is_road_affected": ["no"]})
    out = c2rb.load_labels(df)
    assert set(out.columns) == {"is_road_blocked", "is_road_affected"}
    out2 = c2rb.load_labels(df[["is_road_blocked"]])
    assert list(out2.columns) == ["is_road_blocked"]


def test_prepare_events_derives_civ_flag_and_int_fatalities():
    df = pd.DataFrame({
        "event_date": ["2026-01-01", "2026-02-03"],
        "fatalities": ["3", None],
        "civilian_targeting": ["Civilian targeting", ""],
    })
    out = c2rb.prepare_events(df)
    assert out["event_date"].dtype.kind == "M"           # datetime
    assert list(out["fatalities"]) == [3, 0]
    assert list(out["civ_flag"]) == [1, 0]

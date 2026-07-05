"""Empirical-Bayes P0 calibration and interval math."""
import numpy as np
import pandas as pd
import pytest

import c2rb


def _toy():
    # big group: 10% raw rate over 1000; tiny group: 100% raw rate over 2 events
    label = pd.Series([1] * 100 + [0] * 900 + [1, 1])
    group = pd.Series(["big"] * 1000 + ["tiny"] * 2)
    return label, group


def test_empirical_bayes_shrinks_small_groups_toward_global():
    label, group = _toy()
    tab = c2rb.empirical_bayes_p0(label, group, prior_strength=50)
    glob = label.mean()
    # tiny group's raw 1.0 must be pulled hard toward the global rate...
    assert tab.loc["tiny", "p0_shrunk"] < 0.2
    assert tab.loc["tiny", "p0_shrunk"] > glob
    # ...while the well-observed group barely moves
    assert tab.loc["big", "p0_shrunk"] == pytest.approx(0.1, abs=0.005)


def test_empirical_bayes_posterior_mean_formula():
    # P0_hat = (k + a0) / (n + a0 + b0),  a0 = glob*m, b0 = (1-glob)*m  (methodology 3.2)
    label, group = _toy()
    m = 50.0
    tab = c2rb.empirical_bayes_p0(label, group, prior_strength=m)
    glob = label.mean()
    a0, b0 = glob * m, (1 - glob) * m
    for g in ("big", "tiny"):
        k, n = tab.loc[g, "pos"], tab.loc[g, "n"]
        assert tab.loc[g, "p0_shrunk"] == pytest.approx((k + a0) / (n + a0 + b0))


def test_empirical_bayes_sorted_descending_and_intervals_bracket():
    label, group = _toy()
    tab = c2rb.empirical_bayes_p0(label, group, prior_strength=50)
    assert list(tab["p0_shrunk"]) == sorted(tab["p0_shrunk"], reverse=True)
    # Beta posterior CrI must bracket the shrunk estimate (it's the posterior mean)
    assert ((tab["post_lo"] <= tab["p0_shrunk"]) & (tab["p0_shrunk"] <= tab["post_hi"])).all()


def test_wilson_ci_zero_counts_stable():
    lo, hi = c2rb.wilson_ci(np.array([0]), np.array([176]))
    assert 0.0 <= lo[0] <= hi[0] <= 1.0
    assert hi[0] < 0.05  # 0/176 has a tight upper bound

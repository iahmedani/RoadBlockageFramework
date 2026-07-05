"""Core model math: noisy-OR, kernels, effective radius, severity, temporal decay."""
import numpy as np
import pytest

import c2rb


@pytest.fixture
def cfg():
    return c2rb.C2RBConfig()


# ---- noisy-OR --------------------------------------------------------------------------
def test_noisy_or_matches_complement_product():
    probs = [0.1, 0.2, 0.5]
    assert c2rb.noisy_or(probs) == pytest.approx(1 - 0.9 * 0.8 * 0.5)


def test_noisy_or_single_prob_identity():
    assert c2rb.noisy_or([0.37]) == pytest.approx(0.37)


def test_noisy_or_clips_out_of_range():
    # inputs outside [0,1] are clipped, so the result stays a probability
    assert c2rb.noisy_or([1.5, -0.2]) == pytest.approx(1.0)
    assert 0.0 <= c2rb.noisy_or([-0.5]) <= 1.0


# ---- kernels ---------------------------------------------------------------------------
def test_kernel_gaussian_peak_and_halfwidth():
    r = 4.0
    assert c2rb.kernel(0.0, r, c2rb.GAUSS) == pytest.approx(1.0)
    sigma = r / 2.0  # K(sigma) = exp(-1/2)
    assert c2rb.kernel(sigma, r, c2rb.GAUSS) == pytest.approx(np.exp(-0.5))


def test_kernel_exponential_decay():
    r = 6.0
    lam = r / 3.0  # K(lam) = exp(-1)
    assert c2rb.kernel(lam, r, c2rb.EXPON) == pytest.approx(np.exp(-1))


def test_kernel_uniform_cutoff():
    assert c2rb.kernel(2.99, 3.0, c2rb.UNIFORM) == 1.0
    assert c2rb.kernel(3.01, 3.0, c2rb.UNIFORM) == 0.0


def test_kernel_point_min_radius_0p3():
    # POINT keeps a 300 m floor even when r_eff is tiny
    assert c2rb.kernel(0.25, 0.01, c2rb.POINT) == 1.0
    assert c2rb.kernel(0.35, 0.01, c2rb.POINT) == 0.0


def test_kernel_unknown_kind_raises():
    with pytest.raises(ValueError):
        c2rb.kernel(1.0, 1.0, "triangular")


# ---- effective radius ------------------------------------------------------------------
def test_effective_radius_quadrature(cfg):
    # neutral severity (fatalities == sev_ref, no civ flag) -> multiplier exactly 1
    r = c2rb.effective_radius(["Armed clash"], [1], [cfg.sev_ref_fatalities], [0], cfg)
    expected = np.sqrt(cfg.r_phys["Armed clash"] ** 2 + cfg.r_geo[1] ** 2)
    assert r[0] == pytest.approx(expected)


def test_effective_radius_unknown_type_defaults(cfg):
    # unseen type falls back to r_phys = 2.0; unseen geo code to r_geo = 5.0
    r = c2rb.effective_radius(["Alien invasion"], [9], [cfg.sev_ref_fatalities], [0], cfg)
    assert r[0] == pytest.approx(np.sqrt(2.0 ** 2 + 5.0 ** 2))


# ---- severity multiplier ---------------------------------------------------------------
def test_severity_multiplier_clip_bounds(cfg):
    hi = c2rb.severity_multiplier([100000], [0], cfg)
    assert hi[0] == pytest.approx(cfg.sev_clip[1])
    lo_cfg = c2rb.C2RBConfig(kappa=5.0)  # strong negative stretch at 0 fatalities
    lo = c2rb.severity_multiplier([0], [0], lo_cfg)
    assert lo[0] == pytest.approx(lo_cfg.sev_clip[0])


def test_severity_civ_bump_applied_inside_clip(cfg):
    # Locked semantics (methodology Eq. 3): clip((1 + k(S/Sref - 1)) * (1 + civ), 0.5, 3.0).
    # A max-severity civilian-targeted event must cap at 3.0, NOT 3.0 * 1.3.
    capped = c2rb.severity_multiplier([100000], [1], cfg)
    assert capped[0] == pytest.approx(cfg.sev_clip[1])
    # Mid-range: the bump multiplies the pre-clip value exactly.
    base = c2rb.severity_multiplier([3], [0], cfg)[0]
    bumped = c2rb.severity_multiplier([3], [1], cfg)[0]
    assert bumped == pytest.approx(base * (1 + cfg.civ_bump))


def test_temporal_decay_half_life(cfg):
    assert c2rb.temporal_decay(cfg.tau_days, cfg) == pytest.approx(0.5)
    assert c2rb.temporal_decay(0, cfg) == pytest.approx(1.0)
    assert c2rb.temporal_decay(2 * cfg.tau_days, cfg) == pytest.approx(0.25)

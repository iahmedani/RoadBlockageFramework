"""The parametric model: effective radius, severity, decay kernels, noisy-OR."""
from __future__ import annotations
import numpy as np
import pandas as pd

from .config import C2RBConfig, GAUSS, EXPON, UNIFORM, POINT


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

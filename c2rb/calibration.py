"""Ground-truth labels and P0 calibration (Beta-Binomial empirical-Bayes shrinkage)."""
from __future__ import annotations
import numpy as np
import pandas as pd


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

    Raw rates are unstable for small groups (e.g. Suicide bomb n=289 -> 0.000). We shrink each
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

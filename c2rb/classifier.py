"""Event preparation + the supervised event-level classifier (shared by CLI + notebook)."""
from __future__ import annotations
import numpy as np
import pandas as pd


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

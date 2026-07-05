#!/usr/bin/env python
"""
train.py -- Calibrate a C2RB road-blockage model for one country and emit artifacts.

"Training" here produces TWO artifacts, one per question (see CLAUDE.md "two models,
two questions"):

  1. The parametric P0(sub_event_type) = P(is_road_blocked | type), estimated from the
     country's ground-truth labels with Beta-Binomial empirical-Bayes shrinkage and written
     back into the country config (countries/<name>.yaml). This drives the SPATIAL scorer
     (score.py: which roads are blocked) and stays the interpretable core.
  2. A supervised logistic-regression classifier, cross-validated for the metrics
     (AUC / PR-AUC / Brier) and then refit on all rows and persisted into model.joblib --
     the sanctioned EVENT-LEVEL model consumed by predict.py and app.py.

Usage
-----
    python train.py --config countries/afghanistan.yaml
    python train.py --config countries/<name>.yaml --base params.base.yaml \
        --prior-strength 50 --out artifacts/<name>/ [--no-write-p0] [--no-validate]

Outputs (under --out, default artifacts/<config-stem>/)
    model.joblib        deployable event-level model (classifier + parametric P0); predict.py
    metrics.json        validation metrics + the calibrated P0 table
    model_card.md       human-readable summary of the trained model
    p0_calibration.png  P0 by type with Beta posterior 95% credible intervals
    calibration_curve.png  (only with validation) predicted vs observed, 5-fold CV
and (unless --no-write-p0) the updated `p0` / `default_p0` block in the country config.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import yaml

import matplotlib
matplotlib.use("Agg")  # headless: write PNGs without a display
import matplotlib.pyplot as plt

import c2rb

# Minimum positive labels below which a per-type calibration is too thin to trust.
MIN_POSITIVES_WARN = 30


# ----------------------------------------------------------------------------------------
# Input validation -- how strict to be on a localized dataset.
# ----------------------------------------------------------------------------------------
def check_inputs(df: pd.DataFrame, blocked_col: str) -> int:
    """Fail fast on a malformed export; warn (don't fail) on a thin positive class.

    Returns the number of positive (blocked) labels. Raises SystemExit on a hard problem
    (missing required columns or zero positives -- nothing to calibrate). This is the
    localization gatekeeper: a new country's CSV must carry the ACLED scoring fields plus
    the ground-truth blocked label before training can mean anything.
    """
    required = ["sub_event_type", "geo_precision", "latitude", "longitude",
                "event_date", "fatalities", blocked_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: input CSV is missing required column(s): {missing}\n"
                 f"       a localized export needs the ACLED scoring fields + the "
                 f"ground-truth '{blocked_col}' label. See docs/COUNTRY_GUIDE.md.")
    n_pos = int(c2rb.load_labels(df, blocked_col)["is_road_blocked"].sum())
    if n_pos == 0:
        sys.exit(f"ERROR: no positive '{blocked_col}' labels found -- nothing to "
                 f"calibrate. Classify some events as blocked first.")
    if n_pos < MIN_POSITIVES_WARN:
        print(f"WARNING: only {n_pos} blocked events (< {MIN_POSITIVES_WARN}). Per-type P0 "
              f"will lean heavily on the shrinkage prior; treat results as provisional.")
    return n_pos


# ----------------------------------------------------------------------------------------
# Render the country config (paths + crs + calibrated P0) -- train.py owns this format.
# ----------------------------------------------------------------------------------------
def _q(s) -> str:
    """Double-quote a YAML scalar safely."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# Keys the template below serializes itself; everything else in the country file is a
# user-added override (e.g. r_phys, tau_days) and must be preserved verbatim on rewrite.
TEMPLATED_KEYS = {"paths", "crs_metric", "p0", "default_p0"}


def render_country_yaml(country: dict, name: str, prior_strength: float) -> str:
    """Serialize the country override file with the calibrated P0 block, stable ordering."""
    paths = country.get("paths", {})
    path_order = ["acled_csv", "label_blocked_col", "label_affected_col",
                  "roads", "roads_name_col", "admin"]
    keys = path_order + [k for k in paths if k not in path_order]
    p0 = country.get("p0", {})
    p0_sorted = sorted(p0.items(), key=lambda kv: kv[1], reverse=True)

    L = [
        "# " + "=" * 85,
        f"# countries/{name}.yaml -- COUNTRY override for the c2rb framework.",
        "#",
        "# Merged ON TOP of params.base.yaml by c2rb.load_config(). Holds ONLY what is local:",
        "# data paths, the calibrated blockage propensity P0, an optional crs_metric hint for",
        "# GIS preprocessing, and any country-level physics overrides (preserved on retrain).",
        "#",
        f"# The p0 / default_p0 block below was WRITTEN BY train.py (prior_strength="
        f"{prior_strength:g}), calibrated on this country's ground-truth 'is_road_blocked'",
        "# label. Retrain:  python train.py --config countries/" + name + ".yaml",
        "# " + "=" * 85,
        "",
        "# ---- Data / geometry (LOCAL) " + "-" * 53,
        "paths:",
    ]
    for k in keys:
        if k in paths and paths[k] is not None:
            L.append(f"  {k}: {_q(paths[k])}")
    if country.get("crs_metric"):
        L.append(f"crs_metric: {_q(country['crs_metric'])}"
                 "   # GIS hint (tools/segment_roads.py --metric-crs); not read by the model")

    # Preserve any country-level physics overrides (r_phys, tau_days, ...) verbatim --
    # the localization guide tells users to put them here, so a retrain must not eat them.
    extras = {k: v for k, v in country.items() if k not in TEMPLATED_KEYS}
    if extras:
        L += ["", "# ---- Country-level overrides of params.base.yaml (preserved by train.py) " + "-" * 9]
        L.append(yaml.safe_dump(extras, sort_keys=False, default_flow_style=False,
                                allow_unicode=True).rstrip())

    L += [
        "",
        "# ---- Peak blockage propensity P0 by sub_event_type  (CALIBRATED) " + "-" * 18,
        "# P0(s) = P(is_road_blocked = yes | type) with Beta-Binomial empirical-Bayes shrinkage",
        "# toward the global blocked rate. Validated by logistic regression (see metrics.json).",
        "p0:",
    ]
    for k, v in p0_sorted:
        L.append(f"  {_q(k)}: {float(v):.4f}")
    L.append(f"default_p0: {float(country.get('default_p0', 0.05)):.4f}"
             "        # fallback for any unseen sub_event_type (= global blocked rate)")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------------------
def plot_p0(p0tab: pd.DataFrame, path: str, top: int = 16) -> None:
    show = p0tab.head(top)
    fig, ax = plt.subplots(figsize=(9, 7))
    y = np.arange(len(show))
    ax.barh(y, show["p0_shrunk"], color="#cc4444")
    ax.errorbar(show["p0_shrunk"], y,
                xerr=[show["p0_shrunk"] - show["post_lo"], show["post_hi"] - show["p0_shrunk"]],
                fmt="none", ecolor="0.3", capsize=3)  # Beta posterior 95% credible interval
    ax.set_yticks(y); ax.set_yticklabels(show.index, fontsize=9); ax.invert_yaxis()
    ax.set_xlabel("P0 = P(road blocked | type)")
    ax.set_title("Calibrated blockage propensity by sub_event_type")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def plot_calibration(cal: pd.DataFrame, path: str) -> None:
    hi = float(max(cal["pred"].max(), cal["obs"].max()))
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, hi], [0, hi], "k--", lw=1, label="perfect")
    ax.plot(cal["pred"], cal["obs"], "o-", color="#2266cc", label="model")
    ax.set_xlabel("predicted P(block)"); ax.set_ylabel("observed rate")
    ax.set_title("Calibration curve (5-fold CV)"); ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------------------
def write_model_card(path: str, name: str, meta: dict, p0tab: pd.DataFrame,
                     val: dict | None) -> None:
    lines = [
        f"# Model card -- C2RB road-blockage model: **{name}**",
        "",
        f"- **Trained:** {meta['trained_at']}",
        f"- **Data:** `{meta['acled_csv']}` -- {meta['events']:,} events",
        f"- **Calibration target:** `{meta['blocked_col']}` "
        f"({meta['n_positive']:,} blocked, {100 * meta['blocked_rate']:.2f}% of events)",
        f"- **Estimator:** per-`sub_event_type` Beta-Binomial empirical-Bayes shrinkage "
        f"(prior_strength={meta['prior_strength']:g}) toward the global rate",
        "",
        "## Validation (5-fold cross-validated logistic regression)",
        "",
    ]
    if val is not None:
        passes = "PASS" if val["brier"] < val["brier_baseline"] else "CHECK"
        lines += [
            f"- **AUC** = {val['auc']:.3f}  (discrimination; 0.5 = random)",
            f"- **PR-AUC** = {val['pr_auc']:.4f}  (prevalence {val['prevalence']:.4f})",
            f"- **Brier** = {val['brier']:.5f}  vs no-skill baseline "
            f"{val['brier_baseline']:.5f}  -> **{passes}**",
            "",
            "Validation cross-validates the same classifier that is then refit on all rows "
            "and persisted as `model.joblib` (the event-level model used by predict.py).",
            "",
        ]
    else:
        lines += ["_Validation skipped (--no-validate)._", ""]
    lines += [
        "## Calibrated P0 (peak blockage propensity, highest first)",
        "",
        "| sub_event_type | n | blocked | raw | **P0 (shrunk)** | 95% CrI |",
        "|---|--:|--:|--:|--:|---|",
    ]
    for typ, r in p0tab.iterrows():
        lines.append(
            f"| {typ} | {int(r['n'])} | {int(r['pos'])} | {r['p0_raw']:.4f} | "
            f"**{r['p0_shrunk']:.4f}** | [{r['post_lo']:.4f}, {r['post_hi']:.4f}] |")
    lines += ["", f"_Fallback `default_p0` for unseen types = {meta['blocked_rate']:.4f}._", ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ----------------------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate a C2RB model for one country.")
    ap.add_argument("--config", required=True, help="country config, e.g. countries/afghanistan.yaml")
    ap.add_argument("--base", default="params.base.yaml", help="universal base params")
    ap.add_argument("--prior-strength", type=float, default=50.0,
                    help="Beta-Binomial pseudo-count (higher = more shrinkage)")
    ap.add_argument("--out", default=None, help="artifact dir (default artifacts/<config-stem>/)")
    ap.add_argument("--no-write-p0", action="store_true",
                    help="compute P0 but do NOT write it back into the country config")
    ap.add_argument("--no-validate", action="store_true", help="skip the logistic-regression CV")
    ap.add_argument("--no-save-model", action="store_true",
                    help="skip saving the deployable event-level classifier (model.joblib)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.config))[0]
    out = args.out or os.path.join("artifacts", name)
    os.makedirs(out, exist_ok=True)

    cfg_raw = c2rb.load_config(args.config, args.base)
    blocked_col = cfg_raw["paths"].get("label_blocked_col", "is_road_blocked")
    affected_col = cfg_raw["paths"].get("label_affected_col", "is_road_affected")

    df = pd.read_csv(cfg_raw["paths"]["acled_csv"], encoding="utf-8-sig", low_memory=False)
    n_pos = check_inputs(df, blocked_col)  # gatekeeper first: friendly error on a bad export
    df = c2rb.prepare_events(df)

    # Attach parsed 0/1 labels (assign back -- do NOT concat; that dupes columns).
    labels = c2rb.load_labels(df, blocked_col, affected_col)
    for col in labels.columns:
        df[col] = labels[col].values

    blocked_rate = float(df["is_road_blocked"].mean())
    print(f"[{name}] {len(df):,} events | blocked {n_pos:,} ({100 * blocked_rate:.2f}%)")

    # --- Calibrate (THIS is the model) --------------------------------------------------
    p0tab = c2rb.empirical_bayes_p0(df["is_road_blocked"], df["sub_event_type"],
                                    prior_strength=args.prior_strength)
    p0_dict = {typ: round(float(v), 4) for typ, v in p0tab["p0_shrunk"].items()}
    print(f"[{name}] calibrated P0 for {len(p0_dict)} sub_event_types "
          f"(top: {p0tab.index[0]} = {p0tab['p0_shrunk'].iloc[0]:.4f})")

    # Load the country file alone (not the merged dict) so we rewrite only its keys.
    with open(args.config, encoding="utf-8") as fh:
        country = yaml.safe_load(fh) or {}
    country["p0"] = p0_dict
    country["default_p0"] = round(blocked_rate, 4)
    if not args.no_write_p0:
        with open(args.config, "w", encoding="utf-8") as fh:
            fh.write(render_country_yaml(country, name, args.prior_strength))
        print(f"[{name}] wrote calibrated P0 -> {args.config}")

    # --- Validate (signal check only) ---------------------------------------------------
    val = None
    if not args.no_validate:
        val = c2rb.validate_signal(df, "is_road_blocked", n_splits=5, seed=args.seed)
        plot_calibration(val["calibration"], os.path.join(out, "calibration_curve.png"))
        print(f"[{name}] AUC={val['auc']:.3f}  PR-AUC={val['pr_auc']:.4f}  "
              f"Brier={val['brier']:.5f} (baseline {val['brier_baseline']:.5f})")

    plot_p0(p0tab, os.path.join(out, "p0_calibration.png"))

    # --- Persist the deployable event-level model (classifier + parametric P0) ----------
    # The classifier answers "will THIS event block a road?" from its attributes; the
    # bundled P0/config lets a consumer also run the parametric spatial scorer. predict.py
    # loads this bundle. (Refit on ALL rows -- validation above used CV folds only.)
    if not args.no_save_model:
        classifier = c2rb.train_classifier(df, "is_road_blocked")
        bundle = {
            "format": "c2rb-model-v1",
            "country": name,
            "trained_at": _dt.date.today().isoformat(),
            "label_col": "is_road_blocked",
            "features": {"categorical": c2rb.CLF_CAT_FEATURES, "numeric": c2rb.CLF_NUM_FEATURES},
            "classifier": classifier,                  # fitted sklearn Pipeline (OneHot + LR)
            "p0": p0_dict,                             # parametric model (for spatial scoring)
            "default_p0": round(blocked_rate, 4),
            "config": args.config,
            "metrics": ({k: v for k, v in val.items() if k != "calibration"} if val else None),
        }
        joblib.dump(bundle, os.path.join(out, "model.joblib"))
        print(f"[{name}] saved deployable model -> {os.path.join(out, 'model.joblib')}")

    meta = {
        "country": name,
        "trained_at": _dt.date.today().isoformat(),
        "acled_csv": cfg_raw["paths"]["acled_csv"],
        "blocked_col": blocked_col,
        "events": int(len(df)),
        "n_positive": n_pos,
        "blocked_rate": blocked_rate,
        "prior_strength": args.prior_strength,
    }
    metrics = {**meta, "validation": (
        {k: v for k, v in val.items() if k != "calibration"} if val else None)}
    metrics["validation_calibration"] = (
        val["calibration"].to_dict("records") if val else None)
    metrics["p0"] = p0_dict
    with open(os.path.join(out, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    write_model_card(os.path.join(out, "model_card.md"), name, meta, p0tab, val)
    print(f"[{name}] artifacts -> {out}/  (metrics.json, model_card.md, *.png)")


if __name__ == "__main__":
    main()

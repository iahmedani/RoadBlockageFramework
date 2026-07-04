#!/usr/bin/env python
"""
predict.py -- Predict road-blockage probability for a conflict event from a saved model.

Loads the deployable bundle written by train.py (artifacts/<country>/model.joblib) and
answers "if this event occurs, how likely is it to block a road?" using the persisted
event-level classifier. Works on a single event (CLI flags) or a batch (CSV).

This is the EVENT-LEVEL predictor (one probability per event, from the event's attributes).
For the spatial question -- WHICH roads near an event are blocked -- use score.py, which
runs the parametric scorer over the road network.

Usage
-----
    # single event
    python predict.py --model artifacts/afghanistan/model.joblib \
        --sub-event-type "Armed clash" --geo-precision 1 --fatalities 3

    # or point at a country and let it find artifacts/<country>/model.joblib
    python predict.py --config countries/afghanistan.yaml \
        --sub-event-type "Peaceful protest" --geo-precision 2 --civilian-targeting

    # batch: a CSV of events in, the same CSV + a p_block column out
    python predict.py --config countries/afghanistan.yaml \
        --events new_events.csv --out scored_events.csv [--threshold 0.05]
"""
from __future__ import annotations
import argparse
import os
import sys

import joblib
import pandas as pd

import c2rb


def resolve_model_path(args) -> str:
    if args.model:
        return args.model
    if args.config:
        stem = os.path.splitext(os.path.basename(args.config))[0]
        return os.path.join("artifacts", stem, "model.joblib")
    sys.exit("ERROR: pass --model <path> or --config countries/<name>.yaml")


def normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the columns the classifier reads exist: sub_event_type, geo_precision,
    fatalities, civ_flag. Derives civ_flag from civilian_targeting when absent."""
    out = df.copy()
    if "fatalities" not in out:
        out["fatalities"] = 0
    out["fatalities"] = pd.to_numeric(out["fatalities"], errors="coerce").fillna(0).astype(int)
    if "civ_flag" not in out:
        civ = out.get("civilian_targeting", pd.Series("", index=out.index))
        out["civ_flag"] = (civ.fillna("").astype(str).str.strip() != "").astype(int)
    missing = [c for c in ["sub_event_type", "geo_precision"] if c not in out]
    if missing:
        sys.exit(f"ERROR: events are missing required column(s): {missing}")
    out["geo_precision"] = pd.to_numeric(out["geo_precision"], errors="coerce").fillna(1).astype(int)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Predict road-blockage probability for an event.")
    ap.add_argument("--model", default=None, help="path to model.joblib")
    ap.add_argument("--config", default=None, help="country config (to locate the model)")
    # single-event inputs
    ap.add_argument("--sub-event-type")
    ap.add_argument("--geo-precision", type=int, default=1)
    ap.add_argument("--fatalities", type=int, default=0)
    ap.add_argument("--civilian-targeting", action="store_true")
    # batch inputs
    ap.add_argument("--events", help="CSV of events to score")
    ap.add_argument("--out", default=None, help="output CSV path (batch mode)")
    ap.add_argument("--threshold", type=float, default=None,
                    help="also emit a 0/1 prediction at this probability cut-off")
    args = ap.parse_args()

    model_path = resolve_model_path(args)
    if not os.path.exists(model_path):
        sys.exit(f"ERROR: model not found: {model_path}\n       train one first: "
                 f"python train.py --config countries/<name>.yaml")
    bundle = joblib.load(model_path)
    clf = bundle["classifier"]
    print(f"model: {bundle.get('country','?')} (trained {bundle.get('trained_at','?')}, "
          f"format {bundle.get('format','?')})")

    if args.events:
        df = pd.read_csv(args.events, encoding="utf-8-sig", low_memory=False)
        events = normalize_events(df)
        df["p_block"] = c2rb.predict_blockage(clf, events)
        if args.threshold is not None:
            df["p_block_flag"] = (df["p_block"] >= args.threshold).astype(int)
        out = args.out or "predictions.csv"
        df.to_csv(out, index=False)
        print(f"scored {len(df):,} events -> {out}  "
              f"(mean P={df['p_block'].mean():.4f}, max={df['p_block'].max():.4f})")
    else:
        if not args.sub_event_type:
            sys.exit("ERROR: provide --sub-event-type (single event) or --events CSV (batch).")
        ev = normalize_events(pd.DataFrame([{
            "sub_event_type": args.sub_event_type,
            "geo_precision": args.geo_precision,
            "fatalities": args.fatalities,
            "civ_flag": int(args.civilian_targeting),
        }]))
        p = float(c2rb.predict_blockage(clf, ev)[0])
        print(f"\nevent: {args.sub_event_type} | geo_precision={args.geo_precision} | "
              f"fatalities={args.fatalities} | civilian_targeting={args.civilian_targeting}")
        print(f"P(road blocked by this event) = {p:.4f}")
        if args.threshold is not None:
            print(f"prediction @ {args.threshold}: "
                  f"{'BLOCKED' if p >= args.threshold else 'not blocked'}")


if __name__ == "__main__":
    main()

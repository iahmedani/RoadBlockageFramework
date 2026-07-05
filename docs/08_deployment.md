# 08 — Deployment: the Streamlit app

```bash
streamlit run app.py        # from the repo root; opens http://localhost:8501
```

`app.py` is a point-and-click front end over the same two models the CLI uses.

## Country auto-discovery

On startup the app scans `countries/*.yaml` and lists every country whose
`artifacts/<stem>/model.joblib` exists. **Adding a country to the app = training it** — run
`python train.py --config countries/<name>.yaml` and refresh the browser. No app code changes.

## The two tabs

- **▶ Predict an event** — pick a `sub_event_type`, `geo_precision`, fatalities, and the
  civilian-targeting flag; the app shows `P(road blocked)` from the persisted classifier and a
  ranked bar chart comparing every event type under the same settings. This is `predict.py`
  interactively.
- **🗺️ Which roads near a location** — a folium map of the road network; **click anywhere**
  to drop a hypothetical event and the nearby segments recolor by blockage probability
  (`c2rb.score_targets` under the hood). This is `score.py`'s spatial question for a
  single what-if event.

## Operational notes

- **Run from the repo root** — the app resolves `countries/`, `artifacts/`, and the road layer
  through the same CWD-relative paths as the CLI.
- The model bundle and the road network are cached with `st.cache_resource`, so the first map
  load is the slow one (~seconds for 28k segments); use the sidebar/rerun rather than
  restarting the process.
- To serve beyond localhost: `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`
  behind whatever auth/proxy your deployment requires. The app is read-only over the artifacts —
  it never retrains or writes.
- Long-running deployments should retrain (`train.py`) on a schedule as new labeled data
  arrives, then simply restart or invalidate the cache; the app picks up the new
  `model.joblib` on reload.

Next: [09_troubleshooting.md](09_troubleshooting.md).

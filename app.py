#!/usr/bin/env python
"""
app.py -- Streamlit playground for the C2RB road-blockage model.

Pick a conflict event type (and tweak its precision / fatalities / civilian-targeting) and see
the predicted probability it blocks a road, ranked against every other event type. An optional
"which roads" mode drops a hypothetical event on the map and scores the nearby road network.

Run:
    streamlit run app.py
Requires a trained model -- run `python train.py --config countries/<name>.yaml` first so
`artifacts/<name>/model.joblib` exists.
"""
from __future__ import annotations
import glob
import os

import joblib
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import folium
import branca.colormap as cm
from streamlit_folium import st_folium

import c2rb

st.set_page_config(page_title="C2RB — Road-Blockage Predictor", page_icon="🛣️", layout="wide")


# --------------------------------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------------------------------
def available_countries() -> dict:
    """{country_name: config_path} for every country that has a trained model.joblib."""
    out = {}
    for cfg in sorted(glob.glob("countries/*.yaml")):
        stem = os.path.splitext(os.path.basename(cfg))[0]
        if os.path.exists(os.path.join("artifacts", stem, "model.joblib")):
            out[stem] = cfg
    return out


@st.cache_resource
def load_bundle(model_path: str):
    return joblib.load(model_path)


@st.cache_data
def load_cfg_raw(config_path: str) -> dict:
    return c2rb.load_config(config_path)


@st.cache_resource(show_spinner="Loading road network…")
def load_roads(roads_path: str, name_col: str):
    """Return (simplified roads GeoDataFrame with a `road` name column, midpoints DataFrame).

    Geometry is lightly simplified so the whole network ships to the browser quickly; the
    midpoints are what the spatial scorer measures distance to. Row order is shared, so a
    p_block array scored on the midpoints aligns 1:1 with the GeoDataFrame.
    """
    import geopandas as gpd
    roads = gpd.read_file(roads_path).to_crs(4326)
    roads["road"] = roads[name_col].astype(str) if name_col in roads.columns else "—"
    roads["geometry"] = roads.geometry.simplify(0.001)
    mids = roads.geometry.representative_point()
    midpts = pd.DataFrame({"latitude": mids.y.values, "longitude": mids.x.values,
                           "road": roads["road"].values})
    return roads[["road", "geometry"]].reset_index(drop=True), midpts


def colored_network(roads_gdf, p_block, thr: float):
    """Attach per-segment colour/weight (grey = unaffected, ramp = model risk) and return
    (geojson_str, branca colormap or None)."""
    pb = np.asarray(p_block, dtype=float)
    aff = pb > max(thr, 1e-3)
    g = roads_gdf.copy()
    colors = np.full(len(pb), "#cfcfcf", dtype=object)   # all roads visible, grey by default
    cmap = None
    if aff.any():
        vmax = float(pb[aff].max()); vmin = max(thr, 1e-3)
        cmap = cm.LinearColormap(["#fed976", "#fd8d3c", "#f03b20", "#bd0026"],
                                 vmin=vmin, vmax=max(vmax, vmin + 1e-6), caption="P(road blocked)")
        for i in np.where(aff)[0]:
            colors[i] = cmap(float(pb[i]))
    g["color"] = colors
    g["weight"] = np.where(aff, 3.0, 0.6)
    g["op"] = np.where(aff, 0.95, 0.35)
    g["p_block"] = pb
    return g.to_json(), cmap


def predict_types(bundle, types, geo_prec: int, fatalities: int, civ: int) -> pd.DataFrame:
    """P(road blocked) for every event type under the chosen attributes."""
    ev = pd.DataFrame({
        "sub_event_type": list(types),
        "geo_precision": geo_prec,
        "fatalities": fatalities,
        "civ_flag": civ,
    })
    p = c2rb.predict_blockage(bundle["classifier"], ev)
    return pd.DataFrame({"event_type": list(types), "p_block": p}).sort_values(
        "p_block", ascending=False).reset_index(drop=True)


def score_event_on_roads(cfg_raw: dict, mids: pd.DataFrame, lat: float, lon: float,
                         etype: str, fatalities: int) -> pd.DataFrame:
    """Score every road-segment midpoint against one hypothetical event (spatial model)."""
    cfg = c2rb.config_from_yaml(cfg_raw)
    event = pd.DataFrame([{
        "latitude": lat, "longitude": lon, "sub_event_type": etype,
        "geo_precision": 1, "fatalities": fatalities, "civ_flag": 0,
        "event_date": pd.Timestamp("2025-01-01"),
    }])
    p = c2rb.score_targets(event, mids, cfg, as_of_date="2025-01-01")
    return mids.assign(p_block=p)


# --------------------------------------------------------------------------------------
# Sidebar — country + model info
# --------------------------------------------------------------------------------------
countries = available_countries()
if not countries:
    st.error("No trained model found. Run `python train.py --config countries/afghanistan.yaml` "
             "first, then reload.")
    st.stop()

st.sidebar.header("Model")
country = st.sidebar.selectbox("Country", list(countries), index=0)
cfg_path = countries[country]
cfg_raw = load_cfg_raw(cfg_path)
bundle = load_bundle(os.path.join("artifacts", country, "model.joblib"))

m = bundle.get("metrics") or {}
st.sidebar.caption(f"Trained: {bundle.get('trained_at', '?')}")
if m:
    st.sidebar.metric("Validation AUC", f"{m.get('auc', float('nan')):.3f}")
    st.sidebar.caption(f"Brier {m.get('brier', float('nan')):.5f} "
                       f"(baseline {m.get('brier_baseline', float('nan')):.5f}) · "
                       f"{m.get('n_positive', 0)} blocked / {m.get('n', 0):,} events")
st.sidebar.caption("The model answers *will this event block a road?* — event-level, from event "
                   "attributes. The map tab answers *which roads* near a location.")

# Event types: the full calibrated set, sorted by the parametric P0 for a stable order.
p0 = cfg_raw.get("p0", {})
EVENT_TYPES = sorted(p0, key=lambda k: p0[k], reverse=True) or sorted(cfg_raw.get("r_phys", {}))


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
st.title("🛣️ Conflict → Road-Blockage Predictor")
st.caption(f"Interactive test bench for the **{country}** model. Pick an event and see how "
           "likely it is to block a road.")

tab_event, tab_map = st.tabs(["▶ Predict an event", "🗺️ Which roads near a location"])

with tab_event:
    left, right = st.columns([1, 1.3], gap="large")
    with left:
        st.subheader("Event")
        etype = st.selectbox("Event type (sub_event_type)", EVENT_TYPES, index=0)
        geo = st.radio("Location precision", [1, 2, 3], horizontal=True,
                       format_func=lambda g: {1: "1 · exact town", 2: "2 · near town",
                                              3: "3 · region"}[g])
        fat = st.slider("Fatalities", 0, 50, 0)
        civ = st.checkbox("Civilian targeting", value=False)

    ranked = predict_types(bundle, EVENT_TYPES, geo, fat, int(civ))
    p_sel = float(ranked.loc[ranked.event_type == etype, "p_block"].iloc[0])
    rank_pos = int(ranked.index[ranked.event_type == etype][0]) + 1

    with right:
        st.subheader("Prediction")
        st.metric(f"P(this {etype.lower()} blocks a road)", f"{p_sel:.1%}")
        baseline = float(m.get("prevalence", 0) or 0)
        lift = (p_sel / baseline) if baseline else float("nan")
        band = ("🟥 High" if p_sel >= 0.05 else "🟧 Moderate" if p_sel >= 0.01 else "🟩 Low")
        st.write(f"**{band}** blockage risk · ranks **#{rank_pos} of {len(ranked)}** event types"
                 + (f" · **{lift:.1f}×** the national blocked rate ({baseline:.2%})"
                    if baseline else ""))
        st.caption("Protests and territorial-control events block roads deliberately; explosive "
                   "violence (IED, airstrike) *affects* roads but rarely blocks them — the model "
                   "learned this from the ground-truth labels.")

    st.divider()
    st.subheader("Every event type, ranked (current settings)")
    ranked["selected"] = ranked["event_type"] == etype
    chart = (alt.Chart(ranked).mark_bar().encode(
        x=alt.X("p_block:Q", title="P(road blocked)", axis=alt.Axis(format="%")),
        y=alt.Y("event_type:N", sort="-x", title=None),
        color=alt.condition(alt.datum.selected, alt.value("#cc3333"), alt.value("#bbbbbb")),
        tooltip=[alt.Tooltip("event_type:N", title="type"),
                 alt.Tooltip("p_block:Q", title="P(block)", format=".3%")])
        .properties(height=520))
    st.altair_chart(chart, width="stretch")

with tab_map:
    st.subheader("Click the map to drop an event — see which roads block")
    roads_path = cfg_raw.get("paths", {}).get("roads")
    if not roads_path or not os.path.exists(roads_path):
        st.info("No road layer configured for this country (`paths.roads`). The event-level "
                "predictor on the first tab works without one.")
    else:
        name_col = cfg_raw["paths"].get("roads_name_col", "NAME_OF_RO")
        roads_gdf, mids = load_roads(roads_path, name_col)
        center = [float(mids.latitude.mean()), float(mids.longitude.mean())]

        c1, c2, c3 = st.columns([2, 1, 1])
        etype_m = c1.selectbox("Event type", EVENT_TYPES, key="map_type")
        fat_m = c2.slider("Fatalities", 0, 50, 0, key="map_fat")
        thr = c3.slider("Hide P below", 0.0, 0.30, 0.0, 0.005, key="map_thr",
                        help="Dim segments below this probability to grey. Leave at 0 to colour "
                             "the event's full reach (low-P0 events like Armed clash never exceed "
                             "a few percent — that's the data, not a bug).")
        st.caption("👆 Click anywhere on the map to place a hypothetical event. The **whole road "
                   "network** is shown; segments the model predicts blocked are coloured by "
                   "P(road blocked), the rest stay grey. The red pin is the event.")

        click = st.session_state.get("evt_click")  # (lat, lon) of last placed event

        # Score EVERY segment against the placed event (zeros where unreached), so the full
        # network can be drawn with affected roads coloured and the rest grey.
        scored = None
        if click:
            scored = score_event_on_roads(cfg_raw, mids, click[0], click[1], etype_m, fat_m)
            p_block = scored["p_block"].values
        else:
            p_block = np.zeros(len(roads_gdf))
        gj, cmap = colored_network(roads_gdf, p_block, thr)

        fmap = folium.Map(location=list(click) if click else center,
                          zoom_start=9 if click else 6, tiles="cartodbpositron",
                          prefer_canvas=True)
        folium.GeoJson(gj, style_function=lambda f: {
            "color": f["properties"]["color"], "weight": f["properties"]["weight"],
            "opacity": f["properties"]["op"]}).add_to(fmap)
        if click:
            folium.Marker(list(click), tooltip=f"{etype_m}",
                          icon=folium.Icon(color="red", icon="flag")).add_to(fmap)
        if cmap is not None:
            cmap.add_to(fmap)

        ret = st_folium(fmap, height=560, width="stretch", returned_objects=["last_clicked"])

        # A new click re-places the event and re-scores.
        lc = (ret or {}).get("last_clicked")
        if lc:
            new = (round(lc["lat"], 5), round(lc["lng"], 5))
            if new != st.session_state.get("evt_click"):
                st.session_state["evt_click"] = new
                st.rerun()

        if scored is not None:
            aff = scored[scored.p_block > max(thr, 1e-3)]
            st.write(f"Event at **{click[0]:.3f}, {click[1]:.3f}** · **{len(aff):,}** of "
                     f"{len(scored):,} segments predicted affected. Top roads:")
            if len(aff):
                top = (aff.groupby("road").agg(max_p=("p_block", "max"),
                       segments=("p_block", "size")).sort_values("max_p", ascending=False)
                       .head(15).round(3))
                st.dataframe(top, width="stretch")
            else:
                st.info("This event type barely blocks roads here — try a higher-impact type "
                        "(protest, territorial control), more fatalities, or lower the filter.")
        else:
            st.info("No event placed yet — click the map above to begin. The grey network is the "
                    "full set of road segments.")

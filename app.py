from __future__ import annotations

import io

import numpy as np
import pandas as pd
import streamlit as st

from loader import get_data
from metrics import hourly_volume, pickup_hotspots, distance_fare_scatter, tip_rate_by_weekday
from charts import hourly_volume_line, pickup_hotspot_map, distance_fare_scatter as dist_fare_chart, tip_rate_bar

st.set_page_config(
    page_title="NYC Yellow Taxi Dashboard",
    page_icon="🚕",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    section[data-testid="stSidebar"] { width: 280px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _load_default():
    return get_data()


@st.cache_data(show_spinner=False)
def _load_uploaded(file_bytes: bytes):
    return get_data(io.BytesIO(file_bytes))


with st.sidebar:
    st.header("⚙️ Data Source")
    uploaded = st.file_uploader(
        "Upload your own CSV",
        type=["csv"],
        help="Must match NYC Yellow Taxi column schema",
    )

    if uploaded is not None:
        try:
            df = _load_uploaded(uploaded.getvalue())
            st.success(f"✅ Loaded **{len(df):,}** rows from uploaded file")
        except Exception as exc:
            st.error(f"❌ Failed to load uploaded file:\n\n{exc}")
            df = _load_default()
    else:
        df = _load_default()

    st.divider()
    st.header("🔍 Filters")

    date_min = df["tpep_pickup_datetime"].dt.date.min()
    date_max = df["tpep_pickup_datetime"].dt.date.max()
    date_range = st.date_input(
        "Date range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    pass_range = st.slider(
        "Passenger count",
        min_value=int(df["passenger_count"].min()),
        max_value=int(df["passenger_count"].max()),
        value=(1, int(df["passenger_count"].max())),
    )

    include_tip = st.radio(
        "Tip filter",
        options=["All trips", "With tip only", "No tip only"],
        index=0,
    )

if len(date_range) == 2:
    mask_date = (
        (df["tpep_pickup_datetime"].dt.date >= date_range[0])
        & (df["tpep_pickup_datetime"].dt.date <= date_range[1])
    )
else:
    mask_date = df["tpep_pickup_datetime"].dt.date == date_range[0]

mask_pass = df["passenger_count"].between(pass_range[0], pass_range[1])

if include_tip == "With tip only":
    mask_tip = df["tip_amount"] > 0
elif include_tip == "No tip only":
    mask_tip = df["tip_amount"] == 0
else:
    mask_tip = np.ones(len(df), dtype=bool)

filtered = df[mask_date & mask_pass & mask_tip].copy()

if filtered.empty:
    st.warning("No trips match the current filters. Please adjust and try again.")
    st.stop()

st.title("🚕 NYC Yellow Taxi Dashboard")
st.caption(
    f"Showing **{len(filtered):,}** trips "
    f"({filtered['tpep_pickup_datetime'].dt.date.min()} → "
    f"{filtered['tpep_pickup_datetime'].dt.date.max()})"
)

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.plotly_chart(hourly_volume_line(hourly_volume(filtered)), use_container_width=True)

with col2:
    st.plotly_chart(pickup_hotspot_map(pickup_hotspots(filtered)), use_container_width=True)

col3, col4 = st.columns(2, gap="medium")

with col3:
    st.plotly_chart(dist_fare_chart(distance_fare_scatter(filtered)), use_container_width=True)

with col4:
    st.plotly_chart(tip_rate_bar(tip_rate_by_weekday(filtered)), use_container_width=True)

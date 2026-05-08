from __future__ import annotations

import numpy as np
import pandas as pd

_WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def hourly_volume(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["hour"] = out["tpep_pickup_datetime"].dt.hour
    agg = out.groupby("hour").size().reset_index(name="trip_count")
    all_hours = pd.DataFrame({"hour": range(24)})
    agg = all_hours.merge(agg, on="hour", how="left").fillna(0)
    agg["trip_count"] = agg["trip_count"].astype(int)
    return agg


def pickup_hotspots(df: pd.DataFrame, n_bins: int = 30) -> pd.DataFrame:
    out = df.copy()
    out["lat_bin"] = pd.cut(out["pickup_latitude"], bins=n_bins)
    out["lon_bin"] = pd.cut(out["pickup_longitude"], bins=n_bins)
    agg = (
        out.groupby(["lat_bin", "lon_bin"], observed=True)
        .agg(
            lat_center=("pickup_latitude", "mean"),
            lon_center=("pickup_longitude", "mean"),
            trip_count=("pickup_latitude", "size"),
        )
        .reset_index()
    )
    agg = agg[agg["trip_count"] > 0].sort_values("trip_count", ascending=False)
    return agg


def distance_fare_scatter(df: pd.DataFrame, iqr_factor: float = 2.5) -> pd.DataFrame:
    out = df[["trip_distance", "fare_amount", "tip_amount", "total_amount"]].copy()
    q1 = out["fare_amount"].quantile(0.25)
    q3 = out["fare_amount"].quantile(0.75)
    iqr = q3 - q1
    upper = q3 + iqr_factor * iqr
    out["is_outlier"] = out["fare_amount"] > upper
    return out


def tip_rate_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["weekday"] = out["tpep_pickup_datetime"].dt.weekday
    out["tip_rate"] = np.where(
        out["fare_amount"] > 0,
        out["tip_amount"] / out["fare_amount"],
        0.0,
    )
    agg = out.groupby("weekday")["tip_rate"].mean().reset_index()
    agg["weekday_name"] = agg["weekday"].map(dict(enumerate(_WEEKDAY_NAMES)))
    return agg[["weekday", "weekday_name", "tip_rate"]]

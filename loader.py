from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

_DEFAULT_CSV = Path(__file__).parent / "data" / "sample_trips.csv"

NYC_CENTER = {"lat": 40.7580, "lon": -73.9855}

_REQUIRED_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "pickup_longitude",
    "pickup_latitude",
    "dropoff_longitude",
    "dropoff_latitude",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "tip_amount",
    "total_amount",
]


def generate_synthetic_data(n: int = 15000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    base = pd.date_range("2024-03-01", periods=31, freq="D")
    days = rng.choice(base, size=n)
    hours = rng.choice(range(24), size=n, p=_hour_weights())
    pickup = pd.to_datetime(days) + pd.to_timedelta(hours, unit="h") + pd.to_timedelta(
        rng.integers(0, 3600, size=n), unit="s"
    )
    duration_min = np.clip(rng.exponential(15, size=n), 1, 180)
    dropoff = pickup + pd.to_timedelta(duration_min, unit="m")

    lat_p = NYC_CENTER["lat"] + rng.normal(0, 0.02, size=n)
    lon_p = NYC_CENTER["lon"] + rng.normal(0, 0.02, size=n)
    lat_d = NYC_CENTER["lat"] + rng.normal(0, 0.03, size=n)
    lon_d = NYC_CENTER["lon"] + rng.normal(0, 0.03, size=n)

    trip_distance = np.clip(rng.exponential(3, size=n), 0.1, 40)
    passenger_count = rng.choice([1, 1, 1, 2, 2, 3, 4, 5, 6], size=n)
    fare_amount = 2.5 + trip_distance * 2.5 + rng.normal(0, 2, size=n)
    tip_amount = np.where(
        rng.random(size=n) < 0.6,
        fare_amount * rng.uniform(0.05, 0.25, size=n),
        0.0,
    )
    total_amount = fare_amount + tip_amount + rng.uniform(0.5, 2.0, size=n)

    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": pickup,
            "tpep_dropoff_datetime": dropoff,
            "pickup_longitude": lon_p,
            "pickup_latitude": lat_p,
            "dropoff_longitude": lon_d,
            "dropoff_latitude": lat_d,
            "passenger_count": passenger_count,
            "trip_distance": np.round(trip_distance, 2),
            "fare_amount": np.round(fare_amount, 2),
            "tip_amount": np.round(tip_amount, 2),
            "total_amount": np.round(total_amount, 2),
        }
    )

    dirty_idx = rng.choice(n, size=int(n * 0.02), replace=False)
    df.loc[dirty_idx[: len(dirty_idx) // 3], "fare_amount"] *= -1
    df.loc[
        dirty_idx[len(dirty_idx) // 3 : 2 * len(dirty_idx) // 3], "trip_distance"
    ] = 0
    flip = dirty_idx[2 * len(dirty_idx) // 3 :]
    df.loc[flip, "tpep_pickup_datetime"] = df.loc[flip, "tpep_dropoff_datetime"] + pd.to_timedelta(
        rng.integers(1, 60, size=len(flip)), unit="m"
    )

    return df


def _hour_weights() -> np.ndarray:
    raw = np.array(
        [1.0, 0.7, 0.5, 0.5, 0.6, 1.2, 2.5, 4.0, 4.5, 3.5, 3.0, 3.5,
         4.0, 3.5, 3.0, 3.5, 4.0, 5.0, 5.5, 4.5, 3.5, 3.0, 2.5, 1.5]
    )
    return raw / raw.sum()


def load_csv(source: str | Path | io.BytesIO) -> pd.DataFrame:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")
        df = pd.read_csv(path, parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"])
    else:
        df = pd.read_csv(source, parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"])

    _validate_columns(df)
    return df


def _validate_columns(df: pd.DataFrame) -> None:
    missing = set(_REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    numeric_cols = [
        "fare_amount", "tip_amount", "total_amount",
        "trip_distance", "pickup_latitude", "pickup_longitude",
        "dropoff_latitude", "dropoff_longitude",
    ]
    for c in numeric_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.dropna(subset=[
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "trip_distance", "fare_amount",
    ])

    out = out[out["fare_amount"] > 0]
    out = out[out["trip_distance"] > 0]
    out = out[out["tpep_pickup_datetime"] < out["tpep_dropoff_datetime"]]

    out = out[
        (out["pickup_latitude"].between(40.5, 41.0))
        & (out["pickup_longitude"].between(-74.3, -73.7))
    ]

    out = out.reset_index(drop=True)
    return out


def get_data(csv_path: str | Path | io.BytesIO | None = None) -> pd.DataFrame:
    if csv_path is not None:
        raw = load_csv(csv_path)
    elif _DEFAULT_CSV.exists():
        raw = load_csv(_DEFAULT_CSV)
    else:
        raw = generate_synthetic_data()

    return clean(raw)

from __future__ import annotations

import io
from typing import Optional

import pandas as pd


REQUIRED_COLUMNS = {
    'tpep_pickup_datetime',
    'tpep_dropoff_datetime',
    'passenger_count',
    'trip_distance',
    'fare_amount',
    'tip_amount',
    'total_amount',
}


def load_csv_data(file_path: Optional[str] = None, uploaded_file: Optional[io.BytesIO] = None) -> pd.DataFrame:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif file_path is not None:
        df = pd.read_csv(file_path)
    else:
        raise ValueError('Either file_path or uploaded_file must be provided')

    return _normalize_and_clean(df)


def _normalize_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalize_datetime_columns(df)
    df = _normalize_column_names(df)
    df = _ensure_required_columns(df)
    df = _clean_data(df)
    df = _derive_features(df)
    return df.reset_index(drop=True)


def _normalize_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    pickup_col = _find_datetime_column(df, ['tpep_pickup_datetime', 'pickup_datetime'])
    dropoff_col = _find_datetime_column(df, ['tpep_dropoff_datetime', 'dropoff_datetime'])

    if pickup_col and pickup_col != 'tpep_pickup_datetime':
        df = df.rename(columns={pickup_col: 'tpep_pickup_datetime'})
    if dropoff_col and dropoff_col != 'tpep_dropoff_datetime':
        df = df.rename(columns={dropoff_col: 'tpep_dropoff_datetime'})

    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'], errors='coerce')
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'], errors='coerce')

    return df


def _find_datetime_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        if 'pickup' in col.lower() and 'time' in col.lower():
            return col
        if 'dropoff' in col.lower() and 'time' in col.lower():
            return col
    return None


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    name_map = {
        'passengers': 'passenger_count',
        'distance': 'trip_distance',
        'fare': 'fare_amount',
        'tip': 'tip_amount',
        'total': 'total_amount',
    }
    for old, new in name_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    return df


def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f'Missing required columns: {", ".join(missing)}')
    return df


def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    initial_count = len(df)

    df = df.dropna(subset=[
        'tpep_pickup_datetime',
        'tpep_dropoff_datetime',
        'trip_distance',
        'fare_amount',
        'total_amount',
    ])

    df = df[df['fare_amount'] >= 0]
    df = df[df['total_amount'] >= 0]
    df = df[df['trip_distance'] > 0]

    df = df[df['tpep_dropoff_datetime'] > df['tpep_pickup_datetime']]

    df = df[(df['passenger_count'] >= 1) & (df['passenger_count'] <= 6)]

    cleaned_count = len(df)
    dropped_count = initial_count - cleaned_count

    if dropped_count > 0:
        print(f'Cleaned {dropped_count} invalid records from initial {initial_count}')

    return df


def _derive_features(df: pd.DataFrame) -> pd.DataFrame:
    df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
    df['pickup_day'] = df['tpep_pickup_datetime'].dt.date
    df['pickup_weekday'] = df['tpep_pickup_datetime'].dt.dayofweek
    df['pickup_month'] = df['tpep_pickup_datetime'].dt.month
    df['pickup_year'] = df['tpep_pickup_datetime'].dt.year

    df['trip_duration_minutes'] = (
        df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    ).dt.total_seconds() / 60

    df['has_tip'] = df['tip_amount'] > 0

    df['tip_rate'] = df.apply(_calculate_tip_rate, axis=1)

    return df


def _calculate_tip_rate(row: pd.Series) -> float:
    fare = row['fare_amount']
    tip = row['tip_amount']
    if fare <= 0 or tip <= 0:
        return 0.0
    return tip / fare


def get_date_range(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    return df['tpep_pickup_datetime'].min(), df['tpep_pickup_datetime'].max()


def get_passenger_range(df: pd.DataFrame) -> tuple[int, int]:
    return int(df['passenger_count'].min()), int(df['passenger_count'].max())


def filter_data(
    df: pd.DataFrame,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    min_passengers: Optional[int] = None,
    max_passengers: Optional[int] = None,
    has_tip: Optional[bool] = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if start_date is not None:
        filtered = filtered[filtered['tpep_pickup_datetime'] >= start_date]
    if end_date is not None:
        filtered = filtered[filtered['tpep_pickup_datetime'] <= end_date]

    if min_passengers is not None:
        filtered = filtered[filtered['passenger_count'] >= min_passengers]
    if max_passengers is not None:
        filtered = filtered[filtered['passenger_count'] <= max_passengers]

    if has_tip is not None:
        filtered = filtered[filtered['has_tip'] == has_tip]

    return filtered

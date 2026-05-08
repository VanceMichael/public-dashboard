from __future__ import annotations

import pandas as pd
import numpy as np


def calculate_hourly_volume(df: pd.DataFrame) -> pd.DataFrame:
    hourly = df.groupby('pickup_hour').agg({
        'VendorID': 'count',
        'trip_distance': 'mean',
        'total_amount': 'mean',
    }).reset_index()

    hourly = hourly.rename(columns={
        'VendorID': 'trip_count',
        'trip_distance': 'avg_distance',
        'total_amount': 'avg_total_amount',
    })

    all_hours = pd.DataFrame({'pickup_hour': range(24)})
    hourly = all_hours.merge(hourly, on='pickup_hour', how='left').fillna(0)

    return hourly.sort_values('pickup_hour')


def calculate_pickup_heatmap(
    df: pd.DataFrame,
    lat_col: str = 'pickup_latitude',
    lon_col: str = 'pickup_longitude',
    bins: int = 50,
) -> pd.DataFrame:
    if lat_col not in df.columns or lon_col not in df.columns:
        return pd.DataFrame()

    valid = df[[lat_col, lon_col]].dropna()

    lat_min, lat_max = valid[lat_col].quantile([0.01, 0.99])
    lon_min, lon_max = valid[lon_col].quantile([0.01, 0.99])

    valid = valid[
        (valid[lat_col] >= lat_min) &
        (valid[lat_col] <= lat_max) &
        (valid[lon_col] >= lon_min) &
        (valid[lon_col] <= lon_max)
    ]

    if len(valid) == 0:
        return pd.DataFrame()

    lat_edges = np.linspace(lat_min, lat_max, bins + 1)
    lon_edges = np.linspace(lon_min, lon_max, bins + 1)

    valid['lat_bin'] = pd.cut(valid[lat_col], bins=lat_edges, labels=False)
    valid['lon_bin'] = pd.cut(valid[lon_col], bins=lon_edges, labels=False)

    heatmap = valid.groupby(['lat_bin', 'lon_bin']).size().reset_index(name='count')

    heatmap['latitude'] = lat_edges[heatmap['lat_bin'].astype(int)] + (lat_edges[1] - lat_edges[0]) / 2
    heatmap['longitude'] = lon_edges[heatmap['lon_bin'].astype(int)] + (lon_edges[1] - lon_edges[0]) / 2

    return heatmap[['latitude', 'longitude', 'count']]


def calculate_distance_vs_fare(df: pd.DataFrame, outlier_percentile: float = 99) -> pd.DataFrame:
    result = df[['trip_distance', 'total_amount', 'fare_amount', 'tip_amount']].copy()

    fare_threshold = result['total_amount'].quantile(outlier_percentile / 100)
    distance_threshold = result['trip_distance'].quantile(outlier_percentile / 100)

    result['is_outlier'] = (
        (result['total_amount'] > fare_threshold) |
        (result['trip_distance'] > distance_threshold)
    )

    result['fare_per_mile'] = result['total_amount'] / result['trip_distance']

    return result


def calculate_weekday_tip_rate(df: pd.DataFrame) -> pd.DataFrame:
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    with_tip = df[df['tip_amount'] > 0]

    if len(with_tip) == 0:
        result = pd.DataFrame({
            'weekday': list(range(7)),
            'weekday_name': weekday_names,
            'avg_tip_rate': 0.0,
            'trip_count': 0,
        })
        return result

    grouped = with_tip.groupby('pickup_weekday').agg({
        'tip_rate': 'mean',
        'VendorID': 'count',
    }).reset_index()

    grouped = grouped.rename(columns={
        'tip_rate': 'avg_tip_rate',
        'VendorID': 'trip_count',
    })

    all_weekdays = pd.DataFrame({
        'pickup_weekday': list(range(7)),
        'weekday_name': weekday_names,
    })

    result = all_weekdays.merge(grouped, on='pickup_weekday', how='left')
    result = result.rename(columns={'pickup_weekday': 'weekday'})
    result['avg_tip_rate'] = result['avg_tip_rate'].fillna(0)
    result['trip_count'] = result['trip_count'].fillna(0).astype(int)

    return result


def calculate_summary_stats(df: pd.DataFrame) -> dict:
    if len(df) == 0:
        return {
            'total_trips': 0,
            'total_revenue': 0.0,
            'avg_distance': 0.0,
            'avg_tip_rate': 0.0,
            'tip_percentage': 0.0,
        }

    with_tip = df[df['tip_amount'] > 0]

    return {
        'total_trips': len(df),
        'total_revenue': round(df['total_amount'].sum(), 2),
        'avg_distance': round(df['trip_distance'].mean(), 2),
        'avg_tip_rate': round(with_tip['tip_rate'].mean() * 100, 2) if len(with_tip) > 0 else 0.0,
        'tip_percentage': round(len(with_tip) / len(df) * 100, 2),
    }


def get_top_outliers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if len(df) == 0:
        return pd.DataFrame()

    distance_vs_fare = calculate_distance_vs_fare(df)
    outliers = df[distance_vs_fare['is_outlier'].values].copy()

    if len(outliers) == 0:
        return pd.DataFrame()

    outliers['fare_per_mile'] = outliers['total_amount'] / outliers['trip_distance']
    outliers = outliers.sort_values('fare_per_mile', ascending=False).head(n)

    display_cols = [
        'tpep_pickup_datetime',
        'trip_distance',
        'fare_amount',
        'tip_amount',
        'total_amount',
        'fare_per_mile',
    ]

    available_cols = [c for c in display_cols if c in outliers.columns]

    return outliers[available_cols].reset_index(drop=True)

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

NUM_RECORDS = 50000
START_DATE = datetime(2024, 3, 1)

MANHATTAN_NORTH = 40.7831
MANHATTAN_SOUTH = 40.7000
MANHATTAN_EAST = -73.9680
MANHATTAN_WEST = -74.0060

JFK_LAT, JFK_LON = 40.6413, -73.7781
LGA_LAT, LGA_LON = 40.7769, -73.8740
EWR_LAT, EWR_LON = 40.6895, -74.1745

pickup_zones = [
    (40.7580, -73.9855, 0.25),
    (40.7128, -74.0060, 0.20),
    (40.7614, -73.9776, 0.15),
    (40.7484, -73.9857, 0.15),
    (JFK_LAT, JFK_LON, 0.10),
    (LGA_LAT, LGA_LON, 0.08),
    (EWR_LAT, EWR_LON, 0.07),
]

zone_probs = [z[2] for z in pickup_zones]
zone_indices = np.random.choice(len(pickup_zones), size=NUM_RECORDS, p=zone_probs)

base_lat = np.array([pickup_zones[i][0] for i in zone_indices])
base_lon = np.array([pickup_zones[i][1] for i in zone_indices])

pickup_latitude = base_lat + np.random.normal(0, 0.005, NUM_RECORDS)
pickup_longitude = base_lon + np.random.normal(0, 0.008, NUM_RECORDS)

dropoff_latitude = pickup_latitude + np.random.normal(0, 0.02, NUM_RECORDS)
dropoff_longitude = pickup_longitude + np.random.normal(0, 0.025, NUM_RECORDS)

dropoff_latitude = np.clip(dropoff_latitude, MANHATTAN_SOUTH - 0.1, MANHATTAN_NORTH + 0.1)
dropoff_longitude = np.clip(dropoff_longitude, MANHATTAN_WEST - 0.15, MANHATTAN_EAST + 0.15)

num_days = 31
days = np.random.randint(0, num_days, NUM_RECORDS)
hours = np.zeros(NUM_RECORDS)

hour_probs = np.zeros(24)
for h in range(24):
    if 7 <= h <= 9:
        hour_probs[h] = 1.8
    elif 17 <= h <= 20:
        hour_probs[h] = 2.0
    elif 0 <= h <= 5:
        hour_probs[h] = 0.3
    else:
        hour_probs[h] = 1.0
hour_probs = hour_probs / hour_probs.sum()

hours = np.random.choice(range(24), size=NUM_RECORDS, p=hour_probs)
minutes = np.random.randint(0, 60, NUM_RECORDS)
seconds = np.random.randint(0, 60, NUM_RECORDS)

pickup_datetimes = [
    START_DATE + timedelta(days=int(d), hours=int(h), minutes=int(m), seconds=int(s))
    for d, h, m, s in zip(days, hours, minutes, seconds)
]

trip_duration = np.random.lognormal(mean=4.0, sigma=0.8, size=NUM_RECORDS)
trip_duration = np.clip(trip_duration, 60, 7200)

dropoff_datetimes = [
    pickup + timedelta(seconds=int(t))
    for pickup, t in zip(pickup_datetimes, trip_duration)
]

passenger_count = np.random.choice([1, 2, 3, 4, 5, 6], size=NUM_RECORDS, p=[0.6, 0.2, 0.1, 0.05, 0.03, 0.02])

trip_distance = np.random.lognormal(mean=1.2, sigma=0.9, size=NUM_RECORDS)
trip_distance = np.clip(trip_distance, 0.1, 30.0)

airport_trips = (zone_indices >= 4)
trip_distance[airport_trips] = trip_distance[airport_trips] + np.random.uniform(5, 15, size=airport_trips.sum())

fare_amount = 2.5 + trip_distance * 2.75 + trip_duration / 60 * 0.5
fare_amount += np.random.normal(0, 2, NUM_RECORDS)
fare_amount = np.clip(fare_amount, 3, 200)

extra = np.where(hours >= 16, 1.0, 0.0)
extra += np.random.choice([0, 0.5, 1.0], size=NUM_RECORDS, p=[0.7, 0.2, 0.1])

mta_tax = 0.5
tolls_amount = np.where(trip_distance > 15, np.random.uniform(5, 20, NUM_RECORDS), 0)
improvement_surcharge = 0.3

tip_amount = np.where(
    np.random.random(NUM_RECORDS) < 0.65,
    fare_amount * np.random.uniform(0.15, 0.25, NUM_RECORDS),
    0
)

total_amount = fare_amount + extra + mta_tax + tolls_amount + improvement_surcharge + tip_amount

df = pd.DataFrame({
    'VendorID': np.random.choice([1, 2], size=NUM_RECORDS),
    'tpep_pickup_datetime': pickup_datetimes,
    'tpep_dropoff_datetime': dropoff_datetimes,
    'passenger_count': passenger_count,
    'trip_distance': trip_distance,
    'RatecodeID': np.random.choice([1, 2, 3], size=NUM_RECORDS, p=[0.9, 0.08, 0.02]),
    'store_and_fwd_flag': np.random.choice(['N', 'Y'], size=NUM_RECORDS, p=[0.99, 0.01]),
    'PULocationID': np.random.randint(1, 266, NUM_RECORDS),
    'DOLocationID': np.random.randint(1, 266, NUM_RECORDS),
    'payment_type': np.random.choice([1, 2], size=NUM_RECORDS, p=[0.7, 0.3]),
    'fare_amount': fare_amount,
    'extra': extra,
    'mta_tax': mta_tax,
    'tip_amount': tip_amount,
    'tolls_amount': tolls_amount,
    'improvement_surcharge': improvement_surcharge,
    'total_amount': total_amount,
    'pickup_latitude': pickup_latitude,
    'pickup_longitude': pickup_longitude,
    'dropoff_latitude': dropoff_latitude,
    'dropoff_longitude': dropoff_longitude,
})

outlier_idx = np.random.choice(NUM_RECORDS, size=50, replace=False)
df.loc[outlier_idx, 'total_amount'] *= np.random.uniform(3, 8, size=50)
df.loc[outlier_idx, 'fare_amount'] *= np.random.uniform(3, 8, size=50)

bad_idx = np.random.choice(NUM_RECORDS, size=100, replace=False)
df.loc[bad_idx[:30], 'fare_amount'] *= -1
df.loc[bad_idx[30:60], 'trip_distance'] = 0
df.loc[bad_idx[60:90], 'tpep_dropoff_datetime'] = df.loc[bad_idx[60:90], 'tpep_pickup_datetime'] - pd.Timedelta(hours=2)

df.to_csv('data/yellow_tripdata_sample.csv', index=False)
print(f'Generated {NUM_RECORDS} records to data/yellow_tripdata_sample.csv')

# NYC Yellow Taxi Dashboard

A Streamlit-based interactive dashboard for exploring NYC Yellow Taxi trip data.

## Features

- **Top Filters**: Date range, passenger count, and tip presence filtering
- **Hourly Volume Chart**: Shows peak hours for taxi rides
- **Pickup Heatmap**: Interactive map showing hotspot locations
- **Distance vs Fare Scatter Plot**: Highlights expensive outliers
- **Weekday Tip Rate Chart**: Average tip percentage by day of week
- **Sidebar Upload**: Switch to your own CSV anytime
- **Automatic Data Cleaning**: Removes negative fares, zero distances, and time-travel records

## Project Structure

```
.
├── app.py                    # Streamlit main application
├── loader.py                 # Data loading and preprocessing
├── metrics.py                # Metric calculations and aggregations
├── charts.py                 # Plotly chart rendering
├── generate_sample_data.py   # Synthetic data generator
├── requirements.txt
├── README.md
└── data/
    └── yellow_tripdata_sample.csv  # Generated sample data
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate sample data

```bash
python generate_sample_data.py
```

This creates `data/yellow_tripdata_sample.csv` with ~50,000 synthetic records mimicking NYC Taxi data (Manhattan + airports pattern, morning/evening peaks, outliers, and some dirty data that gets cleaned).

### 3. Run the dashboard

```bash
streamlit run app.py
```

## Using Real NYC Taxi Data

Download actual NYC Yellow Taxi CSV files from the [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

The official TLC CSVs include LocationIDs (zone numbers) instead of raw lat/lng, so the heatmap won't render with those. To get latitude/longitude columns for the heatmap, you can either:

1. Join with the TLC taxi zone shapefile to get zone centroids, or
2. Use an older dataset (pre-2017) that had raw pickup_latitude/pickup_longitude columns, or
3. Upload any CSV with `pickup_latitude` and `pickup_longitude` columns

### Required columns

| Column | Description |
|--------|-------------|
| `tpep_pickup_datetime` | Pickup timestamp |
| `tpep_dropoff_datetime` | Dropoff timestamp |
| `passenger_count` | Number of passengers |
| `trip_distance` | Distance traveled (miles) |
| `fare_amount` | Base fare |
| `tip_amount` | Tip amount |
| `total_amount` | Total charge |

### Optional columns

| Column | Description |
|--------|-------------|
| `pickup_latitude` | Pickup latitude (for heatmap) |
| `pickup_longitude` | Pickup longitude (for heatmap) |

### Upload your CSV

Use the **📂 Data Source** panel in the left sidebar to upload your own CSV. Format must match the columns above.

## Data Cleaning Rules

On load, the following records are automatically removed:

- `fare_amount < 0` or `total_amount < 0` (negative charges)
- `trip_distance <= 0`
- `tpep_dropoff_datetime <= tpep_pickup_datetime` (time-traveling trips)
- `passenger_count` outside 1–6 range
- Any row with nulls in required fields

## Tech Stack

- **Streamlit** – UI layer and interactive widgets
- **Plotly** – All charts (no matplotlib)
- **pandas>=2.0** – Data wrangling
- **numpy** – Synthetic data generation and binning

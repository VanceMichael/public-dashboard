from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

import loader
import metrics
import charts


st.set_page_config(
    page_title='NYC Yellow Taxi Dashboard',
    page_icon='🚕',
    layout='wide',
    initial_sidebar_state='expanded',
)


DEFAULT_DATA_PATH = Path('data/yellow_tripdata_sample.csv')


@st.cache_data(show_spinner='Loading data...')
def load_data_cached(file_path: str | None = None) -> pd.DataFrame:
    if file_path and os.path.exists(file_path):
        return loader.load_csv_data(file_path=file_path)
    if DEFAULT_DATA_PATH.exists():
        return loader.load_csv_data(file_path=str(DEFAULT_DATA_PATH))
    return pd.DataFrame()


@st.cache_data(show_spinner='Processing uploaded file...')
def load_uploaded_data(uploaded_file) -> pd.DataFrame:
    return loader.load_csv_data(uploaded_file=uploaded_file)


def main():
    st.title('🚕 NYC Yellow Trip Data Dashboard')

    with st.sidebar:
        st.header('📂 Data Source')
        uploaded_file = st.file_uploader('Upload your own CSV', type=['csv'])

        if uploaded_file is not None:
            try:
                df = load_uploaded_data(uploaded_file)
                st.success(f'Loaded {len(df):,} records from {uploaded_file.name}')
            except Exception as e:
                st.error(f'Error loading file: {str(e)}')
                df = pd.DataFrame()
        else:
            df = load_data_cached()
            if not df.empty:
                st.info(f'Using sample data ({len(df):,} records)')
            else:
                st.warning(
                    'No sample data found. Please run `python generate_sample_data.py` '
                    'to generate sample data, or upload your own CSV.'
                )

        if not df.empty:
            st.divider()
            st.markdown('### 📊 Data Info')
            st.write(f'Total records: {len(df):,}')
            min_date = df['tpep_pickup_datetime'].min().date()
            max_date = df['tpep_pickup_datetime'].max().date()
            st.write(f'Date range: {min_date} to {max_date}')

            st.divider()
            st.markdown('### 📝 Required Columns')
            st.markdown('''
                - `tpep_pickup_datetime` / `tpep_dropoff_datetime`
                - `passenger_count`
                - `trip_distance`
                - `fare_amount`, `tip_amount`, `total_amount`
                - Optional: `pickup_latitude`, `pickup_longitude` for heatmap
            ''')

    if df.empty:
        st.info('Please upload a CSV file or generate sample data to get started.')
        return

    min_date, max_date = loader.get_date_range(df)
    min_passengers, max_passengers = loader.get_passenger_range(df)

    st.markdown('---')
    st.subheader('🔍 Filters')

    filter_cols = st.columns([2, 2, 2, 2])

    with filter_cols[0]:
        start_date = st.date_input(
            'Start Date',
            min_value=min_date.date(),
            max_value=max_date.date(),
            value=min_date.date(),
        )

    with filter_cols[1]:
        end_date = st.date_input(
            'End Date',
            min_value=min_date.date(),
            max_value=max_date.date(),
            value=max_date.date(),
        )

    with filter_cols[2]:
        passenger_range = st.slider(
            'Passenger Count',
            min_value=min_passengers,
            max_value=max_passengers,
            value=(min_passengers, max_passengers),
        )

    with filter_cols[3]:
        tip_filter = st.selectbox(
            'Has Tip?',
            options=['All', 'With Tip Only', 'No Tip Only'],
            index=0,
        )

    has_tip = None
    if tip_filter == 'With Tip Only':
        has_tip = True
    elif tip_filter == 'No Tip Only':
        has_tip = False

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    filtered_df = loader.filter_data(
        df,
        start_date=start_ts,
        end_date=end_ts,
        min_passengers=passenger_range[0],
        max_passengers=passenger_range[1],
        has_tip=has_tip,
    )

    if filtered_df.empty:
        st.warning('No data matches the current filters.')
        return

    summary_stats = metrics.calculate_summary_stats(filtered_df)
    summary_html = charts.create_summary_metrics_html(summary_stats)
    st.markdown(summary_html, unsafe_allow_html=True)

    st.markdown('---')

    row1_cols = st.columns(2)

    with row1_cols[0]:
        hourly_data = metrics.calculate_hourly_volume(filtered_df)
        hourly_fig = charts.create_hourly_volume_chart(hourly_data)
        st.plotly_chart(hourly_fig, use_container_width=True)

    with row1_cols[1]:
        heatmap_data = metrics.calculate_pickup_heatmap(filtered_df)
        heatmap_fig = charts.create_pickup_heatmap(heatmap_data)
        st.plotly_chart(heatmap_fig, use_container_width=True)

    row2_cols = st.columns(2)

    with row2_cols[0]:
        distance_fare_data = metrics.calculate_distance_vs_fare(filtered_df)
        distance_fig = charts.create_distance_vs_fare_chart(distance_fare_data)
        st.plotly_chart(distance_fig, use_container_width=True)

        with st.expander('Show Top Outliers'):
            outliers = metrics.get_top_outliers(filtered_df, n=10)
            if not outliers.empty:
                st.dataframe(outliers, use_container_width=True)
            else:
                st.info('No outliers found in the filtered data.')

    with row2_cols[1]:
        weekday_data = metrics.calculate_weekday_tip_rate(filtered_df)
        weekday_fig = charts.create_weekday_tip_rate_chart(weekday_data)
        st.plotly_chart(weekday_fig, use_container_width=True)


if __name__ == '__main__':
    main()

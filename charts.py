from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_hourly_volume_chart(hourly_data: pd.DataFrame) -> go.Figure:
    if hourly_data.empty:
        fig = go.Figure()
        fig.update_layout(title='No data available')
        return fig

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hourly_data['pickup_hour'],
        y=hourly_data['trip_count'],
        mode='lines+markers',
        name='Trips',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4'),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)',
    ))

    fig.update_layout(
        title={
            'text': 'Hourly Trip Volume',
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=18),
        },
        xaxis=dict(
            title='Hour of Day',
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
        ),
        yaxis=dict(title='Number of Trips'),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig


def create_pickup_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    if heatmap_data.empty:
        fig = go.Figure()
        fig.update_layout(
            title='Pickup Heatmap (Latitude/Longitude data not available)',
            template='plotly_white',
            height=500,
        )
        return fig

    fig = go.Figure(go.Densitymapbox(
        lat=heatmap_data['latitude'],
        lon=heatmap_data['longitude'],
        z=heatmap_data['count'],
        radius=20,
        colorscale='Viridis',
        opacity=0.7,
        name='Pickup Density',
    ))

    center_lat = heatmap_data['latitude'].mean()
    center_lon = heatmap_data['longitude'].mean()

    fig.update_layout(
        title={
            'text': 'Pickup Location Heatmap',
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=18),
        },
        mapbox=dict(
            style='carto-positron',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11,
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        height=500,
    )

    return fig


def create_distance_vs_fare_chart(distance_fare_data: pd.DataFrame, sample_size: int = 10000) -> go.Figure:
    if distance_fare_data.empty:
        fig = go.Figure()
        fig.update_layout(title='No data available')
        return fig

    if len(distance_fare_data) > sample_size:
        normal = distance_fare_data[~distance_fare_data['is_outlier']]
        outliers = distance_fare_data[distance_fare_data['is_outlier']]
        sampled_normal = normal.sample(n=min(len(normal), sample_size), random_state=42)
        plot_data = pd.concat([sampled_normal, outliers])
    else:
        plot_data = distance_fare_data

    normal = plot_data[~plot_data['is_outlier']]
    outliers = plot_data[plot_data['is_outlier']]

    fig = go.Figure()

    if not normal.empty:
        fig.add_trace(go.Scatter(
            x=normal['trip_distance'],
            y=normal['total_amount'],
            mode='markers',
            name='Normal Trips',
            marker=dict(
                color='#636efa',
                size=5,
                opacity=0.5,
            ),
        ))

    if not outliers.empty:
        fig.add_trace(go.Scatter(
            x=outliers['trip_distance'],
            y=outliers['total_amount'],
            mode='markers',
            name='Outliers (High Value)',
            marker=dict(
                color='#ef553b',
                size=10,
                symbol='circle-open',
                line=dict(width=2),
            ),
        ))

    fig.update_layout(
        title={
            'text': 'Trip Distance vs Total Fare',
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=18),
        },
        xaxis=dict(title='Trip Distance (miles)'),
        yaxis=dict(title='Total Amount ($)'),
        template='plotly_white',
        height=400,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(x=0.02, y=0.98),
        hovermode='closest',
    )

    return fig


def create_weekday_tip_rate_chart(weekday_data: pd.DataFrame) -> go.Figure:
    if weekday_data.empty:
        fig = go.Figure()
        fig.update_layout(title='No data available')
        return fig

    fig = go.Figure(go.Bar(
        x=weekday_data['weekday_name'],
        y=weekday_data['avg_tip_rate'] * 100,
        marker=dict(
            color=weekday_data['avg_tip_rate'] * 100,
            colorscale='RdYlGn',
            showscale=False,
        ),
        text=[f'{rate*100:.1f}%' for rate in weekday_data['avg_tip_rate']],
        textposition='outside',
        hovertext=weekday_data.apply(
            lambda x: f"{x['weekday_name']}<br>"
                     f"Avg Tip Rate: {x['avg_tip_rate']*100:.2f}%<br>"
                     f"Trips with Tips: {x['trip_count']:,}",
            axis=1
        ),
        hoverinfo='text',
    ))

    avg_rate = weekday_data['avg_tip_rate'].mean() * 100

    fig.add_hline(
        y=avg_rate,
        line_dash='dash',
        line_color='gray',
        annotation_text=f'Weekly Avg: {avg_rate:.1f}%',
        annotation_position='top right',
    )

    fig.update_layout(
        title={
            'text': 'Average Tip Rate by Day of Week',
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=18),
        },
        xaxis=dict(title=''),
        yaxis=dict(
            title='Average Tip Rate (%)',
            tickformat='.1f',
        ),
        template='plotly_white',
        height=400,
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig


def create_summary_metrics_html(stats: dict) -> str:
    cards = [
        ('Total Trips', f"{stats['total_trips']:,}", '📊'),
        ('Total Revenue', f"${stats['total_revenue']:,.2f}", '💰'),
        ('Avg Distance', f"{stats['avg_distance']} miles", '🚕'),
        ('Avg Tip Rate', f"{stats['avg_tip_rate']}%", '💵'),
        ('Trips with Tips', f"{stats['tip_percentage']}%", '✨'),
    ]

    html_parts = ['<div style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">']

    for title, value, emoji in cards:
        html_parts.append(f'''
            <div style="
                flex: 1;
                min-width: 140px;
                background: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <div style="font-size: 28px; margin-bottom: 4px;">{emoji}</div>
                <div style="font-size: 12px; color: #666; margin-bottom: 4px;">{title}</div>
                <div style="font-size: 20px; font-weight: bold; color: #1f77b4;">{value}</div>
            </div>
        ''')

    html_parts.append('</div>')
    return ''.join(html_parts)

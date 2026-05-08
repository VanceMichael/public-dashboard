from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_THEME = dict(
    bg="#0e1117",
    paper="#0e1117",
    text="#e0e0e0",
    grid="#2a2a3a",
    accent="#00d4ff",
    accent2="#ff6b6b",
    accent3="#ffd93d",
)


def hourly_volume_line(df_hourly) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_hourly["hour"],
            y=df_hourly["trip_count"],
            mode="lines+markers",
            line=dict(color=_THEME["accent"], width=2.5),
            marker=dict(size=6, color=_THEME["accent"]),
            fill="tozeroy",
            fillcolor=f"rgba(0,212,255,0.08)",
            name="Trips",
        )
    )
    peak_hours = df_hourly.nlargest(3, "trip_count")["hour"].tolist()
    for h in peak_hours:
        fig.add_vline(
            x=h,
            line_dash="dot",
            line_color=_THEME["accent3"],
            opacity=0.7,
        )
    fig.update_layout(
        title="Hourly Trip Volume",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Trips",
        template="plotly_dark",
        paper_bgcolor=_THEME["paper"],
        plot_bgcolor=_THEME["bg"],
        font=dict(color=_THEME["text"]),
        xaxis=dict(dtick=1, gridcolor=_THEME["grid"]),
        yaxis=dict(gridcolor=_THEME["grid"]),
        margin=dict(l=50, r=20, t=50, b=40),
        height=380,
    )
    return fig


def pickup_hotspot_map(df_hotspot) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scattermapbox(
            lat=df_hotspot["lat_center"],
            lon=df_hotspot["lon_center"],
            mode="markers",
            marker=dict(
                size=df_hotspot["trip_count"],
                sizemode="area",
                sizeref=2.0 * df_hotspot["trip_count"].max() / 40**2,
                color=df_hotspot["trip_count"],
                colorscale="YlOrRd",
                colorbar=dict(title="Trips", thickness=12, len=0.7),
                opacity=0.75,
            ),
            text=df_hotspot["trip_count"].apply(lambda x: f"{x} trips"),
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title="Pickup Hotspots",
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=40.758, lon=-73.986),
            zoom=11,
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=420,
        paper_bgcolor=_THEME["paper"],
        font=dict(color=_THEME["text"]),
    )
    return fig


def distance_fare_scatter(df_scatter) -> go.Figure:
    normal = df_scatter[~df_scatter["is_outlier"]]
    outlier = df_scatter[df_scatter["is_outlier"]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=normal["trip_distance"],
            y=normal["fare_amount"],
            mode="markers",
            marker=dict(color=_THEME["accent"], size=4, opacity=0.45),
            name="Normal",
            hovertemplate="Distance: %{x:.1f} mi<br>Fare: $%{y:.2f}<extra></extra>",
        )
    )
    if len(outlier) > 0:
        fig.add_trace(
            go.Scatter(
                x=outlier["trip_distance"],
                y=outlier["fare_amount"],
                mode="markers",
                marker=dict(color=_THEME["accent2"], size=7, opacity=0.9, symbol="x"),
                name="Outlier (expensive)",
                hovertemplate="<b>OUTLIER</b><br>Distance: %{x:.1f} mi<br>Fare: $%{y:.2f}<extra></extra>",
            )
        )
    fig.update_layout(
        title="Trip Distance vs Fare Amount",
        xaxis_title="Distance (mi)",
        yaxis_title="Fare ($)",
        template="plotly_dark",
        paper_bgcolor=_THEME["paper"],
        plot_bgcolor=_THEME["bg"],
        font=dict(color=_THEME["text"]),
        xaxis=dict(gridcolor=_THEME["grid"]),
        yaxis=dict(gridcolor=_THEME["grid"]),
        margin=dict(l=50, r=20, t=50, b=40),
        height=380,
    )
    return fig


def tip_rate_bar(df_weekday) -> go.Figure:
    colors = [_THEME["accent"] if r < df_weekday["tip_rate"].max() else _THEME["accent3"]
              for r in df_weekday["tip_rate"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_weekday["weekday_name"],
            y=df_weekday["tip_rate"] * 100,
            marker_color=colors,
            marker_line_width=0,
            text=df_weekday["tip_rate"].apply(lambda x: f"{x*100:.1f}%"),
            textposition="outside",
            textfont=dict(size=11, color=_THEME["text"]),
        )
    )
    fig.update_layout(
        title="Average Tip Rate by Weekday",
        xaxis_title="Day of Week",
        yaxis_title="Tip Rate (%)",
        template="plotly_dark",
        paper_bgcolor=_THEME["paper"],
        plot_bgcolor=_THEME["bg"],
        font=dict(color=_THEME["text"]),
        yaxis=dict(gridcolor=_THEME["grid"], ticksuffix="%"),
        margin=dict(l=50, r=20, t=50, b=40),
        height=380,
    )
    return fig

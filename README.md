# NYC Yellow Taxi Dashboard

Streamlit 看板，用于交互式探索 NYC Yellow Taxi 出行数据。

## 快速启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

首次启动时没有真实数据，程序会自动生成 15 000 条合成行程用于演示。

## 切换真实数据

### 方式一：侧边栏上传

在页面左侧边栏点击 **"Upload your own CSV"** 即可上传文件，格式一致即可实时切换数据源。

### 方式二：替换本地文件

1. 从 [NYC TLC 官网](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) 下载某月的 Yellow Taxi Trip Records（Parquet 或 CSV）。
2. 若下载的是 Parquet，先用 pandas 转为 CSV：

   ```python
   import pandas as pd
   df = pd.read_parquet("yellow_tripdata_2024-03.parquet")
   df.to_csv("data/sample_trips.csv", index=False)
   ```

3. 将生成的 `sample_trips.csv` 放入项目根目录下的 `data/` 文件夹：
   ```
   data/sample_trips.csv
   ```

4. 重新运行 `streamlit run app.py`，程序会优先读取该文件。

## 必需的 CSV 列

| 列名 | 类型 | 说明 |
|---|---|---|
| `tpep_pickup_datetime` | datetime | 上车时间 |
| `tpep_dropoff_datetime` | datetime | 下车时间 |
| `pickup_latitude` | float | 上车纬度 |
| `pickup_longitude` | float | 上车经度 |
| `dropoff_latitude` | float | 下车纬度 |
| `dropoff_longitude` | float | 下车经度 |
| `passenger_count` | int | 乘客数 |
| `trip_distance` | float | 行驶距离（英里） |
| `fare_amount` | float | 计价器费用 |
| `tip_amount` | float | 小费 |
| `total_amount` | float | 总费用 |

列名必须完全一致，缺列会报错提示。

## 数据清洗规则

自动执行的清洗步骤：

1. **负数费用** → 删除 `fare_amount ≤ 0` 的行
2. **行驶距离为零** → 删除 `trip_distance ≤ 0` 的行
3. **时间倒流** → 删除上车时间晚于下车时间的行
4. **坐标越界** → 删除上车经纬度不在 NYC 范围（lat 40.5–41.0, lon -74.3–-73.7）的行

## 项目结构

```
├── app.py           # Streamlit 主页面：筛选控件 + 四宫格布局
├── loader.py        # 数据加载 / 合成数据生成 / 清洗
├── metrics.py       # 指标计算：小时量、热点、异常检测、小费率
├── charts.py        # Plotly 图表渲染
├── requirements.txt
└── data/
    └── sample_trips.csv   （可选，放入真实数据）
```

## 四块看板说明

| 图表 | 说明 |
|---|---|
| Hourly Trip Volume | 24 小时折线图，虚线标注 Top-3 高峰时段 |
| Pickup Hotspots | Scattermapbox 热力图，圆圈大小 = 订单密度 |
| Distance vs Fare | 散点图，IQR × 2.5 以外的异常贵订单用红色 ✕ 高亮 |
| Tip Rate by Weekday | 按星期几的平均小费率柱状图，最高日标黄 |

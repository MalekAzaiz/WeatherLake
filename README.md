# WeatherLake 🌤️

An end-to-end weather data pipeline built on **Azure Data Lake Storage Gen2**, processing raw API data through a medallion architecture and delivering actionable KPIs via a **Power BI** dashboard.

---

## Architecture

```
┌─────────────────────┐
│   Open-Meteo API    │  Free weather API — 14 cities, hourly data
│  (no API key)       │  temperature, humidity, wind, UV, visibility,
└────────┬────────────┘  weather code, precipitation
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Azure Data Lake Storage Gen2           │
│                                                     │
│  ┌─────────┐    ┌──────────┐    ┌────────────────┐ │
│  │   RAW   │───▶│  SILVER  │───▶│      GOLD      │ │
│  │         │    │          │    │                │ │
│  │ JSON    │    │ Cleaned  │    │ current_       │ │
│  │ per     │    │ hourly   │    │ snapshot       │ │
│  │ city /  │    │ + daily  │    │ hourly_24h     │ │
│  │ fetch   │    │ CSV      │    │ forecast_7days │ │
│  └─────────┘    └──────────┘    └────────┬───────┘ │
└─────────────────────────────────────────-│─────────┘
                                           │
                                           ▼
                                ┌─────────────────────┐
                                │  Power BI Dashboard  │
                                │                      │
                                │ • Current conditions │
                                │ • 24h trend          │
                                │ • 7-day forecast     │
                                └─────────────────────┘
```

---

## Pipeline Design

The pipeline follows a **medallion architecture** with three layers:

| Layer | Format | Content |
|---|---|---|
| **Raw** | JSON | Immutable API responses, versioned by city and timestamp |
| **Silver** | CSV | Cleaned, typed, deduplicated hourly and daily data |
| **Gold** | CSV | KPI-ready tables consumed directly by Power BI |

### Gold tables

| File | Description |
|---|---|
| `current_snapshot_latest.csv` | Latest conditions per city (1 row/city) |
| `hourly_24h_latest.csv` | Past 24h + next 24h, hour by hour |
| `forecast_7days_latest.csv` | Daily min/max/weather for the next 7 days |

---

## Dashboard KPIs

**Current conditions (per city)**
- Temperature, humidity, wind speed, UV index, visibility, precipitation
- Weather state (clear, cloudy, rain, etc.)

**24h trend**
- Hourly temperature curve — historical vs forecast
- Weather state evolution

**7-day forecast**
- Daily min / max temperature
- Weather state per day

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data source | Open-Meteo API (free, no key required) |
| Storage | Azure Data Lake Storage Gen2 |
| Processing | Python (pandas, azure-storage-blob) |
| Orchestration | `run_pipeline.py` — single entry point |
| Visualization | Power BI Desktop (direct ADLS Gen2 connection) |

---

## Project Structure

```
WeatherLake/
├── config/
│   ├── settings.py              # Cities list with coordinates
│   └── weathercode_labels.py   # WMO weather code → label mapping
├── ingestion/
│   └── fetch_and_upload.py     # API call → raw layer
├── processing/
│   ├── raw_to_silver.py        # raw → silver (clean & structure)
│   └── silver_to_gold.py       # silver → gold (KPIs & aggregations)
├── run_pipeline.py             # Full pipeline entry point
├── .env                        # Azure credentials (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/MalekAzaiz/WeatherLake.git
cd WeatherLake
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**2. Configure credentials**

Create a `.env` file:
```
AZURE_CONNECTION_STRING=your_connection_string_here
```

**3. Run the pipeline**
```bash
python run_pipeline.py
```

This will:
1. Fetch weather data for all cities → upload to `raw/`
2. Clean and structure data → write to `silver/`
3. Compute KPIs → write 3 CSV files to `gold/`

---

## Cities covered

| Region | Cities |
|---|---|
| France | Paris, Lyon, Marseille, Bordeaux, Lille, Nice |
| Europe | London, Madrid, Berlin, Rome |
| World | New York, Tokyo, Dubai, Sydney |

---

## Key Design Decisions

- **KPIs defined before development** — dashboard requirements drove the pipeline design, not the other way around
- **Medallion architecture** — raw data is never modified, enabling full reprocessing at any time
- **Single `_latest` file per gold table** — simplifies Power BI refresh (one click, no file management)
- **`weathercode` preserved** — enables icon-based visualization in Power BI alongside human-readable labels


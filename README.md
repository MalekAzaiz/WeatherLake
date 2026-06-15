# WeatherLake 🌤️

An end-to-end weather data pipeline built on **Azure Data Lake Storage Gen2**, processing raw API data through a medallion architecture and delivering actionable KPIs via a **Power BI** dashboard.

---

## Versions

| Branch | Orchestration | Status |
|---|---|---|
| [`main`](../../tree/main) | GitHub Actions (cron every 4h) | ✅ Stable |
| [`azure-functions`](../../tree/azure-functions) | Azure Data Factory + Azure Functions | ✅ Stable |

---

## Architecture

```
┌─────────────────────┐
│   Open-Meteo API    │  Free weather API — 15 cities, hourly data
│  (no API key)       │  temperature, humidity, wind, UV, visibility,
└────────┬────────────┘  weather code, precipitation
         │
         ▼
┌────────────────────────────────────────────────────┐
│              Azure Data Lake Storage Gen2          │
│                                                    │
│  ┌─────────┐    ┌──────────┐    ┌────────────────┐ │
│  │   RAW   │───▶│  SILVER  │───▶│      GOLD     │ │
│  │         │    │          │    │                │ │
│  │ JSON    │    │ Cleaned  │    │ current_       │ │
│  │ per     │    │ hourly   │    │ snapshot       │ │
│  │ city /  │    │ + daily  │    │ hourly_24h     │ │
│  │ fetch   │    │ CSV      │    │ forecast_7days │ │
│  └─────────┘    └──────────┘    └────────┬───────┘ │
└──────────────────────────────────────────│─────────┘
                                           │
                         ┌─────────────────┴──────────────────┐
                         │                                    │
                         ▼                                    ▼
              ┌─────────────────────┐           ┌────────────────────────┐
              │   GitHub Actions    │           │   Azure Data Factory   │
              │   (main branch)     │           │  (azure-functions      │
              │   cron every 4h     │           │   branch) every 4h     │
              └─────────────────────┘           │                        │
                                                │  fetch_and_upload →    │
                                                │  raw_to_silver    →    │
                                                │  silver_to_gold        │
                                                │  (Azure Functions)     │
                                                └────────────────────────┘
                                           │
                                           ▼
                                ┌──────────────────────┐
                                │  Power BI Dashboard  │
                                │                      │
                                │ • Current conditions │
                                │ • 24h trend          │
                                │ • 7-day forecast     │
                                └──────────────────────┘
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
| Orchestration (v1) | GitHub Actions (cron schedule) |
| Orchestration (v2) | Azure Data Factory + Azure Functions |
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
├── azure_functions/             # azure-functions branch only
│   ├── function_app.py         # 3 HTTP Azure Functions
│   ├── ingestion/
│   ├── processing/
│   ├── config/
│   └── requirements.txt
├── .github/workflows/
│   └── pipeline.yml            # main branch only
├── run_pipeline.py             # Local pipeline entry point
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

**3. Run locally**
```bash
python run_pipeline.py
```

---

## Automation

### v1 — GitHub Actions (`main` branch)
The pipeline runs automatically every 4 hours via GitHub Actions.
Each run executes `run_pipeline.py` which chains the 3 steps in sequence.
The workflow can also be triggered manually from the GitHub Actions tab.

### v2 — Azure Data Factory (`azure-functions` branch)
The pipeline runs automatically every 4 hours via an ADF schedule trigger.
Each step is an independent **Azure Function** (HTTP trigger) called in sequence by ADF:
1. `fetch_and_upload` — calls Open-Meteo API → uploads JSON to `raw/`
2. `raw_to_silver` — cleans and structures data → writes to `silver/`
3. `silver_to_gold` — computes KPIs → overwrites 3 `_latest` CSV files in `gold/`

---

## Cities covered

| Region | Cities |
|---|---|
| France | Paris, Lyon, Marseille, Bordeaux, Lille, Nice, Grenoble |
| Europe | London, Madrid, Berlin, Rome |
| World | New York, Tokyo, Dubai, Sydney |

---

## Key Design Decisions

- **KPIs defined before development** — dashboard requirements drove the pipeline design, not the other way around
- **Medallion architecture** — raw data is never modified, enabling full reprocessing at any time
- **Single `_latest` file per gold table** — simplifies Power BI refresh (one click, no file management)
- **Azure Functions over Databricks** — lightweight HTTP triggers are sufficient for this workload; Databricks would add unnecessary cost and cold-start latency
- **Two orchestration versions** — GitHub Actions (v1) for simplicity, ADF (v2) for native Azure integration and monitoring
- **`weathercode` preserved** — enables icon-based visualization in Power BI alongside human-readable labels

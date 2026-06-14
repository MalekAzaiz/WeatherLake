import os
import pandas as pd
from io import StringIO
from datetime import datetime, UTC
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.weathercode_labels import WEATHERCODE_LABELS
load_dotenv()


CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_SILVER = "silver"
CONTAINER_GOLD = "gold"


def read_silver(blob_service, blob_name):
    container = blob_service.get_container_client(CONTAINER_SILVER)
    content = container.get_blob_client(blob_name).download_blob().readall()
    return pd.read_csv(StringIO(content.decode("utf-8")))


def upload_gold(blob_service, df, filename):
    container = blob_service.get_container_client(CONTAINER_GOLD)
    blob_name = f"v2/{filename}_latest.csv"
    csv_buffer = df.to_csv(index=False)
    container.get_blob_client(blob_name).upload_blob(csv_buffer, overwrite=True)
    print(f"Gold uploaded: {blob_name} ({len(df)} rows)")


def compute_current_snapshot(hourly_df):
    """1 ligne par ville — valeurs de l'heure la plus récente passée"""
    historical = hourly_df[hourly_df["type"] == "historical"].copy()
    historical["time"] = pd.to_datetime(historical["time"])
    idx = historical.groupby("city")["time"].idxmax()
    return historical.loc[idx].reset_index(drop=True)


def compute_hourly_24h(hourly_df):
    """48h : 24h passées + 24h futures par ville"""
    hourly_df["time"] = pd.to_datetime(hourly_df["time"])
    now = pd.Timestamp.now()
    mask = (hourly_df["time"] >= now - pd.Timedelta(hours=24)) & \
           (hourly_df["time"] <= now + pd.Timedelta(hours=24))
    return hourly_df[mask].sort_values(["city", "time"]).reset_index(drop=True)


def compute_forecast_7days(daily_df):
    """Forecast 7 jours à partir d'aujourd'hui"""
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    today = pd.Timestamp.now().normalize()
    mask = daily_df["date"] >= today
    return daily_df[mask].sort_values(["city", "date"]).reset_index(drop=True)


def main():
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)

    print("Reading silver...")
    hourly_df = read_silver(blob_service, "v2/hourly_latest.csv")
    daily_df = read_silver(blob_service, "v2/daily_latest.csv")

    hourly_df["weather_label"] = hourly_df["weathercode"].map(WEATHERCODE_LABELS)
    daily_df["weather_label"]  = daily_df["weathercode"].map(WEATHERCODE_LABELS)

    print("\nComputing gold tables...")

    current = compute_current_snapshot(hourly_df)
    upload_gold(blob_service, current, "current_snapshot")

    hourly_24h = compute_hourly_24h(hourly_df)
    upload_gold(blob_service, hourly_24h, "hourly_24h")

    forecast = compute_forecast_7days(daily_df)
    upload_gold(blob_service, forecast, "forecast_7days")

    print("\nCurrent snapshot:")
    print(current[["city", "time", "temperature_2m", "weathercode","weather_label","relativehumidity_2m", "windspeed_10m"]].to_string(index=False))

if __name__ == "__main__":
    main()
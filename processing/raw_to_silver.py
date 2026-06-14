import json
import os
import pandas as pd
from io import StringIO
from datetime import datetime, UTC
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import CITIES

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_RAW = "raw"
CONTAINER_SILVER = "silver"


def list_blobs(container_client, city):
    return [b.name for b in container_client.list_blobs(name_starts_with=f"v2/{city}/")]


def read_json_blob(container_client, blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    content = blob_client.download_blob().readall()
    return json.loads(content)


def parse_hourly(data):
    city = data["city"]
    fetched_at = data["fetched_at"]
    hourly = data["hourly"]

    df = pd.DataFrame({
        "time":               pd.to_datetime(hourly["time"]),
        "temperature_2m":     hourly["temperature_2m"],
        "precipitation":      hourly["precipitation"],
        "windspeed_10m":      hourly["windspeed_10m"],
        "relativehumidity_2m": hourly["relativehumidity_2m"],
        "weathercode":        hourly["weathercode"],
        "uv_index":           hourly["uv_index"],
        "visibility":         hourly["visibility"],
    })

    df["city"] = city
    df["fetched_at"] = fetched_at
    df["type"] = df["time"].apply(
        lambda t: "historical" if t <= pd.Timestamp.now() else "forecast"
    )

    return df


def parse_daily(data):
    city = data["city"]
    daily = data["daily"]

    df = pd.DataFrame({
        "date":          pd.to_datetime(daily["time"]),
        "weathercode":   daily["weathercode"],
        "temp_max":      daily["temperature_2m_max"],
        "temp_min":      daily["temperature_2m_min"],
        "uv_index_max":  daily["uv_index_max"],
    })

    df["city"] = city
    return df


def upload_silver(blob_service, df, blob_name):
    container = blob_service.get_container_client(CONTAINER_SILVER)
    csv_buffer = df.to_csv(index=False)
    container.get_blob_client(blob_name).upload_blob(csv_buffer, overwrite=True)
    print(f"✅ Silver uploaded: {blob_name} ({len(df)} rows)")


if __name__ == "__main__":
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    raw_container = blob_service.get_container_client(CONTAINER_RAW)

    all_hourly = []
    all_daily = []

    for city in CITIES:
        print(f"\n🔄 Processing {city}...")
        blobs = list_blobs(raw_container, city)

        hourly_dfs = []
        daily_dfs = []

        for blob_name in blobs:
            data = read_json_blob(raw_container, blob_name)
            hourly_dfs.append(parse_hourly(data))
            daily_dfs.append(parse_daily(data))

        if hourly_dfs:
            hourly_combined = pd.concat(hourly_dfs).drop_duplicates(subset=["city", "time"])
            hourly_combined = hourly_combined.sort_values("time").reset_index(drop=True)
            all_hourly.append(hourly_combined)

        if daily_dfs:
            daily_combined = pd.concat(daily_dfs).drop_duplicates(subset=["city", "date"])
            daily_combined = daily_combined.sort_values("date").reset_index(drop=True)
            all_daily.append(daily_combined)

    # Upload silver consolidé toutes villes
    if all_hourly:
        upload_silver(blob_service, pd.concat(all_hourly).reset_index(drop=True), "v2/hourly_latest.csv")

    if all_daily:
        upload_silver(blob_service, pd.concat(all_daily).reset_index(drop=True), "v2/daily_latest.csv")
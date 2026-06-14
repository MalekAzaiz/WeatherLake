import requests
import json
import os
from datetime import datetime, UTC
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from config.settings import CITIES, MAX_FETCH_ATTEMPTS, FETCH_DELAY
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


CONTAINER_RAW = "raw"
CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")


def fetch_weather(city, lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,windspeed_10m,"
        f"relativehumidity_2m,weathercode,uv_index,visibility"
        f"&daily=weathercode,temperature_2m_max,temperature_2m_min,uv_index_max"
        f"&past_days=2&forecast_days=7"
        f"&timezone=auto"
    )
    for attempt in range(MAX_FETCH_ATTEMPTS):  # N tentatives
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            data["city"] = city
            data["fetched_at"] = datetime.now(UTC).isoformat()
            return data
        except requests.exceptions.Timeout:
            print(f"Timeout for {city}, attempt {attempt + 1}/{MAX_FETCH_ATTEMPTS}")
            if attempt == MAX_FETCH_ATTEMPTS - 1:
                raise
            time.sleep(FETCH_DELAY)

def upload_to_raw(data, city):
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container = blob_service.get_container_client(CONTAINER_RAW)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    blob_name = f"v2/{city}/weather_{timestamp}.json"

    blob_client = container.get_blob_client(blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)
    print(f"Uploaded: {blob_name}")


def main():
    for city, coords in CITIES.items():
        data = fetch_weather(city, coords["lat"], coords["lon"])
        upload_to_raw(data, city)

if __name__ == "__main__":
    main()
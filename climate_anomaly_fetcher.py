#!/usr/bin/env python3
"""
climate_anomaly_fetcher.py – Fetch climate anomalies from Open-Meteo.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = "climate_data.json"
ZONES = [
    {"name": "Horn of Africa", "lat": 1.0, "lng": 42.0},
    {"name": "Sahel", "lat": 15.0, "lng": 0.0},
    {"name": "Middle East", "lat": 28.0, "lng": 45.0},
    {"name": "South Asia", "lat": 22.0, "lng": 78.0},
    {"name": "Central America", "lat": 15.0, "lng": -90.0},
    {"name": "Ukraine", "lat": 49.0, "lng": 32.0},
    {"name": "South China Sea", "lat": 12.0, "lng": 116.0},
]

def fetch_climate_anomaly(lat, lng, days=30):
    """Fetch temperature and precipitation anomalies for a location."""
    end = datetime.now()
    start = end - timedelta(days=days)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lng,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "timezone": "UTC"
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Calculate simple anomaly: last 7 days vs previous 30 days
        daily = data.get('daily', {})
        temps = daily.get('temperature_2m_mean', [])
        precip = daily.get('precipitation_sum', [])
        if len(temps) < 10:
            return {"anomaly": 0, "precip": 0}
        recent = temps[-7:] if len(temps) >= 7 else temps
        historic = temps[:-7] if len(temps) > 7 else temps
        avg_recent = sum(recent) / len(recent) if recent else 0
        avg_historic = sum(historic) / len(historic) if historic else avg_recent
        temp_anomaly = avg_recent - avg_historic
        precip_anomaly = sum(precip[-7:]) - sum(precip[:-7]) if precip else 0
        return {
            "temp_anomaly": round(temp_anomaly, 2),
            "precip_anomaly": round(precip_anomaly, 2),
            "recent_temp_avg": round(avg_recent, 2),
            "historic_temp_avg": round(avg_historic, 2)
        }
    except Exception as e:
        print(f"Climate API error: {e}")
        return None

def main():
    print("🌡️ Fetching climate anomalies...")
    anomalies = []
    for zone in ZONES:
        result = fetch_climate_anomaly(zone['lat'], zone['lng'])
        if result:
            result['name'] = zone['name']
            anomalies.append(result)
    data = {
        "timestamp": datetime.now().isoformat(),
        "zones": anomalies
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Climate data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

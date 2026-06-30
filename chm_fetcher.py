#!/usr/bin/env python3
"""
chm_fetcher.py – M04 Climate Hazard Module
Real‑time hazard maps (floods, fires, heatwaves).
"""
import json
import requests
from datetime import datetime, timezone

# ── NASA EONET already used by AW11; we'll extend with GDACS ──
def fetch_flood_data():
    # Use GDACS or other API
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist?eventtype=FL&alertlevel=Red,Orange,Yellow,Green"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        events = []
        for item in data.get("features", []):
            props = item.get("properties", {})
            events.append({
                "name": props.get("eventname", "Flood"),
                "severity": props.get("alertlevel", "Yellow"),
                "location": props.get("country", "Unknown")
            })
        return events
    except:
        return []

def fetch_fire_data():
    # Use FIRMS or EONET
    try:
        url = "https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires&limit=10"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        events = []
        for item in data.get("events", []):
            events.append({
                "name": item.get("title", "Wildfire"),
                "geometry": item.get("geometry", [])
            })
        return events
    except:
        return []

def fetch_heatwave_data():
    # Simulated — would use climate APIs
    return [{"region": "India", "temp": 46.5, "alert": "Red"}]

def main():
    print("🌍 M04 – CHM running...")
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "floods": fetch_flood_data(),
        "fires": fetch_fire_data(),
        "heatwaves": fetch_heatwave_data()
    }
    with open("chm_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ CHM data saved to chm_data.json")

if __name__ == "__main__":
    main()

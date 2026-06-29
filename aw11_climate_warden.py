#!/usr/bin/env python3
"""
AW11 – Climate Monitoring Warden
Tracks climate hazards: floods, fires, heatwaves, storms.
"""
import json
import requests
from datetime import datetime, timezone

def fetch_nasa_eonet():
    """Fetch natural events from NASA EONET."""
    try:
        url = "https://eonet.gsfc.nasa.gov/api/v3/events"
        params = {"limit": 50, "days": 30}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        events = []
        for item in data.get("events", []):
            categories = [c.get("title", "") for c in item.get("categories", [])]
            geometry = item.get("geometry", [])
            coords = geometry[0].get("coordinates", []) if geometry else []
            
            # Map categories to climate types
            climate_types = ["Wildfires", "Floods", "Storms", "Heatwaves", "Droughts"]
            event_type = categories[0] if categories else "Natural Event"
            # Normalize
            if "fire" in event_type.lower():
                event_type = "Wildfire"
            elif "flood" in event_type.lower():
                event_type = "Flood"
            elif "storm" in event_type.lower() or "cyclone" in event_type.lower():
                event_type = "Storm"
            elif "heat" in event_type.lower():
                event_type = "Heatwave"
            elif "drought" in event_type.lower():
                event_type = "Drought"
            
            events.append({
                "id": item.get("id", f"CL-{len(events)+1}"),
                "name": item.get("title", "Unknown"),
                "type": event_type,
                "lat": coords[1] if len(coords) > 1 else None,
                "lng": coords[0] if len(coords) > 0 else None,
                "date": item.get("last_modified", datetime.now(timezone.utc).isoformat()),
                "source": "NASA EONET"
            })
        return events
    except Exception as e:
        print(f"⚠️ NASA EONET fetch failed: {e}")
        return []

def main():
    print("🌍 AW11 – Climate Monitoring Warden running...")
    events = fetch_nasa_eonet()
    
    output = {
        "source": "AW11 Climate Warden",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "events": events
    }
    
    with open("climate_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved {len(events)} climate events to climate_data.json")

if __name__ == "__main__":
    main()

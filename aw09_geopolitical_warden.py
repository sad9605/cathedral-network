#!/usr/bin/env python3
"""
AW09 – Geopolitical Monitoring Warden
Tracks geopolitical events: treaties, sanctions, diplomatic moves.
"""
import json
import requests
from datetime import datetime, timezone

def fetch_geopolitical_events():
    """Fetch geopolitical events from GDELT (simplified)."""
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": "treaty OR sanctions OR diplomatic OR summit OR peace OR conflict OR agreement",
            "mode": "artlist",
            "format": "json",
            "maxrecords": 20,
            "timespan": "24h"
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        
        events = []
        for article in articles[:20]:
            events.append({
                "title": article.get("title", "Unknown"),
                "source": article.get("source", "Unknown"),
                "date": article.get("seendate", datetime.now(timezone.utc).isoformat()),
                "url": article.get("url", ""),
                "lat": article.get("lat"),
                "lng": article.get("lng")
            })
        return events
    except Exception as e:
        print(f"⚠️ Geopolitical fetch failed: {e}")
        return []

def main():
    print("🌍 AW09 – Geopolitical Monitoring Warden running...")
    events = fetch_geopolitical_events()
    
    output = {
        "source": "AW09 Geopolitical Warden",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "events": events
    }
    
    with open("geopolitical_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved {len(events)} geopolitical events to geopolitical_data.json")

if __name__ == "__main__":
    main()

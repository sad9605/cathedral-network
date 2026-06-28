#!/usr/bin/env python3
"""
hewd_fetcher.py – HEWD Data Fetcher
Pulls humanitarian crisis data from GDACS, ReliefWeb, NASA EONET, and IDMC.
Outputs hewd_data.json for the HEWD Dashboard.
"""
import json
import requests
from datetime import datetime, timezone, timedelta

# ── Configuration ──
GDACS_API = "https://www.gdacs.org/gdacsapi/api/events/geteventlist"
RELIEFWEB_API = "https://api.reliefweb.int/v1/disasters"
EONET_API = "https://eonet.gsfc.nasa.gov/api/v3/events"
HDX_API = "https://hapi.humdata.org/api/v1/"

# ── Crisis Type Mapping ──
CRISIS_TYPES = {
    "EQ": "Earthquake",
    "TC": "Cyclone",
    "FL": "Flood",
    "VO": "Volcano",
    "DR": "Drought",
    "WF": "Wildfire",
    "LS": "Landslide",
    "TS": "Tsunami",
    "HT": "Heatwave",
    "CW": "Cold Wave",
    "SS": "Storm Surge",
    "EP": "Epidemic",
    "FM": "Famine",
    "MV": "Mass Migration",
}

def fetch_gdacs():
    """Fetch active disasters from GDACS."""
    try:
        params = {
            "eventtype": "EQ,TC,FL,VO,DR,WF,LS,TS",
            "alertlevel": "Red,Orange,Yellow,Green",
            "fromdate": (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
            "todate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        response = requests.get(GDACS_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for item in data.get("features", []):
            props = item.get("properties", {})
            coords = item.get("geometry", {}).get("coordinates", [])
            
            # Extract mortality estimate
            mortality = props.get("mortality", {})
            mortality_estimate = mortality.get("estimation", 0)
            
            events.append({
                "id": props.get("eventid", ""),
                "name": props.get("eventname", "Unknown Event"),
                "type": CRISIS_TYPES.get(props.get("eventtype", ""), props.get("eventtype", "Unknown")),
                "alert_level": props.get("alertlevel", "Green"),
                "country": props.get("country", "Unknown"),
                "location": props.get("location", "Unknown"),
                "lat": coords[1] if len(coords) > 1 else None,
                "lng": coords[0] if len(coords) > 0 else None,
                "severity": props.get("severity", 0),
                "mortality_estimate": mortality_estimate,
                "affected_population": props.get("population", {}).get("estimation", 0),
                "status": props.get("status", "Active"),
                "source": "GDACS",
                "url": props.get("eventurl", ""),
                "last_updated": props.get("lastupdate", datetime.now(timezone.utc).isoformat()),
            })
        return events
    except Exception as e:
        print(f"⚠️ GDACS fetch failed: {e}")
        return []

def fetch_reliefweb():
    """Fetch humanitarian crises from ReliefWeb."""
    try:
        params = {
            "limit": 50,
            "fields": "name,description,country,type,date,status,primary_country",
        }
        response = requests.get(RELIEFWEB_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for item in data.get("data", []):
            fields = item.get("fields", {})
            
            # Extract affected population from description or other fields
            affected = 0
            desc = fields.get("description", "")
            if "affected" in desc.lower():
                # Try to extract number from description
                import re
                numbers = re.findall(r'(\d+[,.]?\d*)\s*(?:million|billion|thousand)', desc)
                if numbers:
                    try:
                        affected = int(float(numbers[0].replace(",", "")) * 1000000)
                    except:
                        affected = 0
            
            events.append({
                "id": fields.get("id", ""),
                "name": fields.get("name", "Unknown Crisis"),
                "type": fields.get("type", {}).get("name", "Unknown"),
                "country": fields.get("primary_country", {}).get("name", "Unknown"),
                "description": desc[:300] if desc else "",
                "status": fields.get("status", "Active"),
                "affected_population": affected,
                "source": "ReliefWeb",
                "url": fields.get("url", ""),
                "last_updated": fields.get("date", datetime.now(timezone.utc).isoformat()),
                "lat": None,
                "lng": None,
            })
        return events
    except Exception as e:
        print(f"⚠️ ReliefWeb fetch failed: {e}")
        return []

def fetch_eonet():
    """Fetch natural events from NASA EONET."""
    try:
        params = {
            "limit": 50,
            "days": 30,
        }
        response = requests.get(EONET_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for item in data.get("events", []):
            categories = [c.get("title", "") for c in item.get("categories", [])]
            geometry = item.get("geometry", [])
            coords = geometry[0].get("coordinates", []) if geometry else []
            
            events.append({
                "id": item.get("id", ""),
                "name": item.get("title", "Unknown Event"),
                "type": categories[0] if categories else "Natural Event",
                "description": item.get("description", ""),
                "lat": coords[1] if len(coords) > 1 else None,
                "lng": coords[0] if len(coords) > 0 else None,
                "source": "NASA EONET",
                "url": item.get("link", ""),
                "last_updated": item.get("last_modified", datetime.now(timezone.utc).isoformat()),
                "status": "Active",
                "mortality_estimate": 0,
                "affected_population": 0,
            })
        return events
    except Exception as e:
        print(f"⚠️ NASA EONET fetch failed: {e}")
        return []

def fetch_idmc():
    """Fetch internal displacement data from IDMC via HDX HAPI."""
    try:
        # Using HDX HAPI for displacement data
        params = {
            "resource-id": "internal-displacement-updates",
            "limit": 50,
        }
        response = requests.get(HDX_API + "indicator-values", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            location = attrs.get("location", {})
            
            events.append({
                "id": f"IDMC-{len(events)+1}",
                "name": f"Displacement in {location.get('name', 'Unknown')}",
                "type": "Mass Migration",
                "country": location.get("name", "Unknown"),
                "affected_population": attrs.get("value", 0),
                "description": f"Internal displacement event reported in {location.get('name', 'Unknown')}",
                "source": "IDMC/HDX",
                "status": "Active",
                "last_updated": attrs.get("period_start", datetime.now(timezone.utc).isoformat()),
                "lat": None,
                "lng": None,
                "mortality_estimate": 0,
            })
        return events
    except Exception as e:
        print(f"⚠️ IDMC fetch failed: {e}")
        return []

def combine_and_rank(events):
    """Combine all events, rank by mortality and severity."""
    for e in events:
        # Calculate a priority score (0-100)
        mortality_weight = min(e.get("mortality_estimate", 0) / 1000, 50)
        affected_weight = min(e.get("affected_population", 0) / 1000000, 30)
        severity_weights = {"Red": 20, "Orange": 10, "Yellow": 5, "Green": 0}
        severity_weight = severity_weights.get(e.get("alert_level", ""), 0)
        
        e["priority_score"] = mortality_weight + affected_weight + severity_weight
        e["priority_score"] = min(e["priority_score"], 100)
    
    # Sort by priority score
    events.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    return events

def main():
    print("🌍 HEWD Data Fetcher running...")
    
    # Fetch from all sources
    all_events = []
    all_events.extend(fetch_gdacs())
    all_events.extend(fetch_reliefweb())
    all_events.extend(fetch_eonet())
    all_events.extend(fetch_idmc())
    
    # Deduplicate by name and location
    seen = set()
    unique_events = []
    for e in all_events:
        key = f"{e.get('name', '')}-{e.get('country', '')}-{e.get('type', '')}"
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    
    # Rank and save
    ranked = combine_and_rank(unique_events)
    
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_crises": len(ranked),
        "critical": len([e for e in ranked if e.get("priority_score", 0) > 70]),
        "watch": len([e for e in ranked if 40 <= e.get("priority_score", 0) <= 70]),
        "monitor": len([e for e in ranked if e.get("priority_score", 0) < 40]),
        "events": ranked[:100]  # Keep top 100
    }
    
    with open("hewd_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ HEWD data saved: {len(ranked)} events, {output['critical']} critical")

if __name__ == "__main__":
    main()

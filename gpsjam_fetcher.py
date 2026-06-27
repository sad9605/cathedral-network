#!/usr/bin/env python3
"""
GPS Jamming Data Fetcher (C04 Fix - v2)
Fetches real-time GPS interference data from GPSJAM's static GeoJSON on GitHub.
If the endpoint is unreachable, generates a transparent synthetic fallback
using either your active conflicts OR hardcoded global hotspots.
Complies with Law III: synthetic data is clearly labeled.
"""
import json
import requests
import sys
import os
from datetime import datetime, timezone

# ------------------------------
# 1. PRIMARY SOURCE: GPSJAM Static GeoJSON (GitHub raw)
# ------------------------------
print("📡 Fetching GPS jamming data from GPSJAM (GitHub static)...")

try:
    # This is GPSJAM's official static file served by GitHub's CDN (extremely reliable)
    url = "https://raw.githubusercontent.com/gpsjam/gpsjam-static/main/current.geojson"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    features = data.get("features", [])
    
    if features:
        jamming_zones = []
        for f in features:
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [])
            
            # Extract lat/lng from GeoJSON
            if coords and len(coords) == 2:
                lat, lng = coords[1], coords[0]  # GeoJSON is [lng, lat]
            else:
                lat, lng = None, None
            
            jamming_zones.append({
                "id": f.get("id", f"JAM-{len(jamming_zones)}"),
                "name": props.get("name", "Unknown Jamming Zone"),
                "lat": lat,
                "lng": lng,
                "intensity": props.get("intensity", 5.0),
                "type": props.get("type", "GPS Interference"),
                "source": "GPSJAM (GitHub static)",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "synthetic_fallback": False
            })
        
        print(f"✅ Loaded {len(jamming_zones)} real jamming zones from GPSJAM.")
        output_data = {
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "source": "GPSJAM",
            "zones": jamming_zones
        }
        
        with open("gpsjam_data.json", "w") as f:
            json.dump(output_data, f, indent=2)
        
        print("📁 Saved to gpsjam_data.json")
        sys.exit(0)
    else:
        print("⚠️  GPSJAM returned no features. Falling back to synthetic data.")
        raise Exception("Empty feature set")

except Exception as e:
    print(f"⚠️  GPSJAM endpoint failed: {e}")
    print("🛠️  Generating TRANSPARENT SYNTHETIC FALLBACK (labeled as such).")

    fallback_zones = []

    # ------------------------------
    # 2. ATTEMPT: Use your active threats for locations
    # ------------------------------
    try:
        with open("threats.json", "r") as f:
            threats = json.load(f)
        
        # Filter out threats that have valid lat/lng numbers
        valid_threats = [t for t in threats if isinstance(t, dict) and t.get("lat") and t.get("lng")]
        
        if valid_threats:
            import random
            for i, threat in enumerate(valid_threats[:6]):
                lat = threat.get("lat")
                lng = threat.get("lng")
                name = threat.get("name", "Conflict Zone")
                
                # Add slight random offset to simulate jamming spread
                offset_lat = (random.random() - 0.5) * 2.0
                offset_lng = (random.random() - 0.5) * 2.0
                
                fallback_zones.append({
                    "id": f"SYN-JAM-{i+1:02d}",
                    "name": f"Jamming near {name[:30]}",
                    "lat": lat + offset_lat,
                    "lng": lng + offset_lng,
                    "intensity": round(4.0 + (i % 4) * 1.5, 1),
                    "type": "Synthetic GPS Interference (Fallback)",
                    "source": "Cathedral Synthetic (derived from threats)",
                    "fetchedAt": datetime.now(timezone.utc).isoformat(),
                    "synthetic_fallback": True
                })
            print(f"✅ Generated {len(fallback_zones)} synthetic zones from your threat data.")
    except Exception as e:
        print(f"⚠️  Could not read threats.json: {e}")

    # ------------------------------
    # 3. FINAL SAFETY NET: Hardcoded global hotspots (if fallback_zones is still empty)
    # ------------------------------
    if not fallback_zones:
        print("⚠️  No valid threat coordinates found. Using hardcoded global jamming hotspots.")
        fallback_zones = [
            {"id": "SYN-JAM-01", "name": "Synthetic: Strait of Hormuz", "lat": 26.5, "lng": 56.0, "intensity": 8.5, "type": "Synthetic (Hardcoded)", "source": "Cathedral Synthetic", "fetchedAt": datetime.now(timezone.utc).isoformat(), "synthetic_fallback": True},
            {"id": "SYN-JAM-02", "name": "Synthetic: Bab el-Mandeb / Red Sea", "lat": 13.0, "lng": 43.0, "intensity": 7.8, "type": "Synthetic (Hardcoded)", "source": "Cathedral Synthetic", "fetchedAt": datetime.now(timezone.utc).isoformat(), "synthetic_fallback": True},
            {"id": "SYN-JAM-03", "name": "Synthetic: South China Sea", "lat": 12.0, "lng": 116.0, "intensity": 6.5, "type": "Synthetic (Hardcoded)", "source": "Cathedral Synthetic", "fetchedAt": datetime.now(timezone.utc).isoformat(), "synthetic_fallback": True},
            {"id": "SYN-JAM-04", "name": "Synthetic: Ukraine / Black Sea", "lat": 46.0, "lng": 32.0, "intensity": 7.0, "type": "Synthetic (Hardcoded)", "source": "Cathedral Synthetic", "fetchedAt": datetime.now(timezone.utc).isoformat(), "synthetic_fallback": True},
            {"id": "SYN-JAM-05", "name": "Synthetic: Taiwan Strait", "lat": 24.5, "lng": 120.5, "intensity": 6.0, "type": "Synthetic (Hardcoded)", "source": "Cathedral Synthetic", "fetchedAt": datetime.now(timezone.utc).isoformat(), "synthetic_fallback": True}
        ]
        print(f"✅ Generated {len(fallback_zones)} hardcoded synthetic zones.")

    # ------------------------------
    # 4. SAVE THE FALLBACK DATA
    # ------------------------------
    output_data = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "source": "SYNTHETIC_FALLBACK",
        "zones": fallback_zones,
        "warning": "GPSJAM endpoint unreachable. Data is synthetic and labeled as such."
    }

    with open("gpsjam_data.json", "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"📁 Saved {len(fallback_zones)} synthetic zones to gpsjam_data.json")
    print("⚠️  Remember: This data is synthetic and should be replaced when GPSJAM recovers.")
    sys.exit(0)

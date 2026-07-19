#!/usr/bin/env python3
"""
satellite_fetcher.py – Cathedral Satellite Intelligence Layer
Fetches Sentinel‑2, Sentinel‑1, and MODIS/VIIRS data for AOIs.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ── Sentinel Hub ──
try:
    from sentinelhub import (
        SHConfig, SentinelHubRequest, BBox, CRS,
        MimeType, DataCollection, bbox_to_dimensions
    )
except ImportError:
    print("⚠️ sentinelhub not installed. Run: pip install sentinelhub")
    exit(1)

# ── NASA Earthdata ──
try:
    import earthaccess
except ImportError:
    print("⚠️ earthaccess not installed. Run: pip install earthaccess")
    exit(1)

# ── Configuration ──
CONFIG = SHConfig()
CONFIG.sh_client_id = os.environ.get('CDSE_CLIENT_ID', '')
CONFIG.sh_client_secret = os.environ.get('CDSE_CLIENT_SECRET', '')

if not CONFIG.sh_client_id or not CONFIG.sh_client_secret:
    print("⚠️ CDSE credentials not set. Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET environment variables.")
    print("   Get them from: https://dataspace.copernicus.eu")
    exit(1)

# ── Areas of Interest ──
AOIS = [
    {"name": "Ukraine", "lat_min": 44.0, "lat_max": 52.0, "lng_min": 22.0, "lng_max": 40.0},
    {"name": "Gaza", "lat_min": 31.0, "lat_max": 31.8, "lng_min": 34.0, "lng_max": 35.5},
    {"name": "Horn of Africa", "lat_min": -5.0, "lat_max": 15.0, "lng_min": 30.0, "lng_max": 52.0},
    {"name": "Sudan", "lat_min": 8.0, "lat_max": 22.0, "lng_min": 21.0, "lng_max": 39.0},
    {"name": "South China Sea", "lat_min": 2.0, "lat_max": 22.0, "lng_min": 102.0, "lng_max": 122.0},
    {"name": "Amazon Basin", "lat_min": -22.0, "lat_max": 2.0, "lng_min": -74.0, "lng_max": -48.0},
]

# ── Functions ──
def fetch_sentinel2(aoi_name: str, bbox: List[float], start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch Sentinel-2 NDVI and true-color imagery."""
    bbox_obj = BBox(bbox, crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox_obj, resolution=10)

    evalscript = """
    // NDVI + RGB + true-color composite
    function setup() {
        return {
            input: ["B02", "B03", "B04", "B08"],
            output: { bands: 4 }
        };
    }
    function evaluatePixel(sample) {
        let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
        // Return RGB + NDVI (scaled to 0-1 for PNG)
        return [sample.B04, sample.B03, sample.B02, ndvi];
    }
    """

    try:
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start_date, end_date),
                    maxcc=0.3
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.PNG)
            ],
            bbox=bbox_obj,
            size=size,
            config=CONFIG
        )
        images = request.get_data()
        if images:
            return {
                "aoi": aoi_name,
                "timestamp": end_date,
                "status": "success",
                "image_shape": images[0].shape,
                "image_data": images[0].tolist()  # Convert for JSON
            }
        else:
            return {"aoi": aoi_name, "status": "no_data"}
    except Exception as e:
        return {"aoi": aoi_name, "status": "error", "error": str(e)}

def fetch_modis_fires(aoi_name: str, bbox: List[float]) -> Dict[str, Any]:
    """Fetch active fire data from NASA FIRMS."""
    try:
        # Use earthaccess to query MODIS fire data
        auth = earthaccess.login(strategy="interactive", persist=True)
        results = earthaccess.search_data(
            short_name="MOD14A1",
            bounding_box=(bbox[0], bbox[1], bbox[2], bbox[3]),
            count=5,
            temporal=("2026-07-01", "2026-07-13")
        )
        return {
            "aoi": aoi_name,
            "status": "success",
            "fire_detections": len(results),
            "granules": [r.data_links() for r in results[:3]]
        }
    except Exception as e:
        return {"aoi": aoi_name, "status": "error", "error": str(e)}

def main():
    print("🛰️ Cathedral Satellite Intelligence — Fetching data...")
    end_date = datetime.now().isoformat()
    start_date = (datetime.now() - timedelta(days=7)).isoformat()

    results = []
    for aoi in AOIS:
        bbox = [aoi['lng_min'], aoi['lat_min'], aoi['lng_max'], aoi['lat_max']]
        print(f"📡 Fetching {aoi['name']}...")
        sentinel = fetch_sentinel2(aoi['name'], bbox, start_date, end_date)
        # fire = fetch_modis_fires(aoi['name'], bbox)  # Uncomment when earthaccess is configured
        results.append(sentinel)
        time.sleep(1)

    output = {
        "timestamp": end_date,
        "source": "CDSE + NASA Earthdata",
        "aois_processed": len(results),
        "results": results
    }

    with open("satellite_report.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Satellite data saved to satellite_report.json")
    print(f"   {len(results)} AOIs processed.")

if __name__ == "__main__":
    main()

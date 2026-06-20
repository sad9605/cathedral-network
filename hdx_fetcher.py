#!/usr/bin/env python3
"""
hdx_fetcher.py – Fetch humanitarian indicators from HDX HAPI.
"""

import json
import requests
from datetime import datetime

HDX_API = "https://api.hapi.humdata.org/v1"
OUTPUT_FILE = "hdx_data.json"

def fetch_food_security():
    # Example endpoint – adjust based on actual HAPI docs
    url = f"{HDX_API}/indicator/food-security"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching HDX food security: {e}")
        return {}

def fetch_conflict():
    url = f"{HDX_API}/indicator/conflict"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching HDX conflict: {e}")
        return {}

def main():
    data = {
        "timestamp": datetime.now().isoformat(),
        "food_security": fetch_food_security(),
        "conflict": fetch_conflict()
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ HDX data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

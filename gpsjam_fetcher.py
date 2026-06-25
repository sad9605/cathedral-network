#!/usr/bin/env python3
"""
gpsjam_fetcher.py – Fetch GPS interference data from gpsjam.org.
"""

import json
import requests
import csv
import io
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = "gpsjam_data.json"

def fetch_gpsjam():
    """Fetch GPS jamming data (CSV from gpsjam.org)."""
    url = "https://data.gpsjam.org/static/latest_high_activity.csv"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        reader = csv.reader(io.StringIO(resp.text))
        rows = []
        for row in reader:
            if len(row) >= 3:
                rows.append({
                    "lat": row[0],
                    "lng": row[1],
                    "intensity": row[2]
                })
        return {"source": "GPSJAM", "count": len(rows), "points": rows[:50]}
    except Exception as e:
        print(f"GPSJAM error: {e}")
        return {}

def main():
    print("🛰️ Fetching GPS jamming data...")
    data = {
        "timestamp": datetime.now().isoformat(),
        "jamming": fetch_gpsjam()
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ GPS jamming data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

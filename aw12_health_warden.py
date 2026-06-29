#!/usr/bin/env python3
"""
AW12 – Health Monitoring Warden
Tracks outbreaks, pandemics, food security.
"""
import json
import requests
from datetime import datetime, timezone

def fetch_who_outbreaks():
    """Fetch WHO outbreak data (mocked for now)."""
    # WHO API requires registration — we'll use a mock until real API is available
    return [
        {"name": "H5N1 Bird Flu", "status": "Active", "region": "North America"},
        {"name": "Marburg Virus", "status": "Active", "region": "East Africa"},
        {"name": "Dengue Fever", "status": "Active", "region": "South America"},
        {"name": "Measles", "status": "Active", "region": "India"},
        {"name": "Cholera", "status": "Active", "region": "Yemen"}
    ]

def main():
    print("🩺 AW12 – Health Monitoring Warden running...")
    
    outbreaks = fetch_who_outbreaks()
    
    output = {
        "source": "AW12 Health Warden",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "outbreaks": outbreaks
    }
    
    with open("health_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved {len(outbreaks)} health events to health_data.json")

if __name__ == "__main__":
    main()

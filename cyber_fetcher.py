#!/usr/bin/env python3
"""
cyber_fetcher.py – Fetch cyber threat intelligence from free feeds.
"""

import json
import requests
import csv
import io
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = "cyber_data.json"

def fetch_feodo_tracker():
    """Fetch C2 IPs from Feodo Tracker (abuse.ch)."""
    url = "https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.txt"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        ips = []
        for line in resp.text.splitlines():
            if line and not line.startswith('#'):
                ips.append(line.strip())
        return {"source": "Feodo Tracker", "count": len(ips), "ips": ips[:50]}
    except Exception as e:
        print(f"Feodo error: {e}")
        return {}

def fetch_urlhaus():
    """Fetch recent URLhaus (malware URLs) data."""
    url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        # CSV format
        reader = csv.reader(io.StringIO(resp.text))
        rows = []
        for row in reader:
            if len(row) > 5 and row[0] != '#id':
                rows.append({"url": row[1], "status": row[4], "date": row[2]})
        return {"source": "URLhaus", "count": len(rows), "urls": rows[:20]}
    except Exception as e:
        print(f"URLhaus error: {e}")
        return {}

def fetch_abuseipdb():
    """Fetch AbuseIPDB blocklist (requires API key)."""
    # Free tier requires API key; we'll skip if not set
    import os
    api_key = os.environ.get('ABUSEIPDB_API_KEY')
    if not api_key:
        return {"source": "AbuseIPDB", "status": "API key missing"}
    url = "https://api.abuseipdb.com/api/v2/blacklist"
    headers = {"Key": api_key, "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return {"source": "AbuseIPDB", "count": len(data.get('data', [])), "ips": data.get('data', [])[:20]}
    except Exception as e:
        print(f"AbuseIPDB error: {e}")
        return {}

def main():
    print("🌐 Fetching cyber threat intelligence...")
    data = {
        "timestamp": datetime.now().isoformat(),
        "feodo": fetch_feodo_tracker(),
        "urlhaus": fetch_urlhaus(),
        "abuseipdb": fetch_abuseipdb()
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Cyber data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

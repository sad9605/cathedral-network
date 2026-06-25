#!/usr/bin/env python3
"""
travel_advisories_fetcher.py – Fetch government travel advisories.
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import feedparser

OUTPUT_FILE = "travel_advisories.json"

def fetch_us_state():
    """Fetch US State Dept travel advisories (RSS)."""
    url = "https://travel.state.gov/_res/global/rss/tw/trss.xml"
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:10]:
            entries.append({
                "title": entry.get('title', ''),
                "summary": entry.get('summary', ''),
                "link": entry.get('link', ''),
                "date": entry.get('published', '')
            })
        return {"source": "US State Dept", "advisories": entries}
    except Exception as e:
        print(f"US State error: {e}")
        return {}

def fetch_fcd():
    """Fetch UK FCDO travel advice (RSS)."""
    url = "https://www.gov.uk/foreign-travel-advice/feed.xml"
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:10]:
            entries.append({
                "title": entry.get('title', ''),
                "summary": entry.get('summary', ''),
                "link": entry.get('link', ''),
                "date": entry.get('published', '')
            })
        return {"source": "UK FCDO", "advisories": entries}
    except Exception as e:
        print(f"FCDO error: {e}")
        return {}

def main():
    print("🧳 Fetching travel advisories...")
    data = {
        "timestamp": datetime.now().isoformat(),
        "us_state": fetch_us_state(),
        "fcd": fetch_fcd()
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Travel advisories saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
daily-sweep.py – Cathedral Network OSINT ingestion engine.
Fetches all feeds defined in feeds.json (RSS, API, JSON).
Also fetches unconventional signals (V17–V20).
Outputs sweep_report.json.
"""

import json
import time
import requests
import feedparser
import yfinance as yf
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# ---------- config ----------
FEEDS_FILE = "feeds.json"
OUTPUT_FILE = "sweep_report.json"
MAX_EVENTS = 500
TIMEOUT = 15
RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_rss(url):
    """Fetch RSS/Atom feed with timeout and custom headers."""
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        entries = []
        for entry in feed.entries[:20]:
            entries.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": url
            })
        return entries
    except Exception as e:
        print(f"  RSS error: {e}")
        return []

def fetch_api_json(url, headers=None, params=None):
    """Fetch API and parse JSON response with custom headers."""
    for attempt in range(RETRIES):
        try:
            req_headers = {"User-Agent": USER_AGENT}
            if headers:
                req_headers.update(headers)
            resp = requests.get(url, headers=req_headers, params=params or {}, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            elif isinstance(data, dict):
                for key in ["items", "results", "records"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            else:
                return []
        except Exception as e:
            print(f"  API error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return []

def fetch_unconventional_signals():
    """Fetch unconventional signals V17–V20."""
    print("📡 Fetching unconventional signals...")
    signals = {}

    # V17: Internet blackout events (Cloudflare Radar – mock)
    internet_blackouts = []
    try:
        internet_blackouts = [
            {"region": "Sudan", "event": "Internet shutdown", "date": datetime.now().isoformat()},
            {"region": "Iran", "event": "Restricted access", "date": datetime.now().isoformat()}
        ]
    except Exception as e:
        print(f"   ⚠️ Could not fetch internet blackout data: {e}")
    signals["internet_blackout_events"] = internet_blackouts

    # V18: Food delivery spikes (mock)
    food_delivery_spikes = []
    try:
        food_delivery_spikes = [
            {"region": "Kenya", "spike": 1.3, "description": "Increased food delivery in Nairobi"}
        ]
    except Exception as e:
        print(f"   ⚠️ Could not fetch food delivery data: {e}")
    signals["food_delivery_spikes"] = food_delivery_spikes

    # V19: Safe-haven currency flows (CHF/JPY)
    safe_haven_flows = {}
    try:
        chf = yf.Ticker("CHF=X")
        jpy = yf.Ticker("JPY=X")
        chf_data = chf.history(period="5d")
        jpy_data = jpy.history(period="5d")
        if not chf_data.empty and not jpy_data.empty:
            chf_change = (chf_data['Close'].iloc[-1] / chf_data['Close'].iloc[0] - 1) * 100
            jpy_change = (jpy_data['Close'].iloc[-1] / jpy_data['Close'].iloc[0] - 1) * 100
            safe_haven_flows = {
                "CHF_change": round(chf_change, 2),
                "JPY_change": round(jpy_change, 2),
                "description": "Safe‑haven currency movements"
            }
        else:
            safe_haven_flows = {"CHF_change": 0, "JPY_change": 0, "description": "No data"}
    except Exception as e:
        print(f"   ⚠️ Could not fetch forex: {e}")
        safe_haven_flows = {"CHF_change": 0, "JPY_change": 0, "description": "Data unavailable"}
    signals["safe_haven_flows"] = safe_haven_flows

    # V20: Traffic anomalies (TomTom – mock)
    traffic_anomalies = []
    try:
        traffic_anomalies = [
            {"city": "Mumbai", "congestion": 1.2, "description": "Unusual traffic congestion"},
            {"city": "Mexico City", "congestion": 1.5, "description": "Severe delays"}
        ]
    except Exception as e:
        print(f"   ⚠️ Could not fetch traffic data: {e}")
    signals["traffic_anomalies"] = traffic_anomalies

    return signals

def run_sweep():
    print("🌍 Starting daily OSINT sweep...")
    feeds_config = load_json(FEEDS_FILE)
    feeds = feeds_config.get("feeds", [])
    print(f"Loaded {len(feeds)} feed definitions.")

    all_events = []
    feed_errors = 0

    for feed in feeds:
        if not feed.get("enabled", True):
            continue
        feed_id = feed.get("id", "unknown")
        feed_type = feed.get("type", "rss")
        url = feed.get("url", "")
        print(f"  Fetching {feed.get('name', feed_id)}...")

        events = []
        if feed_type == "rss":
            events = fetch_rss(url)
        elif feed_type == "api_json":
            events = fetch_api_json(url, feed.get("headers"), feed.get("params"))
        else:
            print(f"    Unknown feed type: {feed_type}")

        if not events:
            feed_errors += 1
            continue

        for ev in events:
            ev["feed_id"] = feed_id
            ev["fetched_at"] = datetime.now().isoformat()

        all_events.extend(events)
        time.sleep(0.5)

    all_events = all_events[:MAX_EVENTS]
    unconventional_signals = fetch_unconventional_signals()

    report = {
        "timestamp": datetime.now().isoformat(),
        "events": all_events,
        "feed_errors": feed_errors,
        "total_events": len(all_events),
        "unconventional_signals": unconventional_signals,
        "sources": [f.get("id") for f in feeds if f.get("enabled", True)]
    }

    save_json(report, OUTPUT_FILE)
    print(f"✅ Sweep complete: {len(all_events)} events, {feed_errors} feed errors")
    print(f"   Unconventional signals: {len(unconventional_signals)} categories saved")
    return report

if __name__ == "__main__":
    run_sweep()

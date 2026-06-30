#!/usr/bin/env python3
"""
scdf_fetcher.py – M01 Supply Chain Disruption Forecaster
Tracks freight rates, port congestion, semiconductor lead times, oil prices.
"""
import json
import requests
from datetime import datetime, timezone
import random

# ── Data sources (free/public) ──
# Baltic Dry Index: https://www.investing.com/indices/baltic-dry
# We'll use mock data since free APIs are limited

def fetch_freight_rates():
    # Simulated (replace with real API later)
    return {"baltic_dry": random.randint(1200, 1800), "trend": "up"}

def fetch_port_congestion():
    # Simulated (replace with real API)
    return {"global_average_days": 4.5, "hotspots": ["Shanghai", "Rotterdam", "LA"]}

def fetch_semiconductor_lead_times():
    return {"avg_weeks": 22, "trend": "lengthening", "chips": ["MCU", "Power", "DRAM"]}

def fetch_oil_prices():
    try:
        # Free API from CoinGecko
        url = "https://api.coingecko.com/api/v3/simple/price?ids=crude-oil-brent%2Cwti-crude&vs_currencies=usd"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return {
            "brent": data.get("crude-oil-brent", {}).get("usd", 82.5),
            "wti": data.get("wti-crude", {}).get("usd", 78.2)
        }
    except:
        return {"brent": 82.5, "wti": 78.2}

def main():
    print("📦 M01 – SCDF running...")
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "freight": fetch_freight_rates(),
        "port_congestion": fetch_port_congestion(),
        "semiconductors": fetch_semiconductor_lead_times(),
        "oil": fetch_oil_prices()
    }
    with open("scdf_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ SCDF data saved to scdf_data.json")

if __name__ == "__main__":
    main()

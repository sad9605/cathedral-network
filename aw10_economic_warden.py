#!/usr/bin/env python3
"""
AW10 – Economic Monitoring Warden
Tracks markets, commodities, supply chains.
"""
import json
import requests
from datetime import datetime, timezone

def fetch_commodity_prices():
    """Fetch commodity prices from a free API (e.g., Yahoo Finance via rapidapi or mock)."""
    # For now, use a mock since free commodity APIs require keys
    # We'll replace with real API later
    return {
        "brent": 82.50,
        "wti": 78.20,
        "gold": 2350.00,
        "copper": 4.80,
        "wheat": 620.00,
        "corn": 440.00
    }

def main():
    print("📊 AW10 – Economic Monitoring Warden running...")
    
    # Fetch commodity prices
    commodities = fetch_commodity_prices()
    
    output = {
        "source": "AW10 Economic Warden",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "commodities": commodities
    }
    
    with open("economic_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved economic data to economic_data.json")

if __name__ == "__main__":
    main()

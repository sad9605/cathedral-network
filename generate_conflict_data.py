#!/usr/bin/env python3
"""
generate_conflict_data.py – Generate conflict monitor data with accurate coordinates.
"""

import json
from pathlib import Path
from datetime import datetime

THREATS_FILE = "threats.json"
HISTORY_FILE = "scp_history.json"
TREND_FILE = "trend.json"
OUTPUT_FILE = "conflict_data.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# ----- COMPREHENSIVE COORDINATE MAP (ALL KNOWN THREATS) -----
COORDINATE_MAP = {
    # Existing geopolitical conflicts
    'C01': {'lat': 26.5, 'lng': 56.5},
    'C-USIRAN': {'lat': 30.0, 'lng': 50.0},
    'C-BELT': {'lat': 28.0, 'lng': 52.0},
    'C-RED-BLOCK': {'lat': 13.0, 'lng': 43.0},
    'C132': {'lat': 35.0, 'lng': 38.0},
    'C129': {'lat': 40.5, 'lng': 45.0},
    'C54': {'lat': 55.0, 'lng': 25.0},
    'C88': {'lat': 23.5, 'lng': 120.0},
    'C90': {'lat': 12.0, 'lng': 116.0},
    'C48': {'lat': 38.0, 'lng': 23.0},
    'C19': {'lat': 47.5, 'lng': 34.5},
    'C25': {'lat': 45.0, 'lng': 25.0},
    'C3': {'lat': 48.0, 'lng': 30.0},
    'C11': {'lat': 33.0, 'lng': 44.0},
    'C58': {'lat': 56.0, 'lng': 15.0},
    'C60': {'lat': 59.0, 'lng': 27.0},
    'C64': {'lat': 35.0, 'lng': 18.0},
    'C85': {'lat': 24.0, 'lng': -102.0},
    'C122': {'lat': 39.0, 'lng': 127.0},
    'C2': {'lat': 38.0, 'lng': 23.0},
    'C4': {'lat': 47.0, 'lng': 29.0},
    'CA4': {'lat': 45.0, 'lng': 65.0},
    'C11E': {'lat': 28.0, 'lng': 50.0},
    'C106': {'lat': 30.0, 'lng': 30.0},
    'C139': {'lat': 15.0, 'lng': 25.0},
    'C126': {'lat': 20.0, 'lng': 10.0},
    'C134': {'lat': 15.0, 'lng': -30.0},
    'C147': {'lat': -75.0, 'lng': 20.0},
    'C100': {'lat': 75.0, 'lng': -40.0},
    'A-STRAT-RES': {'lat': 30.0, 'lng': 45.0},
    'C03': {'lat': 5.0, 'lng': 45.0},
    'C-STRAT-OIL': {'lat': 28.0, 'lng': 50.0},
    'C-SEMI-DROUGHT': {'lat': 20.0, 'lng': 10.0},
    'C-PANDEMIC': {'lat': 20.0, 'lng': 30.0},
    'C-CYBER': {'lat': 35.0, 'lng': 20.0},
    
    # Additional geopolitical threats
    'C02': {'lat': 34.0, 'lng': 35.0},  # Example (add as needed)
    'C05': {'lat': 40.0, 'lng': -75.0}, # Example

    # Economic threats
    'P001': {'lat': 35.0, 'lng': 40.0},
    'P002': {'lat': 28.0, 'lng': 77.0},
    'P003': {'lat': 35.0, 'lng': 139.0},
    'P004': {'lat': 55.0, 'lng': 25.0},
    'P005': {'lat': 5.0, 'lng': 45.0},
    'P006': {'lat': 22.0, 'lng': 114.0},
    'P007': {'lat': 38.0, 'lng': -97.0},
    'P008': {'lat': 46.0, 'lng': 8.0},
    'P009': {'lat': 40.0, 'lng': 45.0},
    'P010': {'lat': 32.0, 'lng': 53.0},
    'P021': {'lat': 15.0, 'lng': 30.0},
    'P033': {'lat': 25.0, 'lng': 121.0},
    'P041': {'lat': 50.0, 'lng': 20.0},
    'P055': {'lat': 38.0, 'lng': -97.0},
    'P089': {'lat': 46.0, 'lng': 8.0},

    # Supply chain / trade threats
    'SC01': {'lat': 30.0, 'lng': 45.0},
    'SC02': {'lat': 1.0, 'lng': 103.0},
    'SC03': {'lat': 20.0, 'lng': -100.0},
}

# ----- EXTENDED COUNTRY/REGION KEYWORD MAP -----
KEYWORD_MAP = {
    # Middle East
    'iran': {'lat': 32.4, 'lng': 53.7},
    'israel': {'lat': 31.0, 'lng': 34.8},
    'iraq': {'lat': 33.0, 'lng': 44.0},
    'syria': {'lat': 34.8, 'lng': 38.9},
    'lebanon': {'lat': 33.8, 'lng': 35.8},
    'jordan': {'lat': 31.0, 'lng': 36.0},
    'saudi arabia': {'lat': 23.9, 'lng': 45.0},
    'yemen': {'lat': 15.0, 'lng': 48.0},
    'oman': {'lat': 21.0, 'lng': 57.0},
    'uae': {'lat': 24.0, 'lng': 54.0},
    'qatar': {'lat': 25.0, 'lng': 51.0},
    'bahrain': {'lat': 26.0, 'lng': 50.5},
    'kuwait': {'lat': 29.0, 'lng': 47.0},
    'turkey': {'lat': 38.9, 'lng': 35.0},
    'hormuz': {'lat': 26.5, 'lng': 56.5},
    'bab el-mandeb': {'lat': 13.0, 'lng': 43.0},

    # Europe
    'ukraine': {'lat': 48.4, 'lng': 31.2},
    'romania': {'lat': 45.9, 'lng': 25.0},
    'moldova': {'lat': 47.4, 'lng': 28.8},
    'estonia': {'lat': 59.0, 'lng': 27.0},
    'latvia': {'lat': 57.0, 'lng': 25.0},
    'lithuania': {'lat': 55.0, 'lng': 24.0},
    'poland': {'lat': 52.0, 'lng': 19.0},
    'germany': {'lat': 51.0, 'lng': 10.0},
    'france': {'lat': 46.0, 'lng': 2.0},
    'uk': {'lat': 55.0, 'lng': -3.0},
    'greece': {'lat': 38.0, 'lng': 23.0},
    'italy': {'lat': 42.0, 'lng': 12.0},
    'spain': {'lat': 40.0, 'lng': -4.0},
    'baltic': {'lat': 55.0, 'lng': 25.0},
    'mediterranean': {'lat': 35.0, 'lng': 18.0},

    # Asia
    'china': {'lat': 35.9, 'lng': 104.2},
    'taiwan': {'lat': 23.7, 'lng': 120.9},
    'india': {'lat': 20.6, 'lng': 78.9},
    'pakistan': {'lat': 30.4, 'lng': 69.3},
    'afghanistan': {'lat': 33.9, 'lng': 67.7},
    'central asia': {'lat': 45.0, 'lng': 65.0},
    'kazakhstan': {'lat': 48.0, 'lng': 68.0},
    'uzbekistan': {'lat': 41.0, 'lng': 64.0},
    'north korea': {'lat': 39.0, 'lng': 127.0},
    'south korea': {'lat': 36.0, 'lng': 127.0},
    'japan': {'lat': 36.0, 'lng': 138.0},
    'vietnam': {'lat': 16.0, 'lng': 108.0},
    'philippines': {'lat': 12.0, 'lng': 122.0},
    'indonesia': {'lat': -5.0, 'lng': 120.0},
    'malaysia': {'lat': 4.0, 'lng': 102.0},
    'singapore': {'lat': 1.3, 'lng': 103.8},

    # Americas
    'us': {'lat': 39.8, 'lng': -98.6},
    'usa': {'lat': 39.8, 'lng': -98.6},
    'mexico': {'lat': 23.6, 'lng': -102.0},
    'canada': {'lat': 56.0, 'lng': -96.0},
    'brazil': {'lat': -14.0, 'lng': -51.0},
    'argentina': {'lat': -36.0, 'lng': -63.0},
    'colombia': {'lat': 4.0, 'lng': -72.0},
    'venezuela': {'lat': 8.0, 'lng': -66.0},

    # Africa
    'egypt': {'lat': 26.0, 'lng': 30.0},
    'libya': {'lat': 27.0, 'lng': 17.0},
    'sudan': {'lat': 15.0, 'lng': 30.0},
    'south sudan': {'lat': 7.0, 'lng': 30.0},
    'ethiopia': {'lat': 9.0, 'lng': 40.0},
    'somalia': {'lat': 6.0, 'lng': 47.0},
    'kenya': {'lat': -1.0, 'lng': 38.0},
    'nigeria': {'lat': 10.0, 'lng': 8.0},
    'sahel': {'lat': 15.0, 'lng': 0.0},
    'horn of africa': {'lat': 5.0, 'lng': 45.0},

    # Other regions
    'south china sea': {'lat': 12.0, 'lng': 116.0},
    'arctic': {'lat': 75.0, 'lng': -40.0},
    'antarctic': {'lat': -75.0, 'lng': 20.0},
    'atlantic': {'lat': 20.0, 'lng': -40.0},
}

def get_coords(threat):
    tid = threat.get('id', '')
    name = threat.get('name', '')
    desc = threat.get('description', '')
    text = (name + ' ' + desc).lower()

    # 1. Explicit ID map
    if tid in COORDINATE_MAP:
        return COORDINATE_MAP[tid]

    # 2. Keyword match (country/region)
    for keyword, coords in KEYWORD_MAP.items():
        if keyword in text:
            return coords

    # 3. Domain-based fallback (intelligent defaults)
    domains = threat.get('domains', [])
    if 'Geopolitical' in domains:
        return {'lat': 35.0, 'lng': 38.0}  # Middle East
    elif 'Energy' in domains:
        return {'lat': 28.0, 'lng': 50.0}  # Persian Gulf
    elif 'Food' in domains:
        return {'lat': 15.0, 'lng': 25.0}  # Sahel
    elif 'Climate' in domains:
        return {'lat': 20.0, 'lng': 0.0}   # Atlantic
    elif 'Financial' in domains:
        return {'lat': 40.0, 'lng': -74.0} # New York
    elif 'Health' in domains:
        return {'lat': 20.0, 'lng': 30.0}  # Egypt
    elif 'Supply Chains' in domains:
        return {'lat': 30.0, 'lng': 45.0}  # Middle East
    elif 'Social' in domains:
        return {'lat': 20.0, 'lng': 20.0}  # Central Africa
    elif 'Information' in domains:
        return {'lat': 38.0, 'lng': 23.0}  # Greece
    elif 'Technology' in domains:
        return {'lat': 37.0, 'lng': -122.0} # Silicon Valley
    else:
        # Global default – not Atlantic!
        return {'lat': 20.0, 'lng': 20.0}   # Central Africa

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    history = load_json(HISTORY_FILE, [])
    trend = load_json(TREND_FILE, {})

    # Include all threats – not just geopolitical
    all_threats = threats

    result = {
        "timestamp": datetime.now().isoformat(),
        "threats": [],
        "history": history[-30:],
        "trend": trend
    }

    for t in all_threats:
        coords = get_coords(t)
        result["threats"].append({
            "id": t.get('id'),
            "name": t.get('name'),
            "scp": t.get('scp', 0.5),
            "status": t.get('status', 'Yellow'),
            "lat": coords['lat'],
            "lng": coords['lng'],
            "domains": t.get('domains', []),
            "priority": t.get('priority_score', 0),
        })

    save_json(result, OUTPUT_FILE)
    print(f"✅ Conflict data saved to {OUTPUT_FILE} with {len(result['threats'])} threats")

    # Print a few examples
    for t in result['threats'][:5]:
        print(f"  {t['id']}: {t['lat']}, {t['lng']} – {t['name']}")

if __name__ == "__main__":
    main()

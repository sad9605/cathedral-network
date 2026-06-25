#!/usr/bin/env python3
"""
generate_conflict_data.py – Generate conflict monitor data with accurate coordinates.
Uses name-based mapping with comprehensive country/region keywords.
"""

import json
import re
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

# ----- COMPREHENSIVE COUNTRY/REGION KEYWORD MAP (with centroids) -----
KEYWORD_MAP = {
    # Americas
    'mexico': {'lat': 23.6, 'lng': -102.0},
    'cartel violence': {'lat': 23.6, 'lng': -102.0},
    'brazil': {'lat': -14.0, 'lng': -51.0},
    'argentina': {'lat': -36.0, 'lng': -63.0},
    'colombia': {'lat': 4.0, 'lng': -72.0},
    'venezuela': {'lat': 8.0, 'lng': -66.0},
    'peru': {'lat': -9.0, 'lng': -75.0},
    'chile': {'lat': -30.0, 'lng': -70.0},
    'ecuador': {'lat': -1.0, 'lng': -78.0},
    'bolivia': {'lat': -17.0, 'lng': -65.0},
    'paraguay': {'lat': -23.0, 'lng': -58.0},
    'uruguay': {'lat': -33.0, 'lng': -56.0},
    'us': {'lat': 39.8, 'lng': -98.6},
    'usa': {'lat': 39.8, 'lng': -98.6},
    'canada': {'lat': 56.0, 'lng': -96.0},
    'central america': {'lat': 15.0, 'lng': -86.0},
    'caribbean': {'lat': 18.0, 'lng': -70.0},

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
    'turkmenistan': {'lat': 40.0, 'lng': 60.0},
    'kyrgyzstan': {'lat': 41.0, 'lng': 75.0},
    'tajikistan': {'lat': 39.0, 'lng': 71.0},
    'north korea': {'lat': 39.0, 'lng': 127.0},
    'south korea': {'lat': 36.0, 'lng': 127.0},
    'japan': {'lat': 36.0, 'lng': 138.0},
    'vietnam': {'lat': 16.0, 'lng': 108.0},
    'laos': {'lat': 18.0, 'lng': 105.0},
    'cambodia': {'lat': 12.0, 'lng': 105.0},
    'thailand': {'lat': 15.0, 'lng': 101.0},
    'myanmar': {'lat': 21.0, 'lng': 96.0},
    'indonesia': {'lat': -5.0, 'lng': 120.0},
    'malaysia': {'lat': 4.0, 'lng': 102.0},
    'singapore': {'lat': 1.3, 'lng': 103.8},
    'philippines': {'lat': 12.0, 'lng': 122.0},
    'south china sea': {'lat': 12.0, 'lng': 116.0},

    # Africa
    'egypt': {'lat': 26.0, 'lng': 30.0},
    'libya': {'lat': 27.0, 'lng': 17.0},
    'sudan': {'lat': 15.0, 'lng': 30.0},
    'south sudan': {'lat': 7.0, 'lng': 30.0},
    'ethiopia': {'lat': 9.0, 'lng': 40.0},
    'somalia': {'lat': 6.0, 'lng': 47.0},
    'kenya': {'lat': -1.0, 'lng': 38.0},
    'nigeria': {'lat': 10.0, 'lng': 8.0},
    'ghana': {'lat': 8.0, 'lng': -2.0},
    'mali': {'lat': 17.0, 'lng': -3.0},
    'niger': {'lat': 17.0, 'lng': 8.0},
    'chad': {'lat': 15.0, 'lng': 19.0},
    'congo': {'lat': -2.0, 'lng': 23.0},
    'drc': {'lat': -4.0, 'lng': 21.0},
    'sahel': {'lat': 15.0, 'lng': 0.0},
    'horn of africa': {'lat': 5.0, 'lng': 45.0},

    # Polar
    'arctic': {'lat': 75.0, 'lng': -40.0},
    'antarctic': {'lat': -75.0, 'lng': 20.0},
    'ross ice shelf': {'lat': -75.0, 'lng': 20.0},

    # General
    'global': {'lat': 20.0, 'lng': 20.0},
    'atlantic': {'lat': 20.0, 'lng': -40.0},
    'pacific': {'lat': 0.0, 'lng': 160.0},
}

# Explicit ID map for threats with IDs that don't match keywords well
ID_MAP = {
    # ... existing entries ... (keep them, then add these)
    
    # Unmatched threats from the recent run
    'C‑RED‑BLOCK': {'lat': 13.0, 'lng': 43.0},   # Bab el-Mandeb Blockade
    'C12': {'lat': 35.0, 'lng': 38.0},           # Generic Middle East
    'C14': {'lat': 35.0, 'lng': 38.0},
    'C15': {'lat': 35.0, 'lng': 38.0},
    'C16': {'lat': 35.0, 'lng': 38.0},
    'C17': {'lat': 35.0, 'lng': 38.0},
    'C20': {'lat': 35.0, 'lng': 38.0},
    'C21': {'lat': 35.0, 'lng': 38.0},
    'C23': {'lat': 35.0, 'lng': 38.0},
    'C26': {'lat': 35.0, 'lng': 38.0},
     'C19': {'lat': 47.5, 'lng': 34.5},          # Zaporizhzhia NPP
    'C60': {'lat': 59.0, 'lng': 27.0},          # Narva Border Crisis (Estonia)
    'C28': {'lat': 35.0, 'lng': 38.0},          # Generic Middle East
    'G-GREENLAND': {'lat': 72.0, 'lng': -42.0}, # Greenland
    'G-SPACE': {'lat': 35.0, 'lng': 38.0},      # Space-related (Middle East default)
    'G-WEST-BANK': {'lat': 31.8, 'lng': 35.2},  # West Bank
    'G-SUD-BLUE': {'lat': 12.0, 'lng': 34.0},   # Blue Nile / Sudan
    'CC2': {'lat': 35.0, 'lng': 38.0},          # Generic
    'C138': {'lat': 35.0, 'lng': 38.0},         # Generic
    'C8': {'lat': 35.0, 'lng': 38.0},           # Generic
    'C5': {'lat': 35.0, 'lng': 38.0},      # Generic Middle East
    'C97': {'lat': 35.0, 'lng': 38.0},     # Generic Middle East
    'I12': {'lat': 38.0, 'lng': 23.0},     # Information/cyber – Greece
    'C2I': {'lat': 38.0, 'lng': 23.0},     # Information Warfare – Greece
    'I12I': {'lat': 38.0, 'lng': 23.0},    # Information/cyber – Greece
    'C142': {'lat': 35.0, 'lng': 38.0},    # Generic Middle East 
 # Add any other IDs you find missing by running the script again
}
def get_coords(threat):
    tid = threat.get('id', '')
    name = threat.get('name', '')
    desc = threat.get('description', '')
    text = (name + ' ' + desc).lower()

    # 1. Explicit ID
    if tid in ID_MAP:
        return ID_MAP[tid]

    # 2. Keyword match (longest match first to avoid false positives)
    # Sort keywords by length (descending) to match more specific phrases first
    sorted_keywords = sorted(KEYWORD_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in text:
            return KEYWORD_MAP[keyword]

    # 3. Domain-based fallback
    domains = threat.get('domains', [])
    if 'Geopolitical' in domains or 'Conflict' in domains:
        return {'lat': 35.0, 'lng': 38.0}
    elif 'Energy' in domains or 'Oil' in domains:
        return {'lat': 28.0, 'lng': 50.0}
    elif 'Food' in domains or 'Famine' in domains:
        return {'lat': 15.0, 'lng': 25.0}
    elif 'Climate' in domains:
        return {'lat': 20.0, 'lng': 0.0}
    elif 'Financial' in domains:
        return {'lat': 40.0, 'lng': -74.0}
    elif 'Health' in domains:
        return {'lat': 20.0, 'lng': 30.0}
    else:
        return {'lat': 35.0, 'lng': 38.0}  # Default to Middle East

def main():
    print("🌍 Generating conflict coordinates...")
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    history = load_json(HISTORY_FILE, [])
    trend = load_json(TREND_FILE, {})

    # Filter only geopolitical threats (conflicts)
    conflict_threats = [t for t in threats if 'Geopolitical' in t.get('domains', [])]

    result = {
        "timestamp": datetime.now().isoformat(),
        "threats": [],
        "history": history[-30:],
        "trend": trend
    }

    unmatched = []

    for t in conflict_threats:
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
        # Track unmatched for debugging
        if coords == {'lat': 35.0, 'lng': 38.0} and t.get('id') not in ID_MAP:
            unmatched.append(t.get('id'))

    save_json(result, OUTPUT_FILE)
    print(f"✅ Saved {len(result['threats'])} conflicts to {OUTPUT_FILE}")
    if unmatched:
        print(f"⚠️ Unmatched threats (using default Middle East): {', '.join(unmatched[:10])}")
    else:
        print("✅ All threats matched successfully!")

if __name__ == "__main__":
    main()

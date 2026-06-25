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

# ----- COMPREHENSIVE COORDINATE MAP -----
# All known threats with their correct coordinates
COORDINATE_MAP = {
    # Geopolitical conflicts
    'C01': {'lat': 26.5, 'lng': 56.5},           # Iran-Israel/US War / Hormuz
    'C-USIRAN': {'lat': 30.0, 'lng': 50.0},       # Direct US-Iran Conflict
    'C-BELT': {'lat': 28.0, 'lng': 52.0},         # Iran Resistance Security Belt
    'C-RED-BLOCK': {'lat': 13.0, 'lng': 43.0},    # Bab el-Mandeb Blockade
    'C132': {'lat': 35.0, 'lng': 38.0},           # Great Power Conflict / US-Iran Entanglement
    'C129': {'lat': 40.5, 'lng': 45.0},           # Armenia-Azerbaijan
    'C54': {'lat': 55.0, 'lng': 25.0},            # Baltic Grey-Zone
    'C88': {'lat': 23.5, 'lng': 120.0},           # Taiwan Strait Incident Risk
    'C90': {'lat': 12.0, 'lng': 116.0},           # South China Sea Militarisation
    'C48': {'lat': 38.0, 'lng': 23.0},            # AI Deepfake Ops (Greece)
    'C19': {'lat': 47.5, 'lng': 34.5},            # Zaporizhzhia NPP
    'C25': {'lat': 45.0, 'lng': 25.0},            # NATO Article 4 (Romania)
    'C3': {'lat': 48.0, 'lng': 30.0},             # Ukraine-Russia spillover
    'C11': {'lat': 33.0, 'lng': 44.0},            # Iraq Instability
    'C58': {'lat': 56.0, 'lng': 15.0},            # Underwater Infrastructure Sabotage
    'C60': {'lat': 59.0, 'lng': 27.0},            # Narva Border Crisis (Estonia)
    'C64': {'lat': 35.0, 'lng': 18.0},            # Mediterranean Migration
    'C85': {'lat': 24.0, 'lng': -102.0},          # Cartel Violence Mexico
    'C122': {'lat': 39.0, 'lng': 127.0},          # North Korea Ballistic
    'C2': {'lat': 38.0, 'lng': 23.0},             # Information Warfare (Greece)
    'C4': {'lat': 47.0, 'lng': 29.0},             # Moldova Transnistria escalation
    'CA4': {'lat': 45.0, 'lng': 65.0},            # Central Asia Export Dependency
    'C11E': {'lat': 28.0, 'lng': 50.0},           # Oil Price Shock (Middle East)
    'C106': {'lat': 30.0, 'lng': 30.0},           # Global Food Price Volatility (Egypt/N Africa)
    'C139': {'lat': 15.0, 'lng': 25.0},           # Mass Displacement (Sudan/Sahel)
    'C126': {'lat': 20.0, 'lng': 10.0},           # North Africa Food Security Collapse
    'C134': {'lat': 15.0, 'lng': -30.0},          # Dry Corridor Famine-Migration (Sahel)
    'C147': {'lat': -75.0, 'lng': 20.0},          # Ross Ice Shelf Acceleration (Antarctica – this one is actually correct!)
    'C100': {'lat': 75.0, 'lng': -40.0},          # Arctic Sea Ice Loss
    'A-STRAT-RES': {'lat': 30.0, 'lng': 45.0},    # Absence of strategic fertiliser reserves (Middle East)
    'C03': {'lat': 5.0, 'lng': 45.0},             # Horn of Africa Famine
    'C-STRAT-OIL': {'lat': 28.0, 'lng': 50.0},    # Strategic oil reserve depletion
    'C-SEMI-DROUGHT': {'lat': 20.0, 'lng': 10.0}, # Semi-arid drought (Sahel)
    'C-PANDEMIC': {'lat': 20.0, 'lng': 30.0},     # Pandemic outbreak (global, but centre on Africa)
    'C-CYBER': {'lat': 35.0, 'lng': 20.0},        # Cyber attack (Mediterranean)
}

# Keywords for country/region matching
KEYWORD_MAP = {
    'iran': {'lat': 32.4, 'lng': 53.7},
    'israel': {'lat': 31.0, 'lng': 34.8},
    'us': {'lat': 39.8, 'lng': -98.6},
    'usa': {'lat': 39.8, 'lng': -98.6},
    'russia': {'lat': 61.5, 'lng': 105.3},
    'china': {'lat': 35.9, 'lng': 104.2},
    'taiwan': {'lat': 23.7, 'lng': 120.9},
    'ukraine': {'lat': 48.4, 'lng': 31.2},
    'romania': {'lat': 45.9, 'lng': 25.0},
    'armenia': {'lat': 40.1, 'lng': 45.0},
    'azerbaijan': {'lat': 40.3, 'lng': 47.5},
    'mexico': {'lat': 23.6, 'lng': -102.0},
    'north korea': {'lat': 39.0, 'lng': 127.0},
    'iraq': {'lat': 33.0, 'lng': 44.0},
    'yemen': {'lat': 15.0, 'lng': 48.0},
    'moldova': {'lat': 47.4, 'lng': 28.8},
    'lebanon': {'lat': 33.8, 'lng': 35.8},
    'syria': {'lat': 34.8, 'lng': 38.9},
    'saudi arabia': {'lat': 23.9, 'lng': 45.0},
    'turkey': {'lat': 38.9, 'lng': 35.0},
    'baltic': {'lat': 55.0, 'lng': 25.0},
    'south china sea': {'lat': 12.0, 'lng': 116.0},
    'hormuz': {'lat': 26.5, 'lng': 56.5},
    'bab el-mandeb': {'lat': 13.0, 'lng': 43.0},
    'central asia': {'lat': 45.0, 'lng': 65.0},
    'estonia': {'lat': 59.0, 'lng': 27.0},
    'mediterranean': {'lat': 35.0, 'lng': 18.0},
    'greece': {'lat': 38.0, 'lng': 23.0},
    'africa': {'lat': 8.0, 'lng': 20.0},
    'horn of africa': {'lat': 5.0, 'lng': 45.0},
    'sahel': {'lat': 15.0, 'lng': 0.0},
    'antarctic': {'lat': -75.0, 'lng': 20.0},
    'arctic': {'lat': 75.0, 'lng': -40.0},
}

def get_coords(threat):
    tid = threat.get('id', '')
    name = threat.get('name', '')
    desc = threat.get('description', '')
    text = (name + ' ' + desc).lower()

    # 1. Explicit map
    if tid in COORDINATE_MAP:
        return COORDINATE_MAP[tid]

    # 2. Keyword match (country/region)
    for keyword, coords in KEYWORD_MAP.items():
        if keyword in text:
            return coords

    # 3. Domain‑based default
    domains = threat.get('domains', [])
    if 'Geopolitical' in domains:
        # If it's geopolitical but we have no match, place it in the Middle East
        return {'lat': 35.0, 'lng': 38.0}
    elif 'Climate' in domains:
        return {'lat': 20.0, 'lng': 0.0}
    elif 'Energy' in domains:
        return {'lat': 30.0, 'lng': 45.0}
    elif 'Food' in domains:
        return {'lat': 15.0, 'lng': 25.0}
    else:
        # Fallback – Atlantic Ocean (not Antarctica!)
        return {'lat': 20.0, 'lng': -20.0}

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    history = load_json(HISTORY_FILE, [])
    trend = load_json(TREND_FILE, {})

    conflict_threats = [t for t in threats if 'Geopolitical' in t.get('domains', [])]

    result = {
        "timestamp": datetime.now().isoformat(),
        "threats": [],
        "history": history[-30:],
        "trend": trend
    }

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

    save_json(result, OUTPUT_FILE)
    print(f"✅ Conflict data saved to {OUTPUT_FILE} with {len(result['threats'])} threats")

if __name__ == "__main__":
    main()

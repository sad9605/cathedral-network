#!/usr/bin/env python3
"""
generate_conflict_data.py – Generate conflict monitor data with accurate coordinates.
Uses comprehensive ID mapping + name-based fallback.
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

# ----- COMPLETE COORDINATE MAP FOR ALL KNOWN THREATS -----
# I've expanded this to cover ALL threats you're likely tracking
COORDINATE_MAP = {
    # === CONFLICT / GEOPOLITICAL (C-series) ===
    'C01': {'lat': 26.5, 'lng': 56.5},      # Iran-Israel/US War / Hormuz
    'C-USIRAN': {'lat': 30.0, 'lng': 50.0}, # Direct US-Iran Conflict
    'C-BELT': {'lat': 28.0, 'lng': 52.0},   # Iran 'Resistance Security Belt'
    'C-RED-BLOCK': {'lat': 13.0, 'lng': 43.0}, # Bab el-Mandeb Blockade
    'C132': {'lat': 35.0, 'lng': 38.0},     # Great Power Conflict / US-Iran Entanglement
    'C129': {'lat': 40.5, 'lng': 45.0},     # Armenia-Azerbaijan
    'C54': {'lat': 55.0, 'lng': 25.0},      # Baltic Grey-Zone
    'C88': {'lat': 23.5, 'lng': 120.0},     # Taiwan Strait Incident Risk
    'C90': {'lat': 12.0, 'lng': 116.0},     # South China Sea Militarisation
    'C48': {'lat': 38.0, 'lng': 23.0},      # AI Deepfake Ops
    'C19': {'lat': 47.5, 'lng': 34.5},      # Zaporizhzhia NPP
    'C25': {'lat': 45.0, 'lng': 25.0},      # NATO Article 4 (Romania)
    'C3': {'lat': 48.0, 'lng': 30.0},       # Ukraine-Russia spillover
    'C11': {'lat': 33.0, 'lng': 44.0},      # Iraq Instability
    'C58': {'lat': 56.0, 'lng': 15.0},      # Underwater Infrastructure Sabotage
    'C60': {'lat': 59.0, 'lng': 27.0},      # Narva Border Crisis (Estonia)
    'C64': {'lat': 35.0, 'lng': 18.0},      # Mediterranean Migration
    'C85': {'lat': 24.0, 'lng': -102.0},    # Cartel Violence Mexico
    'C122': {'lat': 39.0, 'lng': 127.0},    # North Korea Ballistic
    'C2': {'lat': 38.0, 'lng': 23.0},       # Information Warfare
    'C4': {'lat': 47.0, 'lng': 29.0},       # Moldova Transnistria escalation
    'CA4': {'lat': 45.0, 'lng': 65.0},      # Central Asia Export Dependency
    'C11E': {'lat': 28.0, 'lng': 50.0},     # Oil Price Shock
    'C106': {'lat': 30.0, 'lng': 30.0},     # Global Food Price Volatility
    'C139': {'lat': 15.0, 'lng': 25.0},     # Mass Displacement
    'C126': {'lat': 20.0, 'lng': 10.0},     # North Africa Food Security Collapse
    'C134': {'lat': 15.0, 'lng': -30.0},    # Dry Corridor Famine-Migration
    'C147': {'lat': -75.0, 'lng': 20.0},    # Ross Ice Shelf Acceleration
    'C100': {'lat': 75.0, 'lng': -40.0},    # Arctic Sea Ice Loss
    'A-STRAT-RES': {'lat': 30.0, 'lng': 45.0}, # Absence of strategic fertiliser reserves
    'C03': {'lat': 5.0, 'lng': 45.0},       # Horn of Africa Famine
    'C-STRAT-OIL': {'lat': 28.0, 'lng': 50.0}, # Strategic oil reserve depletion
    'C-SEMI-DROUGHT': {'lat': 20.0, 'lng': 10.0}, # Semi-arid drought
    'C-PANDEMIC': {'lat': 20.0, 'lng': 30.0}, # Pandemic outbreak
    'C-CYBER': {'lat': 35.0, 'lng': 20.0},  # Cyber attack

    # === PREDICTIONS / ECONOMIC / HEALTH (P-series) ===
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
    'P37': {'lat': 48.0, 'lng': 30.0},      # Ukraine
    'P34': {'lat': 38.0, 'lng': 23.0},      # AI deepfake
    'P35': {'lat': 30.0, 'lng': 45.0},      # Fertiliser
    'P38': {'lat': 38.0, 'lng': -77.0},     # US
    'P42': {'lat': 38.0, 'lng': -77.0},     # US
    'P45': {'lat': 40.0, 'lng': -74.0},     # US
    'P47': {'lat': 38.0, 'lng': -77.0},     # US
    'P49': {'lat': 38.0, 'lng': -122.0},    # Silicon Valley
    'P52': {'lat': 38.0, 'lng': -77.0},     # US
    'P56': {'lat': 38.0, 'lng': -77.0},     # US
    'P57': {'lat': 38.0, 'lng': -77.0},     # US
    'P58': {'lat': -34.0, 'lng': -64.0},    # Argentina
    'P59': {'lat': -34.0, 'lng': -64.0},    # Argentina
    'P60': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P61': {'lat': 38.0, 'lng': -77.0},     # US
    'P62': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P63': {'lat': 50.0, 'lng': 10.0},      # EU
    'P64': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P65': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P66': {'lat': 38.0, 'lng': -77.0},     # US
    'P67': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P68': {'lat': 38.0, 'lng': -122.0},    # US tech
    'P74': {'lat': 28.0, 'lng': 50.0},      # Oil
    'P75': {'lat': 32.0, 'lng': 34.0},      # Israel
    'P76': {'lat': 32.0, 'lng': 53.0},      # Iran
    'P77': {'lat': 28.0, 'lng': 50.0},      # Oil
    'P78': {'lat': 28.0, 'lng': 50.0},      # Oil
    'P79': {'lat': 13.0, 'lng': 43.0},      # Bab el-Mandeb
    'P80': {'lat': 24.0, 'lng': 45.0},      # Saudi
    'P81': {'lat': 26.5, 'lng': 56.5},      # Hormuz
    'P82': {'lat': 32.0, 'lng': 53.0},      # Iran
    'P83': {'lat': 33.0, 'lng': 35.0},      # Lebanon
    'P84': {'lat': 35.0, 'lng': 38.0},      # Global
    'P85': {'lat': 15.0, 'lng': 25.0},      # Sahel
    'P86': {'lat': 32.0, 'lng': 53.0},      # Iran
    'P87': {'lat': 35.0, 'lng': 38.0},      # Global
    'P88': {'lat': 35.0, 'lng': 38.0},      # Global
    'P89': {'lat': 38.0, 'lng': -77.0},     # US
    'P90': {'lat': 30.0, 'lng': 30.0},      # Egypt
    'P91': {'lat': 32.0, 'lng': 53.0},      # Middle East
    'P92': {'lat': 35.0, 'lng': 38.0},      # Global
    'P93': {'lat': 12.0, 'lng': 122.0},     # Philippines
    'P95': {'lat': 38.0, 'lng': -77.0},     # US
    'P96': {'lat': 29.0, 'lng': 34.0},      # Israel
    'P97': {'lat': 28.0, 'lng': 50.0},      # Oil
    'P98': {'lat': 13.0, 'lng': 43.0},      # Yemen
    'P99': {'lat': 60.0, 'lng': 90.0},      # Russia
    'P100': {'lat': 5.0, 'lng': 45.0},      # Horn
    'P101': {'lat': 26.5, 'lng': 56.5},     # Hormuz
    'P102': {'lat': 28.0, 'lng': 50.0},     # Oil
    'P103': {'lat': 38.0, 'lng': -122.0},   # US tech
    'P104': {'lat': 38.0, 'lng': -122.0},   # US tech
    'P105': {'lat': 38.0, 'lng': -77.0},    # US
    'P109': {'lat': 26.0, 'lng': 57.0},     # Iran
    'P110': {'lat': 26.0, 'lng': 57.0},     # Iran
    'P111': {'lat': 26.0, 'lng': 57.0},     # Iran
}

# ----- COUNTRY KEYWORD MAP (used as fallback) -----
COUNTRY_KEYWORDS = {
    'iran': {'lat': 32.4, 'lng': 53.7},
    'israel': {'lat': 31.0, 'lng': 34.8},
    'iraq': {'lat': 33.0, 'lng': 44.0},
    'syria': {'lat': 34.8, 'lng': 38.9},
    'lebanon': {'lat': 33.8, 'lng': 35.8},
    'turkey': {'lat': 38.9, 'lng': 35.0},
    'egypt': {'lat': 26.0, 'lng': 30.0},
    'libya': {'lat': 27.0, 'lng': 17.0},
    'sudan': {'lat': 15.0, 'lng': 30.0},
    'ethiopia': {'lat': 9.0, 'lng': 40.0},
    'somalia': {'lat': 6.0, 'lng': 47.0},
    'kenya': {'lat': -1.0, 'lng': 38.0},
    'nigeria': {'lat': 10.0, 'lng': 8.0},
    'ukraine': {'lat': 48.4, 'lng': 31.2},
    'romania': {'lat': 45.9, 'lng': 25.0},
    'moldova': {'lat': 47.4, 'lng': 28.8},
    'estonia': {'lat': 59.0, 'lng': 27.0},
    'mexico': {'lat': 23.6, 'lng': -102.0},
    'brazil': {'lat': -14.0, 'lng': -51.0},
    'argentina': {'lat': -36.0, 'lng': -63.0},
    'china': {'lat': 35.9, 'lng': 104.2},
    'taiwan': {'lat': 23.7, 'lng': 120.9},
    'india': {'lat': 20.6, 'lng': 78.9},
    'pakistan': {'lat': 30.4, 'lng': 69.3},
    'afghanistan': {'lat': 33.9, 'lng': 67.7},
    'north korea': {'lat': 39.0, 'lng': 127.0},
    'japan': {'lat': 36.0, 'lng': 138.0},
    'vietnam': {'lat': 16.0, 'lng': 108.0},
    'philippines': {'lat': 12.0, 'lng': 122.0},
    'indonesia': {'lat': -5.0, 'lng': 120.0},
    'saudi arabia': {'lat': 23.9, 'lng': 45.0},
    'yemen': {'lat': 15.0, 'lng': 48.0},
    'oman': {'lat': 21.0, 'lng': 57.0},
    'uae': {'lat': 24.0, 'lng': 54.0},
    'qatar': {'lat': 25.0, 'lng': 51.0},
    'kuwait': {'lat': 29.0, 'lng': 47.0},
    'bahrain': {'lat': 26.0, 'lng': 50.5},
    'jordan': {'lat': 31.0, 'lng': 36.0},
    'sahel': {'lat': 15.0, 'lng': 0.0},
    'horn of africa': {'lat': 5.0, 'lng': 45.0},
    'baltic': {'lat': 55.0, 'lng': 25.0},
    'mediterranean': {'lat': 35.0, 'lng': 18.0},
    'central asia': {'lat': 45.0, 'lng': 65.0},
    'south china sea': {'lat': 12.0, 'lng': 116.0},
    'hormuz': {'lat': 26.5, 'lng': 56.5},
    'bab el-mandeb': {'lat': 13.0, 'lng': 43.0},
    'arctic': {'lat': 75.0, 'lng': -40.0},
    'antarctic': {'lat': -75.0, 'lng': 20.0},
}

def get_coords(threat):
    tid = threat.get('id', '')
    name = threat.get('name', '')
    desc = threat.get('description', '')
    text = (name + ' ' + desc).lower()

    # 1. Direct ID lookup
    if tid in COORDINATE_MAP:
        return COORDINATE_MAP[tid]

    # 2. Country keyword match
    for keyword, coords in COUNTRY_KEYWORDS.items():
        if keyword in text:
            return coords

    # 3. Domain-based fallback
    domains = threat.get('domains', [])
    if 'Geopolitical' in domains or 'Conflict' in domains:
        # For general conflicts, put them in the Middle East
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
        # Last resort – use a reasonable default (not Atlantic)
        return {'lat': 35.0, 'lng': 38.0}

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    history = load_json(HISTORY_FILE, [])
    trend = load_json(TREND_FILE, {})

    # Only include geopolitical threats (conflicts)
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
    print(f"✅ Conflict data saved to {OUTPUT_FILE} with {len(result['threats'])} conflicts")

if __name__ == "__main__":
    main()

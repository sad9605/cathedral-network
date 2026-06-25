#!/usr/bin/env python3
"""
generate_conflict_data.py – Generate conflict monitor data with coordinates.
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

# Country centroids
COUNTRY_COORDS = {
    'Iran': {'lat': 32.4, 'lng': 53.7},
    'Israel': {'lat': 31.0, 'lng': 34.8},
    'US': {'lat': 39.8, 'lng': -98.6},
    'USA': {'lat': 39.8, 'lng': -98.6},
    'Russia': {'lat': 61.5, 'lng': 105.3},
    'China': {'lat': 35.9, 'lng': 104.2},
    'Taiwan': {'lat': 23.7, 'lng': 120.9},
    'Ukraine': {'lat': 48.4, 'lng': 31.2},
    'Romania': {'lat': 45.9, 'lng': 25.0},
    'Armenia': {'lat': 40.1, 'lng': 45.0},
    'Azerbaijan': {'lat': 40.3, 'lng': 47.5},
    'Mexico': {'lat': 23.6, 'lng': -102.0},
    'North Korea': {'lat': 39.0, 'lng': 127.0},
    'Iraq': {'lat': 33.0, 'lng': 44.0},
    'Yemen': {'lat': 15.0, 'lng': 48.0},
    'Moldova': {'lat': 47.4, 'lng': 28.8},
    'Lebanon': {'lat': 33.8, 'lng': 35.8},
    'Syria': {'lat': 34.8, 'lng': 38.9},
    'Saudi Arabia': {'lat': 23.9, 'lng': 45.0},
    'Turkey': {'lat': 38.9, 'lng': 35.0},
    'NATO': {'lat': 50.0, 'lng': 15.0},
    'Baltic': {'lat': 55.0, 'lng': 25.0},
    'South China Sea': {'lat': 12.0, 'lng': 116.0},
    'Hormuz': {'lat': 26.5, 'lng': 56.5},
    'Bab el-Mandeb': {'lat': 13.0, 'lng': 43.0},
    'Global': {'lat': 20.0, 'lng': 0.0},
}

def get_country_from_threat(threat):
    name = threat.get('name', '')
    desc = threat.get('description', '')
    text = name + ' ' + desc
    for country in COUNTRY_COORDS:
        if country.lower() in text.lower():
            return country
    return None

def get_coords(threat):
    tid = threat.get('id', '')
    # Explicit mapping for known threats
    explicit = {
        'C01': {'lat': 26.5, 'lng': 56.5},
        'C-USIRAN': {'lat': 30.0, 'lng': 50.0},
        'C-BELT': {'lat': 28.0, 'lng': 52.0},
        'C-RED-BLOCK': {'lat': 13.0, 'lng': 43.0},
        'C132': {'lat': 35.0, 'lng': 38.0},
        'C129': {'lat': 40.5, 'lng': 45.0},
        'C54': {'lat': 55.0, 'lng': 25.0},
        'C88': {'lat': 23.5, 'lng': 120.0},
        'C90': {'lat': 12.0, 'lng': 116.0},
        'C19': {'lat': 47.5, 'lng': 34.5},
        'C25': {'lat': 45.0, 'lng': 25.0},
        'C3': {'lat': 48.0, 'lng': 30.0},
        'C11': {'lat': 33.0, 'lng': 44.0},
        'C58': {'lat': 56.0, 'lng': 15.0},
        'C85': {'lat': 24.0, 'lng': -102.0},
        'C122': {'lat': 39.0, 'lng': 127.0},
        'C2': {'lat': 38.0, 'lng': 23.0},
        'C4': {'lat': 47.0, 'lng': 29.0},
    }
    if tid in explicit:
        return explicit[tid]
    country = get_country_from_threat(threat)
    if country and country in COUNTRY_COORDS:
        c = COUNTRY_COORDS[country]
        return {'lat': c['lat'], 'lng': c['lng']}
    # Fallback
    return {'lat': (hash(tid) % 180) - 90, 'lng': (hash(tid + 'lng') % 360) - 180}

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    history = load_json(HISTORY_FILE, [])
    trend = load_json(TREND_FILE, {})

    conflict_threats = [t for t in threats if 'Geopolitical' in t.get('domains', [])]

    result = {
        "timestamp": datetime.now().isoformat(),
        "threats": [],
        "history": history[-30:],  # last 30 days
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

#!/usr/bin/env python3
"""
cfr_agent.py – Agentic Warden for CFR Global Conflict Tracker.
Scrapes conflict data and updates Cathedral's intelligence.
"""

import json
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# ---------- Configuration ----------
CFR_URL = "https://www.cfr.org/global-conflict-tracker"
OUTPUT_FILE = "conflict_data.json"
THREATS_FILE = "threats.json"
USER_AGENT = "Cathedral-Network-Agent/1.0 (https://cathedral.network)"

# Geocoding cache to avoid repeated requests
GEO_CACHE = {}

# ---------- Helpers ----------
def log(msg):
    print(f"[CFR Agent] {msg}")

def geocode_location(location_name):
    """Convert place name to lat/lng using Nominatim (OpenStreetMap)."""
    if not location_name:
        return None, None
    if location_name in GEO_CACHE:
        return GEO_CACHE[location_name]

    geolocator = Nominatim(user_agent=USER_AGENT)
    try:
        query = f"{location_name}, world"
        location = geolocator.geocode(query, timeout=10)
        if location:
            GEO_CACHE[location_name] = (location.latitude, location.longitude)
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderUnavailable):
        log(f"Geocoding timeout for {location_name}")
    return None, None

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_conflict_id(name):
    """Generate a stable ID from a conflict name."""
    base = re.sub(r'[^a-zA-Z0-9]', '', name[:30])
    if base:
        return f"CFR-{base.upper()}"
    return f"CFR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ---------- Main Scraper ----------
def fetch_cfr_conflicts():
    """Fetch and parse CFR Global Conflict Tracker."""
    log("Fetching CFR Global Conflict Tracker...")
    headers = {'User-Agent': USER_AGENT}
    try:
        resp = requests.get(CFR_URL, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log(f"Failed to fetch CFR: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    conflicts = []

    # Try primary selector
    cards = soup.select('.c-card--conflict')
    log(f"Found {len(cards)} conflict cards")

    if not cards:
        log("No conflict cards found. Attempting fallback extraction...")
        for header in soup.find_all(['h2', 'h3']):
            text = header.text.strip()
            if any(k in text.lower() for k in ['conflict', 'war', 'crisis']):
                name = text
                desc = ''
                parent = header.find_parent()
                if parent:
                    p = parent.find_next('p')
                    if p:
                        desc = p.text.strip()
                conflicts.append({
                    'name': name,
                    'description': desc,
                    'source': 'CFR (fallback)'
                })
        if not conflicts:
            log("No conflicts found in fallback either.")
            return []

    for card in cards:
        try:
            name_elem = card.select_one('.c-card__title')
            if not name_elem:
                continue
            name = name_elem.text.strip()

            status_elem = card.select_one('.c-card__status')
            status = status_elem.text.strip() if status_elem else 'Unknown'

            region_elem = card.select_one('.c-card__region')
            region = region_elem.text.strip() if region_elem else ''

            desc_elem = card.select_one('.c-card__description')
            description = desc_elem.text.strip() if desc_elem else ''

            location_query = f"{name} {region}".strip()
            lat, lng = geocode_location(location_query)
            if not lat or not lng:
                lat, lng = geocode_location(region)

            conflict_id = generate_conflict_id(name)

            conflicts.append({
                "id": conflict_id,
                "name": name,
                "lat": lat or 0,
                "lng": lng or 0,
                "status": status,
                "description": description,
                "source": "CFR Global Conflict Tracker",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            })
            log(f"  Extracted: {name}")

        except Exception as e:
            log(f"Error parsing card: {e}")

    # Ensure every conflict has an id
    for c in conflicts:
        if 'id' not in c:
            c['id'] = generate_conflict_id(c.get('name', 'Unknown'))

    log(f"Extracted {len(conflicts)} conflicts")
    return conflicts

# ---------- Integration ----------
def update_conflict_data(cfr_conflicts):
    """Merge CFR conflicts into conflict_data.json and threats.json."""
    if not cfr_conflicts:
        log("No conflicts to update.")
        return

    existing_data = load_json(OUTPUT_FILE, {"conflicts": []})
    existing_conflicts = existing_data.get("conflicts", [])
    existing_ids = {c.get("id") for c in existing_conflicts if c.get("id")}

    new_entries = []
    for cfr in cfr_conflicts:
        if 'id' not in cfr:
            cfr['id'] = generate_conflict_id(cfr.get('name', 'Unknown'))
        if cfr['id'] not in existing_ids:
            new_entries.append(cfr)
            existing_ids.add(cfr['id'])

    if new_entries:
        log(f"Adding {len(new_entries)} new CFR conflicts")
        existing_conflicts.extend(new_entries)
        existing_data["conflicts"] = existing_conflicts
        existing_data["timestamp"] = datetime.now().isoformat()
        save_json(existing_data, OUTPUT_FILE)
    else:
        log("No new conflicts to add")

    # Optionally update threats.json
    if new_entries:
        threats_data = load_json(THREATS_FILE, {"threats": []})
        threats = threats_data.get("threats", [])
        threat_ids = {t["id"] for t in threats if "id" in t}

        for cfr in new_entries:
            if cfr["id"] not in threat_ids:
                threat = {
                    "id": cfr["id"],
                    "name": cfr["name"],
                    "domains": ["Geopolitical", "Conflict"],
                    "status": "Yellow",
                    "scp": 0.5,
                    "base_probability": 0.3,
                    "description": cfr["description"],
                    "source": "CFR Agent",
                    "last_updated": datetime.now().isoformat()
                }
                threats.append(threat)
                threat_ids.add(cfr["id"])

        threats_data["threats"] = threats
        threats_data["last_updated"] = datetime.now().isoformat()
        save_json(threats_data, THREATS_FILE)
        log(f"Added {len(new_entries)} new threats to threats.json")

# ---------- Main ----------
def main():
    log("Starting CFR conflict scrape...")
    conflicts = fetch_cfr_conflicts()
    if conflicts:
        update_conflict_data(conflicts)
        log("CFR Agent completed successfully")
    else:
        log("No conflicts fetched – check the website or selectors")

if __name__ == "__main__":
    main()

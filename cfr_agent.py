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
        # Add "world" to help geocoder
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

    # CFR uses card-like containers; inspect the page to adjust selectors
    # We'll look for elements with class 'conflict-card' or similar.
    # As of 2026, they use a pattern: .c-card--conflict
    card_selector = '.c-card--conflict'
    cards = soup.select(card_selector)
    log(f"Found {len(cards)} conflict cards")

    if not cards:
        # Fallback: try to find by heading + description pattern
        # This is a backup; adjust based on page inspection
        log("No conflict cards found. Attempting fallback extraction...")
        # Look for sections with conflict titles
        # We'll parse using a generic approach: find h3 with conflict names
        # This may need adjustment
        for header in soup.select('h3'):
            if 'conflict' in header.text.lower() or 'war' in header.text.lower():
                name = header.text.strip()
                # Get parent or next sibling for description
                parent = header.find_parent()
                if parent:
                    desc_elem = parent.select_one('p') or parent.find_next('p')
                    desc = desc_elem.text.strip() if desc_elem else ''
                else:
                    desc = ''
                conflicts.append({
                    'name': name,
                    'description': desc,
                    'raw': 'fallback'
                })
        return conflicts

    for card in cards:
        try:
            # Extract name
            name_elem = card.select_one('.c-card__title')
            name = name_elem.text.strip() if name_elem else 'Unknown conflict'

            # Extract status (e.g., "Active", "Worsening")
            status_elem = card.select_one('.c-card__status')
            status = status_elem.text.strip() if status_elem else 'Unknown'

            # Extract region
            region_elem = card.select_one('.c-card__region')
            region = region_elem.text.strip() if region_elem else ''

            # Extract description
            desc_elem = card.select_one('.c-card__description')
            description = desc_elem.text.strip() if desc_elem else ''

            # Determine severity (heuristic)
            severity = 'Medium'
            if 'worsen' in status.lower() or 'critical' in status.lower():
                severity = 'High'
            elif 'improve' in status.lower():
                severity = 'Low'

            # Geocode using region + name
            location_query = f"{name} {region}".strip()
            lat, lng = geocode_location(location_query)
            if not lat or not lng:
                # Fallback to region only
                lat, lng = geocode_location(region)

            # Generate a stable ID
            conflict_id = re.sub(r'[^a-zA-Z0-9-]', '', name[:20]).upper()
            if conflict_id:
                conflict_id = f"CFR-{conflict_id}"
            else:
                conflict_id = f"CFR-{len(conflicts)+1:04d}"

            conflicts.append({
                "id": conflict_id,
                "name": name,
                "lat": lat or 0,
                "lng": lng or 0,
                "scp": 0.5,  # placeholder; could be refined
                "status": status,
                "description": description,
                "source": "CFR Global Conflict Tracker",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            })
            log(f"  Extracted: {name}")

        except Exception as e:
            log(f"Error parsing card: {e}")

    log(f"Extracted {len(conflicts)} conflicts")
    return conflicts

# ---------- Integration ----------
def update_conflict_data(cfr_conflicts):
    """Merge CFR conflicts into conflict_data.json and threats.json."""
    # Load existing data
    existing_data = load_json(OUTPUT_FILE, {"conflicts": []})
    existing_conflicts = existing_data.get("conflicts", [])

    # Create map of existing IDs to avoid duplicates
    existing_ids = {c["id"] for c in existing_conflicts if "id" in c}

    # Add new CFR conflicts that are not already present
    new_entries = []
    for cfr in cfr_conflicts:
        if cfr["id"] not in existing_ids:
            new_entries.append(cfr)
            existing_ids.add(cfr["id"])

    if new_entries:
        log(f"Adding {len(new_entries)} new CFR conflicts")
        existing_conflicts.extend(new_entries)
        existing_data["conflicts"] = existing_conflicts
        existing_data["timestamp"] = datetime.now().isoformat()
        save_json(existing_data, OUTPUT_FILE)
    else:
        log("No new conflicts to add")

    # Optionally create threats in threats.json
    if new_entries:
        threats_data = load_json(THREATS_FILE, {"threats": []})
        threats = threats_data.get("threats", [])
        threat_ids = {t["id"] for t in threats if "id" in t}

        for cfr in new_entries:
            if cfr["id"] not in threat_ids:
                # Create a basic threat entry
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

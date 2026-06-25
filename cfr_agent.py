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

# Optional geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderRateLimited
    GEOCODING_AVAILABLE = True
except ImportError:
    GEOCODING_AVAILABLE = False
    print("⚠️ Geopy not installed. Conflicts will have lat/lng = 0,0.")

# ---------- Configuration ----------
CFR_URL = "https://www.cfr.org/global-conflict-tracker"
OUTPUT_FILE = "conflict_data.json"
THREATS_FILE = "threats.json"
USER_AGENT = "Cathedral-Network-Agent/1.0 (https://cathedral.network)"

# ---------- Helpers ----------
def log(msg):
    print(f"[CFR Agent] {msg}")

GEO_CACHE = {}

def geocode_location(location_name, max_retries=3):
    """Convert place name to lat/lng using Nominatim with retries and backoff."""
    if not GEOCODING_AVAILABLE or not location_name:
        return None, None
    if location_name in GEO_CACHE:
        return GEO_CACHE[location_name]

    geolocator = Nominatim(user_agent=USER_AGENT)
    attempt = 0
    while attempt < max_retries:
        try:
            query = f"{location_name}, world"
            location = geolocator.geocode(query, timeout=10)
            if location:
                GEO_CACHE[location_name] = (location.latitude, location.longitude)
                return location.latitude, location.longitude
            break
        except (GeocoderTimedOut, GeocoderUnavailable, GeocoderRateLimited) as e:
            attempt += 1
            wait = 2 ** attempt
            log(f"Geocoding error for {location_name}: {e}. Retry {attempt}/{max_retries} in {wait}s...")
            time.sleep(wait)
            if attempt >= max_retries:
                log(f"Geocoding failed for {location_name} after {max_retries} attempts.")
                break
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

def parse_date(text):
    """Try to extract a date from text."""
    patterns = [
        r'(\d{4})',  # 2024
        r'(\d{1,2}\s+\w+\s+\d{4})',  # 15 March 2024
        r'(\w+\s+\d{1,2},\s+\d{4})',  # March 15, 2024
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return datetime.now().strftime("%Y-%m-%d")

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

    # ---- Option 1: Try multiple primary selectors ----
    selectors = [
        '.c-card--conflict',
        '.card--conflict',
        '.conflict-card',
        '.conflict-item',
        '.c-card__conflict',
        '.card-conflict'
    ]

    cards = []
    for selector in selectors:
        cards = soup.select(selector)
        if cards:
            log(f"Found {len(cards)} conflicts with selector: {selector}")
            break

    if not cards:
        log("No conflict cards found with primary selectors.")
        # ---- Option 3: Enhanced fallback extraction ----
        log("Using enhanced fallback extraction...")
        cards = soup.find_all(['h2', 'h3', 'h4'])
        fallback_conflicts = []

        keywords = [
            'conflict', 'war', 'crisis', 'violence', 'escalation',
            'tension', 'dispute', 'battle', 'fighting', 'clash',
            'insurgency', 'rebellion', 'uprising', 'civil', 'military'
        ]

        for elem in cards:
            text = elem.text.strip()
            if not text:
                continue
            if any(k in text.lower() for k in keywords):
                name = text
                desc = ''
                status = 'Unknown'
                region = ''

                parent = elem.find_parent()
                if parent:
                    for p in parent.find_all(['p', 'div']):
                        p_text = p.text.strip()
                        if len(p_text) > 50 and len(p_text) < 1000:
                            desc = p_text
                            break

                    status_elem = parent.find(string=re.compile(r'Active|Worsening|Critical|Improving|Ceasefire|Ongoing|Stalemate'))
                    if status_elem:
                        status = status_elem.strip()

                    region_elem = parent.find(string=re.compile(r'Africa|Asia|Europe|Middle East|Americas|Global|Eastern Europe|East Asia|South Asia|Latin America'))
                    if region_elem:
                        region = region_elem.strip()

                if not desc:
                    next_p = elem.find_next('p')
                    if next_p:
                        desc = next_p.text.strip()

                if name:
                    conflict_id = generate_conflict_id(name)
                    lat, lng = geocode_location(f"{name} {region}".strip())
                    if not lat or not lng:
                        lat, lng = geocode_location(region)

                    fallback_conflicts.append({
                        "id": conflict_id,
                        "name": name,
                        "lat": lat or 0,
                        "lng": lng or 0,
                        "status": status,
                        "description": desc[:500] if desc else f"Conflict: {name}",
                        "source": "CFR Global Conflict Tracker (fallback)",
                        "last_updated": parse_date(desc)
                    })
                    log(f"  Extracted (fallback): {name}")

        if fallback_conflicts:
            log(f"Fallback extracted {len(fallback_conflicts)} conflicts")
            return fallback_conflicts
        else:
            log("No conflicts found in fallback either.")
            return []

    # Process primary selector cards
    for card in cards:
        try:
            name_elem = card.select_one('.c-card__title')
            if not name_elem:
                name_elem = card.find(['h2', 'h3', 'h4'])
            if not name_elem:
                continue

            name = name_elem.text.strip()

            status_elem = card.select_one('.c-card__status')
            if not status_elem:
                status_elem = card.find(string=re.compile(r'Active|Worsening|Critical|Improving|Ceasefire|Ongoing|Stalemate'))
            status = status_elem.text.strip() if status_elem else 'Unknown'

            region_elem = card.select_one('.c-card__region')
            if not region_elem:
                region_elem = card.find(string=re.compile(r'Africa|Asia|Europe|Middle East|Americas|Global|Eastern Europe|East Asia|South Asia|Latin America'))
            region = region_elem.text.strip() if region_elem else ''

            desc_elem = card.select_one('.c-card__description')
            if not desc_elem:
                desc_elem = card.find('p')
            description = desc_elem.text.strip() if desc_elem else ''

            conflict_id = generate_conflict_id(name)
            lat, lng = geocode_location(f"{name} {region}".strip())
            if not lat or not lng:
                lat, lng = geocode_location(region)

            conflicts.append({
                "id": conflict_id,
                "name": name,
                "lat": lat or 0,
                "lng": lng or 0,
                "status": status,
                "description": description[:500] if description else f"Conflict: {name}",
                "source": "CFR Global Conflict Tracker",
                "last_updated": parse_date(description)
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
        log(f"Total conflicts in CFR: {len(conflicts)}")
    else:
        log("No conflicts fetched – check the website or selectors")

if __name__ == "__main__":
    main()

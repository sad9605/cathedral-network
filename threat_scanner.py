#!/usr/bin/env python3
"""
threat_scanner.py – Cathedral Threat Scanner
Fetches emerging threats from GDELT and merges them into threats.json.
Now with safe loading and deduplication.
"""
import json
import requests
from datetime import datetime, timezone
import sys

# --------------------------------------------------
# 1. LOAD EXISTING THREATS (SAFE MODE)
# --------------------------------------------------
print("🔎 Scanning for emerging threats...")

try:
    with open("threats.json", "r") as f:
        raw_threats = json.load(f)
    # Only clean if it's truly broken (not a list)
    if isinstance(raw_threats, list):
        existing_threats = [t for t in raw_threats if isinstance(t, dict)]
        if len(existing_threats) != len(raw_threats):
            print(f"⚠️  Found {len(raw_threats) - len(existing_threats)} invalid threat entries. Fixing...")
            with open("threats.json", "w") as f:
                json.dump(existing_threats, f, indent=2)
            print("✅ threats.json has been cleaned.")
        else:
            existing_threats = raw_threats
    elif isinstance(raw_threats, dict) and "threats" in raw_threats:
        existing_threats = raw_threats["threats"]
    else:
        print("⚠️  threats.json is not a list. Initializing empty list.")
        existing_threats = []
except FileNotFoundError:
    print("⚠️  threats.json not found. Creating empty list.")
    existing_threats = []

# --------------------------------------------------
# 2. LOAD EXISTING CANDIDATES (SAFE MODE)
# --------------------------------------------------
try:
    with open("new_threat_candidates.json", "r") as f:
        raw_candidates = json.load(f)
    if isinstance(raw_candidates, list):
        existing_candidates = [c for c in raw_candidates if isinstance(c, dict)]
        if len(existing_candidates) != len(raw_candidates):
            print(f"⚠️  Found {len(raw_candidates) - len(existing_candidates)} invalid candidate entries. Fixing...")
            with open("new_threat_candidates.json", "w") as f:
                json.dump(existing_candidates, f, indent=2)
            print("✅ new_threat_candidates.json has been cleaned.")
        else:
            existing_candidates = raw_candidates
    elif isinstance(raw_candidates, dict) and "candidates" in raw_candidates:
        existing_candidates = raw_candidates["candidates"]
    else:
        print("⚠️  new_threat_candidates.json is not a list. Initializing empty list.")
        existing_candidates = []
except FileNotFoundError:
    print("⚠️  new_threat_candidates.json not found. Creating empty list.")
    existing_candidates = []

# --------------------------------------------------
# 3. BUILD EXISTING NAME LOOKUPS
# --------------------------------------------------
existing_names = [t.get("name", "").lower() for t in existing_threats if isinstance(t, dict)]
candidate_names = [c.get("name", "").lower() for c in existing_candidates if isinstance(c, dict)]

# --------------------------------------------------
# 4. FETCH FROM GDELT (with fallback)
# --------------------------------------------------
print("🌐 Fetching GDELT articles...")
try:
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "conflict OR war OR clash OR riot OR protest OR attack",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 20,
        "timespan": "24h"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    if not articles:
        raise Exception("Empty response")
    print(f"✅ Fetched {len(articles)} articles from GDELT.")
    use_fallback = False
except Exception as e:
    print(f"⚠️  GDELT fetch failed ({e}). Using fallback mock data.")
    use_fallback = True
    # Fallback data
    articles = [
        {"title": "Sudan-Ethiopia Border Clashes over Al-Fashaga", "source": "Mock OSINT", "url": "", "seendate": datetime.now(timezone.utc).isoformat(), "lat": 12.0, "lng": 36.0},
        {"title": "Philippines-China Scarborough Shoal Standoff", "source": "Mock OSINT", "url": "", "seendate": datetime.now(timezone.utc).isoformat(), "lat": 15.0, "lng": 117.0},
        {"title": "Haiti Gang Alliance Targets Port-au-Prince Airport", "source": "Mock OSINT", "url": "", "seendate": datetime.now(timezone.utc).isoformat(), "lat": 18.56, "lng": -72.29},
        {"title": "Myanmar Junta Airstrikes in Karen State", "source": "Mock OSINT", "url": "", "seendate": datetime.now(timezone.utc).isoformat(), "lat": 17.2, "lng": 97.7},
        {"title": "DRC M23 Rebel Advance on Goma", "source": "Mock OSINT", "url": "", "seendate": datetime.now(timezone.utc).isoformat(), "lat": -1.67, "lng": 29.23}
    ]

# --------------------------------------------------
# 5. PROCESS ARTICLES INTO CANDIDATES
# --------------------------------------------------
new_candidates = []
now = datetime.now(timezone.utc)

for article in articles:
    title = article.get("title", "").strip()
    if not title:
        continue
    source = article.get("source", "Unknown")
    url = article.get("url", "")
    date = article.get("seendate", now.isoformat())
    lat = article.get("lat")
    lng = article.get("lng")

    # Skip if already in threats or candidates
    if title.lower() in existing_names or title.lower() in candidate_names:
        continue
    if len(title.split()) < 3:
        continue

    candidate = {
        "id": f"CAN-{now.strftime('%Y%m%d')}-{len(new_candidates)+1:02d}",
        "name": title[:80],
        "status": "Candidate",
        "candidateStatus": "Pending Review",
        "source": source,
        "url": url,
        "date": date,
        "lat": float(lat) if lat else None,
        "lng": float(lng) if lng else None,
        "description": f"Detected by GDELT on {date[:10]}" if not use_fallback else f"Fallback: {title[:100]}",
        "detectedDate": now.isoformat()
    }
    new_candidates.append(candidate)

print(f"🆕 Found {len(new_candidates)} new candidate threats.")

# --------------------------------------------------
# 6. SAVE NEW CANDIDATES
# --------------------------------------------------
if new_candidates:
    updated_candidates = existing_candidates + new_candidates
    with open("new_threat_candidates.json", "w") as f:
        json.dump(updated_candidates, f, indent=2)
    print(f"\n✅ Added {len(new_candidates)} candidate(s) to new_threat_candidates.json.")
    for c in new_candidates:
        print(f"   - {c['name']} ({c['source']})")
else:
    print("\nℹ️  No new candidates found. All events already tracked.")

# --------------------------------------------------
# 7. SUMMARY
# --------------------------------------------------
print(f"\n📊 Summary:")
print(f"   Existing threats: {len(existing_threats)}")
print(f"   Total candidates: {len(updated_candidates) if new_candidates else len(existing_candidates)}")

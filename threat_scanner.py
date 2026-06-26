import json
import requests
from datetime import datetime
import sys

# ----------------------------
# 1. LOAD EXISTING THREATS
# ----------------------------
# 1. LOAD EXISTING THREATS (with automatic cleanup)
try:
    with open('threats.json', 'r') as f:
        raw_threats = json.load(f)
    # Only keep items that are dictionaries (ignore random strings)
    existing_threats = [t for t in raw_threats if isinstance(t, dict)]
    if len(existing_threats) != len(raw_threats):
        print("⚠️  threats.json had invalid entries. They were automatically skipped.")
        # Save the cleaned version back to the file
        with open('threats.json', 'w') as f:
            json.dump(existing_threats, f, indent=2)
        print("✅ threats.json has been cleaned automatically.")
except FileNotFoundError:
    print("⚠️  threats.json not found. Creating empty list.")
    existing_threats = []

# Load existing candidates (clean up bad data too)
try:
    with open('new_threat_candidates.json', 'r') as f:
        raw_candidates = json.load(f)
    existing_candidates = [c for c in raw_candidates if isinstance(c, dict)]
    if len(existing_candidates) != len(raw_candidates):
        print("⚠️  new_threat_candidates.json had invalid entries. They were skipped.")
        with open('new_threat_candidates.json', 'w') as f:
            json.dump(existing_candidates, f, indent=2)
except FileNotFoundError:
    existing_candidates = []

# Get names of existing threats for duplicate checking
existing_names = [t.get("name", "").lower() for t in existing_threats]
candidate_names = [c.get("name", "").lower() for c in existing_candidates]

# ----------------------------
# 2. FETCH REAL EVENTS FROM GDELT
# ----------------------------
print("🔎 Scanning GDELT for emerging threats...")

try:
    # GDELT's free article search API - last 24 hours, conflict-related
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
        print("⚠️  GDELT returned no articles. Using fallback mock data.")
        raise Exception("Empty response")
    
    print(f"✅ Fetched {len(articles)} articles from GDELT.")
    
    new_candidates = []
    for article in articles:
        title = article.get("title", "Unknown Event")
        source = article.get("source", "Unknown")
        url = article.get("url", "")
        date = article.get("seendate", datetime.utcnow().isoformat())
        lat = article.get("lat")
        lng = article.get("lng")
        
        # Skip if this title is already in threats or candidates
        if title.lower() in existing_names or title.lower() in candidate_names:
            continue
        
        # Skip if no title or title is too short/generic
        if len(title.split()) < 3:
            continue
        
        # Build candidate threat
        candidate = {
            "id": f"CAN-{datetime.utcnow().strftime('%Y%m%d')}-{len(new_candidates)+1}",
            "name": title[:80],  # Trim if too long
            "status": "Candidate",
            "candidateStatus": "Pending Review",
            "source": source,
            "url": url,
            "date": date,
            "lat": float(lat) if lat else None,
            "lng": float(lng) if lng else None,
            "description": f"Detected by GDELT on {date[:10]}",
            "detectedDate": datetime.utcnow().isoformat()
        }
        new_candidates.append(candidate)
    
    print(f"🆕 Found {len(new_candidates)} new candidate threats.")

except Exception as e:
    print(f"⚠️  GDELT fetch failed ({e}). Using fallback mock data instead.")
    
    # ----------------------------
    # FALLBACK: Realistic mock threats for testing
    # ----------------------------
    fallback_candidates = [
        {
            "id": "CAN-FALLBACK-01",
            "name": "Sudan-Ethiopia Border Clashes over Al-Fashaga",
            "status": "Candidate",
            "candidateStatus": "Pending Review",
            "source": "Mock OSINT (fallback)",
            "date": datetime.utcnow().isoformat(),
            "lat": 12.0,
            "lng": 36.0,
            "description": "Ethiopian militia crossed into Sudanese territory near the disputed farming region.",
            "detectedDate": datetime.utcnow().isoformat()
        },
        {
            "id": "CAN-FALLBACK-02",
            "name": "Philippines-China Scarborough Shoal Standoff",
            "status": "Candidate",
            "candidateStatus": "Pending Review",
            "source": "Mock OSINT (fallback)",
            "date": datetime.utcnow().isoformat(),
            "lat": 15.0,
            "lng": 117.0,
            "description": "Chinese coastguard vessels block Filipino fishermen from traditional fishing grounds.",
            "detectedDate": datetime.utcnow().isoformat()
        },
        {
            "id": "CAN-FALLBACK-03",
            "name": "Haiti Gang Alliance Targets Port-au-Prince Airport",
            "status": "Candidate",
            "candidateStatus": "Pending Review",
            "source": "Mock OSINT (fallback)",
            "date": datetime.utcnow().isoformat(),
            "lat": 18.56,
            "lng": -72.29,
            "description": "Multiple gangs unite to besiege the international airport, cutting off aid routes.",
            "detectedDate": datetime.utcnow().isoformat()
        }
    ]
    
    new_candidates = []
    for candidate in fallback_candidates:
        # Check duplicates against existing threats and candidates
        if candidate["name"].lower() not in existing_names and candidate["name"].lower() not in candidate_names:
            new_candidates.append(candidate)
    
    print(f"🆕 Found {len(new_candidates)} new candidate threats from fallback.")

# ----------------------------
# 4. SAVE NEW CANDIDATES
# ----------------------------
if new_candidates:
    # Append to existing candidates
    updated_candidates = existing_candidates + new_candidates
    with open('new_threat_candidates.json', 'w') as f:
        json.dump(updated_candidates, f, indent=2)
    
    print(f"\n✅ Added {len(new_candidates)} candidate(s) to new_threat_candidates.json.")
    print("\n📋 New candidates:")
    for c in new_candidates:
        print(f"   - {c['name']} ({c['source']})")
else:
    print("\nℹ️  No new candidates found. All events already tracked.")

# ----------------------------
# 5. SUMMARY
# ----------------------------
print(f"\n📊 Summary:")
print(f"   Existing threats: {len(existing_threats)}")
print(f"   Total candidates: {len(updated_candidates) if new_candidates else len(existing_candidates)}")

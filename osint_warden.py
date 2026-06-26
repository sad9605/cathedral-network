#!/usr/bin/env python3
"""
H11 – OSINT Triage Warden
Automatically reviews new threat candidates, scores them, and promotes urgent ones.
"""
import json
import math
from datetime import datetime, timezone

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
PROMOTE_THRESHOLD = 70   # If triage_score >= 70, auto-promote to threats.json
SOURCE_WEIGHTS = {
    "gdelt": 80,
    "reuters": 90,
    "bbc": 85,
    "ap": 85,
    "un": 90,
    "osint": 60,
    "twitter": 40,
    "telegram": 50,
    "mock": 30
}
URGENT_KEYWORDS = ["attack", "clash", "siege", "blockade", "missile", "drone", "offensive", "breakthrough", "escalate"]

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------
print("🔍 OSINT Triage Warden (H11) running...")

try:
    with open("new_threat_candidates.json", "r") as f:
        candidates = json.load(f)
    if not candidates:
        print("ℹ️  No candidates to triage.")
        exit(0)
except FileNotFoundError:
    print("⚠️  new_threat_candidates.json not found.")
    exit(0)

try:
    with open("threats.json", "r") as f:
        threats = json.load(f)
except FileNotFoundError:
    threats = []

# --------------------------------------------------
# 2. SCORE EACH CANDIDATE
# --------------------------------------------------
promoted = []
updated_candidates = []

for candidate in candidates:
    # Skip if already promoted or ignored
    if candidate.get("triage_status") in ["Promoted", "Ignored"]:
        updated_candidates.append(candidate)
        continue

    name = candidate.get("name", "").lower()
    source = candidate.get("source", "unknown").lower()
    description = candidate.get("description", "").lower()
    lat = candidate.get("lat")
    lng = candidate.get("lng")

    # Base score from source
    base_score = 50
    for src, weight in SOURCE_WEIGHTS.items():
        if src in source:
            base_score = weight
            break

    # Keyword boost
    keyword_boost = 0
    for word in URGENT_KEYWORDS:
        if word in name or word in description:
            keyword_boost += 10
    keyword_boost = min(keyword_boost, 30)  # Cap at 30

    # Proximity to existing Red/Orange threats
    proximity_boost = 0
    if lat and lng:
        for t in threats:
            if t.get("status") in ["Red", "Orange"]:
                t_lat = t.get("lat")
                t_lng = t.get("lng")
                if t_lat and t_lng:
                    # Simple Euclidean distance (rough)
                    distance = math.sqrt((lat - t_lat)**2 + (lng - t_lng)**2)
                    if distance < 5:  # Within ~5 degrees (roughly 500km)
                        proximity_boost += 20
                        break
                    elif distance < 10:
                        proximity_boost += 10

    # Final score (capped at 100)
    triage_score = min(base_score + keyword_boost + proximity_boost, 100)

    # Determine status
    if triage_score >= PROMOTE_THRESHOLD:
        triage_status = "Promote"
    elif triage_score >= 40:
        triage_status = "Watch"
    else:
        triage_status = "Ignore"

    # Update candidate with score
    candidate["triage_score"] = triage_score
    candidate["triage_status"] = triage_status
    candidate["last_triage"] = datetime.now(timezone.utc).isoformat()

    # If Promote, move to threats.json
    if triage_status == "Promote":
        # Create a new threat entry
        new_threat = {
            "id": f"C{len(threats)+100:03d}",  # Keep new IDs separate
            "name": candidate.get("name"),
            "status": "Yellow",  # Start as Yellow, let human upgrade
            "lat": candidate.get("lat"),
            "lng": candidate.get("lng"),
            "scp": 0.35,  # Conservative start
            "priority_score": 35.0,
            "description": candidate.get("description", "Promoted by OSINT Warden"),
            "source": candidate.get("source"),
            "promoted_date": datetime.now(timezone.utc).isoformat()
        }
        threats.append(new_threat)
        promoted.append(new_threat)
        print(f"✅ Promoted: {new_threat['name']} (Score: {triage_score})")

    updated_candidates.append(candidate)

# --------------------------------------------------
# 3. SAVE UPDATED FILES
# --------------------------------------------------
# Save updated candidates (remove promoted ones if you want, or keep them as record)
# We'll keep them but mark as Promoted
with open("new_threat_candidates.json", "w") as f:
    json.dump(updated_candidates, f, indent=2)

# Save updated threats
with open("threats.json", "w") as f:
    json.dump(threats, f, indent=2)

# --------------------------------------------------
# 4. SUMMARY
# --------------------------------------------------
print(f"📊 Triage complete.")
print(f"   Candidates reviewed: {len(updated_candidates)}")
print(f"   Promoted: {len(promoted)}")
print(f"   Watch: {len([c for c in updated_candidates if c.get('triage_status') == 'Watch'])}")
print(f"   Ignored: {len([c for c in updated_candidates if c.get('triage_status') == 'Ignore'])}")

if promoted:
    print("\n✅ Auto-promoted threats added to threats.json.")
    print("   ⚠️  Please review them and adjust status/SCP if needed.")

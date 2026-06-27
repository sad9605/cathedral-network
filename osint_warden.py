#!/usr/bin/env python3
"""
H11 – OSINT Triage Warden
Automatically reviews new threat candidates, scores them, and promotes urgent ones.
Supports --dry-run flag to preview actions without modifying threats.json.
"""
import json
import math
import sys
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

# Check for --dry-run flag
DRY_RUN = "--dry-run" in sys.argv
if DRY_RUN:
    print("🔒 DRY RUN MODE: Will score candidates but NOT promote them.")

# --------------------------------------------------
# 1. LOAD CANDIDATES (SAFE)
# --------------------------------------------------
print("🔍 OSINT Triage Warden (H11) running...")

try:
    with open("new_threat_candidates.json", "r") as f:
        raw_candidates = json.load(f)
    if isinstance(raw_candidates, list):
        candidates = [c for c in raw_candidates if isinstance(c, dict)]
        if len(candidates) != len(raw_candidates):
            print(f"⚠️  Found {len(raw_candidates) - len(candidates)} invalid candidate entries. Skipping.")
    elif isinstance(raw_candidates, dict) and "candidates" in raw_candidates:
        candidates = [c for c in raw_candidates["candidates"] if isinstance(c, dict)]
    else:
        print("⚠️  new_threat_candidates.json is not a list. Initializing empty list.")
        candidates = []
except FileNotFoundError:
    print("⚠️  new_threat_candidates.json not found.")
    candidates = []

if not candidates:
    print("ℹ️  No candidates to triage.")
    sys.exit(0)

# --------------------------------------------------
# 2. LOAD EXISTING THREATS (SAFE)
# --------------------------------------------------
try:
    with open("threats.json", "r") as f:
        raw_threats = json.load(f)
    if isinstance(raw_threats, list):
        threats = [t for t in raw_threats if isinstance(t, dict)]
        if len(threats) != len(raw_threats):
            print(f"⚠️  Found {len(raw_threats) - len(threats)} invalid threat entries. Skipping.")
    elif isinstance(raw_threats, dict) and "threats" in raw_threats:
        threats = [t for t in raw_threats["threats"] if isinstance(t, dict)]
    else:
        print("⚠️  threats.json is not a list. Initializing empty list.")
        threats = []
except FileNotFoundError:
    print("⚠️  threats.json not found. Creating empty list.")
    threats = []

# --------------------------------------------------
# 3. SCORE EACH CANDIDATE
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
                    distance = math.sqrt((lat - t_lat)**2 + (lng - t_lng)**2)
                    if distance < 5:
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

    # If Promote, move to threats.json (skip if DRY_RUN)
    if triage_status == "Promote":
        if DRY_RUN:
            print(f"🔒 [DRY RUN] Would promote: {candidate.get('name')} (Score: {triage_score})")
            candidate["triage_status"] = "Would-Promote (DRY)"
            updated_candidates.append(candidate)
            continue
        else:
            # Create a new threat entry
            # Generate a new ID based on existing IDs
            max_id = 0
            for t in threats:
                tid = t.get("id", "")
                if tid.startswith("C"):
                    try:
                        num = int(tid[1:])
                        if num > max_id:
                            max_id = num
                    except:
                        pass
            new_id = f"C{max_id+1:03d}"
            new_threat = {
                "id": new_id,
                "name": candidate.get("name"),
                "status": "Yellow",  # Start as Yellow, let human upgrade
                "lat": candidate.get("lat"),
                "lng": candidate.get("lng"),
                "scp": 0.35,
                "priority_score": 35.0,
                "description": candidate.get("description", "Promoted by OSINT Warden"),
                "source": candidate.get("source"),
                "promoted_date": datetime.now(timezone.utc).isoformat()
            }
            threats.append(new_threat)
            promoted.append(new_threat)
            print(f"✅ Promoted: {new_threat['name']} (Score: {triage_score})")
            updated_candidates.append(candidate)
            continue
    else:
        updated_candidates.append(candidate)

# --------------------------------------------------
# 4. SAVE UPDATED FILES
# --------------------------------------------------
# Save updated candidates (always save)
with open("new_threat_candidates.json", "w") as f:
    json.dump(updated_candidates, f, indent=2)

# Save updated threats only if NOT dry-run
if not DRY_RUN:
    with open("threats.json", "w") as f:
        json.dump(threats, f, indent=2)

# --------------------------------------------------
# 5. SUMMARY
# --------------------------------------------------
print(f"📊 Triage complete.")
print(f"   Candidates reviewed: {len(updated_candidates)}")
if not DRY_RUN:
    print(f"   Promoted: {len(promoted)}")
else:
    promoted_dry = [c for c in updated_candidates if c.get('triage_status') == 'Would-Promote (DRY)']
    print(f"   Would-Promote (DRY): {len(promoted_dry)}")
print(f"   Watch: {len([c for c in updated_candidates if c.get('triage_status') == 'Watch'])}")
print(f"   Ignored: {len([c for c in updated_candidates if c.get('triage_status') == 'Ignore'])}")

if promoted and not DRY_RUN:
    print("\n✅ Auto-promoted threats added to threats.json.")
    print("   ⚠️  Please review them and adjust status/SCP if needed.")
elif DRY_RUN and any(c.get('triage_status') == 'Would-Promote (DRY)' for c in updated_candidates):
    print("\n🔒 DRY RUN: No changes were made to threats.json.")
    print("   To enable auto-promotion, run without --dry-run or set OSINT_DRY_RUN=False in run_wardens.py.")

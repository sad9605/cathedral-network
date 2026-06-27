#!/usr/bin/env python3
"""
H04 – Rule Suggester
Analyzes threats and existing cascades to suggest new cascade rules.
Suggests geographic, escalation, and pattern-based rules.
"""
import json
import math
from datetime import datetime, timezone

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
PROXIMITY_THRESHOLD = 10.0  # degrees (roughly 1,000 km)
CONFIDENCE_MIN = 50         # Minimum confidence % to show a suggestion

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------
print("🧠 Rule Suggester (H04) running...")

try:
    with open("threats.json", "r") as f:
        threats = json.load(f)
except FileNotFoundError:
    print("❌ threats.json not found.")
    exit(1)

try:
    with open("cascade_log.json", "r") as f:
        cascade_data = json.load(f)
        existing_cascades = cascade_data.get("cascades", []) if isinstance(cascade_data, dict) else cascade_data
except FileNotFoundError:
    existing_cascades = []

try:
    with open("archive.json", "r") as f:
        archive = json.load(f)
except FileNotFoundError:
    archive = []

# --------------------------------------------------
# 2. BUILD THREAT MAP
# --------------------------------------------------
# Create lookup by ID
threat_map = {t.get("id"): t for t in threats}

# Extract Red/Orange threats (sources)
critical_threats = [t for t in threats if t.get("status") in ["Red", "Orange"]]
# Extract Yellow/Green threats (potential targets)
secondary_threats = [t for t in threats if t.get("status") in ["Yellow", "Green"]]

# --------------------------------------------------
# 3. GEOGRAPHIC PROXIMITY SUGGESTIONS
# --------------------------------------------------
geo_suggestions = []

print("\n📍 Checking geographic proximity...")
for source in critical_threats:
    s_lat = source.get("lat")
    s_lng = source.get("lng")
    if not s_lat or not s_lng:
        continue
    for target in secondary_threats:
        t_lat = target.get("lat")
        t_lng = target.get("lng")
        if not t_lat or not t_lng:
            continue
        # Euclidean distance
        distance = math.sqrt((s_lat - t_lat)**2 + (s_lng - t_lng)**2)
        if distance < PROXIMITY_THRESHOLD and distance > 0.1:
            # Confidence decreases with distance
            confidence = int(80 - (distance / PROXIMITY_THRESHOLD) * 30)
            if confidence >= CONFIDENCE_MIN:
                geo_suggestions.append({
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "target_id": target.get("id"),
                    "target_name": target.get("name"),
                    "rule_type": "proximity",
                    "confidence": confidence,
                    "distance_degrees": round(distance, 2),
                    "description": f"{source.get('name')} and {target.get('name')} are geographically close ({distance:.1f}° apart). Escalation in one may trigger the other.",
                    "active": False
                })

print(f"   Found {len(geo_suggestions)} geographic proximity suggestions.")

# --------------------------------------------------
# 4. STATUS ESCALATION SUGGESTIONS (If Red is near Yellow)
# --------------------------------------------------
escalation_suggestions = []

print("\n📈 Checking status escalation patterns...")
for source in critical_threats:
    for target in secondary_threats:
        # If target is already Yellow or Green, suggest it could escalate to Orange/Red
        if target.get("status") == "Yellow" and source.get("status") == "Red":
            # Check if they are somewhat close (within 20 degrees)
            s_lat, s_lng = source.get("lat"), source.get("lng")
            t_lat, t_lng = target.get("lat"), target.get("lng")
            if s_lat and s_lng and t_lat and t_lng:
                distance = math.sqrt((s_lat - t_lat)**2 + (s_lng - t_lng)**2)
                if distance < 20:
                    confidence = int(70 - (distance / 20) * 20)
                    if confidence >= CONFIDENCE_MIN:
                        escalation_suggestions.append({
                            "source_id": source.get("id"),
                            "source_name": source.get("name"),
                            "target_id": target.get("id"),
                            "target_name": target.get("name"),
                            "rule_type": "escalation",
                            "confidence": confidence,
                            "description": f"If {source.get('name')} (Red) intensifies, {target.get('name')} (Yellow) may escalate to Orange/Red.",
                            "active": False
                        })

print(f"   Found {len(escalation_suggestions)} escalation suggestions.")

# --------------------------------------------------
# 5. PATTERN-BASED SUGGESTIONS (from existing cascades)
# --------------------------------------------------
pattern_suggestions = []

print("\n🔗 Checking cascade patterns...")
if existing_cascades:
    # Extract all source-target pairs
    existing_pairs = [(c.get("source"), c.get("target")) for c in existing_cascades if c.get("active")]
    # Look for threats that appear as targets but not sources, and vice versa
    all_ids = [t.get("id") for t in threats]
    source_ids = [c.get("source") for c in existing_cascades if c.get("active")]
    target_ids = [c.get("target") for c in existing_cascades if c.get("active")]

    # Suggest that if a threat is often a source, its nearby neighbors could become targets
    for source in critical_threats:
        s_id = source.get("id")
        if s_id in source_ids:
            # This threat is already a known source
            for target in secondary_threats:
                t_id = target.get("id")
                # Check if they are close and not already a cascade
                s_lat, s_lng = source.get("lat"), source.get("lng")
                t_lat, t_lng = target.get("lat"), target.get("lng")
                if s_lat and s_lng and t_lat and t_lng:
                    distance = math.sqrt((s_lat - t_lat)**2 + (s_lng - t_lng)**2)
                    if distance < 15 and (s_id, t_id) not in existing_pairs:
                        confidence = 75
                        pattern_suggestions.append({
                            "source_id": s_id,
                            "source_name": source.get("name"),
                            "target_id": t_id,
                            "target_name": target.get("name"),
                            "rule_type": "pattern",
                            "confidence": confidence,
                            "description": f"{source.get('name')} is already a known cascade source. Nearby {target.get('name')} may become a new target.",
                            "active": False
                        })

print(f"   Found {len(pattern_suggestions)} pattern-based suggestions.")

# --------------------------------------------------
# 6. COMBINE AND SCORE SUGGESTIONS
# --------------------------------------------------
all_suggestions = geo_suggestions + escalation_suggestions + pattern_suggestions

# Remove duplicates (same source-target pair)
unique_suggestions = []
seen_pairs = set()
for s in all_suggestions:
    pair = (s.get("source_id"), s.get("target_id"))
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        unique_suggestions.append(s)

# Sort by confidence (highest first)
unique_suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)

# --------------------------------------------------
# 7. SAVE RESULTS
# --------------------------------------------------
output = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "suggestions": unique_suggestions,
    "stats": {
        "total_suggestions": len(unique_suggestions),
        "proximity": len(geo_suggestions),
        "escalation": len(escalation_suggestions),
        "pattern": len(pattern_suggestions)
    }
}

with open("suggested_rules.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Saved {len(unique_suggestions)} unique rule suggestions to suggested_rules.json.")

# --------------------------------------------------
# 8. DISPLAY TOP SUGGESTIONS
# --------------------------------------------------
print("\n🏆 TOP 5 SUGGESTED RULES:")
for i, s in enumerate(unique_suggestions[:5], 1):
    print(f"   {i}. {s['source_name']} → {s['target_name']}")
    print(f"      Type: {s['rule_type']} | Confidence: {s['confidence']}%")
    print(f"      {s['description']}\n")

print("💡 To add a rule, copy the source-target pair from suggested_rules.json into cascade_log.json.")

#!/usr/bin/env python3
"""
H03 - SCP Recalibration Tool
Adjusts dampening, ML weight, and learning rates to restore Red/Black threat prominence.
Run this whenever you want to rebalance your threat scores.
"""
import json
import sys
from datetime import datetime, timezone

# --------------------------------------------------
# CONFIGURATION KNOBS (Adjust these to tune the engine)
# --------------------------------------------------
ML_WEIGHT = {
    "Red": 1.45,      # Red threats get a 45% boost
    "Orange": 1.20,   # Orange get 20% boost
    "Yellow": 0.95,   # Yellow get slightly reduced (dampened)
    "Green": 0.80,    # Green get dampened the most
    "Candidate": 0.70 # Candidates are kept low until verified
}

DAMPENING_FACTOR = 0.90  # Prevents scores from drifting too high overall
LR_BOOST = 1.08          # Extra "learning rate" push for critical items

# --------------------------------------------------
# 1. LOAD CURRENT THREATS
# --------------------------------------------------
try:
    with open("threats.json", "r") as f:
        threats = json.load(f)
    if not isinstance(threats, list):
        print("⚠️ threats.json is not a list. Creating empty list.")
        threats = []
    else:
        # Filter out non-dict entries
        threats = [t for t in threats if isinstance(t, dict)]
        print(f"📂 Loaded {len(threats)} threats from threats.json")
except FileNotFoundError:
    print("⚠️ threats.json not found. Creating new file.")
    threats = []
    with open("threats.json", "w") as f:
        json.dump(threats, f, indent=2)

if not threats:
    print("ℹ️ No threats to recalibrate. Exiting.")
    sys.exit(0)

# --------------------------------------------------
# 2. RECALCULATE SCP AND PRIORITY SCORES
# --------------------------------------------------
print("\n⚙️  Recalibrating SCP scores...")
updated_count = 0

for threat in threats:
    status = threat.get("status", "Yellow")
    old_scp = threat.get("scp", 0.5)
    old_priority = threat.get("priority_score", 50.0)
    
    # Get the weight for this status (default to 1.0 if not found)
    weight = ML_WEIGHT.get(status, 1.0)
    
    # Apply ML Weight and Dampening
    new_scp = old_scp * weight * DAMPENING_FACTOR
    
    # Apply Learning Rate boost for critical statuses
    if status in ["Red", "Orange"]:
        new_scp = new_scp * LR_BOOST
    
    # Cap SCP between 0.1 and 0.99 (never reach 1.0, keeps room for escalation)
    new_scp = max(0.1, min(0.99, new_scp))
    
    # Recalculate priority_score: SCP * 100 + status bonus
    status_bonus = {"Red": 15, "Orange": 8, "Yellow": 0, "Green": -5, "Candidate": -10}
    bonus = status_bonus.get(status, 0)
    new_priority = (new_scp * 100) + bonus
    
    # Round for cleanliness
    new_scp = round(new_scp, 4)
    new_priority = round(new_priority, 2)
    
    # Update the threat
    threat["scp"] = new_scp
    threat["priority_score"] = new_priority
    
    # Track change
    if abs(new_scp - old_scp) > 0.01:
        updated_count += 1
        print(f"   {threat['id']}: {old_scp:.4f} → {new_scp:.4f} (Status: {status})")

# --------------------------------------------------
# 3. SAVE THE UPDATED THREATS
# --------------------------------------------------
with open("threats.json", "w") as f:
    json.dump(threats, f, indent=2)

print(f"\n✅ Updated {updated_count} threats with recalibrated SCP scores.")
print(f"📁 Saved to threats.json")

# --------------------------------------------------
# 4. SHOW TOP 5 THREATS AFTER RECALIBRATION
# --------------------------------------------------
if threats:
    print("\n🏆 TOP 5 THREATS (After Recalibration):")
    sorted_threats = sorted(threats, key=lambda x: x.get("priority_score", 0), reverse=True)
    for i, t in enumerate(sorted_threats[:5], 1):
        print(f"   {i}. {t.get('name', 'Unnamed')} (SCP: {t.get('scp', 0):.4f} | Priority: {t.get('priority_score', 0):.2f} | Status: {t.get('status', 'Unknown')})")

print("\n⚙️  H03 Recalibration complete.")

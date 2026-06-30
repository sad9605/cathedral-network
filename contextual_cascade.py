#!/usr/bin/env python3
"""
contextual_cascade.py – DeepCausality integration for Cathedral Network
Adds context‑aware cascade propagation:
- Region weight multipliers
- Time decay / urgency
- IVF adjustment
- Cascade density scaling
"""

import json
from datetime import datetime, timezone

# ── Context multipliers ──
REGION_WEIGHTS = {
    "Middle East": 1.3,
    "South Asia": 1.2,
    "Europe": 1.1,
    "East Asia": 1.4,
    "North America": 1.0,
    "Africa": 1.2,
    "Latin America": 1.1,
    "Southeast Asia": 1.2,
    "Arctic": 0.8,
    "Global": 1.0
}

IVF_MULTIPLIER = 1.2  # If IVF > 0.7, amplify

CASCADE_DENSITY_MULTIPLIER = 1.1  # If > 10 active cascades in region, amplify

def load_threats():
    with open("threats.json", "r") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("threats", [])

def load_rules():
    with open("cascade_rules.json", "r") as f:
        data = json.load(f)
        return data.get("rules", [])

def load_status():
    try:
        with open("cascade_status.json", "r") as f:
            return json.load(f)
    except:
        return {}

def apply_contextual_multipliers(threats, rules, status_data):
    """
    Apply contextual multipliers to cascade propagation.
    """
    active_statuses = status_data.get("statuses", {})
    active_list = active_statuses.get("active", []) + active_statuses.get("armed", []) + active_statuses.get("triggered", [])

    # Count active cascades per region
    region_counts = {}
    for t in threats:
        region = t.get("region", "Global")
        if region in region_counts:
            region_counts[region] += 1
        else:
            region_counts[region] = 1

    for t in threats:
        region = t.get("region", "Global")
        base_scp = t.get("scp", 0.5)

        # 1. Region weight
        region_weight = REGION_WEIGHTS.get(region, 1.0)

        # 2. IVF multiplier
        ivf = t.get("ivf", 0.5)
        if ivf > 0.7:
            ivf_weight = IVF_MULTIPLIER
        else:
            ivf_weight = 1.0

        # 3. Cascade density multiplier
        region_count = region_counts.get(region, 0)
        if region_count > 10:
            density_weight = CASCADE_DENSITY_MULTIPLIER
        else:
            density_weight = 1.0

        # Apply multipliers
        contextual_scp = base_scp * region_weight * ivf_weight * density_weight
        contextual_scp = min(contextual_scp, 0.99)

        t["scp_contextual"] = round(contextual_scp, 4)
        t["contextual_multipliers"] = {
            "region_weight": round(region_weight, 2),
            "ivf_weight": round(ivf_weight, 2),
            "density_weight": round(density_weight, 2)
        }

    return threats

def main():
    print("🧠 DeepCausality (Contextual Cascade) running...")

    threats = load_threats()
    rules = load_rules()
    status_data = load_status()

    if not threats:
        print("⚠️ No threats found.")
        return

    updated = apply_contextual_multipliers(threats, rules, status_data)

    with open("threats.json", "w") as f:
        json.dump(updated, f, indent=2)

    print("✅ Contextual multipliers applied.")
    print("   - Region weights")
    print("   - IVF amplification")
    print("   - Cascade density scaling")

if __name__ == "__main__":
    main()

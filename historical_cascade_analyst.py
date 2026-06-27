#!/usr/bin/env python3
"""
historical_cascade_analyst.py – Cathedral Cascade Rule Reverse-Engineer
Extracts cascade rules from historical crisis patterns.
Outputs suggested_rules.json with historical cascade suggestions.
"""
import json
from datetime import datetime, timezone

# ── Historical cascade knowledge ──
HISTORICAL_CASCADES = {
    "Global Financial Crisis": [
        {"trigger": "US housing market collapse", "effect": "Subprime mortgage defaults", "delay_days": 30},
        {"trigger": "Subprime mortgage defaults", "effect": "Lehman Brothers bankruptcy", "delay_days": 45},
        {"trigger": "Lehman Brothers bankruptcy", "effect": "Global credit freeze", "delay_days": 7},
        {"trigger": "Global credit freeze", "effect": "Stock market crash", "delay_days": 3},
        {"trigger": "Stock market crash", "effect": "Banking bailouts", "delay_days": 14}
    ],
    "COVID-19 Pandemic": [
        {"trigger": "Wuhan outbreak", "effect": "WHO declaration", "delay_days": 60},
        {"trigger": "WHO declaration", "effect": "Global lockdowns", "delay_days": 7},
        {"trigger": "Global lockdowns", "effect": "Supply chain disruption", "delay_days": 14},
        {"trigger": "Supply chain disruption", "effect": "Economic contraction", "delay_days": 30}
    ],
    "Russia-Ukraine Full-Scale Invasion": [
        {"trigger": "Troop buildup", "effect": "Russian invasion", "delay_days": 60},
        {"trigger": "Russian invasion", "effect": "Western sanctions", "delay_days": 5},
        {"trigger": "Western sanctions", "effect": "Energy price spike", "delay_days": 14},
        {"trigger": "Energy price spike", "effect": "Global inflation", "delay_days": 30}
    ]
}

def extract_rules(crisis_name, cascade_chain):
    rules = []
    for step in cascade_chain:
        trigger = step["trigger"]
        effect = step["effect"]
        delay = step["delay_days"]
        confidence = 85 if delay < 30 else 70
        # Determine SCP threshold
        if "collapse" in trigger.lower() or "bankruptcy" in trigger.lower():
            trigger_scp = 0.85
        elif "declaration" in trigger.lower() or "lockdown" in trigger.lower():
            trigger_scp = 0.75
        elif "spike" in trigger.lower() or "surge" in trigger.lower():
            trigger_scp = 0.70
        else:
            trigger_scp = 0.65

        rules.append({
            "id": f"RC-{crisis_name[:4].upper()}-{len(rules)+1:02d}",
            "name": f"{trigger} → {effect}",
            "source_pattern": trigger,
            "target_pattern": effect,
            "source_domain": "historical",
            "target_domain": "historical",
            "trigger_scp_threshold": trigger_scp,
            "average_delay_days": delay,
            "confidence": confidence,
            "historical_basis": crisis_name,
            "active": False,
            "suggested_for_cascade_log": True
        })
    return rules

def main():
    print("🏛️  Historical Cascade Analyst running...")
    all_rules = []
    for crisis, chain in HISTORICAL_CASCADES.items():
        rules = extract_rules(crisis, chain)
        all_rules.extend(rules)
        print(f"   Extracted {len(rules)} rules from {crisis}")

    # Load existing suggestions if any
    try:
        with open("suggested_rules.json", "r") as f:
            existing = json.load(f)
            if isinstance(existing, dict) and "suggestions" in existing:
                existing_list = existing["suggestions"]
            else:
                existing_list = existing if isinstance(existing, list) else []
    except FileNotFoundError:
        existing_list = []

    # Deduplicate by name
    existing_names = {r.get("name") for r in existing_list}
    new_rules = [r for r in all_rules if r.get("name") not in existing_names]

    combined = existing_list + new_rules

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suggestions": combined,
        "stats": {
            "total_suggestions": len(combined),
            "historical_suggestions_added": len(new_rules),
            "historical_sources": list(HISTORICAL_CASCADES.keys())
        }
    }

    with open("suggested_rules.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Added {len(new_rules)} historical cascade rules to suggested_rules.json")
    print(f"📊 Total suggested rules: {len(combined)}")

if __name__ == "__main__":
    main()

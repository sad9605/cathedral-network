#!/usr/bin/env python3
"""
ascension_tuner.py – Cathedral Ascension Tuner
Calibrates the Ascension Engine and Optimism Matrix using historical recoveries.
Outputs ascension_config.json.
"""
import json
from datetime import datetime, timezone

# ── Historical recovery data ──
RECOVERIES = {
    "Global Financial Crisis": {
        "peak_crisis": "2008-09-15",
        "recovery_start": "2009-03-09",
        "recovery_complete": "2012-06-30",
        "recovery_type": "gradual",
        "peak_scp": 0.89,
        "optimism_reset": 0.35,
        "ascension_trigger": 0.42,
        "time_to_ascension_days": 175
    },
    "COVID-19 Pandemic": {
        "peak_crisis": "2020-03-11",
        "recovery_start": "2020-05-01",
        "recovery_complete": "2021-06-30",
        "recovery_type": "V-shaped",
        "peak_scp": 0.92,
        "optimism_reset": 0.65,
        "ascension_trigger": 0.38,
        "time_to_ascension_days": 140
    },
    "Russia-Ukraine Full-Scale Invasion": {
        "peak_crisis": "2022-03-01",
        "recovery_start": "2022-10-01",
        "recovery_complete": "2024-12-31",
        "recovery_type": "slow-burn",
        "peak_scp": 0.81,
        "optimism_reset": 0.25,
        "ascension_trigger": 0.45,
        "time_to_ascension_days": 270
    }
}

def derive_ascension_rule(data):
    recovery_type = data["recovery_type"]
    trigger = data["ascension_trigger"]
    time_to = data["time_to_ascension_days"]
    optimism = data["optimism_reset"]
    speed = "fast" if time_to < 180 else "moderate" if time_to < 360 else "slow"
    return {
        "trigger_threshold": trigger,
        "expected_timeframe_days": time_to,
        "recovery_type": recovery_type,
        "recovery_speed": speed,
        "optimism_boost": optimism,
        "confidence": 75 + (10 if recovery_type == "V-shaped" else 5)
    }

def main():
    print("🏛️  Ascension Tuner running...")

    config = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "historical_basis": list(RECOVERIES.keys()),
        "recovery_thresholds": {},
        "optimism_matrix": {},
        "ascension_rules": []
    }

    for crisis, data in RECOVERIES.items():
        rule = derive_ascension_rule(data)
        config["ascension_rules"].append({"crisis": crisis, "rule": rule})
        config["optimism_matrix"][crisis] = {
            "recovery_type": data["recovery_type"],
            "optimism_reset": data["optimism_reset"],
            "time_to_ascension_days": data["time_to_ascension_days"],
            "confidence": rule["confidence"]
        }
        config["recovery_thresholds"][crisis] = {
            "ascension_trigger": data["ascension_trigger"],
            "peak_scp": data["peak_scp"],
            "recovery_complete": data["recovery_complete"]
        }

    with open("ascension_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Ascension Engine config saved to ascension_config.json")
    print(f"   - {len(config['ascension_rules'])} ascension rules derived")
    print(f"   - {len(config['optimism_matrix'])} optimism matrix entries")
    print(f"   - {len(config['recovery_thresholds'])} recovery thresholds")

if __name__ == "__main__":
    main()

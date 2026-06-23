#!/usr/bin/env python3
"""
generate_prediction_intelligence.py – Build reasoning traces for all predictions.
"""

import json
from datetime import datetime
from pathlib import Path

PREDICTIONS_FILE = "predictions.json"
THREATS_FILE = "threats.json"
CASCADE_LOG_FILE = "cascade_log.json"
OUTPUT_FILE = "prediction_intelligence.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("🧠 Generating prediction intelligence...")
    predictions = load_json(PREDICTIONS_FILE, {})
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    cascade_log = load_json(CASCADE_LOG_FILE, [])

    intelligence = {}

    # Helper to find threat by ID
    threat_map = {t.get('id'): t for t in threats if t.get('id')}

    # Process all predictions (pending, confirmed, falsified)
    for status in ['pending', 'confirmed', 'falsified']:
        for p in predictions.get(status, []):
            tid = p.get('id')
            if not tid:
                continue

            # Find threat data
            threat = threat_map.get(tid)
            base_prob = threat.get('base_probability', 0.5) if threat else 0.5

            # Build evidence sources
            evidence = []

            # Cascade evidence
            for entry in cascade_log[-50:]:  # last 50 entries
                if entry.get('source') == tid or entry.get('target') == tid:
                    evidence.append({
                        "type": "Cascade",
                        "description": f"Cascade from {entry.get('source')} to {entry.get('target')}",
                        "likelihood_ratio": 1.5,
                        "weight": 0.8
                    })
                    break  # only need one cascade entry

            # OSINT evidence (if available in threat)
            if threat and threat.get('description'):
                evidence.append({
                    "type": "OSINT",
                    "description": threat.get('description', '')[:80],
                    "likelihood_ratio": 2.0,
                    "weight": 0.9
                })

            # Build reasoning object
            intelligence[tid] = {
                "id": tid,
                "prediction": p.get('description', ''),
                "current_probability": p.get('probability', 0),
                "date_made": p.get('date_made', ''),
                "horizon": p.get('horizon', ''),
                "status": status.capitalize(),
                "reasoning": {
                    "prior": {
                        "value": base_prob,
                        "source": "Historical baseline from threats.json"
                    },
                    "evidence": evidence if evidence else [{"type": "Default", "description": "No specific evidence recorded", "likelihood_ratio": 1.0, "weight": 1.0}],
                    "calculation": {
                        "prior_odds": f"{base_prob:.2f} / {1-base_prob:.2f} = {(base_prob/(1-base_prob+0.001)):.2f}",
                        "posterior_odds": "N/A",
                        "posterior_probability": f"{p.get('probability', 0)}%"
                    },
                    "adjusted_probability": p.get('probability', 0),
                    "adjustment_reason": "Daily sweep update"
                },
                "forecast": "See current status in Ground Truth.",
                "recommendations": ["Monitor related cascades", "Verify against OSINT"],
                "confidence": 0.7,
                "sources": ["Cascade Engine", "OSINT", "TSF"]
            }

    save_json(intelligence, OUTPUT_FILE)
    print(f"✅ Prediction intelligence generated: {len(intelligence)} entries")

if __name__ == "__main__":
    main()

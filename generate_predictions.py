#!/usr/bin/env python3
"""
generate_predictions.py – Automatically generate predictions from engine data.
Timestamped, auditable, and hit-rate verified.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

THREATS_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
PREDICTIONS_FILE = "predictions.json"

def load_json(filepath):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_predictions():
    # Load engine data
    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])
    last_updated = threats_data.get('last_updated', datetime.now().isoformat())

    # Load existing predictions (preserve confirmed/falsified history)
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        predictions = {
            "confirmed": [],
            "falsified": [],
            "pending": [],
            "watchlist": [],
            "stats": {
                "confirmed": 0,
                "falsified": 0,
                "hit_rate": 0,
                "pending": 0,
                "watchlist": 0
            },
            "history": []  # audit log
        }

    # Map existing pending predictions by ID
    existing_pending = {p['id']: p for p in predictions.get('pending', [])}
    existing_confirmed_ids = {p['id'] for p in predictions.get('confirmed', [])}
    existing_falsified_ids = {p['id'] for p in predictions.get('falsified', [])}

    # Generate new predictions from threats
    new_predictions = []
    for t in threats:
        # Skip if already confirmed or falsified
        if t['id'] in existing_confirmed_ids or t['id'] in existing_falsified_ids:
            continue

        # Generate prediction for high-priority threats
        priority = t.get('priority_score', 0)
        scp = t.get('scp', 0.5)
        
        if priority > 60 or scp > 0.6:
            pred = {
                "id": t['id'],
                "description": t.get('name', '')[:80],
                "probability": round(t.get('base_probability', 0.5) * 100),
                "scp": round(scp, 2),
                "created": datetime.now().isoformat(),
                "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "Active"
            }
            
            # Update if exists, otherwise add
            if t['id'] in existing_pending:
                # Update probability and scp
                existing_pending[t['id']].update({
                    "probability": pred['probability'],
                    "scp": pred['scp'],
                    "updated": datetime.now().isoformat()
                })
            else:
                new_predictions.append(pred)

    # Add new predictions to pending
    predictions['pending'].extend(new_predictions)

    # Update stats
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    pending = predictions.get('pending', [])
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)

    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(pending),
        "watchlist": len(predictions.get('watchlist', []))
    }
    predictions['last_updated'] = datetime.now().isoformat()

    # Append to history (audit log)
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "auto_generate",
        "new_predictions": len(new_predictions),
        "pending_count": len(pending),
        "hit_rate": hit_rate
    })

    # Keep history at last 100 entries
    predictions['history'] = predictions['history'][-100:]

    save_json(predictions, PREDICTIONS_FILE)
    
    print(f"✅ Prediction Log Updated:")
    print(f"   New predictions generated: {len(new_predictions)}")
    print(f"   Total pending: {len(pending)}")
    print(f"   Confirmed: {len(confirmed)}")
    print(f"   Falsified: {len(falsified)}")
    print(f"   Hit rate: {hit_rate}%")

if __name__ == "__main__":
    generate_predictions()

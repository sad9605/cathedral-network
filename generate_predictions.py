#!/usr/bin/env python3
"""
generate_predictions.py – Auto-generate predictions from engine data.
Preserves confirmed/falsified history, updates pending probabilities, adds date_made to all.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

THREATS_FILE = "threats.json"
PREDICTIONS_FILE = "predictions.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_predictions():
    print("📋 Generating prediction log (preserving history, adding date_made)...")
    
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        predictions = {
            "confirmed": [],
            "falsified": [],
            "pending": [],
            "watchlist": [],
            "stats": {},
            "history": [],
            "last_updated": ""
        }
    
    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])
    
    pending_map = {p['id']: p for p in predictions.get('pending', [])}
    confirmed_ids = {p['id'] for p in predictions.get('confirmed', [])}
    falsified_ids = {p['id'] for p in predictions.get('falsified', [])}
    
    updated_count = 0
    added_count = 0
    now = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    
    for t in threats:
        tid = t.get('id', '')
        if not tid:
            continue
        if tid in confirmed_ids or tid in falsified_ids:
            continue
        if tid in pending_map:
            # Update existing pending – preserve date_made
            pending_map[tid]['probability'] = round(t.get('base_probability', 0.5) * 100)
            pending_map[tid]['scp'] = round(t.get('scp', 0.5), 2)
            pending_map[tid]['priority_score'] = round(t.get('priority_score', 0), 2)
            pending_map[tid]['updated'] = now
            # Ensure date_made exists (should already)
            if 'date_made' not in pending_map[tid]:
                pending_map[tid]['date_made'] = today
            updated_count += 1
        else:
            # New prediction – add date_made
            new_pred = {
                "id": tid,
                "description": t.get('name', tid)[:80],
                "probability": round(t.get('base_probability', 0.5) * 100),
                "scp": round(t.get('scp', 0.5), 2),
                "priority_score": round(t.get('priority_score', 0), 2),
                "horizon": "30 days",
                "status": "Active",
                "date_made": today,      # <-- creation date
                "created": today,
                "updated": now
            }
            predictions['pending'].append(new_pred)
            pending_map[tid] = new_pred
            added_count += 1
    
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    pending = predictions.get('pending', [])
    watchlist = predictions.get('watchlist', [])
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)
    
    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(pending),
        "watchlist": len(watchlist)
    }
    predictions['last_updated'] = datetime.now().isoformat()
    
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "auto_generate",
        "updated": updated_count,
        "added": added_count,
        "pending_count": len(pending),
        "hit_rate": hit_rate
    })
    predictions['history'] = predictions['history'][-100:]
    
    save_json(predictions, PREDICTIONS_FILE)
    print(f"✅ Prediction Log Updated:")
    print(f"   Updated pending: {updated_count}, Added: {added_count}")
    print(f"   Confirmed: {len(confirmed)}")
    print(f"   Falsified: {len(falsified)}")
    print(f"   Hit rate: {hit_rate}%")
    print(f"   Pending: {len(pending)}")

if __name__ == "__main__":
    generate_predictions()

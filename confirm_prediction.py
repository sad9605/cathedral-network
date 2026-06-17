#!/usr/bin/env python3
"""
confirm_prediction.py – Confirm or falsify a prediction by ID.
"""

import json
from datetime import datetime
import sys

PREDICTIONS_FILE = "predictions.json"

def confirm(prediction_id):
    with open(PREDICTIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Find and move from pending to confirmed
    pending = data.get('pending', [])
    for i, p in enumerate(pending):
        if p['id'] == prediction_id:
            p['confirmed_date'] = datetime.now().isoformat()
            p['outcome'] = True
            data['confirmed'].append(p)
            data['pending'].pop(i)
            break
    
    # Recalculate stats
    confirmed = data.get('confirmed', [])
    falsified = data.get('falsified', [])
    total = len(confirmed) + len(falsified)
    data['stats']['hit_rate'] = round((len(confirmed) / total * 100) if total > 0 else 0, 2)
    data['stats']['confirmed'] = len(confirmed)
    data['stats']['falsified'] = len(falsified)
    data['stats']['pending'] = len(data.get('pending', []))
    data['last_updated'] = datetime.now().isoformat()
    
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Prediction {prediction_id} confirmed. Hit rate: {data['stats']['hit_rate']}%")

def falsify(prediction_id, reason=""):
    with open(PREDICTIONS_FILE, 'r') as f:
        data = json.load(f)
    
    pending = data.get('pending', [])
    for i, p in enumerate(pending):
        if p['id'] == prediction_id:
            p['falsified_date'] = datetime.now().isoformat()
            p['outcome'] = False
            p['reason'] = reason
            data['falsified'].append(p)
            data['pending'].pop(i)
            break
    
    confirmed = data.get('confirmed', [])
    falsified = data.get('falsified', [])
    total = len(confirmed) + len(falsified)
    data['stats']['hit_rate'] = round((len(confirmed) / total * 100) if total > 0 else 0, 2)
    data['stats']['confirmed'] = len(confirmed)
    data['stats']['falsified'] = len(falsified)
    data['stats']['pending'] = len(data.get('pending', []))
    data['last_updated'] = datetime.now().isoformat()
    
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"❌ Prediction {prediction_id} falsified. Hit rate: {data['stats']['hit_rate']}%")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: confirm_prediction.py <confirm|falsify> <prediction_id> [reason]")
        sys.exit(1)
    
    action = sys.argv[1]
    pred_id = sys.argv[2]
    reason = sys.argv[3] if len(sys.argv) > 3 else ""
    
    if action == "confirm":
        confirm(pred_id)
    elif action == "falsify":
        falsify(pred_id, reason)
    else:
        print("Invalid action. Use 'confirm' or 'falsify'.")

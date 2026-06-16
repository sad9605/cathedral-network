#!/usr/bin/env python3
"""
update_prediction.py – Add/confirm/falsify predictions and auto-commit.
"""

import json
from datetime import datetime

PREDICTIONS_FILE = "predictions.json"

def add_confirmed(prediction_id, description):
    with open(PREDICTIONS_FILE, 'r') as f:
        data = json.load(f)
    
    data['confirmed'].append({
        "id": prediction_id,
        "description": description,
        "date": datetime.now().strftime("%d %b %Y")
    })
    data['stats']['confirmed'] += 1
    data['stats']['pending'] -= 1
    data['stats']['hit_rate'] = round(
        data['stats']['confirmed'] / (data['stats']['confirmed'] + data['stats']['falsified']) * 100, 2
    )
    
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_falsified(prediction_id, description, reason):
    with open(PREDICTIONS_FILE, 'r') as f:
        data = json.load(f)
    
    data['falsified'].append({
        "id": prediction_id,
        "description": description,
        "date": datetime.now().strftime("%d %b %Y"),
        "reason": reason
    })
    data['stats']['falsified'] += 1
    data['stats']['pending'] -= 1
    data['stats']['hit_rate'] = round(
        data['stats']['confirmed'] / (data['stats']['confirmed'] + data['stats']['falsified']) * 100, 2
    )
    
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    # Example usage:
    # add_confirmed("P112", "AI deepfake delays US county election certification within 14 days")
    # add_falsified("P78", "Brent >$120/bbl within 7 days", "Oil prices remained below $120")
    print("Run with: python -c 'from update_prediction import add_confirmed; add_confirmed(\"P112\", \"...\")'")

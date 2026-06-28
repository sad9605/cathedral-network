#!/usr/bin/env python3
"""
create_prediction.py – Add a new prediction to the log.
Usage: python3 create_prediction.py "Statement" YYYY-MM-DD 72 "Confirmation criteria" "Falsification criteria"
"""
import json
import sys
from datetime import datetime, timezone

def main():
    if len(sys.argv) < 6:
        print("Usage: python3 create_prediction.py 'Statement' YYYY-MM-DD 72 'Confirmation criteria' 'Falsification criteria'")
        print("Example: python3 create_prediction.py 'Oil prices will exceed $90/barrel' 2026-12-31 72 'Oil prices > $90' 'Oil prices < $90'")
        sys.exit(1)
    
    statement = sys.argv[1]
    deadline = sys.argv[2]
    confidence = int(sys.argv[3])
    confirmation_criteria = sys.argv[4]
    falsification_criteria = sys.argv[5]
    
    # Load existing predictions
    try:
        with open("predictions.json", "r") as f:
            preds = json.load(f)
        if isinstance(preds, dict) and "predictions" in preds:
            preds = preds["predictions"]
        if not isinstance(preds, list):
            preds = []
        preds = [p for p in preds if isinstance(p, dict)]
    except FileNotFoundError:
        preds = []
    
    # Generate new ID
    existing_ids = [int(p.get("id", "P000").replace("P", "")) for p in preds if p.get("id", "").startswith("P")]
    max_id = max(existing_ids) if existing_ids else 0
    new_id = f"P{max_id+1:03d}"
    
    new_pred = {
        "id": new_id,
        "statement": statement,
        "logged_date": datetime.now(timezone.utc).isoformat(),
        "deadline": deadline,
        "confidence": confidence,
        "confirmation_criteria": confirmation_criteria,
        "falsification_criteria": falsification_criteria,
        "verification_status": "Pending",
        "verified": False,
        "hit": None,
        "verification_note": None,
        "validation_issues": []
    }
    
    preds.append(new_pred)
    
    with open("predictions.json", "w") as f:
        json.dump(preds, f, indent=2)
    
    print(f"✅ Prediction {new_id} added!")
    print(f"   Statement: {statement}")
    print(f"   Deadline: {deadline}")
    print(f"   Confidence: {confidence}%")
    print(f"   Confirmation criteria: {confirmation_criteria}")
    print(f"   Falsification criteria: {falsification_criteria}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
prediction_checker.py – Cathedral Prediction Checker
Daily sweep that checks predictions against current data.
Marks confirmed or falsified based on criteria.
"""
import json
from datetime import datetime, timezone

def load_data():
    """Load all relevant data for checking predictions."""
    try:
        with open("threats.json", "r") as f:
            threats = json.load(f)
        if not isinstance(threats, list):
            threats = []
        threats = [t for t in threats if isinstance(t, dict)]
    except FileNotFoundError:
        threats = []
    
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
    
    try:
        with open("cascade_log.json", "r") as f:
            cascades = json.load(f)
        if isinstance(cascades, dict) and "cascades" in cascades:
            cascades = cascades["cascades"]
        if not isinstance(cascades, list):
            cascades = []
        cascades = [c for c in cascades if isinstance(c, dict)]
    except FileNotFoundError:
        cascades = []
    
    return threats, preds, cascades

def check_prediction(pred, threats, cascades):
    """Check a single prediction against current data."""
    # Skip if already resolved
    if pred.get("verification_status") in ["Confirmed", "Falsified", "Expired"]:
        return pred
    
    # Check if deadline has passed
    deadline_str = pred.get("deadline")
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline < datetime.now(timezone.utc):
                pred["verification_status"] = "Expired"
                pred["verification_note"] = f"Deadline {deadline_str} passed without confirmation."
                print(f"⏰ Prediction {pred.get('id')} expired on {deadline_str}")
                return pred
        except:
            pass
    
    # Check against threats
    statement = pred.get("statement", "").lower()
    confirmation_criteria = pred.get("confirmation_criteria", "").lower()
    falsification_criteria = pred.get("falsification_criteria", "").lower()
    
    # Look for matching threats
    matched_threats = []
    for t in threats:
        name = t.get("name", "").lower()
        if any(kw in name for kw in statement.split()[:5]):
            matched_threats.append(t)
    
    # If we found matching threats, check their status
    if matched_threats:
        # Check for confirmation criteria
        if confirmation_criteria:
            # Simple check: see if any matched threat has the criteria in its name or description
            for t in matched_threats:
                t_name = t.get("name", "").lower()
                t_desc = t.get("description", "").lower()
                if confirmation_criteria in t_name or confirmation_criteria in t_desc:
                    pred["verification_status"] = "Confirmed"
                    pred["verification_note"] = f"Confirmed by threat: {t.get('name')}"
                    pred["hit"] = True
                    pred["verified"] = True
                    print(f"✅ Prediction {pred.get('id')} confirmed!")
                    return pred
        
        # Check for falsification criteria
        if falsification_criteria:
            # If the opposite of the criteria is true (e.g., "oil below $80" and oil is above)
            for t in matched_threats:
                t_name = t.get("name", "").lower()
                if "not" in falsification_criteria:
                    continue  # Too complex for simple check
                # If the threat exists but doesn't match the criteria, it might be falsified
                # This is a placeholder for more complex logic
                pass
    
    # Check against cascades (if prediction was about a cascade)
    for c in cascades:
        source = c.get("source", "").lower()
        target = c.get("target", "").lower()
        if "cascade" in statement and (source in statement or target in statement):
            if c.get("active"):
                pred["verification_status"] = "Confirmed"
                pred["verification_note"] = f"Cascade active: {c.get('source')} → {c.get('target')}"
                pred["hit"] = True
                pred["verified"] = True
                print(f"✅ Prediction {pred.get('id')} confirmed (cascade active)!")
                return pred
    
    return pred

def main():
    print("📊 Prediction Checker (Daily Sweep) running...")
    
    threats, preds, cascades = load_data()
    print(f"📊 Loaded {len(threats)} threats, {len(preds)} predictions, {len(cascades)} cascades")
    
    updated = 0
    confirmed = 0
    falsified = 0
    expired = 0
    
    for i, p in enumerate(preds):
        p = check_prediction(p, threats, cascades)
        preds[i] = p
        
        if p.get("verification_status") == "Confirmed":
            confirmed += 1
            updated += 1
        elif p.get("verification_status") == "Falsified":
            falsified += 1
            updated += 1
        elif p.get("verification_status") == "Expired":
            expired += 1
            updated += 1
    
    # Save updates
    if updated > 0:
        with open("predictions.json", "w") as f:
            json.dump(preds, f, indent=2)
    
    print(f"\n📊 Sweep Summary:")
    print(f"   Total predictions: {len(preds)}")
    print(f"   Confirmed: {confirmed}")
    print(f"   Falsified: {falsified}")
    print(f"   Expired: {expired}")
    print(f"   Updated: {updated}")

if __name__ == "__main__":
    main()

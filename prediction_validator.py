#!/usr/bin/env python3
"""
prediction_validator.py – Cathedral Prediction Validator
Ensures all predictions meet the required standards.
Flags missing deadlines, unclear criteria, and expired predictions.
"""
import json
from datetime import datetime, timezone

REQUIRED_FIELDS = [
    "id",
    "statement",
    "logged_date",
    "deadline",
    "confidence",
    "falsification_criteria",
    "confirmation_criteria"
]

def validate_prediction(pred):
    """Validate a single prediction against the standards."""
    issues = []
    for field in REQUIRED_FIELDS:
        if field not in pred or not pred[field]:
            issues.append(f"Missing required field: {field}")
    
    # Check confidence is a number
    if "confidence" in pred:
        try:
            conf = float(pred["confidence"])
            if conf < 0 or conf > 100:
                issues.append(f"Confidence must be between 0-100, got {conf}")
        except:
            issues.append("Confidence must be a number")
    
    # Check deadline is a valid date
    if "deadline" in pred and pred["deadline"]:
        try:
            deadline = datetime.strptime(pred["deadline"], "%Y-%m-%d")
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline < datetime.now(timezone.utc):
                if "verification_status" not in pred or pred["verification_status"] != "Resolved":
                    issues.append(f"Deadline {pred['deadline']} has passed without resolution")
        except ValueError:
            issues.append(f"Invalid deadline format: {pred['deadline']} (use YYYY-MM-DD)")
    
    return issues

def main():
    print("📋 Prediction Validator running...")
    
    try:
        with open("predictions.json", "r") as f:
            preds = json.load(f)
        if isinstance(preds, dict) and "predictions" in preds:
            preds = preds["predictions"]
        elif not isinstance(preds, list):
            print("⚠️ predictions.json is not a list. Creating empty list.")
            preds = []
    except FileNotFoundError:
        print("ℹ️ predictions.json not found. Creating empty file.")
        preds = []
        with open("predictions.json", "w") as f:
            json.dump([], f, indent=2)
        exit(0)
    
    # Filter out non-dict entries
    preds = [p for p in preds if isinstance(p, dict)]
    print(f"📊 Found {len(preds)} predictions.")
    
    validated = []
    expired_count = 0
    missing_count = 0
    
    for p in preds:
        issues = validate_prediction(p)
        if issues:
            p["validation_issues"] = issues
            missing_count += 1
            print(f"⚠️ Prediction {p.get('id', 'UNKNOWN')}: {', '.join(issues[:2])}")
        else:
            p["validation_issues"] = []
        
        # Check if expired
        if "deadline" in p and p["deadline"] and "verification_status" not in p:
            try:
                deadline = datetime.strptime(p["deadline"], "%Y-%m-%d")
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if deadline < datetime.now(timezone.utc):
                    p["verification_status"] = "Expired"
                    expired_count += 1
                    print(f"⏰ Prediction {p.get('id', 'UNKNOWN')} has expired (deadline: {p['deadline']})")
            except:
                pass
        
        validated.append(p)
    
    # Save updated predictions
    with open("predictions.json", "w") as f:
        json.dump(validated, f, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"   Total predictions: {len(validated)}")
    print(f"   Missing required fields: {missing_count}")
    print(f"   Expired (unresolved): {expired_count}")

if __name__ == "__main__":
    main()

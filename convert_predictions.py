#!/usr/bin/env python3
"""
convert_predictions.py – One-time conversion of legacy predictions.json
to the new flat format with proper fields.
"""
import json
from datetime import datetime, timezone

def infer_criteria(description, pred_type="pending"):
    """Generate basic criteria from description."""
    if pred_type == "confirmed":
        return f"Event described occurred: {description}"
    elif pred_type == "falsified":
        return f"Event described did NOT occur: {description}"
    else:
        return f"Monitor: {description}"

def convert_prediction(p, pred_type):
    """Convert a single prediction to the new format."""
    # Extract ID
    pred_id = p.get("id", f"UNKNOWN-{datetime.now().timestamp()}")
    
    # Extract statement
    statement = p.get("description", "No description")
    
    # Extract deadline/horizon
    if pred_type == "pending":
        deadline = p.get("horizon", "2026-12-31")
        # Convert "31 Jul 2026" to "2026-07-31"
        try:
            # Try to parse various date formats
            from dateutil import parser
            dt = parser.parse(deadline, fuzzy=True)
            deadline = dt.strftime("%Y-%m-%d")
        except:
            # If parsing fails, leave as is or set a default
            if "days" in deadline or "months" in deadline:
                # It's a relative timeframe, set a default
                deadline = "2026-12-31"
    else:
        # For confirmed/falsified, use the date it happened as the deadline
        date_str = p.get("date", "2026-12-31")
        try:
            from dateutil import parser
            dt = parser.parse(date_str, fuzzy=True)
            deadline = dt.strftime("%Y-%m-%d")
        except:
            deadline = "2026-12-31"
    
    # Extract confidence
    confidence = p.get("probability", 50)
    if pred_type == "confirmed":
        confidence = 100
    elif pred_type == "falsified":
        confidence = 0
    
    # Generate criteria
    confirmation_criteria = infer_criteria(statement, pred_type)
    falsification_criteria = f"Opposite of: {confirmation_criteria}"
    
    # Build the new prediction object
    new_pred = {
        "id": pred_id,
        "statement": statement,
        "logged_date": p.get("date_made", p.get("created", datetime.now(timezone.utc).isoformat())),
        "deadline": deadline,
        "confidence": confidence,
        "confirmation_criteria": confirmation_criteria,
        "falsification_criteria": falsification_criteria,
        "verification_status": "Confirmed" if pred_type == "confirmed" else "Falsified" if pred_type == "falsified" else "Pending",
        "verified": pred_type in ["confirmed", "falsified"],
        "hit": True if pred_type == "confirmed" else False if pred_type == "falsified" else None,
        "verification_note": p.get("reason", None),
        "validation_issues": [],
        "original_source": pred_type
    }
    return new_pred

def main():
    print("🔄 Converting predictions.json to new format...")
    
    # Load existing predictions
    with open("predictions.json", "r") as f:
        data = json.load(f)
    
    all_predictions = []
    
    # Convert confirmed
    for p in data.get("confirmed", []):
        all_predictions.append(convert_prediction(p, "confirmed"))
    
    # Convert falsified
    for p in data.get("falsified", []):
        all_predictions.append(convert_prediction(p, "falsified"))
    
    # Convert pending
    for p in data.get("pending", []):
        all_predictions.append(convert_prediction(p, "pending"))
    
    print(f"✅ Converted {len(all_predictions)} predictions.")
    
    # Save backup of original
    import shutil
    shutil.copy("predictions.json", "predictions.json.backup")
    print("📁 Backup saved as predictions.json.backup")
    
    # Save converted predictions
    with open("predictions.json", "w") as f:
        json.dump(all_predictions, f, indent=2)
    
    print("✅ Converted predictions saved to predictions.json")

if __name__ == "__main__":
    main()

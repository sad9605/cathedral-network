#!/usr/bin/env python3
"""
AW05 – Prediction Validation
Auto-validates expired predictions and suggests manual validation for others.
"""
import json
from datetime import datetime, timezone, timedelta

print("✅ Prediction Validation (AW05) running...")

# --------------------------------------------------
# 1. LOAD PREDICTIONS
# --------------------------------------------------
try:
    with open("predictions.json", "r") as f:
        preds = json.load(f)
    if not preds:
        print("ℹ️  No predictions to validate.")
        exit(0)
except FileNotFoundError:
    print("❌ predictions.json not found.")
    exit(1)

if isinstance(preds, dict):
    preds = preds.get("predictions", [])

# --------------------------------------------------
# 2. VALIDATE EACH PREDICTION
# --------------------------------------------------
now = datetime.now(timezone.utc)
updated = 0
auto_validated = 0
suggest_manual = 0

for p in preds:
    # Skip already verified
    if p.get("verified") is True:
        continue

    # If missed deadline -> auto-falsify
    if p.get("verification_status") == "Missed Deadline":
        p["verified"] = True
        p["hit"] = False
        p["validation_note"] = "Auto-falsified: deadline passed without evidence."
        auto_validated += 1
        updated += 1
        continue

    # If pending and older than 7 days -> suggest manual validation
    if p.get("verification_status") == "Pending":
        # Check creation date if available
        created_str = p.get("created_at")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if now - created > timedelta(days=7):
                    p["verification_status"] = "Needs Manual Validation"
                    p["validation_note"] = f"Prediction is { (now - created).days } days old. Please verify manually."
                    suggest_manual += 1
                    updated += 1
                    continue
            except:
                pass  # malformed date

# --------------------------------------------------
# 3. SAVE UPDATED PREDICTIONS
# --------------------------------------------------
if updated > 0:
    with open("predictions.json", "w") as f:
        json.dump(preds, f, indent=2)
    print(f"✅ Updated {updated} predictions.")

# --------------------------------------------------
# 4. GENERATE VALIDATION REPORT
# --------------------------------------------------
report = {
    "validated_at": now.isoformat(),
    "auto_validated_count": auto_validated,
    "suggest_manual_count": suggest_manual
}
with open("validation_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\n📊 Validation Summary:")
print(f"   Auto-falsified (missed deadlines): {auto_validated}")
print(f"   Suggested manual validation: {suggest_manual}")

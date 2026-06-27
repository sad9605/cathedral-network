#!/usr/bin/env python3
"""
AW04 – Warden Verification
Triage predictions: flag missed deadlines, low confidence, and pending ones.
"""
import json
from datetime import datetime, timezone

print("🧐 Warden Verification (AW04) running...")

# --------------------------------------------------
# 1. LOAD PREDICTIONS
# --------------------------------------------------
try:
    with open("predictions.json", "r") as f:
        preds = json.load(f)
    if not preds:
        print("ℹ️  No predictions to verify.")
        exit(0)
except FileNotFoundError:
    print("❌ predictions.json not found.")
    exit(1)

# Ensure we have a list
if isinstance(preds, dict):
    preds = preds.get("predictions", [])

# --------------------------------------------------
# 2. VERIFY EACH PREDICTION
# --------------------------------------------------
now = datetime.now(timezone.utc)
updated = 0
report = {
    "checked_at": now.isoformat(),
    "total": len(preds),
    "verified": 0,
    "missed_deadline": 0,
    "need_review": 0,
    "pending": 0,
    "details": []
}

for p in preds:
    # Skip if already verified (hit or miss)
    if p.get("verified") is True:
        report["verified"] += 1
        continue

    # Check if there's a deadline
    deadline_str = p.get("deadline")
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            if now > deadline:
                p["verification_status"] = "Missed Deadline"
                p["verified"] = False
                p["verification_note"] = f"Deadline passed on {deadline.isoformat()}"
                report["missed_deadline"] += 1
                updated += 1
                report["details"].append({
                    "id": p.get("id", "unknown"),
                    "statement": p.get("statement", "")[:60],
                    "status": "Missed Deadline"
                })
                continue
        except:
            pass  # malformed date, skip

    # Check confidence
    confidence = p.get("confidence", 50)
    if confidence < 60:
        p["verification_status"] = "Need Human Review"
        p["verification_note"] = f"Confidence is {confidence}% – below 60% threshold."
        report["need_review"] += 1
        updated += 1
        report["details"].append({
            "id": p.get("id", "unknown"),
            "statement": p.get("statement", "")[:60],
            "status": "Need Human Review"
        })
        continue

    # Otherwise, mark as pending
    if "verification_status" not in p:
        p["verification_status"] = "Pending"
        report["pending"] += 1
        updated += 1
        report["details"].append({
            "id": p.get("id", "unknown"),
            "statement": p.get("statement", "")[:60],
            "status": "Pending"
        })

# --------------------------------------------------
# 3. SAVE UPDATED PREDICTIONS
# --------------------------------------------------
if updated > 0:
    with open("predictions.json", "w") as f:
        json.dump(preds, f, indent=2)
    print(f"✅ Updated {updated} predictions with verification statuses.")

# --------------------------------------------------
# 4. SAVE VERIFICATION REPORT
# --------------------------------------------------
with open("verification_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\n📊 Verification Summary:")
print(f"   Total predictions: {report['total']}")
print(f"   Already verified: {report['verified']}")
print(f"   Missed deadline: {report['missed_deadline']}")
print(f"   Need human review: {report['need_review']}")
print(f"   Pending: {report['pending']}")

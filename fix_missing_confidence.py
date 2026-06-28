#!/usr/bin/env python3
"""
fix_missing_confidence.py – Add default confidence to predictions missing it.
"""
import json

try:
    with open("predictions.json", "r") as f:
        preds = json.load(f)
    if not isinstance(preds, list):
        print("⚠️ predictions.json is not a list.")
        exit(1)
except FileNotFoundError:
    print("⚠️ predictions.json not found.")
    exit(1)

updated = 0
for p in preds:
    if "confidence" not in p or p.get("confidence") is None:
        p["confidence"] = 50
        updated += 1

with open("predictions.json", "w") as f:
    json.dump(preds, f, indent=2)

print(f"✅ Added default confidence (50%) to {updated} predictions.")

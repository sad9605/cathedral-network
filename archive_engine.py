#!/usr/bin/env python3
"""
archive_engine.py – Cathedral Archive Engine
Moves resolved/inactive threats from threats.json to archive.json.
Now handles broad statuses: Recovered, Peace, Retreated, Ended, etc.
"""
import json
import shutil
from datetime import datetime, timezone

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
ARCHIVE_STATUSES = [
    "Green",
    "Resolved",
    "Inactive",
    "Archived",
    "Recovered",
    "Dormant",
    "Peace",
    "Retreated",
    "Ended"
]

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
print("📦 Archive Engine (H01) running...")

try:
    with open("threats.json", "r") as f:
        threats = json.load(f)
    if not isinstance(threats, list):
        threats = []
except FileNotFoundError:
    print("❌ threats.json not found.")
    exit(1)

try:
    with open("archive.json", "r") as f:
        archive = json.load(f)
    if not isinstance(archive, list):
        archive = []
except FileNotFoundError:
    archive = []

# --------------------------------------------------
# SEPARATE ACTIVE AND ARCHIVE-READY
# --------------------------------------------------
active_threats = []
archived_threats = []

for t in threats:
    if t.get("status") in ARCHIVE_STATUSES:
        # Add archive metadata
        t["archivedDate"] = datetime.now(timezone.utc).isoformat()
        t["archiveReason"] = f"Status changed to {t.get('status')}"
        archived_threats.append(t)
    else:
        active_threats.append(t)

# --------------------------------------------------
# UPDATE FILES
# --------------------------------------------------
if archived_threats:
    # Merge into archive (avoid duplicates by ID)
    existing_ids = {a.get("id") for a in archive}
    new_archive = archive.copy()
    for t in archived_threats:
        if t.get("id") not in existing_ids:
            new_archive.append(t)
            existing_ids.add(t.get("id"))
        else:
            # Update existing entry
            for i, a in enumerate(new_archive):
                if a.get("id") == t.get("id"):
                    new_archive[i] = t
                    break

    # Write updated files
    with open("threats.json", "w") as f:
        json.dump(active_threats, f, indent=2)

    with open("archive.json", "w") as f:
        json.dump(new_archive, f, indent=2)

    print(f"✅ Archived {len(archived_threats)} threat(s).")
    for t in archived_threats:
        print(f"   - {t.get('name')} (Status: {t.get('status')})")
else:
    print("ℹ️ No threats matched archive criteria.")

print(f"\n📊 Active threats remaining: {len(active_threats)}")
print(f"📦 Total threats in archive: {len(new_archive) if archived_threats else len(archive)}")

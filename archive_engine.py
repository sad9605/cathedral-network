#!/usr/bin/env python3
"""
archive_engine.py – Cathedral Archive Engine
Moves resolved, inactive, or stale low-risk threats to the archive.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

# ------------------------------------------------------------------
# 1. LOAD AND NORMALIZE THREATS
# ------------------------------------------------------------------

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def normalize_threats(data):
    """Convert various threat.json formats into a list of dicts."""
    if isinstance(data, list):
        if data and isinstance(data[0], str):
            # list of IDs – skip
            return []
        return data
    elif isinstance(data, dict):
        return data.get('threats', [])
    return []

# ------------------------------------------------------------------
# 2. ARCHIVE CRITERIA
# ------------------------------------------------------------------

def should_archive(threat: Dict[str, Any]) -> tuple[bool, str]:
    """
    Determine if a threat should be archived and the reason.
    Returns (should_archive, reason).
    """
    # Explicit status
    status = threat.get('status', '').lower()
    if status in ['resolved', 'inactive', 'peace_agreement', 'disaster_ended']:
        return True, f"Status: {status}"

    # Peace agreement confirmed flag
    if threat.get('peace_agreement_confirmed', False):
        return True, "Peace agreement confirmed"

    # Stale + low risk: no updates in 90 days and SCP < 0.25
    last_updated = threat.get('last_updated')
    if last_updated:
        try:
            last_dt = datetime.fromisoformat(last_updated)
            # Make it timezone-aware (assume UTC if naive)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            # If parsing fails, treat as old
            last_dt = datetime.now(timezone.utc) - timedelta(days=100)
        days_since = (datetime.now(timezone.utc) - last_dt).days
        scp = threat.get('scp', 0)
        if days_since > 90 and scp < 0.25:
            return True, f"Inactive for {days_since} days, low SCP ({scp:.2f})"
    else:
        # No timestamp – treat as old if it has no recent evidence
        if threat.get('scp', 0) < 0.25:
            return True, "No update timestamp and low SCP"

    return False, ""

# ------------------------------------------------------------------
# 3. MAIN ARCHIVE FUNCTION
# ------------------------------------------------------------------

def archive_old_threats(
    threats_file='threats.json',
    archive_file='archive.json'
) -> int:
    """
    Move archived threats from the main threats file to the archive.
    Returns the number of threats archived.
    """
    # Load threats
    threats_raw = load_json(threats_file)
    threats = normalize_threats(threats_raw)
    if not threats:
        print("⚠️ No threats found to archive.")
        return 0

    # Load existing archive
    existing_archive = load_json(archive_file) or []

    now = datetime.now(timezone.utc)
    active = []
    archived = []

    for threat in threats:
        should, reason = should_archive(threat)
        if should:
            # Add archive metadata
            threat['archived_date'] = now.isoformat()
            threat['archive_reason'] = reason
            archived.append(threat)
        else:
            active.append(threat)

    if not archived:
        print("📭 No threats met archive criteria.")
        return 0

    # Save active threats back
    with open(threats_file, 'w') as f:
        json.dump(active, f, indent=2)

    # Append to existing archive (deduplicate by id)
    existing_ids = {t.get('id') for t in existing_archive if t.get('id')}
    new_archived = [t for t in archived if t.get('id') not in existing_ids]
    if new_archived:
        existing_archive.extend(new_archived)
        with open(archive_file, 'w') as f:
            json.dump(existing_archive, f, indent=2)
    else:
        print("⚠️ All archived threats were already in archive.")

    print(f"✅ Archived {len(new_archived)} threats to {archive_file}")
    return len(new_archived)
   
    print(f"\n📊 Active threats remaining: {len(active_threats)}")
    print(f"📦 Total threats in archive: {len(archive)}")
# ------------------------------------------------------------------
# 4. STANDALONE RUN
# ------------------------------------------------------------------

if __name__ == '__main__':
    archive_old_threats()

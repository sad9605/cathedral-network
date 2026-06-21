#!/usr/bin/env python3
"""
generate_predictions.py – Auto-generate predictions from engine data.
Preserves confirmed/falsified history, updates pending probabilities,
applies filtering, adds date_made, and reincorporates CERES timestamp.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Import CERES hash function
from cathedral_math import hash_prediction

THREATS_FILE = "threats.json"
SWEEP_FILE = "sweep_report.json"
CASCADE_LOG_FILE = "cascade_log.json"
PREDICTIONS_FILE = "predictions.json"
CONFIG_FILE = "prediction_filter_config.json"
ARCHIVE_FILE = "predictions_archive.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_sweep_date():
    """Get the timestamp from sweep_report.json, fallback to today."""
    sweep = load_json(SWEEP_FILE, {})
    ts = sweep.get('timestamp')
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%Y-%m-%d")
        except:
            pass
    return datetime.now().strftime("%Y-%m-%d")

def parse_horizon_to_days(horizon_str):
    """Convert horizon string (e.g., '30 days', '31 Jul 2026') to days from today."""
    if not horizon_str:
        return 0
    # Try date format "31 Jul 2026"
    try:
        dt = datetime.strptime(horizon_str, "%d %b %Y")
        return (dt - datetime.now()).days
    except:
        pass
    # Try "30 days"
    match = re.search(r'(\d+)\s*day', horizon_str, re.I)
    if match:
        return int(match.group(1))
    # Try "~6 weeks"
    match = re.search(r'(\d+)\s*week', horizon_str, re.I)
    if match:
        return int(match.group(1)) * 7
    # If we can't parse, assume 30 days
    return 30

def check_event_triggered(tid, cascade_log, sweep_data):
    """Check if there is recent evidence for this threat."""
    # Look in cascade_log for this threat ID
    for entry in cascade_log:
        if entry.get('source') == tid or entry.get('target') == tid:
            return True
    # Look in sweep_report for event mentioning this threat ID
    events = sweep_data.get('events', [])
    for ev in events:
        if tid in ev.get('description', ''):
            return True
    return False

def generate_predictions():
    print("📋 Generating prediction log (preserving history, adding date_made)...")

    # Load config
    config = load_json(CONFIG_FILE, {})
    min_prob = config.get("min_probability", 0.25)
    min_delta = config.get("min_delta", 0.10)
    max_horizon_days = config.get("max_horizon_days", 90)
    require_event = config.get("require_event", True)

    # Load data
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        predictions = {
            "confirmed": [],
            "falsified": [],
            "pending": [],
            "watchlist": [],
            "stats": {},
            "history": [],
            "last_updated": "",
            "last_hash": "0"  # for CERES chain
        }

    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])
    sweep_data = load_json(SWEEP_FILE, {})
    cascade_log = load_json(CASCADE_LOG_FILE, [])

    sweep_date = get_sweep_date()
    now = datetime.now().isoformat()

    pending_map = {p['id']: p for p in predictions.get('pending', [])}
    confirmed_ids = {p['id'] for p in predictions.get('confirmed', [])}
    falsified_ids = {p['id'] for p in predictions.get('falsified', [])}

    updated_count = 0
    added_count = 0
    archived_count = 0
    archived = []

    last_hash = predictions.get('last_hash', '0')

    for t in threats:
        tid = t.get('id', '')
        if not tid:
            continue
        if tid in confirmed_ids or tid in falsified_ids:
            continue

        # Current probability
        current_prob = t.get('base_probability', 0.5)

        # Compute delta from previous pending entry if exists
        previous = pending_map.get(tid)
        if previous:
            previous_prob = previous.get('probability', 0.5) / 100.0
            delta = current_prob - previous_prob
        else:
            # For new threats, we can either skip delta check or set delta = 0
            delta = 0.0

        # Parse horizon
        horizon_str = t.get('horizon', '30 days')
        horizon_days = parse_horizon_to_days(horizon_str)

        # Check event trigger (if required)
        event_triggered = check_event_triggered(tid, cascade_log, sweep_data)

        # ---- Apply filters ----
        if current_prob < min_prob:
            archived.append({"id": tid, "reason": f"Probability {current_prob:.0%} < {min_prob:.0%}"})
            archived_count += 1
            continue
        if delta < min_delta:
            archived.append({"id": tid, "reason": f"Delta {delta:.2f} < {min_delta:.2f}"})
            archived_count += 1
            continue
        if horizon_days > max_horizon_days:
            archived.append({"id": tid, "reason": f"Horizon {horizon_days}d > {max_horizon_days}d"})
            archived_count += 1
            continue
        if require_event and not event_triggered:
            archived.append({"id": tid, "reason": "No recent OSINT/cascade event"})
            archived_count += 1
            continue

        # ---- Passed filters ----
        if tid in pending_map:
            # Update existing pending – preserve date_made and ceres_hash
            pending_map[tid]['probability'] = round(current_prob * 100)
            pending_map[tid]['scp'] = round(t.get('scp', 0.5), 2)
            pending_map[tid]['priority_score'] = round(t.get('priority_score', 0), 2)
            pending_map[tid]['updated'] = now
            if 'date_made' not in pending_map[tid]:
                pending_map[tid]['date_made'] = sweep_date
            updated_count += 1
        else:
            # New prediction – generate CERES hash
            pred_data = {
                "id": tid,
                "probability": round(current_prob * 100),
                "horizon": horizon_str,
                "date_made": sweep_date
            }
            ceres_hash = hash_prediction(
                prediction=pred_data,
                previous_hash=last_hash,
                timestamp=now
            )
            last_hash = ceres_hash

            new_pred = {
                "id": tid,
                "description": t.get('name', tid)[:80],
                "probability": round(current_prob * 100),
                "scp": round(t.get('scp', 0.5), 2),
                "priority_score": round(t.get('priority_score', 0), 2),
                "horizon": horizon_str,
                "status": "Active",
                "date_made": sweep_date,
                "created": sweep_date,
                "updated": now,
                "ceres_hash": ceres_hash
            }
            predictions['pending'].append(new_pred)
            pending_map[tid] = new_pred
            added_count += 1

    # Update last_hash in predictions
    predictions['last_hash'] = last_hash

    # ---- Archive filtered predictions ----
    if archived:
        existing_archive = load_json(ARCHIVE_FILE, [])
        # Avoid duplicates by ID
        seen = {a.get('id') for a in existing_archive}
        for a in archived:
            if a['id'] not in seen:
                existing_archive.append(a)
                seen.add(a['id'])
        save_json(existing_archive, ARCHIVE_FILE)
        print(f"📦 Archived {archived_count} filtered predictions (total archive: {len(existing_archive)})")

    # ---- Recalculate stats ----
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    pending = predictions.get('pending', [])
    watchlist = predictions.get('watchlist', [])
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)

    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(pending),
        "watchlist": len(watchlist)
    }
    predictions['last_updated'] = datetime.now().isoformat()

    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "auto_generate",
        "updated": updated_count,
        "added": added_count,
        "pending_count": len(pending),
        "hit_rate": hit_rate
    })
    predictions['history'] = predictions['history'][-100:]

    save_json(predictions, PREDICTIONS_FILE)

    print(f"✅ Prediction Log Updated:")
    print(f"   Updated pending: {updated_count}, Added: {added_count}")
    print(f"   Confirmed: {len(confirmed)}")
    print(f"   Falsified: {len(falsified)}")
    print(f"   Hit rate: {hit_rate}%")
    print(f"   Pending: {len(pending)}")
    print(f"   Archived: {archived_count}")

if __name__ == "__main__":
    generate_predictions()

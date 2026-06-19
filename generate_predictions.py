#!/usr/bin/env python3
"""
generate_predictions.py – Filtered prediction log generator.
Preserves confirmed/falsified, applies configurable thresholds to pending.
Outputs predictions.json (same schema) and archive.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

THREATS_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
PREDICTIONS_FILE = "predictions.json"
ARCHIVE_FILE = "predictions_archive.json"
CONFIG_FILE = "prediction_filter_config.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_predictions():
    # Load config
    config = load_json(CONFIG_FILE, {})
    min_prob = config.get("min_probability", 0.25)
    min_delta = config.get("min_delta", 0.10)
    max_horizon_days = config.get("max_horizon_days", 90)
    require_event = config.get("require_event", False)
    archive_low = config.get("archive_low_prob", True)

    print(f"📋 Generating prediction log with filters: min_prob={min_prob}, max_horizon={max_horizon_days}d")

    # Load existing predictions (to preserve confirmed/falsified)
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        predictions = {
            "confirmed": [],
            "falsified": [],
            "pending": [],
            "watchlist": [],
            "stats": {},
            "history": [],
            "last_updated": ""
        }

    # Load threats and cascade log (for event detection)
    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])
    cascade_log = load_json(CASCADE_LOG, [])  # list of events

    # Get confirmed/falsified IDs to preserve
    confirmed_ids = {p['id'] for p in predictions.get('confirmed', [])}
    falsified_ids = {p['id'] for p in predictions.get('falsified', [])}
    preserved_ids = confirmed_ids | falsified_ids

    # Build a map of existing pending IDs
    existing_pending = {p['id']: p for p in predictions.get('pending', [])}

    # We'll build a new pending list from threats, filtering them
    new_pending = []
    archived = []
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat()

    # Determine which threats are significant events (if require_event is True)
    # For simplicity, we consider a threat "event‑based" if it has a recent cascade log entry
    # or if its priority_score > some threshold. You can refine this.
    event_threat_ids = set()
    if require_event:
        # Example: threats that appear in cascade_log within the last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        for entry in cascade_log:
            if isinstance(entry, dict):
                ts = entry.get('timestamp')
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        if dt > cutoff:
                            threat_id = entry.get('threat_id')
                            if threat_id:
                                event_threat_ids.add(threat_id)
                    except:
                        pass

    for t in threats:
        tid = t.get('id')
        if not tid:
            continue
        if tid in preserved_ids:
            continue  # don't touch historical entries

        # Compute probability (e.g., base_probability or scp)
        prob = t.get('base_probability', 0.5)  # as float
        # Use scp if available
        scp = t.get('scp', prob)
        # Check if we have a delta (change) – we can compute from history if needed
        # For now, we just use the probability

        # Apply filters
        if prob < min_prob:
            archived.append({"id": tid, "reason": f"Probability {prob:.0%} < {min_prob:.0%}", "data": t})
            continue
        # Horizon filter – if horizon is provided and too long, skip
        horizon = t.get('horizon', '30 days')
        # simple parsing: if horizon is a number of days, check; else we may skip horizon check
        try:
            # assume horizon is string like "30 days" or "3 months"
            # we'll convert to days roughly; for simplicity, if it contains 'days' we parse number
            if 'day' in horizon:
                days = int(''.join(filter(str.isdigit, horizon)))
                if days > max_horizon_days:
                    archived.append({"id": tid, "reason": f"Horizon {days}d > {max_horizon_days}d", "data": t})
                    continue
        except:
            pass  # ignore if can't parse

        # Event requirement
        if require_event and tid not in event_threat_ids:
            archived.append({"id": tid, "reason": "No recent event", "data": t})
            continue

        # If we passed filters, create or update pending entry
        if tid in existing_pending:
            # Update existing pending (preserve creation date, but update prob)
            pred = existing_pending[tid]
            pred['probability'] = round(prob * 100)
            pred['scp'] = round(scp, 2)
            pred['priority_score'] = round(t.get('priority_score', 0), 2)
            pred['updated'] = now
            # Ensure date_made is present (it should already be there from first creation)
            if 'date_made' not in pred:
                pred['date_made'] = today
            new_pending.append(pred)
        else:
            # New prediction
            pred = {
                "id": tid,
                "description": t.get('name', tid)[:80],
                "probability": round(prob * 100),
                "scp": round(scp, 2),
                "priority_score": round(t.get('priority_score', 0), 2),
                "horizon": t.get('horizon', '30 days'),
                "status": "Active",
                "date_made": today,      # <-- added date field
                "created": today,
                "updated": now
            }
            new_pending.append(pred)

    # Preserve watchlist as is (we can also filter them later if desired)
    watchlist = predictions.get('watchlist', [])

    # Update predictions
    predictions['pending'] = new_pending
    predictions['watchlist'] = watchlist  # keep unchanged

    # Recalculate stats
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)

    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(new_pending),
        "watchlist": len(watchlist)
    }
    predictions['last_updated'] = datetime.now().isoformat()

    # Log history
    predictions['history'] = predictions.get('history', [])
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "filtered_generate",
        "pending_count": len(new_pending),
        "archived_count": len(archived),
        "hit_rate": hit_rate,
        "filters": config
    })
    predictions['history'] = predictions['history'][-100:]

    # Save predictions.json (same format)
    save_json(predictions, PREDICTIONS_FILE)

    # Save archive if enabled
    if archive_low and archived:
        existing_archive = load_json(ARCHIVE_FILE, [])
        existing_archive.extend(archived)
        # Keep unique by id
        seen = set()
        unique_archive = []
        for item in existing_archive:
            if item['id'] not in seen:
                seen.add(item['id'])
                unique_archive.append(item)
        save_json(unique_archive, ARCHIVE_FILE)
        print(f"📦 Archived {len(archived)} filtered predictions (total archive: {len(unique_archive)})")

    print(f"✅ Prediction Log Updated:")
    print(f"   Pending: {len(new_pending)} (filtered from {len(threats)} threats)")
    print(f"   Confirmed: {len(confirmed)}")
    print(f"   Falsified: {len(falsified)}")
    print(f"   Hit rate: {hit_rate}%")

if __name__ == "__main__":
    generate_predictions()

#!/usr/bin/env python3
"""
verify_predictions.py – Daily verification of pending predictions.
Moves predictions to confirmed/falsified based on threat status or horizon expiry.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import re

PREDICTIONS_FILE = "predictions.json"
THREATS_FILE = "threats.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def parse_horizon(horizon_str):
    """Convert horizon string like '31 Jul 2026' or '14 days' to a date object."""
    if not horizon_str:
        return None
    # Try to parse as a date (e.g., "31 Jul 2026")
    date_patterns = [
        r'(\d{1,2})\s+(\w{3})\s+(\d{4})',  # 31 Jul 2026
        r'(\d{4})-(\d{2})-(\d{2})',          # 2026-07-31
    ]
    for pattern in date_patterns:
        match = re.search(pattern, horizon_str)
        if match:
            if len(match.groups()) == 3:
                # Try to parse month name
                try:
                    day = int(match.group(1))
                    month_str = match.group(2)
                    year = int(match.group(3))
                    # Convert month name to number
                    months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                              'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
                    month = months.get(month_str.lower(), 1)
                    return datetime(year, month, day)
                except:
                    pass
            else:
                # YYYY-MM-DD format
                try:
                    return datetime.strptime(horizon_str, "%Y-%m-%d")
                except:
                    pass
    # If horizon is like "14 days", compute from today
    if 'day' in horizon_str.lower():
        try:
            days = int(re.search(r'(\d+)', horizon_str).group(1))
            return datetime.now() + timedelta(days=days)
        except:
            pass
    return None

def verify_predictions():
    print("🔍 Verifying pending predictions...")
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        print("No predictions.json found. Skipping verification.")
        return

    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])

    # Build a map of threat id -> status
    threat_status = {}
    for t in threats:
        tid = t.get('id')
        if tid:
            threat_status[tid] = t.get('status', 'Active')

    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    pending = predictions.get('pending', [])
    watchlist = predictions.get('watchlist', [])

    # Existing ids
    confirmed_ids = {p['id'] for p in confirmed}
    falsified_ids = {p['id'] for p in falsified}

    new_confirmed = []
    new_falsified = []
    still_pending = []
    now = datetime.now()

    for p in pending:
        pid = p.get('id')
        if pid in confirmed_ids or pid in falsified_ids:
            continue  # should not happen, but skip

        # Check threat status
        if pid in threat_status:
            status = threat_status[pid]
            if status in ['Resolved', 'Confirmed', 'Occurred']:
                # Confirm it
                p['date'] = now.strftime("%d %b %Y")
                p['reason'] = f"Threat marked as {status} in threat database."
                new_confirmed.append(p)
                print(f"✅ Confirmed: {pid} – {p.get('description', '')[:50]}...")
                continue

        # Check horizon expiry
        horizon = p.get('horizon', '')
        if horizon:
            horizon_date = parse_horizon(horizon)
            if horizon_date and horizon_date < now:
                # Deadline passed – falsify if no evidence of occurrence
                # (we already checked threat status, so if it's not confirmed, it's falsified)
                p['date'] = now.strftime("%d %b %Y")
                p['reason'] = f"Deadline ({horizon}) passed without confirmation."
                new_falsified.append(p)
                print(f"❌ Falsified: {pid} – {p.get('description', '')[:50]}...")
                continue

        # If we get here, keep it pending
        still_pending.append(p)

    # Update predictions
    predictions['confirmed'] = confirmed + new_confirmed
    predictions['falsified'] = falsified + new_falsified
    predictions['pending'] = still_pending
    # Watchlist unchanged

    # Recalc stats
    total_resolved = len(predictions['confirmed']) + len(predictions['falsified'])
    hit_rate = round((len(predictions['confirmed']) / total_resolved * 100) if total_resolved > 0 else 0, 2)
    predictions['stats'] = {
        "confirmed": len(predictions['confirmed']),
        "falsified": len(predictions['falsified']),
        "hit_rate": hit_rate,
        "pending": len(predictions['pending']),
        "watchlist": len(predictions['watchlist'])
    }
    predictions['last_updated'] = datetime.now().isoformat()

    # Add history entry
    predictions['history'] = predictions.get('history', [])
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "daily_verification",
        "confirmed_moved": len(new_confirmed),
        "falsified_moved": len(new_falsified),
        "pending_remaining": len(still_pending),
        "hit_rate": hit_rate
    })
    predictions['history'] = predictions['history'][-100:]

    save_json(predictions, PREDICTIONS_FILE)
    print(f"✅ Verification complete. Confirmed: {len(new_confirmed)}, Falsified: {len(new_falsified)}, Still pending: {len(still_pending)}")

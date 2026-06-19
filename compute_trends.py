#!/usr/bin/env python3
"""
compute_trends.py – Compute SCP trend (7-day delta) from history.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = "scp_history.json"
TREND_FILE = "trend.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    history = load_json(HISTORY_FILE, [])
    if len(history) < 2:
        print("Not enough history for trend.")
        return

    history.sort(key=lambda x: x.get('timestamp', ''))
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    recent_entry = None
    old_entry = None
    for entry in reversed(history):
        ts = datetime.fromisoformat(entry['timestamp'])
        if ts >= seven_days_ago and recent_entry is None:
            recent_entry = entry
        if ts < seven_days_ago and old_entry is None:
            old_entry = entry
        if recent_entry and old_entry:
            break

    if not recent_entry or not old_entry:
        print("Not enough history for 7-day trend.")
        return

    recent_scp = recent_entry.get('scp', {})
    old_scp = old_entry.get('scp', {})

    trends = {}
    for tid, new_val in recent_scp.items():
        old_val = old_scp.get(tid, new_val)
        delta = new_val - old_val
        if delta > 0.05:
            trend = "up"
        elif delta < -0.05:
            trend = "down"
        else:
            trend = "stable"
        trends[tid] = {"delta": round(delta, 3), "trend": trend}

    save_json(trends, TREND_FILE)
    print(f"✅ Trends computed for {len(trends)} threats.")

if __name__ == "__main__":
    main()

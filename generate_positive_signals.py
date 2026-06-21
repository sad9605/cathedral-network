#!/usr/bin/env python3
"""
generate_positive_signals.py – Extract positive signals from sweep_report.json.
"""
import json
from datetime import datetime
from pathlib import Path

SWEEP_FILE = "sweep_report.json"
OUTPUT_FILE = "positive_signals.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def main():
    sweep = load_json(SWEEP_FILE, {})
    events = sweep.get('events', [])
    positives = []
    keywords = ["ceasefire", "aid", "vaccine", "peace", "treaty", "reconstruction", "diplomatic"]
    for ev in events:
        desc = ev.get('description', '').lower()
        if any(k in desc for k in keywords):
            positives.append({
                "type": ev.get('type', 'positive_signal'),
                "region": ev.get('region', 'Global'),
                "date": ev.get('date', datetime.now().strftime("%Y-%m-%d")),
                "description": ev.get('description', '')
            })
    # Write to positive_signals.json
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(positives, f, indent=2)
    print(f"✅ Generated {len(positives)} positive signals")
if __name__ == "__main__":
    main()

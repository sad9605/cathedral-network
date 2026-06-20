#!/usr/bin/env python3
"""
generate_health.py – Produce health.json with pipeline status.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

SWEEP_FILE = "sweep_report.json"
THREATS_FILE = "threats.json"
HEALTH_FILE = "health.json"
LOG_FILE = "cron.log"  # optional

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def main():
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
        "last_sweep": None,
        "threats": 0,
        "errors": []
    }

    # Check sweep timestamp
    sweep = load_json(SWEEP_FILE, {})
    if sweep.get('timestamp'):
        health['last_sweep'] = sweep['timestamp']
        last = datetime.fromisoformat(sweep['timestamp'])
        if datetime.now() - last > timedelta(hours=8):
            health['status'] = "warning"
            health['errors'].append("No sweep in the last 8 hours")

    # Check threats
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    health['threats'] = len(threats)

    # Check if cron.log exists and has recent activity (optional)
    if Path(LOG_FILE).exists():
        mtime = datetime.fromtimestamp(Path(LOG_FILE).stat().st_mtime)
        if datetime.now() - mtime > timedelta(hours=12):
            health['status'] = "warning"
            health['errors'].append("cron.log not updated in 12 hours")

    # Write health.json
    with open(HEALTH_FILE, 'w') as f:
        json.dump(health, f, indent=2)

    print(f"✅ Health data written to {HEALTH_FILE}")
    print(f"   Status: {health['status']}")
    print(f"   Threats: {health['threats']}")

if __name__ == "__main__":
    main()

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
LOG_FILE = "cron.log"

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

    # Get a naive "now" for comparisons
    now = datetime.now().replace(tzinfo=None)

    # Check sweep timestamp
    sweep = load_json(SWEEP_FILE, {})
    if sweep.get('timestamp'):
        health['last_sweep'] = sweep['timestamp']
        try:
            last = datetime.fromisoformat(sweep['timestamp']).replace(tzinfo=None)
            if now - last > timedelta(hours=8):
                health['status'] = "warning"
                health['errors'].append("No sweep in the last 8 hours")
        except Exception as e:
            health['errors'].append(f"Error parsing sweep timestamp: {e}")

    # Check threats
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    health['threats'] = len(threats)

    # Check cron.log for recent activity (if it exists)
    if Path(LOG_FILE).exists():
        mtime = datetime.fromtimestamp(Path(LOG_FILE).stat().st_mtime).replace(tzinfo=None)
        if now - mtime > timedelta(hours=12):
            health['status'] = "warning"
            health['errors'].append("cron.log not updated in 12 hours")
        # Read last 5 lines for errors
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[-5:]
                errors = [line.strip() for line in lines if 'error' in line.lower()]
                if errors:
                    health['errors'].extend(errors[:3])
        except:
            pass

    # Write health.json
    with open(HEALTH_FILE, 'w') as f:
        json.dump(health, f, indent=2)

    print(f"✅ Health data written to {HEALTH_FILE}")
    print(f"   Status: {health['status']}")
    print(f"   Threats: {health['threats']}")

if __name__ == "__main__":
    main()

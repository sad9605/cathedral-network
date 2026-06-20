#!/usr/bin/env python3
"""
generate_health.py – Produce health.json with pipeline status.
Robust datetime handling – all times UTC naive.
"""

import json
from datetime import datetime, timedelta, timezone
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

def parse_timestamp(ts_str):
    """Parse ISO timestamp, handle both naive and aware, return naive UTC."""
    if not ts_str:
        return None
    # Replace 'Z' with '+00:00' for parsing
    if ts_str.endswith('Z'):
        ts_str = ts_str[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(ts_str)
        # If aware, convert to UTC naive
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None

def main():
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

    health = {
        "timestamp": datetime.now(timezone.utc).isoformat() + 'Z',
        "status": "ok",
        "last_sweep": None,
        "threats": 0,
        "errors": [],
        "pipeline_steps": []
    }

    # Check sweep timestamp
    sweep = load_json(SWEEP_FILE, {})
    if sweep.get('timestamp'):
        health['last_sweep'] = sweep['timestamp']
        last = parse_timestamp(sweep['timestamp'])
        if last:
            if (now - last) > timedelta(hours=8):
                health['status'] = "warning"
                health['errors'].append("No sweep in the last 8 hours")
        else:
            health['errors'].append(f"Could not parse sweep timestamp: {sweep['timestamp']}")

    # Check threats
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    health['threats'] = len(threats)

    # Check cron.log for recent activity
    if Path(LOG_FILE).exists():
        mtime = datetime.utcfromtimestamp(Path(LOG_FILE).stat().st_mtime)
        if (now - mtime) > timedelta(hours=12):
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

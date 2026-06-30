#!/usr/bin/env python3
"""
sentinel_monitor.py – AW19 Sentinel Monitor
Tracks Sentinel activity and alerts if a Sentinel is underperforming.
"""
import json
from datetime import datetime, timezone, timedelta

ALERT_FILE = "sentinel_alerts.json"
MAX_INACTIVITY_DAYS = 7

def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return {}

def main():
    print("🛰️  Sentinel Monitor (AW19) running...")
    
    sentinels = load_json("sentinel_assignments.json")
    cascades = load_json("cascade_rules.json")
    statuses = load_json("cascade_status.json")
    
    alerts = []
    
    # Check if sentinel assignments exist
    sentinel_map = sentinels.get("sentinels", {})
    if not sentinel_map:
        print("⚠️ No sentinel assignments found. Exiting.")
        return
    
    # Check last updated timestamp
    if "last_updated" not in statuses:
        print("⚠️ No last_updated field in cascade_status.json. Skipping inactivity check.")
    else:
    # Ensure both datetimes are timezone-aware
    last_updated = datetime.fromisoformat(statuses["last_updated"].replace("Z", "+00:00"))
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_update = (now - last_updated).days

        now = datetime.now(timezone.utc)
        days_since_update = (now - last_updated).days
        if days_since_update > MAX_INACTIVITY_DAYS:
            alerts.append({
                "type": "sentinel_inactivity",
                "message": f"Sentinel activity stale: last update {days_since_update} days ago.",
                "severity": "high",
                "timestamp": now.isoformat()
            })
    
    # Check for sentinels with no assigned cascades
    for sentinel, data in sentinel_map.items():
        assigned = data.get("cascades", [])
        if not assigned:
            alerts.append({
                "type": "sentinel_no_cascades",
                "message": f"Sentinel {sentinel} has no cascades assigned.",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # Save alerts
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alerts": alerts,
        "summary": {
            "total": len(alerts),
            "high": len([a for a in alerts if a.get("severity") == "high"]),
            "medium": len([a for a in alerts if a.get("severity") == "medium"])
        }
    }
    with open(ALERT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Sentinel Monitor complete. {len(alerts)} alert(s) generated.")
    for a in alerts:
        print(f"   {a['severity'].upper()}: {a['message']}")

if __name__ == "__main__":
    main()

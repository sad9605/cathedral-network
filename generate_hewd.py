#!/usr/bin/env python3
"""
generate_hewd.py – Generate HEWD dashboard data from threats.json and sweep_report.json.
"""

import json
from pathlib import Path
from datetime import datetime

THREATS_FILE = "threats.json"
SWEEP_FILE = "sweep_report.json"
OUTPUT_FILE = "hewd_data.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    sweep = load_json(SWEEP_FILE, {})

    status_counts = {'Black': 0, 'Red': 0, 'Orange': 0, 'Yellow': 0, 'Green': 0}
    domains = set()

    for t in threats:
        status = t.get('status', 'Yellow')
        if 'Black' in status:
            status_counts['Black'] += 1
        elif status in status_counts:
            status_counts[status] += 1
        if t.get('domains'):
            for d in t['domains']:
                domains.add(d)

    # Build indicators
    indicators = [
        {
            "id": "total_threats",
            "title": "Total Threats",
            "value": len(threats),
            "description": "All tracked threats across all domains",
            "status": "normal",
            "source": "threats.json"
        },
        {
            "id": "black_red",
            "title": "Critical Threats (Black/Red)",
            "value": status_counts['Black'] + status_counts['Red'],
            "description": "Immediate humanitarian risk requiring urgent attention",
            "status": "critical" if status_counts['Black'] + status_counts['Red'] > 5 else "warning",
            "source": "threats.json"
        },
        {
            "id": "orange",
            "title": "Orange Level Threats",
            "value": status_counts['Orange'],
            "description": "Elevated risk – monitoring required",
            "status": "warning" if status_counts['Orange'] > 5 else "normal",
            "source": "threats.json"
        },
        {
            "id": "domains",
            "title": "Domains Affected",
            "value": len(domains),
            "description": f"Humanitarian domains impacted: {', '.join(domains) if domains else 'None'}",
            "status": "warning" if len(domains) > 5 else "normal",
            "source": "threats.json"
        }
    ]

    output = {
        "timestamp": sweep.get('timestamp', datetime.now().isoformat()),
        "total_threats": len(threats),
        "critical_count": status_counts['Black'] + status_counts['Red'],
        "alert_count": status_counts['Red'] + status_counts['Black'],
        "domains_covered": len(domains),
        "indicators": indicators
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ HEWD data written to {OUTPUT_FILE}")
    print(f"   Total threats: {len(threats)}")
    print(f"   Critical: {status_counts['Black'] + status_counts['Red']}")
    print(f"   Domains: {len(domains)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate_hewd.py – Produce hewd_data.json from threats.json.
Selects top humanitarian threats, computes mortality-weighted score.
"""

import json
from pathlib import Path
from datetime import datetime

THREATS_FILE = "threats.json"
OUTPUT_FILE = "hewd_data.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_severity_factor(status):
    if 'Black' in status:
        return 4
    if status == 'Red':
        return 3
    if status == 'Orange':
        return 2
    return 1

def get_severity_short(status):
    if 'Black' in status:
        return 'black'
    if status == 'Red':
        return 'red'
    if status == 'Orange':
        return 'orange'
    return 'yellow'

def get_recommendation(threat):
    status = threat.get('status', '')
    if 'Black' in status or status == 'Red':
        return "🚨 Immediate response required. Coordinate with humanitarian partners."
    if 'Orange' in status:
        return "📋 Monitor closely. Pre‑position supplies and update contingency plans."
    return "📊 Continue surveillance. Prepare for potential escalation."

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    if not threats:
        print("⚠️ No threats found. Skipping HEWD generation.")
        return

    humanitarian = []
    for t in threats:
        domains = t.get('domains', [])
        if any(d in ['Food', 'Famine', 'Health', 'Ebola', 'Conflict', 'War', 'Displacement', 'Water', 'Sanitation', 'Climate', 'Weather'] for d in domains):
            humanitarian.append(t)

    if not humanitarian:
        print("⚠️ No humanitarian threats found.")
        humanitarian = threats[:10]

    hewd_threats = []
    for t in humanitarian:
        status = t.get('status', 'Yellow')
        severity_factor = get_severity_factor(status)
        severity_short = get_severity_short(status)
        mortality_weight = 7  # default, could be refined by domain later
        recency = 2  # assume recent
        chronic_class = 2
        compound_alert = False
        score = (t.get('scp', 0.5) * 100) * severity_factor * (1 + 0.2 * (recency - 1))

        hewd_threats.append({
            "name": f"{t.get('id', '')} – {t.get('name', 'Unknown Threat')}",
            "status": status,
            "severity": severity_short,
            "severityFactor": severity_factor,
            "mortalityWeight": mortality_weight,
            "recency": recency,
            "chronicClass": chronic_class,
            "compoundAlert": compound_alert,
            "recommendation": get_recommendation(t),
            "source": "Cathedral Engine",
            "score": round(score, 2)
        })

    hewd_threats.sort(key=lambda x: x['score'], reverse=True)
    top_threats = hewd_threats[:10]

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_humanitarian_threats": len(humanitarian),
        "threats": top_threats
    }

    save_json(output, OUTPUT_FILE)
    print(f"✅ HEWD data written to {OUTPUT_FILE}")
    print(f"   Selected {len(top_threats)} humanitarian threats.")
    for t in top_threats:
        print(f"   - {t['name']}: {t['score']}")

if __name__ == "__main__":
    main()

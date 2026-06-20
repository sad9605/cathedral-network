#!/usr/bin/env python3
"""
generate_hewd.py – Produce hewd_data.json for the dynamic HEWD dashboard.
Selects top humanitarian threats from threats.json, computes mortality-weighted score.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

THREATS_FILE = "threats.json"
PREDICTIONS_FILE = "predictions.json"
OUTPUT_FILE = "hewd_data.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

# Domain → mortality weight (original HEWD used weights 7-10)
DOMAIN_WEIGHTS = {
    "Food": 10,
    "Famine": 10,
    "Health": 9,
    "Ebola": 9,
    "Conflict": 9,
    "War": 9,
    "Displacement": 9,
    "Water": 8,
    "Sanitation": 8,
    "Climate": 7,
    "Weather": 7,
    "Economic": 7,
    "Financial": 6,
    "Institutional": 6,
    "Information": 5,
    "Cyber": 5
}

def get_mortality_weight(domains):
    """Return highest matching weight."""
    if not domains:
        return 5
    for d in domains:
        for key, weight in DOMAIN_WEIGHTS.items():
            if key.lower() in d.lower():
                return weight
    return 5

def get_severity_factor(status):
    """Map status to severity factor (Black=4, Red=3, Orange=2, Yellow=1)."""
    if 'Black' in status:
        return 4
    if status == 'Red':
        return 3
    if status == 'Orange':
        return 2
    return 1

def get_recency(last_updated):
    """Compute recency factor: 2 if updated in last 2 days, else 1."""
    if not last_updated:
        return 1
    try:
        dt = datetime.fromisoformat(last_updated).replace(tzinfo=None)
        days = (datetime.now().replace(tzinfo=None) - dt).days
        return 2 if days <= 2 else 1
    except:
        return 1

def get_recommendation(threat):
    """Generate a simple recommendation based on domain and status."""
    domains = threat.get('domains', [])
    status = threat.get('status', '')
    if 'Black' in status or status == 'Red':
        return "🚨 Immediate response required. Coordinate with humanitarian partners."
    elif 'Orange' in status:
        return "📋 Monitor closely. Pre‑position supplies and update contingency plans."
    else:
        return "📊 Continue surveillance. Prepare for potential escalation."

def get_source(threat):
    """Get source from threat data or return generic."""
    return threat.get('source', 'Cathedral Engine')

def get_chronic_class(threat):
    """Assign chronic class based on domain – simple heuristic."""
    domains = threat.get('domains', [])
    if any(d in ['Famine', 'Food', 'Displacement', 'Conflict'] for d in domains):
        return 3
    if any(d in ['Health', 'Water', 'Climate'] for d in domains):
        return 2
    return None

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    if not threats:
        print("⚠️ No threats found. Skipping HEWD generation.")
        return

    # Filter to humanitarian-relevant threats (broad filter)
    humanitarian_domains = ['Food', 'Famine', 'Health', 'Ebola', 'Conflict', 'War',
                            'Displacement', 'Water', 'Sanitation', 'Climate', 'Weather']
    filtered = []
    for t in threats:
        domains = t.get('domains', [])
        if any(d in domains for d in humanitarian_domains):
            filtered.append(t)

    if not filtered:
        print("⚠️ No humanitarian threats found.")
        filtered = threats[:10]  # fallback

    # Compute score and build HEWD entries
    hewd_threats = []
    for t in filtered:
        status = t.get('status', 'Yellow')
        severity_factor = get_severity_factor(status)
        mortality_weight = get_mortality_weight(t.get('domains', []))
        recency = get_recency(t.get('last_updated'))
        chronic_class = get_chronic_class(t)
        compound_alert = t.get('compound_alert', False)

        # Compute score: mortality_weight^0.7 * severity_factor * recency_factor
        score = (mortality_weight ** 0.7) * severity_factor * (1 + 0.2 * (recency - 1))

        # Build display name
        tid = t.get('id', '')
        name = t.get('name', 'Unknown Threat')
        display_name = f"{tid} – {name}" if tid else name

        # Map status to severity label and emoji
        if 'Black' in status:
            severity_label = "⚫ Black Acute" if 'Acute' in status else "🟣 Black Structural"
            severity_short = "black"
        elif status == 'Red':
            severity_label = "🔴 Red"
            severity_short = "red"
        elif status == 'Orange':
            severity_label = "🟠 Orange"
            severity_short = "orange"
        else:
            severity_label = "🟡 Yellow"
            severity_short = "yellow"

        hewd_threats.append({
            "name": display_name,
            "status": severity_label,
            "severity": severity_short,
            "severityFactor": severity_factor,
            "mortalityWeight": mortality_weight,
            "recency": recency,
            "chronicClass": chronic_class,
            "compoundAlert": compound_alert,
            "recommendation": get_recommendation(t),
            "source": get_source(t),
            "score": round(score, 2)
        })

    # Sort by score descending
    hewd_threats.sort(key=lambda x: x['score'], reverse=True)
    # Take top 10
    top_threats = hewd_threats[:10]

    # Prepare output
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_humanitarian_threats": len(filtered),
        "threats": top_threats
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ HEWD data written to {OUTPUT_FILE}")
    print(f"   Selected {len(top_threats)} humanitarian threats.")
    for t in top_threats:
        print(f"   - {t['name']}: {t['score']}")

if __name__ == "__main__":
    main()

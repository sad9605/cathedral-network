#!/usr/bin/env python3
"""
generate_threat_intelligence.py – Auto‑generate intelligence reports for all threats.
"""

import json
from datetime import datetime
from pathlib import Path

THREATS_FILE = "threats.json"
CASCADE_LOG_FILE = "cascade_log.json"
PREDICTIONS_FILE = "predictions.json"
OUTPUT_FILE = "threat_intelligence.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("📊 Generating threat intelligence reports...")
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    cascade_log = load_json(CASCADE_LOG_FILE, [])
    predictions = load_json(PREDICTIONS_FILE, {})

    intelligence = {}

    # Build a map of threat IDs to their reports
    for t in threats:
        tid = t.get('id')
        if not tid:
            continue

        name = t.get('name', 'Unknown')
        status = t.get('status', 'Yellow')
        scp = t.get('scp', 0.5)
        priority = t.get('priority_score', 0)
        domains = t.get('domains', [])
        description = t.get('description', 'No description available.')

        # Timeline – collect events from cascade log
        timeline = {}
        for entry in cascade_log:
            source = entry.get('source')
            target = entry.get('target')
            if source == tid or target == tid:
                ts = entry.get('timestamp', '')
                if ts:
                    date = ts[:10]  # YYYY-MM-DD
                    if date not in timeline:
                        timeline[date] = []
                    desc = entry.get('description', 'Cascade event')
                    if source == tid:
                        timeline[date].append(f"{source} → {target} (boost {entry.get('boost', 0):.2f})")
                    else:
                        timeline[date].append(f"{source} → {target} affected {tid}")

        # Cascade effects – which threats are affected by this one
        cascade_effects = []
        for entry in cascade_log:
            if entry.get('source') == tid:
                target = entry.get('target')
                if target:
                    cascade_effects.append({
                        "target": target,
                        "impact": f"SCP boost of {entry.get('boost', 0):.2f}",
                        "scp_boost": entry.get('boost', 0)
                    })

        # Human cost – heuristic based on domains and status
        human_cost = {
            "casualties": "Unknown",
            "displaced": "Unknown",
            "affected": "Unknown"
        }
        if "Famine" in name or "Food" in domains:
            human_cost["affected"] = "Millions at risk"
            if "Famine" in name:
                human_cost["casualties"] = "Hundreds of thousands projected"
        if "Conflict" in name or "War" in name or "Geopolitical" in domains:
            human_cost["displaced"] = "Hundreds of thousands"
        if "Health" in domains or "Ebola" in name:
            human_cost["casualties"] = "Thousands at risk"

        # Economic cost – heuristic
        economic_cost = {
            "oil_impact": "N/A",
            "global_gdp": "N/A",
            "estimated_loss": "N/A"
        }
        if "Energy" in domains or "Oil" in name:
            economic_cost["oil_impact"] = "Potential oil price spike"
        if "Financial" in domains:
            economic_cost["estimated_loss"] = "Billions of dollars"

        # Recommendations – based on status
        recommendations = []
        if "Black" in status or status == "Red":
            recommendations.append("Immediate humanitarian response required.")
            recommendations.append("Coordinate with Warden Corps and local authorities.")
        elif status == "Orange":
            recommendations.append("Monitor closely. Pre‑position supplies.")
        else:
            recommendations.append("Continue surveillance and OSINT verification.")

        # Confidence – from threat data or default
        confidence = t.get('confidence', 0.7)

        # Sources – from cascade log or predictions
        # Build sets of confirmed and falsified prediction IDs
        confirmed_ids = {p.get('id') for p in predictions.get('confirmed', [])}
        falsified_ids = {p.get('id') for p in predictions.get('falsified', [])}

        sources = ["Cascade Engine"]
        if tid in confirmed_ids:
            sources.append("Prediction Log (confirmed)")
        elif tid in falsified_ids:
            sources.append("Prediction Log (falsified)")

        # Build the report
        intelligence[tid] = {
            "id": tid,
            "name": name,
            "narrative": description,
            "timeline": timeline,
            "current_status": f"{status} – SCP: {scp:.2f}, Priority: {priority:.0f}",
            "forecast": f"Based on current trends, this threat is expected to remain active. Monitor cascade activations.",
            "cascade_effects": cascade_effects[:5],  # limit to 5
            "human_cost": human_cost,
            "economic_cost": economic_cost,
            "recommendations": recommendations,
            "confidence": confidence,
            "sources": sources[:3],
            "last_updated": datetime.now().isoformat()
        }

    # Merge with any existing manual entries (if we want to preserve them)
    manual = load_json("threat_intelligence.json", {})
    for tid, report in manual.items():
        if tid not in intelligence:
            intelligence[tid] = report  # keep manual if it exists

    # Save
    save_json(intelligence, OUTPUT_FILE)
    print(f"✅ Threat intelligence generated: {len(intelligence)} entries")

if __name__ == "__main__":
    main()

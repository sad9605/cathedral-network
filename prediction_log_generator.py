#!/usr/bin/env python3
"""
Prediction Log Generator – Cathedral Network
Filters predictions by probability, delta, horizon, and event significance.
Adds "Date Made" field and generates public HTML log.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
THREATS_FILE = "threats.json"
CASCADE_LOG_FILE = "cascade_log.json"
CONFIG_FILE = "prediction_filter_config.json"
OUTPUT_JSON = "predictions.json"
OUTPUT_HTML = "prediction-log.html"
ARCHIVE_JSON = "predictions_archive.json"

# Load config
with open(CONFIG_FILE, 'r') as f:
    CONFIG = json.load(f)

MIN_PROB = CONFIG.get("min_probability", 0.25)
MIN_DELTA = CONFIG.get("min_delta", 0.10)
MAX_HORIZON_DAYS = CONFIG.get("max_horizon_days", 90)
REQUIRE_EVENT = CONFIG.get("require_event", True)
ARCHIVE_LOW_PROB = CONFIG.get("archive_low_prob", True)

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ------------------------------------------------------------------
# Filter logic
# ------------------------------------------------------------------
def is_significant_event(entry: Dict) -> bool:
    """Check if cascade log entry has a significant event trigger."""
    keywords = ["ceasefire", "airstrike", "missile", "blockade", "closure",
                "explosion", "earthquake", "outbreak", "declaration", "attack"]
    desc = entry.get('description', '').lower()
    return any(kw in desc for kw in keywords)

def generate_predictions(threats: Dict, cascade_log: List[Dict]) -> List[Dict]:
    """Generate filtered predictions from threats and cascade log."""
    predictions = []
    now = datetime.now(timezone.utc)
    threat_dict = {t['id']: t for t in threats.get('threats', [])}

    # 1. From threat SCPs (baseline predictions)
    for threat_id, threat in threat_dict.items():
        scp = threat.get('scp', 0.0)
        if scp >= MIN_PROB:
            # Estimate horizon based on threat type (simplified)
            if 'imminent' in threat.get('notes', '').lower():
                horizon_days = 7
            elif 'ongoing' in threat.get('notes', '').lower():
                horizon_days = 30
            else:
                horizon_days = 60

            if horizon_days <= MAX_HORIZON_DAYS:
                # Check if there's a recent cascade log entry for this threat
                recent_events = [e for e in cascade_log if e.get('target') == threat_id and
                                 (datetime.fromisoformat(e['timestamp']) - now).days > -2]
                if REQUIRE_EVENT and not recent_events:
                    continue

                predictions.append({
                    'id': f"P{threat_id.replace('-', '')[:8]}",
                    'prediction': f"{threat.get('name', threat_id)} – current SCP {scp:.2f}",
                    'date_made': now.strftime("%Y-%m-%d"),
                    'probability': round(scp, 2),
                    'horizon': f"{horizon_days} days",
                    'status': 'active',
                    'source': 'threat_matrix'
                })

    # 2. From cascade log events
    for entry in cascade_log:
        delta = entry.get('delta', 0.0)
        if abs(delta) >= MIN_DELTA:
            target_id = entry.get('target')
            if target_id in threat_dict:
                target = threat_dict[target_id]
                scp = target.get('scp', 0.0)
                if scp >= MIN_PROB:
                    if REQUIRE_EVENT and not is_significant_event(entry):
                        continue
                    predictions.append({
                        'id': f"C{entry.get('source', '')}_{target_id}",
                        'prediction': f"{target.get('name', target_id)} changed by {delta:.2f} due to {entry.get('source', 'unknown')}",
                        'date_made': entry.get('timestamp', now.isoformat())[:10],
                        'probability': round(scp, 2),
                        'horizon': '30 days',
                        'status': 'active',
                        'source': 'cascade'
                    })

    # Remove duplicates
    seen = set()
    unique = []
    for p in predictions:
        key = (p['prediction'], p['date_made'])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    unique.sort(key=lambda x: x['probability'], reverse=True)
    return unique

# ------------------------------------------------------------------
# Archive low-probability predictions
# ------------------------------------------------------------------
def archive_low_prob_predictions(predictions: List[Dict]) -> List[Dict]:
    if not ARCHIVE_LOW_PROB:
        return predictions
    active = []
    archived = []
    for p in predictions:
        if p['probability'] < MIN_PROB:
            archived.append(p)
        else:
            active.append(p)
    if archived:
        existing = load_json(ARCHIVE_JSON)
        if not existing:
            existing = []
        existing.extend(archived)
        save_json(existing, ARCHIVE_JSON)
    return active

# ------------------------------------------------------------------
# Generate HTML
# ------------------------------------------------------------------
def generate_html(predictions: List[Dict]) -> str:
    rows = ""
    for p in predictions[:100]:
        status_class = "active"
        status_badge = "🟡 Active"
        if p.get('status') == 'confirmed':
            status_class = "confirmed"
            status_badge = "✅ Confirmed"
        elif p.get('status') == 'falsified':
            status_class = "falsified"
            status_badge = "❌ Falsified"
        rows += f"""
        <tr class="{status_class}">
            <td>{p.get('id', 'N/A')}</td>
            <td>{p['prediction']}</td>
            <td>{p.get('date_made', 'N/A')}</td>
            <td>{p.get('probability', 0.0)*100:.0f}%</td>
            <td>{p.get('horizon', 'N/A')}</td>
            <td>{status_badge}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cathedral Network — Prediction Log</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      background: #0a0a0a;
      color: #eee;
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }}
    th, td {{
      border: 1px solid #333;
      padding: 0.5rem;
      text-align: left;
    }}
    th {{
      background: #1e1e2f;
      color: #b39ddb;
    }}
    .confirmed {{ background: #1a3a1a; }}
    .falsified {{ background: #3a1a1a; }}
    .active {{ background: #1a2a3a; }}
  </style>
</head>
<body>
  <h1>📋 Cathedral Network – Prediction Log</h1>
  <p>Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
  <p><strong>Filtered:</strong> min probability {MIN_PROB*100:.0f}%, min delta {MIN_DELTA*100:.0f}%, max horizon {MAX_HORIZON_DAYS} days, require event: {REQUIRE_EVENT}</p>
  <table>
    <thead>
      <tr><th>ID</th><th>Prediction</th><th>Date Made</th><th>Probability</th><th>Horizon</th><th>Status</th></tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  <p style="margin-top:2rem; font-style:italic;">Always and Forever, Coco.</p>
</body>
</html>"""

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    threats = load_json(THREATS_FILE)
    cascade_log = load_json(CASCADE_LOG_FILE)
    if not cascade_log:
        cascade_log = cascade_log.get('entries', [])

    predictions = generate_predictions(threats, cascade_log)
    predictions = archive_low_prob_predictions(predictions)

    save_json(predictions, OUTPUT_JSON)

    html = generate_html(predictions)
    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)

    print(f"Generated {len(predictions)} active predictions (filtered).")
    print(f"Saved to {OUTPUT_JSON} and {OUTPUT_HTML}")
    if ARCHIVE_LOW_PROB:
        archived = load_json(ARCHIVE_JSON)
        print(f"Archived {len(archived)} low-probability predictions.")

if __name__ == "__main__":
    main()

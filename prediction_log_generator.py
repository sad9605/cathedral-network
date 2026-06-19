#!/usr/bin/env python3
"""
Prediction Log Generator – Cathedral Network (Diagnostic Version)
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
# Main with diagnostics
# ------------------------------------------------------------------
def main():
    print("📊 Loading threats.json...")
    threats_data = load_json(THREATS_FILE)
    # Extract threats list – handle both {"threats": [...]} and plain list
    if isinstance(threats_data, dict) and 'threats' in threats_data:
        threats = threats_data['threats']
    elif isinstance(threats_data, list):
        threats = threats_data
    else:
        print("❌ Could not find threats list in threats.json")
        return

    print(f"✅ Found {len(threats)} threats.")
    # Filter threats with SCP >= MIN_PROB
    eligible = [t for t in threats if t.get('scp', 0.0) >= MIN_PROB]
    print(f"🔍 Threats with SCP >= {MIN_PROB*100:.0f}%: {len(eligible)}")
    if eligible:
        print("   (first few SCPs: " + ", ".join([f"{t.get('id','?')}:{t.get('scp',0):.2f}" for t in eligible[:5]]) + ")")

    # Load cascade log
    cascade_log = load_json(CASCADE_LOG_FILE)
    if not cascade_log:
        cascade_log = []
        print("⚠️ No cascade_log.json found or it's empty.")
    else:
        if isinstance(cascade_log, dict) and 'entries' in cascade_log:
            cascade_log = cascade_log['entries']
        print(f"📋 Loaded {len(cascade_log)} cascade log entries.")

    # If no cascade entries and REQUIRE_EVENT is True, we warn and disable the requirement for this run.
    actual_require_event = REQUIRE_EVENT
    if REQUIRE_EVENT and not cascade_log:
        print("⚠️ require_event is True but no cascade log entries found. Disabling require_event for this run.")
        actual_require_event = False

    # Generate predictions from threats
    predictions = []
    now = datetime.now(timezone.utc)

    # 1. From threat SCPs
    for threat in eligible:
        threat_id = threat.get('id', 'unknown')
        scp = threat.get('scp', 0.0)
        if actual_require_event:
            recent = [e for e in cascade_log if e.get('target') == threat_id and
                     (datetime.fromisoformat(e.get('timestamp', now.isoformat())) - now).days > -2]
            if not recent:
                continue

        notes = threat.get('notes', '').lower()
        if 'imminent' in notes:
            horizon_days = 7
        elif 'ongoing' in notes:
            horizon_days = 30
        else:
            horizon_days = 60
        if horizon_days > MAX_HORIZON_DAYS:
            continue

        predictions.append({
            'id': f"P{threat_id.replace('-', '')[:8]}",
            'prediction': f"{threat.get('name', threat_id)} – SCP {scp:.2f}",
            'date_made': now.strftime("%Y-%m-%d"),
            'probability': round(scp, 2),
            'horizon': f"{horizon_days} days",
            'status': 'active',
            'source': 'threat_matrix'
        })

    # 2. From cascade log events (additional predictions)
    for entry in cascade_log:
        delta = entry.get('delta', 0.0)
        if abs(delta) >= MIN_DELTA:
            target_id = entry.get('target')
            if target_id:
                threat = next((t for t in threats if t.get('id') == target_id), None)
                if threat:
                    scp = threat.get('scp', 0.0)
                    if scp >= MIN_PROB:
                        predictions.append({
                            'id': f"C{entry.get('source', '')}_{target_id}",
                            'prediction': f"{threat.get('name', target_id)} changed by {delta:.2f} due to {entry.get('source', 'unknown')}",
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

    # Archive low-probability predictions if enabled
    if ARCHIVE_LOW_PROB:
        active = []
        archived = []
        for p in unique:
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
        unique = active

    # Save JSON
    save_json(unique, OUTPUT_JSON)
    print(f"💾 Saved {len(unique)} active predictions to {OUTPUT_JSON}")

    # Generate HTML
    html = generate_html(unique)
    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)
    print(f"🌐 Saved HTML to {OUTPUT_HTML}")

def generate_html(predictions):
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

if __name__ == "__main__":
    main()

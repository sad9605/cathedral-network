#!/usr/bin/env python3
"""
engine_sanity_check.py – Validate engine outputs and pipeline status.
"""

import json
from pathlib import Path
from datetime import datetime

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def check_scp_distribution(threats):
    scps = [t.get('scp', 0) for t in threats]
    if not scps:
        return "⚠️ No threats found."
    avg = sum(scps) / len(scps)
    min_scp = min(scps)
    max_scp = max(scps)
    if avg > 0.85:
        return f"⚠️ SCP average too high: {avg:.3f} (saturation risk)."
    elif avg < 0.05:
        return f"⚠️ SCP average too low: {avg:.3f} (under‑calibrated)."
    elif max_scp - min_scp < 0.1:
        return f"⚠️ SCP range too narrow: {min_scp:.3f}–{max_scp:.3f} (no variation)."
    else:
        return f"✅ SCP distribution normal: avg {avg:.3f}, range {min_scp:.3f}–{max_scp:.3f}"

def check_statuses(threats):
    statuses = [t.get('status', 'Unknown') for t in threats]
    unique = set(statuses)
    if len(unique) < 3:
        return f"⚠️ Only {len(unique)} unique statuses – likely over‑calibrated."
    return f"✅ Statuses spread across {len(unique)} categories."

def check_predictions(predictions):
    required_fields = ['id', 'description', 'probability', 'date_made', 'horizon', 'status']
    missing = []
    for p in predictions.get('pending', []):
        for field in required_fields:
            if field not in p:
                missing.append(f"{field} missing in {p.get('id', 'unknown')}")
    if missing:
        return f"⚠️ Missing fields: {', '.join(missing[:3])}"
    return "✅ Predictions have all required fields."

def check_pipeline_log():
    log_path = Path('cron.log')
    if not log_path.exists():
        return "⚠️ cron.log not found."
    with open(log_path, 'r') as f:
        content = f.read()
    if 'failed' in content.lower():
        return "⚠️ Pipeline failures detected in cron.log."
    return "✅ Pipeline log shows no failures."

def main():
    print("🔍 Running engine sanity check...")
    threats_data = load_json('threats.json')
    threats = threats_data.get('threats', []) if isinstance(threats_data, dict) else threats_data
    predictions = load_json('predictions.json', {})
    health = load_json('health.json', {})

    checks = []
    if threats:
        checks.append(check_scp_distribution(threats))
        checks.append(check_statuses(threats))
    else:
        checks.append("⚠️ No threats loaded.")
    checks.append(check_predictions(predictions))
    checks.append(check_pipeline_log())

    if health.get('status') != 'ok':
        checks.append("⚠️ Health status is not 'ok'.")

    for check in checks:
        print(check)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
data_quality_warden.py – AW21 Data Quality Warden
Checks OSINT data sources for freshness, completeness, and validity.
"""
import json
import os
from datetime import datetime, timezone, timedelta

QUALITY_FILE = "data_quality_report.json"
MAX_AGE_HOURS = 24
CRITICAL_FILES = [
    "threats.json",
    "sweep_report.json",
    "telegram_data.json",
    "gpsjam_data.json",
    "hewd_data.json",
    "indices.json"
]

def check_file_age(filepath):
    if not os.path.exists(filepath):
        return None, "Missing"
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
    age = datetime.now(timezone.utc) - mtime
    return age.total_seconds() / 3600, "Ok"

def check_json_schema(filepath, required_keys):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            missing = [k for k in required_keys if k not in data]
            if missing:
                return False, f"Missing keys: {missing}"
            return True, "Valid"
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                missing = [k for k in required_keys if k not in data[0]]
                if missing:
                    return False, f"Missing keys in first item: {missing}"
            return True, "Valid"
        else:
            return False, "Unknown format"
    except Exception as e:
        return False, str(e)

def main():
    print("📋 Data Quality Warden (AW21) running...")
    
    reports = {}
    alert_issues = []
    
    for filepath in CRITICAL_FILES:
        age_hours, status = check_file_age(filepath)
        if age_hours is None:
            reports[filepath] = {"status": "missing", "age": None, "valid": False, "issues": ["File missing"]}
            alert_issues.append(f"{filepath} missing")
            continue
        if age_hours > MAX_AGE_HOURS:
            reports[filepath] = {"status": "stale", "age": age_hours, "valid": False, "issues": [f"Age {age_hours:.1f}h > {MAX_AGE_HOURS}h"]}
            alert_issues.append(f"{filepath} stale ({age_hours:.1f}h)")
            continue
        
        # Check schema for JSON files (basic required fields)
        is_valid, msg = check_json_schema(filepath, ["id", "name"])
        if not is_valid:
            reports[filepath] = {"status": "invalid", "age": age_hours, "valid": False, "issues": [msg]}
            alert_issues.append(f"{filepath} invalid: {msg}")
        else:
            reports[filepath] = {"status": "ok", "age": age_hours, "valid": True, "issues": []}
    
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reports": reports,
        "summary": {
            "total": len(reports),
            "ok": sum(1 for r in reports.values() if r["valid"]),
            "issues": alert_issues
        }
    }
    
    with open(QUALITY_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Data Quality Warden complete. {len(alert_issues)} issue(s) found.")
    for issue in alert_issues:
        print(f"   ⚠️ {issue}")

if __name__ == "__main__":
    main()

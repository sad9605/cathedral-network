#!/usr/bin/env python3
"""
H12 – Pipeline Monitoring Warden
Watches for failures, stale files, and alerts if something is broken.
"""
import os
import json
import subprocess
from datetime import datetime, timezone, timedelta

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
CRITICAL_FILES = [
    "threats.json",
    "gpsjam_data.json",
    "daily-brief.html",
    "daily-brief.md",
    "new_threat_candidates.json"
]
MAX_AGE_HOURS = 48  # Alert if file not updated in 48 hours

def log_alert(message, severity="WARNING"):
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] [{severity}] {message}"
    print(log_entry)
    with open("pipeline_health.log", "a") as f:
        f.write(log_entry + "\n")

# --------------------------------------------------
# 1. CHECK FILE EXISTENCE AND AGE
# --------------------------------------------------
print("🩺 Pipeline Monitoring Warden (H12) running...")
now = datetime.now(timezone.utc)

all_good = True

for filepath in CRITICAL_FILES:
    if not os.path.exists(filepath):
        log_alert(f"❌ CRITICAL: {filepath} is missing!", "ERROR")
        all_good = False
    else:
        # Check age
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
        age = now - mtime
        if age > timedelta(hours=MAX_AGE_HOURS):
            log_alert(f"⚠️  {filepath} is stale (last updated {age.days}d {age.seconds//3600}h ago)", "WARNING")
            all_good = False
        else:
            print(f"✅ {filepath} present and fresh.")

# --------------------------------------------------
# 2. RUN DRY-RUN TESTS (Quick checks)
# --------------------------------------------------
def test_script(script_name):
    try:
        result = subprocess.run(
            ["python3", script_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {script_name} runs without errors.")
            return True
        else:
            log_alert(f"❌ {script_name} failed (exit code {result.returncode})", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log_alert(f"⏰ {script_name} timed out", "ERROR")
        return False
    except Exception as e:
        log_alert(f"💥 {script_name} crashed: {str(e)}", "ERROR")
        return False

# Test key scripts (quick, non-destructive)
print("\n🧪 Running dry-run tests...")
test_script("recalibrate_engine.py")  # Should run fast
test_script("archive_engine.py")      # Should run fast (if no Green threats, it just exits)

# --------------------------------------------------
# 3. CHECK JSON VALIDITY
# --------------------------------------------------
print("\n📄 Validating JSON files...")
json_files = ["threats.json", "new_threat_candidates.json", "gpsjam_data.json"]
for f in json_files:
    if os.path.exists(f):
        try:
            with open(f, "r") as fp:
                json.load(fp)
            print(f"✅ {f} is valid JSON.")
        except json.JSONDecodeError as e:
            log_alert(f"❌ {f} is corrupted JSON: {str(e)}", "ERROR")
            all_good = False

# --------------------------------------------------
# 4. SUMMARY
# --------------------------------------------------
if all_good:
    log_alert("✅ All systems healthy.", "INFO")
    print("\n🟢 Pipeline status: HEALTHY")
else:
    log_alert("⚠️  Issues detected. Check pipeline_health.log for details.", "WARNING")
    print("\n🟡 Pipeline status: DEGRADED – check pipeline_health.log")

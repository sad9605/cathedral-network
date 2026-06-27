#!/usr/bin/env python3
"""
H13 – Self-Tuning Warden
Automatically runs recalibrate_engine.py when thresholds are met.
Now with safe threat loading.
"""
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
MAX_DAYS_BETWEEN_TUNING = 7
SCP_FLATNESS_THRESHOLD = 0.15  # If max-min SCP < 0.15, recalibrate

# --------------------------------------------------
# 1. LOAD THREATS (SAFE MODE)
# --------------------------------------------------
print("⚙️ Self-Tuning Warden (H13) running...")

def load_threats_safe():
    """Load threats.json safely, filtering out non-dict entries."""
    try:
        with open("threats.json", "r") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            threats = [t for t in raw if isinstance(t, dict)]
            if len(threats) != len(raw):
                print(f"⚠️  Found {len(raw) - len(threats)} invalid entries. Skipping.")
            return threats
        elif isinstance(raw, dict) and "threats" in raw:
            threats = [t for t in raw["threats"] if isinstance(t, dict)]
            return threats
        else:
            print("⚠️  threats.json is not a list or dict. Creating empty list.")
            return []
    except json.JSONDecodeError:
        print("⚠️  threats.json is corrupted. Creating empty list.")
        return []
    except FileNotFoundError:
        print("⚠️  threats.json not found. Creating empty list.")
        return []

threats = load_threats_safe()

if not threats:
    print("ℹ️  No threats to evaluate. Exiting.")
    # Save a clean empty file
    with open("threats.json", "w") as f:
        json.dump([], f, indent=2)
    print("✅ Cleaned threats.json (empty list).")
    exit(0)

# --------------------------------------------------
# 2. CHECK LAST TUNING DATE
# --------------------------------------------------
last_tune_file = "last_tune_date.json"
last_tune = None
if os.path.exists(last_tune_file):
    try:
        with open(last_tune_file, "r") as f:
            data = json.load(f)
            last_tune = datetime.fromisoformat(data.get("last_tune", ""))
    except:
        last_tune = None

now = datetime.now(timezone.utc)
should_tune = False
reasons = []

# Check age of last tuning
if last_tune is None:
    reasons.append("Never tuned before.")
    should_tune = True
else:
    days_since = (now - last_tune).days
    if days_since >= MAX_DAYS_BETWEEN_TUNING:
        reasons.append(f"Last tuning was {days_since} days ago (threshold: {MAX_DAYS_BETWEEN_TUNING}).")
        should_tune = True

# --------------------------------------------------
# 3. CHECK SCP FLATNESS
# --------------------------------------------------
if threats and len(threats) > 2:
    scp_values = [t.get("scp", 0.5) for t in threats if isinstance(t, dict)]
    if scp_values:
        max_scp = max(scp_values)
        min_scp = min(scp_values)
        spread = max_scp - min_scp
        if spread < SCP_FLATNESS_THRESHOLD:
            reasons.append(f"SCP spread is too flat ({spread:.3f} < {SCP_FLATNESS_THRESHOLD}).")
            should_tune = True

# --------------------------------------------------
# 4. RUN TUNING IF NEEDED
# --------------------------------------------------
if should_tune:
    print(f"🔧 Tuning triggered for: {'; '.join(reasons)}")
    print("🔧 Running recalibrate_engine.py...")
    try:
        result = subprocess.run(
            ["python3", "recalibrate_engine.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Recalibration successful.")
            with open(last_tune_file, "w") as f:
                json.dump({"last_tune": now.isoformat()}, f, indent=2)
            print(f"📅 Last tune date updated to {now.isoformat()}")
        else:
            print(f"❌ Recalibration failed: {result.stderr}")
    except Exception as e:
        print(f"💥 Self-tune crashed: {str(e)}")
else:
    print("ℹ️  No tuning needed. All SCP scores are healthy.")
    if last_tune:
        print(f"   Last tuned: {last_tune.isoformat()}")

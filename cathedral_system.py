#!/usr/bin/env python3
"""
cathedral_system.py – Master orchestrator for Cathedral Network daily pipeline.
Runs: sweep → forecast → cascade engine → indices → early warning → SCP history → cascade graph → trends → verify predictions → generate predictions → update sources → archive → git push.
"""

import subprocess
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime

# ------------- helper functions -------------

def run_script(script_name, description):
    """Run a Python script and log success/failure."""
    print(f"\n🔹 {description} ...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"✅ {description} completed.")
            if result.stdout:
                print(result.stdout.strip())
            return True
        else:
            print(f"❌ {description} failed (exit {result.returncode}).")
            if result.stderr:
                print("STDERR:", result.stderr.strip())
            return False
    except Exception as e:
        print(f"❌ {description} crashed: {e}")
        traceback.print_exc()
        return False

# ------------- main -------------

def main():
    print("=" * 60)
    print(f"🏛️  CATHEDRAL NETWORK – DAILY PIPELINE")
    print(f"   Started at {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. Daily sweep – OSINT ingestion
    run_script("daily-sweep.py", "Daily OSINT sweep")

    # 2. Time‑series forecasting (Prophet)
    run_script("tsf_prototype.py", "Time‑series forecasting")

    # 3. Cascade Engine – Bayesian updates, SCP, GSCI, etc.
    run_script("cascade_engine.py", "Cascade Engine (v8)")

    # 4. Regional indices
    run_script("indices.py", "Regional indices")

    # 5. Early warning report
    run_script("early_warning.py", "Early warning report")

    # --- NEW BACKEND INTEGRATIONS ---
    # 6. Record SCP history (daily snapshots)
    run_script("record_scp_history.py", "SCP history logging")

    # 7. Generate cascade graph for Cytoscape
    run_script("generate_cascade_graph.py", "Cascade graph generation")

    # 8. Compute trends (7‑day SCP delta)
    run_script("compute_trends.py", "Trend computation")

    # 9. Verify predictions – auto‑confirm/falsify
    run_script("verify_predictions.py", "Prediction verification")

    # 10. Generate prediction log (filtered, with date_made)
    run_script("generate_predictions.py", "Prediction log generation")

    # 11. Update sources list
    run_script("update_sources.py", "Sources update")

    # 12. Generate daily archive
    run_script("generate_archive.py", "Daily archive generation")

    # 13. Git commit and push (to trigger GitHub Pages rebuild)
    run_script("git_commit_push.py", "Git commit and push")

    print("\n" + "=" * 60)
    print("✅ Cathedral pipeline finished.")
    print(f"   Completed at {datetime.now().isoformat()}")
    print("=" * 60)

if __name__ == "__main__":
    main()

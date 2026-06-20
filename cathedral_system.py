#!/usr/bin/env python3
"""
cathedral_system.py – Master orchestrator for Cathedral Network daily pipeline.
Runs: sweep → forecast → cascade engine → indices → early warning → SCP history → cascade graph → trends → verify predictions → generate predictions → update sources → archive → git push.
"""

import json
import sys
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from cathedral_math import compute_gsci

# ------------- helper functions -------------

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

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

    # ---- v9 ML Likelihoods ----
    print("🧠 Computing ML likelihood ratios...")
    try:
        from cathedral_ml import get_ml_likelihoods
        data = load_json("threats.json")
        threats = data.get('threats', [])
        ml_lrs = get_ml_likelihoods(threats)
    
        # Store ML LRs in a separate file for now
        save_json(ml_lrs, "ml_likelihoods.json")
    
        # Also attach them to each threat in threats.json
        for t in threats:
            tid = t.get('id')
            if tid and tid in ml_lrs:
                t['ml_likelihood_ratio'] = ml_lrs[tid]
    
        # Save updated threats
        data['threats'] = threats
        save_json(data, "threats.json")
    
        print(f"   ✅ ML LRs computed for {len(ml_lrs)} threats")
    except Exception as e:
        print(f"   ⚠️ ML step failed: {e}")

    # ---- Generate HEWD data ----
    run_script("generate_hewd.py", "HEWD data generation")

    # 4. Regional indices
    run_script("indices.py", "Regional indices")

    # ---- Compute and store GSCI ----
    print("📊 Computing and storing GSCI...")
    data = load_json("threats.json")
    threats = data.get('threats', [])
    gsci = compute_gsci(threats)
    data['gsci'] = gsci
    save_json(data, "threats.json")
    print(f"   GSCI = {gsci}")

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

    # ---- Generate archive index ----
    run_script("generate_archive_index.py", "Archive index generation")

    # 13. Git commit and push (to trigger GitHub Pages rebuild)
    run_script("git_commit_push.py", "Git commit and push")

    # ---- Generate health check ----
    run_script("generate_health.py", "Health check generation")

    print("\n" + "=" * 60)
    print("✅ Cathedral pipeline finished.")
    print(f"   Completed at {datetime.now().isoformat()}")
    print("=" * 60)

if __name__ == "__main__":
    main()

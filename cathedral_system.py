#!/usr/bin/env python3
"""
cathedral_system.py – Cathedral Network Orchestrator
Runs the full mathematical pipeline.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cathedral_math import (
    compute_ssi, compute_ds, compute_gsci, compute_sca_tier,
    bayesian_log_odds, compute_scp_linear
)
from indices import generate_regional_indices
from early_warning import generate_early_warning_report

def load_json(filepath):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def run_module(module_name):
    """Run a Python module and return success."""
    try:
        result = subprocess.run(
            [sys.executable, module_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"⚠️ {module_name} failed: {result.stderr}")
            return False
        print(f"✅ {module_name} completed")
        return True
    except Exception as e:
        print(f"⚠️ {module_name} error: {e}")
        return False

def main():
    print("🏛️ Cathedral System – Full Pipeline\n")
    
    # 1. Run daily sweep
    print("📡 Running OSINT sweep...")
    run_module("daily-sweep.py")
    
    # 2. Run TSF
    print("📈 Running TSF forecast...")
    run_module("tsf_prototype.py")
    
    # 3. Run cascade engine
    print("⚙️ Running cascade engine...")
    run_module("cascade_engine.py")
    
    # 4. Compute additional math metrics
    print("🧮 Computing mathematical indices...")
    threats = load_json("threats.json").get('threats', [])
    
    # Compute SSI
    ssi = compute_ssi(threats)
    ds = compute_ds(threats)
    
    # Compute SCA tier
    cascade_log = load_json("cascade_log.json")
    sca_tier = compute_sca_tier(len(cascade_log))
    
    # Load threats.json and update with new metrics
    threats_data = load_json("threats.json")
    threats_data['ssi'] = ssi
    threats_data['ds'] = ds
    threats_data['sca_tier'] = sca_tier['tier']
    threats_data['sca_label'] = sca_tier['label']
    threats_data['sca_count'] = sca_tier['count']
    threats_data['last_updated'] = datetime.now().isoformat()
    
    save_json(threats_data, "threats.json")
    print(f"✅ SSI: {ssi:.2f}, DS: {ds}, SCA Tier: {sca_tier['tier']} ({sca_tier['label']})")
    
    # 5. Generate regional indices
    print("🌍 Generating regional indices...")
    generate_regional_indices()
    
    # 6. Generate early warning report
    print("🚨 Generating early warning report...")
    early_report = generate_early_warning_report(threats)
    save_json(early_report, "early_warning_report.json")
    
    # 7. Run predictions generator
    print("📋 Generating prediction log...")
    run_module("generate_predictions.py")
    
    # 8. Update sources
    print("📡 Updating sources...")
    run_module("update_sources.py")
    
    # 9. Git commit and push
    print("📤 Committing and pushing updates...")
    run_module("git_commit_push.py")
    
    print("\n✅ Cathedral system pipeline complete")
    print(f"   SSI: {ssi:.2f}")
    print(f"   DS: {ds}")
    print(f"   SCA Tier: {sca_tier['label']}")
    print(f"   GSCI: {threats_data.get('gsci', 0)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
cathedral_system.py – Cathedral Network Full Orchestrator
Runs the complete mathematical pipeline with all modules activated.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Core math
from cathedral_math import (
    compute_ssi,
    compute_ds,
    compute_gsci,
    compute_sca_tier,
    bayesian_log_odds,
    compute_scp_linear,
    temporal_baseline_anomaly,
    nts_band,
    das_band
)

# Indices
from indices import generate_regional_indices

# Early warning
from early_warning import generate_early_warning_report

# AI thermoregulation
from arifos_floors import arifOS

# Financial module
from keem import kelly_fraction, implied_volatility_filter, adaptive_slippage

# Archive generation
from generate_archive import generate_archive

# Prediction generation
from generate_predictions import generate_predictions

# Sources update
from update_sources import update_sources

# Git commit/push
from git_commit_push import git_commit_push

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
            print(f"⚠️ {module_name} failed: {result.stderr[:200]}")
            return False
        print(f"✅ {module_name} completed")
        return True
    except Exception as e:
        print(f"⚠️ {module_name} error: {e}")
        return False

def main():
    print("🏛️ Cathedral System – Full Pipeline (All Modules Active)\n")
    
    # ------------------------------------------------------------------
    # 1. Daily OSINT Sweep
    print("📡 Running OSINT sweep...")
    run_module("daily-sweep.py")
    
    # ------------------------------------------------------------------
    # 2. TSF Forecasting
    print("📈 Running TSF forecast...")
    run_module("tsf_prototype.py")
    
    # ------------------------------------------------------------------
    # 3. AI Thermoregulation (arifOS)
    print("🌡️ Running arifOS floors (AI thermoregulation)...")
    try:
        arifos = arifOS()
        adjustment = arifos.adjust_policy()
        print(f"✅ arifOS applied: {adjustment['load_level']} load, confidence floor: {adjustment['confidence_floor']}")
    except Exception as e:
        print(f"⚠️ arifOS failed: {e}")
    
    # ------------------------------------------------------------------
    # 4. Cascade Engine
    print("⚙️ Running cascade engine...")
    run_module("cascade_engine.py")
    
    # ------------------------------------------------------------------
    # 5. Load threats for math processing
    print("🧮 Computing mathematical indices...")
    threats_data = load_json("threats.json")
    threats = threats_data.get('threats', [])
    
    # Compute core metrics
    ssi = compute_ssi(threats)
    ds = compute_ds(threats)
    gsci = compute_gsci([t.get('scp', 0) * 100 for t in threats])
    
    # SCA tier
    cascade_log = load_json("cascade_log.json")
    sca_tier = compute_sca_tier(len(cascade_log))
    
    # Update threats.json with new metrics
    threats_data['ssi'] = round(ssi, 2)
    threats_data['ds'] = ds
    threats_data['gsci'] = round(gsci, 2)
    threats_data['sca_tier'] = sca_tier['tier']
    threats_data['sca_label'] = sca_tier['label']
    threats_data['sca_count'] = sca_tier['count']
    threats_data['last_updated'] = datetime.now().isoformat()
    
    save_json(threats_data, "threats.json")
    print(f"✅ SSI: {ssi:.2f}, DS: {ds}, GSCI: {gsci:.2f}")
    print(f"✅ SCA Tier: {sca_tier['tier']} ({sca_tier['label']})")
    
    # ------------------------------------------------------------------
    # 6. Regional Indices
    print("🌍 Generating regional indices...")
    generate_regional_indices()
    
    # ------------------------------------------------------------------
    # 7. Early Warning Report
    print("🚨 Generating early warning report...")
    early_report = generate_early_warning_report(threats)
    save_json(early_report, "early_warning_report.json")
    print(f"✅ Anomalies detected: {early_report.get('anomaly_count', 0)}")
    
    # ------------------------------------------------------------------
    # 8. Archive Generation
    print("📁 Generating archive...")
    generate_archive()
    
    # ------------------------------------------------------------------
    # 9. Prediction Log Generation
    print("📋 Generating prediction log...")
    generate_predictions()
    
    # ------------------------------------------------------------------
    # 10. Sources Update
    print("📡 Updating sources...")
    update_sources()
    
    # ------------------------------------------------------------------
    # 11. Financial Module (optional – logs only)
    print("💹 Running financial module (KEEM)...")
    try:
        # Sample calculation for demonstration
        kelly = kelly_fraction(0.65, 0.50)
        print(f"✅ Kelly fraction: {kelly:.4f}")
    except Exception as e:
        print(f"⚠️ KEEM error: {e}")
    
    # ------------------------------------------------------------------
    # 12. Unconventional Modules (run separately if needed)
    print("🔄 Unconventional modules ready – run unconventional_orchestrator.py separately")
    
    # ------------------------------------------------------------------
    # 13. Git Commit and Push
    print("📤 Committing and pushing updates...")
    git_commit_push()
    
    # ------------------------------------------------------------------
    print("\n✅ Cathedral system pipeline complete")
    print(f"   SSI: {ssi:.2f}")
    print(f"   DS: {ds}")
    print(f"   SCA Tier: {sca_tier['label']}")
    print(f"   GSCI: {gsci:.2f}")
    print(f"   Anomalies: {early_report.get('anomaly_count', 0)}")

if __name__ == "__main__":
    main()

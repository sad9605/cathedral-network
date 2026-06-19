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

# Verification
from verify_predictions import verify_predictions

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
    # 2. TSF Forecasting (oil, food, disaster)
    print("📈 Running TSF forecasts...")
    run_module("tsf_prototype.py")
    
    # ------------------------------------------------------------------
    # 3. Cascade Engine – Bayesian updates & threat propagation
    print("⚙️ Running Cascade Engine...")
    run_module("cascade_engine.py")
    
    # ------------------------------------------------------------------
    # 4. Verify Predictions – confirm/falsify pending based on threat status/horizon
    print("🔍 Running prediction verification...")
    verify_predictions()   # <-- NEW INTEGRATION
    
    # ------------------------------------------------------------------
    # 5. Generate Prediction Log (filtered, with date_made)
    print("📋 Generating prediction log...")
    generate_predictions()
    
    # ------------------------------------------------------------------
    # 6. Compute Cathedral Math (SSI, DS, GSCI, SCA, etc.)
    print("🧮 Computing Cathedral Math...")
    threats = load_json("threats.json").get("threats", [])
    if threats:
        # Compute SSI
        ssi = compute_ssi(threats)
        # Compute DS
        ds = compute_ds(threats)
        # Compute GSCI
        gsci = compute_gsci(threats)
        # Compute SCA tier
        # Count threats that are active (non-green status) – proxy for active cascades 
        active_count = len([t for t in threats if t.get('status') != 'Green'])
        sca = compute_sca_tier(active_count)
        # Update threats.json with computed values
        data = load_json("threats.json")
        data["ssi"] = ssi
        data["ds"] = ds
        data["gsci"] = gsci
        data["sca_tier"] = sca
        data["last_calculated"] = datetime.now().isoformat()
        save_json(data, "threats.json")
        print(f"   SSI: {ssi}, DS: {ds}, GSCI: {gsci}, SCA: {sca}")
    
    # ------------------------------------------------------------------
    # 7. Regional Indices
    print("🌍 Generating regional indices...")
    generate_regional_indices()
    
    # ------------------------------------------------------------------
    # 8. Early Warning Report (CAP, DAS, source credibility)
    print("⚠️ Generating early warning report...")
    generate_early_warning_report(threats)
    
    # ------------------------------------------------------------------
    # 9. AI Thermoregulation
    print("🌡️ Running arifOS thermoregulation...")
    arifOS()
    
    # ------------------------------------------------------------------
    # 10. Financial Module (Kalshi, kelly, slippage)
    print("💰 Running financial module...")
    # Example: load predictions to compute kelly fractions
    predictions = load_json("predictions.json")
    if predictions:
        for p in predictions.get("pending", []):
            prob = p.get("probability", 50) / 100.0
            kelly = kelly_fraction(prob, 2.0)  # assuming 2:1 payout
            p["kelly"] = round(kelly, 3)
        save_json(predictions, "predictions.json")
    
    # ------------------------------------------------------------------
    # 11. Archive Generation
    print("📦 Generating archive...")
    generate_archive()
    
    # ------------------------------------------------------------------
    # 12. Update Sources
    print("📰 Updating sources...")
    update_sources()
    
    # ------------------------------------------------------------------
    # 13. Git Commit & Push
    print("📤 Committing and pushing to GitHub...")
    git_commit_push()
    
    print("\n✅ Cathedral pipeline complete. All modules executed successfully.")
    print(f"   Last updated: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()

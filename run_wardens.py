#!/usr/bin/env python3
"""
run_wardens.py – Cathedral Master Orchestrator
Runs all pipeline steps with Threat Matrix integrity protection.
"""
import subprocess
import sys
import os
from datetime import datetime, timezone

# ── Threat Matrix Guardian Integration ──
def guardian(action):
    """Run guardian.py with the given action."""
    try:
        subprocess.run(["python3", "guardian.py", action], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Guardian {action} failed: {e.stderr.decode()}")
        return False

# ── Step Runner ──
def run_step(name, command):
    print("\n" + "="*60)
    print(f"🏛️  RUNNING: {name}")
    print("="*60)
    try:
        result = subprocess.run(command, shell=True, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"✅ {name} completed successfully.")
            return True
        else:
            print(f"❌ {name} failed with exit code {result.returncode}.")
            return False
    except Exception as e:
        print(f"💥 {name} crashed: {str(e)}")
        return False

# ── Main Pipeline ──
def main():
    start_time = datetime.now(timezone.utc)
    print("🏛️  CATHEDRAL MASTER PIPELINE START")
    print(f"⏰ Started at: {start_time.isoformat()}")

    # Lock the Threat Matrix
    if not guardian("lock"):
        print("💀 Could not lock Threat Matrix. Aborting.")
        sys.exit(1)

    results = []

    results.append(run_step("Cascade Engine", "python3 cascade_engine.py"))

   # ── After Cascade Engine ──
   results.append(run_step("DeepCausality Contextual Engine", "python3 contextual_cascade.py"))

    # ── STEP 1: Data Collection ──
    results.append(run_step("Threat Scanner (H02)", "python3 threat_scanner.py"))
    # ── After Threat Scanner ──
    results.append(run_step("Causal Validator (DoWhy)", "python3 causal_validator.py"))
    results.append(run_step("GPSJAM Fetcher (C04)", "python3 gpsjam_fetcher.py"))
    results.append(run_step("HEWD Fetcher", "python3 hewd_fetcher.py"))
    results.append(run_step("Telegram Fetcher (AW15)", "python3 telegram_fetcher.py"))
 
    # ── After Threat Scanner ──
    results.append(run_step("Causal Cartographer", "python3 causal_cartographer.py"))

    # ── STEP 2: Archive Resolved Threats ──
    results.append(run_step("Archive Engine (H01)", "python3 archive_engine.py"))

    # ── STEP 3: OSINT Triage ──
    results.append(run_step("OSINT Triage Warden (H11) - DRY RUN", "python3 osint_warden.py --dry-run"))

    # ── STEP 4: Historical Validation & Tuning ──
    results.append(run_step("Historical Validator", "python3 historical_validator.py"))
    results.append(run_step("Historical Tuner", "python3 historical_tuner.py"))
    results.append(run_step("Historical Cascade Analyst", "python3 historical_cascade_analyst.py"))
    results.append(run_step("Ascension Tuner", "python3 ascension_tuner.py"))

    # ── STEP: Prediction Validator ──
    results.append(run_step("Prediction Validator", "python3 prediction_validator.py"))

    # ── STEP: Prediction Checker (Daily Sweep) ──
    results.append(run_step("Prediction Checker (Daily Sweep)", "python3 prediction_checker.py"))

    # ── STEP 5: Generate Output ──
    results.append(run_step("Daily Brief Generator (C03/H05-H10)", "python3 generate_daily_brief.py"))

    # ── STEP 6: Health & Monitoring ──
    results.append(run_step("Pipeline Monitor (H12)", "python3 pipeline_warden.py"))
    results.append(run_step("Self-Tuning Warden (H13)", "python3 self_tune_warden.py"))

    # ── STEP 7: Verification & Validation ──
    results.append(run_step("Warden Verification (AW04)", "python3 verification_warden.py"))
    results.append(run_step("Prediction Validation (AW05)", "python3 validation_warden.py"))

    # ── STEP: Domain Wardens (AW09-AW13) ──
    results.append(run_step("AW11 Climate Warden", "python3 aw11_climate_warden.py"))
    results.append(run_step("AW10 Economic Warden", "python3 aw10_economic_warden.py"))
    results.append(run_step("AW12 Health Warden", "python3 aw12_health_warden.py"))
    # AW09 and AW13 can be added later

    results.append(run_step("AW09 Geopolitical Warden", "python3 aw09_geopolitical_warden.py"))
    results.append(run_step("AW13 Social Sentiment Warden", "python3 aw13_social_warden.py"))

    # ── Check Threat Matrix integrity ──
    if not guardian("check"):
        print("⚠️ Threat Matrix integrity check failed. Pipeline will continue, but check logs.")
    else:
        print("✅ Threat Matrix integrity verified.")

    # Unlock the Threat Matrix (optional)
    guardian("unlock")

    # ── Summary ──
    print("\n" + "="*60)
    print("📊 PIPELINE EXECUTION SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r)
    failed = len(results) - passed
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print("\n⚠️  Some steps failed. Check the logs above for errors.")
        sys.exit(1)
    else:
        print("\n🎉 ALL STEPS PASSED! The Cathedral is healthy.")
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        print(f"⏱️  Total runtime: {duration:.2f} seconds.")
        sys.exit(0)

if __name__ == "__main__":
    main()

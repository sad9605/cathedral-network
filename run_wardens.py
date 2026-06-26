#!/usr/bin/env python3
"""
Master Warden Orchestrator
Runs the entire Cathedral pipeline in the correct order:
1. Fetch data (Threat Scanner, GPSJAM,Telegram Fetcher)
2. Archive resolved threats
3. OSINT Triage (DRY RUN by default)
4. Generate Daily Brief
5. Pipeline Health Monitor
6. Self-Tuning
7. Warden Verification
8. Prediction Validation
"""
import subprocess
import sys
import os
from datetime import datetime, timezone

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
# Set this to False to ENABLE auto-promotion in OSINT Warden
OSINT_DRY_RUN = True  # True = Safe mode (prints what it would do, doesn't modify threats.json)

def run_step(name, command):
    """Runs a shell command and prints the result."""
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

def main():
    start_time = datetime.now(timezone.utc)
    print("🏛️  CATHEDRAL MASTER PIPELINE START")
    print(f"⏰ Started at: {start_time.isoformat()}")
    print(f"🔒 OSINT Triage DRY-RUN mode: {'ENABLED' if OSINT_DRY_RUN else 'DISABLED (auto-promote ON)'}")

    results = []

    # --------------------------------------------------
    # STEP 1: Fetch fresh data
    # --------------------------------------------------
    results.append(run_step("Threat Scanner (H02)", "python3 threat_scanner.py"))
    results.append(run_step("GPSJAM Fetcher (C04)", "python3 gpsjam_fetcher.py"))
    results.append(run_step("Telegram Fetcher (AW15)", "python3 telegram_fetcher.py"))

    # --------------------------------------------------
    # STEP 2: Archive resolved threats
    # --------------------------------------------------
    results.append(run_step("Archive Engine (H01)", "python3 archive_engine.py"))

    # --------------------------------------------------
    # STEP 3: OSINT Triage (with DRY RUN toggle)
    # --------------------------------------------------
    if OSINT_DRY_RUN:
        # Run in dry-run mode: it will score candidates but NOT promote them
        results.append(run_step("OSINT Triage Warden (H11) - DRY RUN", "python3 osint_warden.py --dry-run"))
    else:
        results.append(run_step("OSINT Triage Warden (H11) - LIVE", "python3 osint_warden.py"))

    # --------------------------------------------------
    # STEP 4: Generate Daily Brief
    # --------------------------------------------------
    results.append(run_step("Daily Brief Generator (C03/H05-H10)", "python3 generate_daily_brief.py"))

    # --------------------------------------------------
    # STEP 5: Pipeline Health Monitor
    # --------------------------------------------------
    results.append(run_step("Pipeline Monitor (H12)", "python3 pipeline_warden.py"))

    # --------------------------------------------------
    # STEP 6: Self-Tuning
    # --------------------------------------------------
    results.append(run_step("Self-Tuning Warden (H13)", "python3 self_tune_warden.py"))

    # --------------------------------------------------
    # STEP 7: Warden Verification (AW04)
    # --------------------------------------------------
    results.append(run_step("Warden Verification (AW04)", "python3 verification_warden.py"))

    # --------------------------------------------------
    # STEP 8: Prediction Validation (AW05)
    # --------------------------------------------------
    results.append(run_step("Prediction Validation (AW05)", "python3 validation_warden.py"))

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
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

#!/usr/bin/env python3
"""
Cathedral Network – Orchestrator
Runs daily sweep, TSF, cascade, and optionally crisis simulation
"""

import subprocess
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_step(name, command):
    logging.info(f"Starting: {name}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"{name} failed: {result.stderr}")
        return False
    logging.info(f"{name} completed successfully")
    return True

def main():
    logging.info("=== Cathedral Network Daily Orchestration ===")
    logging.info(f"Start time: {datetime.now().isoformat()}")
    
    steps = [
        ("Daily Sweep", "python3 daily_sweep.py"),
        ("TSF Forecast", "python3 tsf_prototype.py"),
        ("Cascade Engine", "python3 cascade_engine.py"),
        # ("Crisis Simulation", "python3 crisis_simulation_engine.py"),  # Optional
    ]
    
    for name, cmd in steps:
        if not run_step(name, cmd):
            logging.error(f"Stopping orchestration due to {name} failure")
            sys.exit(1)
    
    logging.info(f"=== Orchestration complete at {datetime.now().isoformat()} ===")

if __name__ == "__main__":
    main()

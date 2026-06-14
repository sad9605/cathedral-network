#!/bin/bash
cd /home/sad9605/cathedral-core
source venv/bin/activate

# 1. OSINT sweep
python daily-sweep.py

# 2. TSF forecasts
python tsf_prototype.py

# 3. Cascade engine (Bayesian + rules + confidence filters)
python cascade_engine.py

# 4. Push updated data to GitHub (auto-deploys to GitHub Pages)
git add threats.json cascade_log.json gsci_log.json sweep_report.json ground_truth_summary.md tsf_forecasts.json
git commit -m "Automated daily sweep $(date +%Y-%m-%d)" || echo "No changes"
git push origin main

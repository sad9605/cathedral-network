#!/bin/bash
cd /home/sad9605/cathedral-core
source venv/bin/activate

python daily-sweep.py
python tsf_prototype.py
python cascade_engine.py
python generate_predictions.py   # <-- NEW: auto-update prediction log

git add threats.json cascade_log.json sweep_report.json ground_truth_summary.md tsf_forecasts.json predictions.json
git commit -m "Automated daily sweep $(date +%Y-%m-%d)" || echo "No changes"
git push origin main

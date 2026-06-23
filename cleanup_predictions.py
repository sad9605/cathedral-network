#!/usr/bin/env python3
"""
cleanup_predictions.py – One‑time cleanup of low‑value/historical predictions.
Moves low‑probability or expired predictions to archive.
"""

import json
from datetime import datetime
from pathlib import Path

PREDICTIONS_FILE = "predictions.json"
ARCHIVE_FILE = "predictions_archive.json"
MIN_PROBABILITY = 50  # keep predictions ≥ 50%

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def parse_horizon(horizon_str):
    """Simple horizon parser – returns datetime or None."""
    if not horizon_str:
        return None
    try:
        return datetime.strptime(horizon_str, "%d %b %Y")
    except:
        return None

def main():
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        print("No predictions.json found.")
        return

    pending = predictions.get('pending', [])
    kept = []
    archived = []

    now = datetime.now()

    for p in pending:
        prob = p.get('probability', 0)
        horizon_str = p.get('horizon', '')

        # Skip if probability is too low
        if prob < MIN_PROBABILITY:
            archived.append({**p, "archive_reason": f"Probability {prob}% < {MIN_PROBABILITY}%"})
            continue

        # Skip if horizon has passed
        horizon_date = parse_horizon(horizon_str)
        if horizon_date and horizon_date < now:
            archived.append({**p, "archive_reason": f"Horizon {horizon_str} passed"})
            continue

        kept.append(p)

    predictions['pending'] = kept

    # Recalculate stats
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)

    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(kept),
        "watchlist": len(predictions.get('watchlist', []))
    }

    predictions['last_updated'] = datetime.now().isoformat()

    # Add to history
    predictions['history'] = predictions.get('history', [])
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "cleanup",
        "removed": len(archived),
        "kept": len(kept)
    })

    save_json(predictions, PREDICTIONS_FILE)

    # Append to archive
    existing_archive = load_json(ARCHIVE_FILE, [])
    existing_archive.extend(archived)
    save_json(existing_archive, ARCHIVE_FILE)

    print(f"✅ Cleanup complete:")
    print(f"   Kept: {len(kept)}")
    print(f"   Archived: {len(archived)}")

if __name__ == "__main__":
    main()

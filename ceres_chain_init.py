#!/usr/bin/env python3
"""
ceres_chain_init.py – Initialize CERES chain from existing predictions.
"""
import json
import hashlib
from datetime import datetime, timezone

PREDICTIONS_FILE = "predictions.json"
CHAIN_FILE = "ceres_chain.json"

def hash_prediction(pred):
    """Create a deterministic hash from a prediction object."""
    pred_str = json.dumps(pred, sort_keys=True)
    return hashlib.sha256(pred_str.encode()).hexdigest()

def main():
    # Load predictions
    with open(PREDICTIONS_FILE, 'r') as f:
        preds = json.load(f)
    if isinstance(preds, dict):
        # Flatten all categories if needed
        all_preds = []
        for key in ['confirmed', 'falsified', 'pending', 'watchlist']:
            all_preds.extend(preds.get(key, []))
    else:
        all_preds = preds

    # Build chain
    chain = []
    prev_hash = "0" * 64  # genesis

    for idx, p in enumerate(all_preds):
        pred_id = p.get('id', f'P{idx+1:03d}')
        pred_hash = hash_prediction(p)
        timestamp = p.get('logged_date', p.get('date_made', datetime.now(timezone.utc).isoformat()))
        statement = p.get('statement', p.get('description', ''))[:80]

        chain_hash = hashlib.sha256(
            (prev_hash + pred_hash + timestamp).encode()
        ).hexdigest()

        entry = {
            "index": idx + 1,
            "prediction_id": pred_id,
            "prediction_hash": pred_hash,
            "previous_hash": prev_hash,
            "timestamp": timestamp,
            "statement": statement,
            "chain_hash": chain_hash
        }
        chain.append(entry)
        prev_hash = chain_hash

    # Save the chain
    output = {
        "chain": chain,
        "last_hash": prev_hash
    }

    with open(CHAIN_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ CERES chain generated with {len(chain)} entries.")
    print(f"🔗 Last hash: {prev_hash[:16]}...")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
#!/usr/bin/env python3
"""
generate_predictions.py – Auto-generate predictions from engine data.
Timestamped, auditable, and hit-rate verified.

Integrates with:
- threats.json (threat data)
- cascade_log.json (cascade events)
- predictions.json (historical predictions)
- confirm_prediction.py (confirmation/falsification)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Import confirmation functions if available
try:
    from confirm_prediction import add_confirmed, add_falsified
except ImportError:
    # Fallback: define placeholder functions
    def add_confirmed(prediction_id, description):
        print(f"⚠️ confirm_prediction.py not found – would confirm {prediction_id}")
        return False
    
    def add_falsified(prediction_id, description, reason):
        print(f"⚠️ confirm_prediction.py not found – would falsify {prediction_id}")
        return False

THREATS_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
PREDICTIONS_FILE = "predictions.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in {filepath}, using default")
            return default if default is not None else {}
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_predictions():
    """
    Generate predictions from threat data and cascade logs.
    Updates predictions.json with new active predictions.
    """
    print("📋 Generating prediction log from engine data...")
    
    # Load existing predictions (preserve history)
    predictions = load_json(PREDICTIONS_FILE)
    if not predictions:
        predictions = {
            "confirmed": [],
            "falsified": [],
            "pending": [],
            "watchlist": [],
            "stats": {
                "confirmed": 0,
                "falsified": 0,
                "hit_rate": 0.0,
                "pending": 0,
                "watchlist": 0
            },
            "history": [],
            "last_updated": ""
        }
    
    # Load threats
    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get('threats', [])
    if not threats:
        print("⚠️ No threats found in threats.json")
        return
    
    # Load cascade log for recent activity
    cascade_log = load_json(CASCADE_LOG, default=[])
    recent_cascades = cascade_log[-50:] if len(cascade_log) > 50 else cascade_log
    
    # Build set of existing prediction IDs
    existing_pending = {p.get('id', '') for p in predictions.get('pending', [])}
    existing_confirmed = {p.get('id', '') for p in predictions.get('confirmed', [])}
    existing_falsified = {p.get('id', '') for p in predictions.get('falsified', [])}
    existing_watchlist = {p.get('id', '') for p in predictions.get('watchlist', [])}
    
    # Generate new predictions from high-priority threats
    new_predictions = []
    updated_count = 0
    
    for t in threats:
        threat_id = t.get('id', '')
        if not threat_id:
            continue
        
        # Skip if already resolved
        if threat_id in existing_confirmed or threat_id in existing_falsified:
            continue
        
        # Check if threat is high priority
        priority_score = t.get('priority_score', 0)
        scp = t.get('scp', 0.5)
        base_prob = t.get('base_probability', 0.5)
        
        # Generate prediction for high-priority threats
        if priority_score > 60 or scp > 0.6 or base_prob > 0.7:
            # Check if it's already pending
            if threat_id in existing_pending:
                # Update existing pending prediction
                updated_count += 1
                continue
            
            # Create new prediction
            pred = {
                "id": threat_id,
                "description": t.get('name', threat_id)[:80],
                "probability": round(base_prob * 100),
                "scp": round(scp, 2),
                "priority_score": round(priority_score, 2),
                "created": datetime.now().isoformat(),
                "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "Active",
                "source": "auto_generated"
            }
            new_predictions.append(pred)
    
    # Add new predictions to pending
    if new_predictions:
        predictions['pending'].extend(new_predictions)
        print(f"✅ Generated {len(new_predictions)} new predictions")
    
    if updated_count > 0:
        print(f"🔄 Updated {updated_count} existing predictions")
    
    # Update stats
    confirmed = predictions.get('confirmed', [])
    falsified = predictions.get('falsified', [])
    pending = predictions.get('pending', [])
    watchlist = predictions.get('watchlist', [])
    
    total_resolved = len(confirmed) + len(falsified)
    hit_rate = round((len(confirmed) / total_resolved * 100) if total_resolved > 0 else 0, 2)
    
    predictions['stats'] = {
        "confirmed": len(confirmed),
        "falsified": len(falsified),
        "hit_rate": hit_rate,
        "pending": len(pending),
        "watchlist": len(watchlist)
    }
    predictions['last_updated'] = datetime.now().isoformat()
    
    # Add history entry
    predictions['history'].append({
        "timestamp": datetime.now().isoformat(),
        "action": "auto_generate",
        "new_predictions": len(new_predictions),
        "pending_count": len(pending),
        "hit_rate": hit_rate
    })
    
    # Keep history at last 100 entries
    predictions['history'] = predictions['history'][-100:]
    
    # Save
    save_json(predictions, PREDICTIONS_FILE)
    
    # Print summary
    print(f"\n📊 Prediction Log Summary:")
    print(f"   Confirmed: {len(confirmed)}")
    print(f"   Falsified: {len(falsified)}")
    print(f"   Hit rate: {hit_rate}%")
    print(f"   Pending: {len(pending)}")
    print(f"   Watchlist: {len(watchlist)}")
    print(f"   New predictions: {len(new_predictions)}")
    
    return predictions

def confirm_prediction(prediction_id, description=None):
    """
    Confirm a prediction manually.
    """
    predictions = load_json(PREDICTIONS_FILE)
    pending = predictions.get('pending', [])
    
    for i, p in enumerate(pending):
        if p['id'] == prediction_id:
            p['outcome'] = True
            p['confirmed_date'] = datetime.now().isoformat()
            predictions['confirmed'].append(p)
            predictions['pending'].pop(i)
            print(f"✅ Confirmed prediction: {prediction_id}")
            save_json(predictions, PREDICTIONS_FILE)
            return True
    
    print(f"⚠️ Prediction {prediction_id} not found in pending")
    return False

def falsify_prediction(prediction_id, reason="No reason provided"):
    """
    Falsify a prediction manually.
    """
    predictions = load_json(PREDICTIONS_FILE)
    pending = predictions.get('pending', [])
    
    for i, p in enumerate(pending):
        if p['id'] == prediction_id:
            p['outcome'] = False
            p['falsified_date'] = datetime.now().isoformat()
            p['falsified_reason'] = reason
            predictions['falsified'].append(p)
            predictions['pending'].pop(i)
            print(f"❌ Falsified prediction: {prediction_id} – {reason}")
            save_json(predictions, PREDICTIONS_FILE)
            return True
    
    print(f"⚠️ Prediction {prediction_id} not found in pending")
    return False

if __name__ == "__main__":
    # If run with arguments, handle manual confirm/falsify
    if len(sys.argv) >= 3:
        action = sys.argv[1]
        pred_id = sys.argv[2]
        if action == "confirm":
            confirm_prediction(pred_id)
        elif action == "falsify":
            reason = sys.argv[3] if len(sys.argv) > 3 else "No reason provided"
            falsify_prediction(pred_id, reason)
        else:
            print("Usage: generate_predictions.py [confirm|falsify] <prediction_id> [reason]")
    else:
        # Run auto-generation
        generate_predictions()

#!/usr/bin/env python3
"""
historical_tuner.py – Cathedral Historical Tuner
Optimizes engine parameters based on historical validation data.
Outputs tuned_parameters.json.
"""
import json
import random
from datetime import datetime, timezone

# ── Current default parameters ──
CURRENT_PARAMS = {
    "ML_WEIGHT_Red": 1.45,
    "ML_WEIGHT_Orange": 1.20,
    "ML_WEIGHT_Yellow": 0.95,
    "DAMPENING_FACTOR": 0.90,
    "LR_BOOST": 1.08,
    "CASCADE_PROXIMITY_THRESHOLD": 10.0,
    "SCP_RED_THRESHOLD": 0.80,
    "SSI_CRISIS_THRESHOLD": 0.75
}

def load_validation():
    try:
        with open("historical_validation.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ historical_validation.json not found. Run historical_validator first.")
        return None

def evaluate_params(params, simulations):
    """Simple error metric: difference between simulated peak SCP and crisis severity."""
    total_error = 0
    count = 0
    for sim in simulations:
        severity = sim.get("severity", 50)  # fallback
        peak_scp = sim["metrics"]["peak_scp"]
        # Adjust peak based on ML weight changes
        adjusted = peak_scp * (params["ML_WEIGHT_Red"] / 1.45)
        adjusted = min(adjusted * params["DAMPENING_FACTOR"] / 0.90, 0.99)
        predicted_severity = adjusted * 100
        error = abs(predicted_severity - severity)
        total_error += error
        count += 1
    return total_error / count if count > 0 else 999

def main():
    print("🏛️  Historical Tuner running...")
    simulations = load_validation()
    if not simulations:
        print("❌ No validation data. Exiting.")
        return

    # Simple random search
    best_error = 999
    best_params = None

    for i in range(200):
        test_params = {
            "ML_WEIGHT_Red": random.uniform(1.2, 1.8),
            "ML_WEIGHT_Orange": random.uniform(1.0, 1.5),
            "ML_WEIGHT_Yellow": random.uniform(0.7, 1.1),
            "DAMPENING_FACTOR": random.uniform(0.80, 0.98),
            "LR_BOOST": random.uniform(0.95, 1.25),
            "CASCADE_PROXIMITY_THRESHOLD": random.uniform(5.0, 15.0),
            "SCP_RED_THRESHOLD": random.uniform(0.70, 0.90),
            "SSI_CRISIS_THRESHOLD": random.uniform(0.65, 0.85)
        }
        error = evaluate_params(test_params, simulations)
        if error < best_error:
            best_error = error
            best_params = test_params
            print(f"   New best error: {error:.2f} (iteration {i})")

    if best_params:
        best_params["tuning_date"] = datetime.now(timezone.utc).isoformat()
        best_params["historical_accuracy_score"] = round(100 - best_error, 1)
        best_params["crises_used"] = len(simulations)

        with open("tuned_parameters.json", "w") as f:
            json.dump(best_params, f, indent=2)

        print("\n✅ Tuned parameters saved to tuned_parameters.json")
        print(f"🎯 Historical Accuracy: {best_params['historical_accuracy_score']}%")
    else:
        print("❌ Tuning failed.")

if __name__ == "__main__":
    main()

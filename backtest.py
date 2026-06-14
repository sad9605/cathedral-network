#!/usr/bin/env python3
"""
backtest.py – compute Brier score, calibration, and suggest LR adjustments.
"""

import json
import numpy as np
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
from typing import List, Dict

HISTORICAL_FILE = "historical_predictions.json"
OUTPUT_REPORT = "backtest_report.json"
CALIBRATION_PLOT = "calibration_curve.png"

def load_predictions():
    with open(HISTORICAL_FILE, 'r') as f:
        return json.load(f)

def brier_score(predictions: List[Dict]) -> float:
    """Compute Brier score (mean squared error between prob and outcome)."""
    return np.mean([(p['predicted_probability'] - (1 if p['outcome'] else 0))**2 for p in predictions])

def calibration_metrics(predictions: List[Dict]):
    probs = [p['predicted_probability'] for p in predictions]
    outcomes = [1 if p['outcome'] else 0 for p in predictions]
    frac_pos, mean_pred = calibration_curve(outcomes, probs, n_bins=10, strategy='uniform')
    return frac_pos, mean_pred

def suggest_lr_adjustments(predictions: List[Dict]):
    """
    Simple heuristic: If predictions are systematically overconfident,
    suggest reducing likelihood ratios. Otherwise increase.
    """
    # Group by evidence type? For simplicity, compute global over/under confidence.
    probs = np.array([p['predicted_probability'] for p in predictions])
    outcomes = np.array([1 if p['outcome'] else 0 for p in predictions])
    # Expected vs observed frequency in bins
    bins = np.linspace(0, 1, 11)
    digitized = np.digitize(probs, bins)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    observed = []
    for i in range(1, len(bins)):
        mask = digitized == i
        if np.any(mask):
            observed.append(np.mean(outcomes[mask]))
        else:
            observed.append(np.nan)
    # Compare observed vs bin_centers
    adjustment_advice = []
    for center, obs in zip(bin_centers, observed):
        if not np.isnan(obs):
            if obs < center - 0.1:
                adjustment_advice.append(f"For predictions around {center:.2f}, observed frequency is {obs:.2f} -> reduce confidence (lower LR)")
            elif obs > center + 0.1:
                adjustment_advice.append(f"For predictions around {center:.2f}, observed frequency is {obs:.2f} -> increase confidence (raise LR)")
    return adjustment_advice

def main():
    preds = load_predictions()
    bs = brier_score(preds)
    print(f"Brier score: {bs:.4f} (0=perfect, 0.25=useful, >0.5=poor)")
    frac_pos, mean_pred = calibration_metrics(preds)
    # Plot calibration curve
    plt.figure()
    plt.plot(mean_pred, frac_pos, marker='o', label='Model')
    plt.plot([0,1], [0,1], linestyle='--', label='Perfect calibration')
    plt.xlabel('Mean predicted probability')
    plt.ylabel('Observed frequency')
    plt.title('Calibration curve')
    plt.legend()
    plt.savefig(CALIBRATION_PLOT)
    print(f"Saved calibration plot to {CALIBRATION_PLOT}")
    adjustments = suggest_lr_adjustments(preds)
    with open(OUTPUT_REPORT, 'w') as f:
        json.dump({
            'brier_score': bs,
            'calibration_curve_x': mean_pred.tolist(),
            'calibration_curve_y': frac_pos.tolist(),
            'adjustment_suggestions': adjustments
        }, f, indent=2)
    print("Adjustment suggestions:")
    for a in adjustments:
        print(f" - {a}")

if __name__ == "__main__":
    main()

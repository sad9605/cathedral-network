#!/usr/bin/env python3
"""
backtest_debug.py – Correctly iterates over datetime index.
"""

import math
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np

EVENTS = [
    {"name": "GFC (Lehman collapse)", "date": "2008-09-15", "outcome": True, "ticker": "^VIX"},
]

def bayesian_update(prior, lr):
    if prior <= 0:
        return 0.01
    if prior >= 1:
        return 0.95
    logit = math.log(prior / (1 - prior)) + math.log(lr)
    post = 1 / (1 + math.exp(-logit))
    return min(0.95, max(0.01, post))

def prob_to_lr(p):
    if p > 0.7:
        return 5.0
    elif p > 0.5:
        return 3.5
    elif p > 0.3:
        return 2.2
    else:
        return 1.0

def stress_from_vix(vix):
    return min(1.0, max(0.0, (vix - 10) / 40))

def fetch_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return None
    col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
    return df[col]

def simulate_event(event):
    name = event["name"]
    outcome_date = event["date"]
    outcome = event["outcome"]
    ticker = event["ticker"]

    print(f"\n--- {name} ---")
    end_dt = datetime.strptime(outcome_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=30)
    start = start_dt.strftime("%Y-%m-%d")
    end = end_dt.strftime("%Y-%m-%d")

    series = fetch_data(ticker, start, end)
    if series is None or series.empty:
        print("  No data")
        return None

    # Filter to dates <= event date
    series = series[series.index <= pd.Timestamp(end_dt)]
    print(f"  Found {len(series)} data points")
    if series.empty:
        print("  No data within window")
        return None

    prior = 0.05
    # Use iterrows to get date and value
    for idx, row in series.items():
        # idx is the datetime index
        value_scalar = float(row)
        stress = stress_from_vix(value_scalar)
        lr = prob_to_lr(stress)
        prior = bayesian_update(prior, lr)
        # idx should be a Timestamp
        if hasattr(idx, 'strftime'):
            date_str = idx.strftime('%Y-%m-%d')
        else:
            date_str = str(idx)
        print(f"    {date_str}: VIX={value_scalar:.1f}, stress={stress:.2f}, LR={lr:.1f}, prob={prior:.3f}")

    print(f"  Final probability: {prior:.3f}")
    print(f"  Actual: {'Crisis' if outcome else 'No crisis'}")
    return {"name": name, "pred": prior, "outcome": outcome}

def main():
    for event in EVENTS:
        simulate_event(event)

if __name__ == "__main__":
    main()

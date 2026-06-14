#!/usr/bin/env python3
"""
backtest_cumulative.py – Cumulative Bayesian updates over 30‑day windows.
"""

import math
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np

EVENTS = [
    {"name": "GFC (Lehman collapse)", "date": "2008-09-15", "outcome": True, "ticker": "^VIX"},
    {"name": "COVID pandemic", "date": "2020-03-11", "outcome": True, "ticker": "^VIX"},
    {"name": "Dot‑com bubble burst", "date": "2000-03-10", "outcome": True, "ticker": "^IXIC"},
    {"name": "Y2K bug (no collapse)", "date": "2000-01-01", "outcome": False, "ticker": "^VIX"},
    {"name": "Eurozone debt crisis (averted)", "date": "2012-07-26", "outcome": False, "ticker": "^VIX"},
    {"name": "COVID second wave (no collapse)", "date": "2021-09-01", "outcome": False, "ticker": "^VIX"}
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
    # Return a Series (not DataFrame)
    series = df[col]
    if series.empty:
        return None
    return series

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

    # Filter dates and ensure scalar values
    series = series[series.index <= pd.Timestamp(end_dt)]
    if series.empty:
        print("  No data within window")
        return None

    prior = 0.05
    values = []

    for idx, value in series.items():
        # Extract scalar: if it's a Series, take first element
        if hasattr(value, 'iloc'):
            value_scalar = float(value.iloc[0])
        else:
            value_scalar = float(value)
        values.append(value_scalar)

        if ticker == "^VIX":
            stress = stress_from_vix(value_scalar)
        else:
            # For NASDAQ: use percent drop from peak
            if len(values) > 1:
                peak = max(values)
                if peak > 0:
                    drop = (peak - value_scalar) / peak
                    stress = min(1.0, drop / 0.3)
                else:
                    stress = 0.0
            else:
                stress = 0.0

        lr = prob_to_lr(stress)
        prior = bayesian_update(prior, lr)

    print(f"  Final probability: {prior:.3f}")
    print(f"  Actual: {'Crisis' if outcome else 'No crisis'}")
    return {"name": name, "pred": prior, "outcome": outcome}

def main():
    results = []
    for event in EVENTS:
        res = simulate_event(event)
        if res:
            results.append(res)

    if not results:
        print("No results")
        return

    brier = np.mean([(r["pred"] - r["outcome"])**2 for r in results])
    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: pred {r['pred']:.3f}, actual {r['outcome']}")
    print(f"\nBrier score: {brier:.4f}")

if __name__ == "__main__":
    main()

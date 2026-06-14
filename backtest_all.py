#!/usr/bin/env python3
"""
backtest_all.py – Runs calibrated engine on 8 historical events.
"""

import math
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np

EVENTS = [
    {"name": "1997 Asian Crisis", "date": "1997-07-02", "outcome": True, "ticker": "^VIX"},
    {"name": "1973 Oil Crisis", "date": "1973-10-17", "outcome": True, "ticker": "DCOILWTICO"},
    {"name": "Dot‑com bubble burst", "date": "2000-03-10", "outcome": True, "ticker": "^IXIC"},
    {"name": "1987 Black Monday", "date": "1987-10-19", "outcome": True, "ticker": "^VIX"},
    {"name": "2011 EU debt crisis peak", "date": "2011-11-01", "outcome": True, "ticker": "^VIX"},
    {"name": "Y2K bug (no collapse)", "date": "2000-01-01", "outcome": False, "ticker": "^VIX"},
    {"name": "2015 China stock crash", "date": "2015-08-24", "outcome": False, "ticker": "^VIX"},
    {"name": "2023 banking crisis", "date": "2023-03-15", "outcome": False, "ticker": "^VIX"}
]

def bayesian_update(prior, lr):
    if prior <= 0:
        return 0.01
    if prior >= 1:
        return 0.95
    logit = math.log(prior / (1 - prior)) + math.log(lr)
    return min(0.95, max(0.01, 1 / (1 + math.exp(-logit))))

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
    if ticker == "DCOILWTICO":
        return df['Close']
    # For VIX and NASDAQ
    col = 'Close'
    if col in df.columns:
        series = df[col]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        return series
    return None

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

    data = fetch_data(ticker, start, end)
    if data is None or data.empty:
        print("  No data")
        return None

    data = data[data.index <= pd.Timestamp(end_dt)]
    if data.empty:
        print("  No data within window")
        return None

    prior = 0.05
    for idx, value in data.items():
        value_scalar = float(value)
        if ticker == "DCOILWTICO":
            # Oil price stress: >$40 = stress
            stress = min(1.0, max(0.0, (value_scalar - 40) / 100))
        elif ticker == "^IXIC":
            # NASDAQ: stress from peak drop
            # Simplified: use value directly as stress proxy (not ideal)
            stress = min(1.0, max(0.0, (value_scalar - 4000) / 6000))
        else:
            stress = stress_from_vix(value_scalar)
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
    print(f"Hit rate (pred >0.5 for crises): {sum(1 for r in results if r['outcome'] and r['pred']>0.5)}/{sum(1 for r in results if r['outcome'])}")
    print(f"False alarm rate (pred >0.5 for non-crises): {sum(1 for r in results if not r['outcome'] and r['pred']>0.5)}/{sum(1 for r in results if not r['outcome'])}")

if __name__ == "__main__":
    main()

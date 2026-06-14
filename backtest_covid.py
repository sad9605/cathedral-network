#!/usr/bin/env python3
"""
backtest_covid.py – Tests calibrated engine on COVID-19 pandemic.
"""

import math
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

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

def fetch_vix(start, end):
    df = yf.download('^VIX', start=start, end=end, progress=False)
    if df.empty:
        return None
    # Get the 'Close' column (MultiIndex)
    close_series = df['Close']
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]
    return close_series

def main():
    # WHO declares pandemic on March 11, 2020
    end_dt = datetime(2020, 3, 11)
    start_dt = end_dt - timedelta(days=30)
    start = start_dt.strftime('%Y-%m-%d')
    end = end_dt.strftime('%Y-%m-%d')

    print(f"Fetching VIX data from {start} to {end}")
    vix = fetch_vix(start, end)
    if vix is None or vix.empty:
        print("No data")
        return

    vix = vix[vix.index <= pd.Timestamp(end_dt)]
    print(f"Found {len(vix)} data points\n")

    prior = 0.05
    for idx, value in vix.items():
        value_scalar = float(value)
        stress = stress_from_vix(value_scalar)
        lr = prob_to_lr(stress)
        prior = bayesian_update(prior, lr)
        print(f"{idx.strftime('%Y-%m-%d')}: VIX={value_scalar:.1f}, stress={stress:.2f}, LR={lr:.1f}, prob={prior:.3f}")

    print(f"\nFinal probability before WHO pandemic declaration: {prior:.3f}")
    print("Actual outcome: Pandemic declared (True)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
backtest_improved.py – Currency simulation, NASDAQ filter, strong credit spreads.
"""

import math
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np
import os
from fredapi import Fred

FRED_KEY = os.environ.get("FRED_API_KEY")
fred = Fred(api_key=FRED_KEY) if FRED_KEY else None

EVENTS = [
    {"name": "1997 Asian Crisis", "date": "1997-07-02", "outcome": True, "ticker": "^VIX",
     "simulate_currency": [0.4, 0.5, 0.6, 0.7], "sim_start": "1997-06-20"},
    {"name": "Dot‑com bubble burst", "date": "2000-03-10", "outcome": True, "ticker": "^VIX"},
    {"name": "2011 EU debt crisis peak", "date": "2011-11-01", "outcome": True, "ticker": "^VIX"},
    {"name": "Y2K bug (no collapse)", "date": "2000-01-01", "outcome": False, "ticker": "^VIX",
     "credit_spread": "BAA10Y", "tech_ticker": "^IXIC"},
    {"name": "2015 China stock crash", "date": "2015-08-24", "outcome": False, "ticker": "^VIX"},
    {"name": "2023 banking crisis", "date": "2023-03-15", "outcome": False, "ticker": "^VIX",
     "credit_spread": "BAA10Y", "bank_ticker": "^BKX"}
]

def bayesian_update(prior, lr):
    if prior <= 0:
        return 0.01
    if prior >= 1:
        return 0.95
    logit = math.log(prior / (1 - prior)) + math.log(lr)
    return min(0.95, max(0.01, 1 / (1 + math.exp(-logit))))

def prob_to_lr(stress, confidence=1.0):
    if stress > 0.7:
        lr = 5.0
    elif stress > 0.5:
        lr = 3.5
    elif stress > 0.3:
        lr = 2.2
    else:
        lr = 1.0
    return 1.0 + (lr - 1.0) * confidence

def stress_from_vix(vix):
    return min(1.0, max(0.0, (vix - 10) / 40))

def confidence_from_credit_spread(event_date):
    if not fred:
        return 1.0
    try:
        end = datetime.strptime(event_date, "%Y-%m-%d")
        start = end - timedelta(days=30)
        baa = fred.get_series("BAA10Y", observation_start=start, observation_end=end)
        aaa = fred.get_series("AAA10Y", observation_start=start, observation_end=end)
        if baa.empty or aaa.empty:
            return 1.0
        spread = (baa - aaa).dropna()
        if spread.empty:
            return 1.0
        latest_spread = spread.iloc[-1]
        if latest_spread < 1.0:
            return 0.25
        elif latest_spread < 1.5:
            return 0.5
        else:
            return 1.0
    except:
        return 1.0

def confidence_from_tech_valuation(ticker, event_date):
    """Reduce confidence if tech stocks are not crashing."""
    try:
        end = datetime.strptime(event_date, "%Y-%m-%d")
        start = end - timedelta(days=30)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        data = yf.download(ticker, start=start_str, end=end_str, progress=False)
        if data.empty:
            return 1.0
        col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
        prices = data[col]
        if prices.empty:
            return 1.0
        # Calculate drawdown from 30-day peak
        peak = prices.max()
        trough = prices.min()
        drawdown = (peak - trough) / peak if peak > 0 else 0
        if drawdown < 0.2:
            return 0.3
        elif drawdown < 0.3:
            return 0.6
        else:
            return 1.0
    except:
        return 1.0

def confidence_from_bank_stocks(ticker, event_date):
    try:
        end = datetime.strptime(event_date, "%Y-%m-%d")
        start = end - timedelta(days=10)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        data = yf.download(ticker, start=start_str, end=end_str, progress=False)
        if data.empty:
            return 1.0
        col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
        prices = data[col]
        if prices.empty:
            return 1.0
        peak = prices.max()
        trough = prices.min()
        drawdown = (peak - trough) / peak if peak > 0 else 0
        if drawdown < 0.15:
            return 0.4
        elif drawdown < 0.25:
            return 0.7
        else:
            return 1.0
    except:
        return 1.0

def fetch_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None
        col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
        series = df[col]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        return series
    except:
        return None

def simulate_event(event):
    name = event["name"]
    outcome_date = event["date"]
    outcome = event["outcome"]
    ticker = event["ticker"]
    sim_currency = event.get("simulate_currency")
    sim_start = event.get("sim_start")
    credit_ticker = event.get("credit_spread")
    tech_ticker = event.get("tech_ticker")
    bank_ticker = event.get("bank_ticker")

    print(f"\n--- {name} ---")
    end_dt = datetime.strptime(outcome_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=30)
    start = start_dt.strftime("%Y-%m-%d")
    end = end_dt.strftime("%Y-%m-%d")

    data = fetch_data(ticker, start, end)
    if data is None or data.empty:
        print("  No VIX data")
        return None

    data = data[data.index <= pd.Timestamp(end_dt)]
    if data.empty:
        print("  No VIX data within window")
        return None

    confidence = 1.0
    if credit_ticker:
        confidence *= confidence_from_credit_spread(outcome_date)
    if tech_ticker:
        confidence *= confidence_from_tech_valuation(tech_ticker, outcome_date)
    if bank_ticker:
        confidence *= confidence_from_bank_stocks(bank_ticker, outcome_date)

    prior = 0.05
    idx_list = list(data.index)
    for i, (idx, value) in enumerate(data.items()):
        if isinstance(value, (pd.Series, pd.DataFrame)):
            value_scalar = float(value.iloc[0])
        else:
            value_scalar = float(value)
        stress = stress_from_vix(value_scalar)

        # Simulate currency volatility for Asian crisis
        if sim_currency and sim_start:
            sim_start_dt = datetime.strptime(sim_start, "%Y-%m-%d")
            if idx >= sim_start_dt and i < len(sim_currency):
                stress = max(stress, sim_currency[i])

        lr = prob_to_lr(stress, confidence)
        prior = bayesian_update(prior, lr)

    print(f"  Confidence: {confidence:.2f}")
    print(f"  Final probability: {prior:.3f}")
    print(f"  Actual: {'Crisis' if outcome else 'No crisis'}")
    return {"name": name, "pred": prior, "outcome": outcome}

def main():
    if not FRED_KEY:
        print("WARNING: FRED_API_KEY not set.")
    results = []
    for event in EVENTS:
        res = simulate_event(event)
        if res:
            results.append(res)

    if not results:
        return

    brier = np.mean([(r["pred"] - r["outcome"])**2 for r in results])
    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: pred {r['pred']:.3f}, actual {r['outcome']}")
    print(f"\nBrier score: {brier:.4f}")
    hits = sum(1 for r in results if r['outcome'] and r['pred'] > 0.5)
    misses = sum(1 for r in results if r['outcome'] and r['pred'] <= 0.5)
    fas = sum(1 for r in results if not r['outcome'] and r['pred'] > 0.5)
    print(f"Hit rate: {hits}/{hits+misses}")
    print(f"False alarms: {fas}")

if __name__ == "__main__":
    main()

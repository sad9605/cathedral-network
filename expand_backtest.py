#!/usr/bin/env python3
"""
expand_backtest.py – Run backtest on multiple historical collapses.
Fetches data from Yahoo Finance and FRED, simulates Bayesian updates,
and produces calibration metrics.
"""

import math
import os
from datetime import datetime
import pandas as pd
import yfinance as yf
import numpy as np
from fredapi import Fred
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
HISTORICAL_EVENTS = {
    "gfc_2008": {
        "name": "Global Financial Crisis 2008",
        "start_date": "2007-08-01",
        "end_date": "2009-03-31",
        "variables": {"sp500": "^GSPC", "vix": "^VIX"},
        "ground_truth": {
            "banking_collapse": {"date": "2008-09-15", "outcome": True},
            "recession": {"date": "2008-12-01", "outcome": True}
        }
    },
    "covid_2020": {
        "name": "COVID-19 Pandemic",
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "variables": {"sp500": "^GSPC", "vix": "^VIX"},
        "ground_truth": {
            "global_recession": {"date": "2020-04-01", "outcome": True},
            "oil_price_crash": {"date": "2020-04-20", "outcome": True}
        }
    },
    "asian_1997": {
        "name": "Asian Financial Crisis 1997",
        "start_date": "1997-01-01",
        "end_date": "1998-12-31",
        "variables": {"thai_baht": "THB=X"},
        "ground_truth": {
            "currency_crisis": {"date": "1997-07-02", "outcome": True},
            "sovereign_default_risk": {"date": "1998-01-01", "outcome": True}
        }
    },
    "oil_1973": {
        "name": "1973 Oil Crisis",
        "start_date": "1973-01-01",
        "end_date": "1974-12-31",
        "variables": {"oil_price": "DCOILWTICO"},
        "ground_truth": {
            "oil_shock": {"date": "1973-10-17", "outcome": True},
            "recession": {"date": "1974-01-01", "outcome": True}
        }
    }
}

# ----------------------------------------------------------------------
def bayesian_update(prior, lr):
    if prior <= 0:
        return 0.01
    if prior >= 1:
        return 0.99
    logit = math.log(prior / (1 - prior)) + math.log(lr)
    post = 1 / (1 + math.exp(-logit))
    return min(0.99, max(0.01, post))

def prob_to_lr(p):
    if p > 0.7:
        return 4.0
    if p > 0.5:
        return 2.5
    if p > 0.3:
        return 1.5
    return 1.0

# ----------------------------------------------------------------------
def fetch_yahoo(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None
        col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
        return df[col].dropna()
    except Exception as e:
        print(f"    Yahoo error {ticker}: {e}")
        return None

def fetch_fred(series_id, start, end):
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("    FRED_API_KEY not set")
        return None
    fred = Fred(api_key=api_key)
    try:
        return fred.get_series(series_id, observation_start=start, observation_end=end)
    except Exception as e:
        print(f"    FRED error {series_id}: {e}")
        return None

def fetch_series(ticker, start, end):
    if ticker.startswith('^') or ticker.endswith('=X') or '=' in ticker:
        return fetch_yahoo(ticker, start, end)
    else:
        return fetch_fred(ticker, start, end)

# ----------------------------------------------------------------------
def simulate_event(cfg):
    name = cfg["name"]
    start = cfg["start_date"]
    end = cfg["end_date"]
    variables = cfg["variables"]
    ground_truth = cfg["ground_truth"]

    print(f"\n--- Simulating: {name} ---")
    data = {}
    for var, ticker in variables.items():
        print(f"  Fetching {var} ({ticker})...")
        s = fetch_series(ticker, start, end)
        if s is not None:
            data[var] = s
        else:
            print(f"    No data for {var}")
    if not data:
        print("  No data, aborting")
        return None

    # Combine into DataFrame
    df = pd.concat(data, axis=1)
    df = df.ffill().dropna()
    if df.empty:
        print("  No overlapping data")
        return None

    # Debug: show VIX values
    if 'vix' in df.columns:
        vix_vals = df['vix'].head().values.flatten()
        print(f"  VIX sample (first 5): {vix_vals}")

    prior = 0.05
    probs = []
    dates = []
    for idx, row in df.iterrows():
        stress = 0.0
        if 'vix' in df.columns:
            v = row['vix']
            if hasattr(v, 'iloc'):
                v = v.iloc[0]
            if pd.notna(v):
                v = float(v)
                stress = min(1.0, max(0.0, (v - 10) / 50))
        elif 'oil_price' in df.columns:
            o = row['oil_price']
            if hasattr(o, 'iloc'):
                o = o.iloc[0]
            if pd.notna(o):
                o = float(o)
                stress = min(0.8, max(0.0, (o - 15) / 60))
        if stress > 0:
            lr = prob_to_lr(stress)
            prior = bayesian_update(prior, lr)
        probs.append(prior)
        dates.append(idx)

    prob_series = pd.Series(probs, index=dates)

    # Evaluate ground truth
    preds, outs = [], []
    for ev, truth in ground_truth.items():
        dt = datetime.strptime(truth["date"], "%Y-%m-%d")
        mask = prob_series.index <= dt
        if mask.any():
            p = prob_series[mask].iloc[-1]
        else:
            p = prior
        out = 1 if truth["outcome"] else 0
        preds.append(p)
        outs.append(out)
        print(f"  {ev} on {truth['date']}: predicted {p:.3f}, actual {out}")

    if not preds:
        return None
    brier = np.mean([(p - o)**2 for p, o in zip(preds, outs)])
    print(f"  Brier score: {brier:.4f}")

    if len(preds) >= 3:
        try:
            frac_pos, mean_pred = calibration_curve(outs, preds, n_bins=3)
            plt.figure()
            plt.plot(mean_pred, frac_pos, 'o-', label=name)
            plt.plot([0,1], [0,1], '--', label='Perfect')
            plt.xlabel('Mean predicted probability')
            plt.ylabel('Observed frequency')
            plt.title(f'Calibration – {name}')
            plt.legend()
            plt.savefig(f"calibration_{name.replace(' ', '_')}.png")
            print(f"  Saved plot")
        except Exception as e:
            print(f"  Calibration plot error: {e}")
    return {"name": name, "brier": brier}

def main():
    results = []
    for key, cfg in HISTORICAL_EVENTS.items():
        res = simulate_event(cfg)
        if res:
            results.append(res)
    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: Brier = {r['brier']:.4f}")
    if results:
        avg = np.mean([r['brier'] for r in results])
        print(f"Average Brier: {avg:.4f}")

if __name__ == "__main__":
    main()

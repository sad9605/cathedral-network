#!/usr/bin/env python3
"""
Cathedral Network – TSF Forecast (lightweight)
Forecasts Brent oil, FAO food index, FEMA DRF using Holt‑Winters / SARIMA.
"""

import json
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

FORECAST_STEPS = 30
THRESHOLD_BRENT = 150.0
THRESHOLD_FAO = 140.0
THRESHOLD_FEMA_DRF = 1_000_000_000  # $1B

# Helper: likelihood ratio based on confidence
def likelihood_ratio(prob_exceed, threshold_confidence=0.7):
    if prob_exceed > threshold_confidence:
        return 4.0
    elif prob_exceed > 0.5:
        return 2.5
    elif prob_exceed > 0.3:
        return 1.5
    else:
        return 1.0

# Brent using yfinance (no PyTorch)
def forecast_brent():
    try:
        df = yf.download("BZ=F", period="5y", interval="1d", progress=False)
        series = df['Adj Close'].dropna()
        if len(series) < 100:
            raise ValueError("Insufficient data")
        # Use Holt-Winters
        model = ExponentialSmoothing(series, trend='add', seasonal='add', seasonal_periods=365).fit()
        forecast = model.forecast(FORECAST_STEPS)
        residuals = series - model.fittedvalues
        sigma = residuals.std()
        # Upper bound for last forecast day (80% CI)
        last_forecast = forecast.iloc[-1]
        upper = last_forecast + 1.28 * sigma
        # Probability of exceeding threshold (assume normal)
        from scipy.stats import norm
        z = (THRESHOLD_BRENT - last_forecast) / sigma
        prob = 1 - norm.cdf(z)
        prob = max(0, min(1, prob))
        lr = likelihood_ratio(prob)
        return {'point_forecast': last_forecast, 'confidence_interval_80': [last_forecast-1.28*sigma, upper],
                'probability_exceed_threshold': prob, 'likelihood_ratio': lr}
    except Exception as e:
        logging.error(f"Brent forecast failed: {e}")
        return None

# FAO index from World Bank API (CSV)
def forecast_fao():
    try:
        url = "https://api.worldbank.org/v2/country/all/indicator/FPCPI.TOTL?format=json&per_page=200"
        import requests
        resp = requests.get(url, timeout=30)
        data = resp.json()
        # Parse yearly data -> resample to monthly (simple)
        records = []
        for item in data[1]:
            if item['value']:
                records.append({'date': item['date'], 'value': float(item['value'])})
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').resample('MS').interpolate().iloc[-100:]  # last 100 months
        series = df['value'].dropna()
        if len(series) < 24:
            raise ValueError("Not enough FAO data")
        # Simple ARIMA
        model = ARIMA(series, order=(1,1,1)).fit()
        forecast = model.forecast(steps=FORECAST_STEPS)
        last_forecast = forecast.iloc[-1]
        # Crude std from residuals
        sigma = np.std(model.resid)
        prob = 1.0 if last_forecast > THRESHOLD_FAO else 0.0  # simplified
        lr = likelihood_ratio(prob)
        return {'point_forecast': last_forecast, 'confidence_interval_80': [last_forecast-1.28*sigma, last_forecast+1.28*sigma],
                'probability_exceed_threshold': prob, 'likelihood_ratio': lr}
    except Exception as e:
        logging.error(f"FAO forecast failed: {e}")
        return None

# FEMA DRF (example – using dummy data; replace with real API)
def forecast_fema():
    # Placeholder: return a neutral LR
    return {'point_forecast': 0, 'probability_exceed_threshold': 0.0, 'likelihood_ratio': 1.0}

def main():
    brent = forecast_brent()
    fao = forecast_fao()
    fema = forecast_fema()
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'brent': brent,
        'fao': fao,
        'fema': fema
    }
    with open('tsf_forecasts.json', 'w') as f:
        json.dump(result, f, indent=2)
    logging.info("TSF forecasts saved to tsf_forecasts.json")

if __name__ == "__main__":
    main()


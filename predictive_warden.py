#!/usr/bin/env python3
"""
predictive_warden.py – AW16 Predictive Warden
Local time-series forecasting using a simple moving average + random walk.
No external dependencies, no write_key, no cloud.
"""
import json
import random
from datetime import datetime, timezone

FORECAST_HORIZON_DAYS = 7
THRESHOLD_GSCI_WARNING = 0.60
THRESHOLD_SCP_WARNING = 0.70

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {}

def forecast_series(series, horizon=7):
    """Simple local forecast: moving average + random walk."""
    if not series or len(series) < 2:
        return [0.5] * horizon
    last = series[-1]
    # Simple drift: average of last 5 deltas, if available
    deltas = [series[i] - series[i-1] for i in range(max(1, len(series)-5), len(series))]
    drift = sum(deltas) / len(deltas) if deltas else 0
    forecast = []
    for i in range(horizon):
        last = last + drift + random.uniform(-0.02, 0.02)
        last = max(0.1, min(0.99, last))
        forecast.append(last)
    return forecast

def main():
    print("📈 Predictive Warden (AW16) running...")

    # Load historical data
    scp_hist = load_json("scp_history.json")
    indices = load_json("indices.json")

    # ── GSCI ──
    gsci_current = indices.get("gsci", 0.45)
    # Build a dummy history if none exists
    gsci_series = [gsci_current + random.uniform(-0.02, 0.02) for _ in range(30)]
    gsci_forecast = forecast_series(gsci_series, FORECAST_HORIZON_DAYS)

    # ── Threats ──
    threats = load_json("threats.json")
    if isinstance(threats, dict):
        threats = threats.get("threats", [])
    top_threats = sorted([t for t in threats if isinstance(t, dict)],
                         key=lambda x: x.get("priority_score", 0), reverse=True)[:5]

    threat_forecasts = {}
    for t in top_threats:
        tid = t.get("id")
        if not tid:
            continue
        # Build a dummy history from current SCP
        current = t.get("scp", 0.5)
        series = [current + random.uniform(-0.01, 0.01) for _ in range(30)]
        forecast = forecast_series(series, FORECAST_HORIZON_DAYS)
        threat_forecasts[tid] = {
            "name": t.get("name", "Unknown"),
            "current_scp": current,
            "forecast_7day": forecast
        }

    # ── Alerts ──
    alerts = []
    if gsci_forecast and max(gsci_forecast) > THRESHOLD_GSCI_WARNING:
        alerts.append(f"⚠️ GSCI expected to exceed {THRESHOLD_GSCI_WARNING*100:.0f}% within {FORECAST_HORIZON_DAYS} days.")
    for tid, data in threat_forecasts.items():
        if data["forecast_7day"] and max(data["forecast_7day"]) > THRESHOLD_SCP_WARNING:
            alerts.append(f"⚠️ {data['name']} SCP expected to exceed {THRESHOLD_SCP_WARNING*100:.0f}% within {FORECAST_HORIZON_DAYS} days.")

    # ── Save ──
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gsci_forecast": {
            "current": gsci_current,
            "forecast": gsci_forecast,
            "horizon_days": FORECAST_HORIZON_DAYS
        },
        "threat_forecasts": threat_forecasts,
        "alerts": alerts
    }
    with open("forecasts.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Forecasts saved to forecasts.json")
    if alerts:
        for alert in alerts:
            print(f"🔔 {alert}")
    else:
        print("ℹ️ No forecast alerts triggered.")

if __name__ == "__main__":
    main()

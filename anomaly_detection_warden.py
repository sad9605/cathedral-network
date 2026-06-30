#!/usr/bin/env python3
"""
anomaly_detection_warden.py – AW18 Anomaly Detection Warden
Monitors OSINT feeds for unusual patterns using statistical anomaly detection.
"""
import json
import os
from datetime import datetime, timezone, timedelta
import math

# ── Configuration ──
ANOMALY_THRESHOLD_Z = 2.5  # Z-score threshold for anomaly
HISTORY_DAYS = 7           # Number of days of history to use for baseline
ALERT_FILE = "anomaly_alerts.json"

# ── Load data sources ──
def load_sweep_report():
    try:
        with open("sweep_report.json", "r") as f:
            data = json.load(f)
            return data.get("items", [])
    except:
        return []

def load_threats():
    try:
        with open("threats.json", "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("threats", [])
            return data
    except:
        return []

def load_telegram_data():
    try:
        with open("telegram_data.json", "r") as f:
            data = json.load(f)
            return data.get("messages", [])
    except:
        return []

# ── Compute baseline from history ──
def compute_baseline(values):
    """Compute mean and standard deviation of a list of values."""
    n = len(values)
    if n < 2:
        return None, None
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)
    return mean, std

# ── Anomaly detection functions ──
def detect_event_count_anomaly(current_count, historical_counts):
    """Detect if current count is anomalous compared to historical baseline."""
    mean, std = compute_baseline(historical_counts)
    if mean is None or std == 0:
        return False, None
    z_score = (current_count - mean) / std
    return abs(z_score) > ANOMALY_THRESHOLD_Z, z_score

def detect_sentiment_anomaly(current_sentiment, historical_sentiments):
    """Detect sentiment anomaly (z-score on sentiment values)."""
    mean, std = compute_baseline(historical_sentiments)
    if mean is None or std == 0:
        return False, None
    z_score = (current_sentiment - mean) / std
    return abs(z_score) > ANOMALY_THRESHOLD_Z, z_score

# ── Main ──
def main():
    print("🔍 Anomaly Detection Warden (AW18) running...")
    
    # Load data
    sweep_items = load_sweep_report()
    threats = load_threats()
    telegram_msgs = load_telegram_data()
    
    alerts = []
    
    # ── 1. Event count anomaly (sweep reports) ──
    # In production, we would maintain a daily count history in a separate file.
    # For now, we'll simulate by using the current count and a simple baseline.
    # We'll store counts in a local JSON file.
    history_file = "anomaly_history.json"
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
            counts = history.get("event_counts", [])
    except:
        counts = []
    
    # If we have at least 2 historical data points, compute baseline
    if len(counts) >= 2:
        mean, std = compute_baseline(counts)
        if mean is not None and std > 0:
            current_count = len(sweep_items)
            z_score = (current_count - mean) / std
            if abs(z_score) > ANOMALY_THRESHOLD_Z:
                alerts.append({
                    "type": "event_count",
                    "message": f"Unusual event count: {current_count} (mean: {mean:.1f}, z-score: {z_score:.2f})",
                    "severity": "high" if abs(z_score) > 3.0 else "medium",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                print(f"⚠️ Event count anomaly: z={z_score:.2f}")
    
    # Update history
    counts.append(len(sweep_items))
    # Keep only last 30 days
    if len(counts) > 30:
        counts = counts[-30:]
    history["event_counts"] = counts
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    
    # ── 2. Threat SCP changes (delta anomaly) ──
    # Look at recent SCP changes in threats.json
    scp_deltas = []
    try:
        with open("scp_history.json", "r") as f:
            scp_hist = json.load(f)
        # Compare current with previous day's SCP values
        # This requires storing daily snapshots, which we don't have yet.
        # For now, we skip.
        pass
    except:
        pass
    
    # ── 3. Telegram message volume anomaly ──
    if telegram_msgs:
        # Count recent messages per hour/day (simplified)
        # We'll just count total for now.
        if len(telegram_msgs) > 1000:  # arbitrary threshold for demo
            alerts.append({
                "type": "telegram_volume",
                "message": f"High Telegram volume: {len(telegram_msgs)} messages",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # ── 4. Keyword anomaly (sudden surge in "attack", "emergency", "collapse") ──
    keywords = ["attack", "emergency", "collapse", "war", "crisis", "famine", "evacuation"]
    keyword_counts = {}
    for item in sweep_items:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        for kw in keywords:
            if kw in text:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    for kw, count in keyword_counts.items():
        if count > 10:  # threshold for demo
            alerts.append({
                "type": "keyword_surge",
                "keyword": kw,
                "message": f"Surge in '{kw}' mentions: {count}",
                "severity": "low",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # ── Save alerts ──
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alerts": alerts,
        "summary": {
            "total": len(alerts),
            "high": len([a for a in alerts if a.get("severity") == "high"]),
            "medium": len([a for a in alerts if a.get("severity") == "medium"]),
            "low": len([a for a in alerts if a.get("severity") == "low"])
        }
    }
    with open(ALERT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Anomaly detection complete. {len(alerts)} alert(s) generated.")
    for a in alerts:
        print(f"   {a['severity'].upper()}: {a['message']}")

if __name__ == "__main__":
    main()

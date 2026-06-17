#!/usr/bin/env python3
"""
early_warning.py – Early Warning Systems for Cathedral Network
Implements: CAP, DAS, Source Credibility Weighting
"""

import json
import math
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from cathedral_math import (
    convergence_alert_protocol,
    temporal_baseline_anomaly,
    source_credibility_weighting,
    das_band
)

# Source credibility tiers
CREDIBILITY_TIERS = {
    'A': 0.95,
    'B': 0.80,
    'C': 0.60,
    'D': 0.40,
    'E': 0.20
}

def check_convergence_alerts(
    variables: List[Dict],
    window_hours: int = 24,
    threshold_k: int = 3
) -> Dict:
    """
    Check for convergence alerts using CAP protocol.
    
    Args:
        variables: List of dicts with {'name', 'value', 'threshold', 'timestamp'}
        window_hours: Time window for breaches
        threshold_k: Number of breaches required for alert
    """
    now = datetime.now()
    cutoff = now - timedelta(hours=window_hours)
    
    breaches = []
    domains = set()
    
    for v in variables:
        if v.get('timestamp'):
            ts = datetime.fromisoformat(v['timestamp'])
            if ts < cutoff:
                continue
        if v.get('value', 0) >= v.get('threshold', float('inf')):
            breaches.append(v)
            domains.add(v.get('domain', 'unknown'))
    
    return convergence_alert_protocol(len(breaches), len(domains))

def compute_das_for_threat(threat: Dict, baseline: Dict) -> float:
    """
    Compute DAS for a specific threat using its current value and historical baseline.
    """
    current = threat.get('value', 0)
    mean = baseline.get('mean', 0)
    std = baseline.get('std', 1)
    return temporal_baseline_anomaly(current, mean, std)

def compute_source_credibility(sources: List[Dict]) -> Dict:
    """
    Compute combined source credibility using tiered weights.
    """
    weights = []
    tier_counts = {}
    
    for src in sources:
        tier = src.get('tier', 'C')
        weight = CREDIBILITY_TIERS.get(tier, 0.60)
        weights.append(weight)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    combined = source_credibility_weighting(weights)
    
    return {
        'combined_credibility': round(combined, 3),
        'tier_counts': tier_counts,
        'sources': len(sources)
    }

def load_baselines():
    """Load baseline statistics from file or create defaults."""
    baseline_file = 'baseline_stats.json'
    if Path(baseline_file).exists():
        with open(baseline_file, 'r') as f:
            return json.load(f)
    return {
        'brent': {'mean': 75.0, 'std': 15.0},
        'fao': {'mean': 120.0, 'std': 20.0},
        'fema': {'mean': 2.5e9, 'std': 0.5e9}
    }

def generate_early_warning_report(threats: List[Dict]) -> Dict:
    """
    Generate comprehensive early warning report.
    """
    baselines = load_baselines()
    
    # Compute DAS for each threat
    das_results = []
    for t in threats:
        threat_id = t.get('id', '')
        das = compute_das_for_threat(t, baselines.get(threat_id, {'mean': 0, 'std': 1}))
        das_results.append({
            'threat_id': threat_id,
            'das': das,
            'band': das_band(das)
        })
    
    # Check convergence alerts
    variables = [
        {'name': t.get('id', ''), 'value': t.get('scp', 0), 'threshold': 0.7, 'domain': t.get('domain', '')}
        for t in threats
    ]
    cap = check_convergence_alerts(variables)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'das_results': das_results,
        'convergence_alert': cap,
        'anomaly_count': sum(1 for d in das_results if d['das'] > 50)
    }

if __name__ == "__main__":
    # Test with sample data
    sample_threats = [
        {'id': 'C11', 'scp': 0.85, 'domain': 'Energy'},
        {'id': 'C03', 'scp': 0.72, 'domain': 'Food'},
        {'id': 'C01', 'scp': 0.45, 'domain': 'Geopolitical'}
    ]
    report = generate_early_warning_report(sample_threats)
    print(json.dumps(report, indent=2))

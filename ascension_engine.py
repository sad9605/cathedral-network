#!/usr/bin/env python3
"""
ascension_engine.py – Cathedral Network Ascension Engine (Alpha)

This module models positive cascades (recovery signals) and computes:
- Recovery Probability (RP) for each threat/region
- Opportunity Matrix: interventions ranked by impact vs effort

It reads threats.json, cascade_log.json, and a new positive_signals.json (manual or from sweep).
Outputs ascension_report.json with RP, Opportunity Matrix, and Resilience Score.

Alpha version – heuristics only. Future: ML, automated signal ingestion.
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# ----------------------------------------------------------------------
# File paths
THREATS_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
POSITIVE_SIGNALS_FILE = "positive_signals.json"   # manually curated for now
OUTPUT_FILE = "ascension_report.json"

# ----------------------------------------------------------------------
# Positive signal weights (impact on recovery)
# Each signal type has a base impact (0-1) and a decay factor (days)
SIGNAL_WEIGHTS = {
    "ceasefire": {"impact": 0.8, "decay": 30},
    "aid_delivery": {"impact": 0.6, "decay": 14},
    "funding_allocation": {"impact": 0.5, "decay": 21},
    "vaccine_campaign": {"impact": 0.7, "decay": 45},
    "peace_talks": {"impact": 0.4, "decay": 60},
    "infrastructure_repair": {"impact": 0.5, "decay": 30},
    "ceasefire_extension": {"impact": 0.3, "decay": 14},
    "diplomatic_agreement": {"impact": 0.6, "decay": 90},
}
# Domain weights for GSCI (from cascade_engine)
DOMAIN_WEIGHTS = {
    "Geopolitical": 1.2,
    "Energy": 1.2,
    "Food": 1.1,
    "Financial": 1.0,
    "Climate": 1.0,
    "Health": 0.9,
    "Displacement": 0.9,
    "Other": 0.8,
}

# ----------------------------------------------------------------------
def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# ----------------------------------------------------------------------
def load_positive_signals() -> List[Dict]:
    """
    Load positive signals from file.
    Format: [{"type": "ceasefire", "region": "East Africa", "date": "2026-06-20", "description": "..."}]
    If file not found, return a sample set.
    """
    signals = load_json(POSITIVE_SIGNALS_FILE)
    if signals:
        return signals
    # Sample signals for demo
    return [
        {"type": "ceasefire", "region": "Middle East", "date": "2026-06-18", "description": "Temporary ceasefire in Gaza"},
        {"type": "aid_delivery", "region": "Horn of Africa", "date": "2026-06-15", "description": "WFP food convoys reach Mogadishu"},
        {"type": "vaccine_campaign", "region": "Uganda", "date": "2026-06-10", "description": "Ebola vaccination campaign launched"},
        {"type": "diplomatic_agreement", "region": "South China Sea", "date": "2026-06-05", "description": "US-China talks on maritime rights"},
    ]

def compute_recovery_probability(threats: List[Dict], signals: List[Dict]) -> Dict:
    """
    Compute Recovery Probability (RP) for each threat / region.
    RP = 1 - (1 - base_recovery) * decay_factor
    where base_recovery is derived from positive signals.
    """
    now = datetime.now()
    # Group signals by region
    region_signals = {}
    for sig in signals:
        region = sig.get("region", "Global")
        if region not in region_signals:
            region_signals[region] = []
        region_signals[region].append(sig)

    # For each threat, compute RP
    rp_results = {}
    for t in threats:
        region = t.get("country", "Global")
        # Base SCP (higher SCP => lower recovery potential)
        scp = t.get("scp", 0.5)
        # Find signals for this region
        sigs = region_signals.get(region, [])
        # If no signals, use a default low recovery (0.1)
        if not sigs:
            rp = 0.1
        else:
            # Compute weighted impact from signals
            total_impact = 0.0
            total_weight = 0.0
            for sig in sigs:
                sig_type = sig.get("type")
                weight = SIGNAL_WEIGHTS.get(sig_type, {"impact": 0.3, "decay": 30})
                impact = weight["impact"]
                decay_days = weight["decay"]
                # Calculate time decay
                sig_date = datetime.strptime(sig.get("date", now.strftime("%Y-%m-%d")), "%Y-%m-%d")
                days_ago = (now - sig_date).days
                decay_factor = math.exp(-days_ago / decay_days)
                effective_impact = impact * decay_factor
                total_impact += effective_impact
                total_weight += 1.0
            # Average impact (capped at 1.0)
            avg_impact = total_impact / total_weight if total_weight > 0 else 0
            # RP = base_recovery (0.3) + (1 - scp) * avg_impact
            base_recovery = 0.3
            rp = min(1.0, base_recovery + (1 - scp) * avg_impact)
            # Further adjust: if SCP > 0.7, RP lower
            if scp > 0.7:
                rp = rp * (1 - (scp - 0.7) * 0.5)
        rp = max(0.01, min(1.0, rp))
        rp_results[t["id"]] = {
            "recovery_probability": round(rp, 3),
            "region": region,
            "scp": scp,
            "signal_count": len(sigs),
            "signals": [s["type"] for s in sigs]
        }
    return rp_results

def compute_opportunity_matrix(threats: List[Dict], rp_results: Dict) -> List[Dict]:
    """
    Generate Opportunity Matrix: rank interventions by potential impact and effort.
    Impact = (1 - RP) * SCP * domain_weight
    Effort = estimated (simplified: inverse of signal count, or heuristic)
    """
    opportunities = []
    for t in threats:
        tid = t["id"]
        scp = t.get("scp", 0.5)
        domain = t.get("domains", ["Other"])[0]  # simplified
        weight = DOMAIN_WEIGHTS.get(domain, 1.0)
        rp_info = rp_results.get(tid, {})
        rp = rp_info.get("recovery_probability", 0.1)
        # Impact: how much recovery would improve the situation
        impact = (1 - rp) * scp * weight
        # Effort: heuristic based on signal count (more signals = easier? Actually, signals indicate ongoing efforts, but effort is about new intervention)
        # For alpha, use inverse of SCP (lower SCP = easier to intervene)
        effort = 1.0 / (scp + 0.1) if scp > 0 else 10
        # Normalise effort to 0-1 range
        effort = min(1.0, effort / 10)
        # Score = impact / effort (higher is better)
        score = impact / (effort + 0.01)
        opportunities.append({
            "threat_id": tid,
            "name": t.get("name", tid),
            "impact": round(impact, 3),
            "effort": round(effort, 3),
            "score": round(score, 3),
            "recovery_probability": rp,
            "scp": scp,
            "domain": domain,
            "current_signals": rp_info.get("signal_count", 0)
        })
    # Sort by score descending (highest impact per effort)
    opportunities.sort(key=lambda x: x["score"], reverse=True)
    return opportunities

def compute_resilience_score(threats: List[Dict], rp_results: Dict) -> float:
    """
    Compute a global Resilience Score (0-100) as weighted average of RPs.
    """
    total_weight = 0.0
    total_rp = 0.0
    for t in threats:
        scp = t.get("scp", 0.5)
        domain = t.get("domains", ["Other"])[0]
        weight = DOMAIN_WEIGHTS.get(domain, 1.0)
        rp = rp_results.get(t["id"], {}).get("recovery_probability", 0.1)
        total_rp += rp * weight
        total_weight += weight
    if total_weight == 0:
        return 0
    return round((total_rp / total_weight) * 100, 2)

# ----------------------------------------------------------------------
def main():
    print("🌱 Ascension Engine Alpha started")
    # Load threats
    threats_data = load_json(THREATS_FILE)
    threats = threats_data.get("threats", [])
    if not threats:
        print("No threats found. Exiting.")
        return

    # Load positive signals
    signals = load_positive_signals()
    print(f"Loaded {len(signals)} positive signals")

    # Compute Recovery Probabilities
    rp_results = compute_recovery_probability(threats, signals)
    print(f"Computed Recovery Probability for {len(rp_results)} threats")

    # Generate Opportunity Matrix
    opportunities = compute_opportunity_matrix(threats, rp_results)
    print(f"Generated Opportunity Matrix with {len(opportunities)} entries")

    # Compute global Resilience Score
    resilience_score = compute_resilience_score(threats, rp_results)
    print(f"Resilience Score: {resilience_score:.2f}")

    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "resilience_score": resilience_score,
        "recovery_probabilities": rp_results,
        "opportunity_matrix": opportunities[:20],  # top 20
        "positive_signals_count": len(signals),
        "signals": signals,
        "summary": {
            "total_threats": len(threats),
            "threats_with_recovery_signals": sum(1 for t in threats if rp_results.get(t["id"], {}).get("signal_count", 0) > 0),
            "average_recovery_probability": round(sum(rp_results.get(t["id"], {}).get("recovery_probability", 0) for t in threats) / len(threats), 3)
        }
    }

    save_json(report, OUTPUT_FILE)
    print(f"✅ Ascension report saved to {OUTPUT_FILE}")

    # Print top 5 opportunities
    print("\n📊 Top 5 Recovery Opportunities:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"  {i}. {opp['name']} (ID: {opp['threat_id']})")
        print(f"     Impact: {opp['impact']:.2f}, Effort: {opp['effort']:.2f}, Score: {opp['score']:.2f}")
        print(f"     Current RP: {opp['recovery_probability']:.2f}, SCP: {opp['scp']:.2f}")

if __name__ == "__main__":
    main()

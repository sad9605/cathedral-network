#!/usr/bin/env python3
"""
cascade_engine.py – Cathedral Network Cascade Engine v8 (with v9 ML integration).
Bayesian log‑odds fusion, calibrated likelihood ratios, SCP decay, GSCI, SSI, DS, SCA tiers, DAS, and formal verification.
ML likelihood ratios from cathedral_ml.py are loaded and fused if available.
"""

import json
import math
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# Import math functions
from cathedral_math import (
    bayesian_log_odds,
    compute_scp_linear,
    compute_gsci,
    compute_ssi,
    compute_ds,
    compute_sca_tier,
    convergence_alert_protocol,
    temporal_baseline_anomaly,
    source_credibility_weighting
)

# ---------- constants ----------
DEFAULT_PRIOR = 0.12  # 12% base probability (macro-priors)
DECAY_FACTOR = 0.95   # SCP decay per day if no new evidence
ML_WEIGHT = 0.3       # Weight for ML likelihood ratio (0-1)

# ---------- helper functions ----------
def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def compute_threat_status(scp: float, previous_status: Optional[str] = None) -> str:
    """
    Determine threat status based on SCP.
    Black Acute: ≥0.90, Black Structural: ≥0.80, Red: ≥0.70,
    Orange: ≥0.50, Yellow: ≥0.30, Green: <0.30
    """
    if scp >= 0.90:
        return "Black Acute"
    elif scp >= 0.80:
        return "Black Structural"
    elif scp >= 0.70:
        return "Red"
    elif scp >= 0.50:
        return "Orange"
    elif scp >= 0.30:
        return "Yellow"
    else:
        return "Green"

def apply_scp_decay(scp: float, days_since_update: float = 1.0) -> float:
    """
    Apply exponential decay to SCP if no new evidence.
    SCP(t+1) = SCP(t) * DECAY_FACTOR^days
    """
    return scp * (DECAY_FACTOR ** days_since_update)

# ---------- main cascade engine ----------
def run_cascade_engine(
    threats_file: str = "threats.json",
    sweep_file: str = "sweep_report.json",
    cascade_rules_file: str = "cascade_rules.json",
    ml_lrs_file: str = "ml_likelihoods.json"
) -> Dict:
    """
    Main cascade engine entry point.
    Loads threats, applies Bayesian updates, propagates cascades, computes metrics.
    """
    print("🏛️ Cascade Engine v8 (with v9 ML integration) running...")

    # Load data
    threats_data = load_json(threats_file, {})
    threats = threats_data.get('threats', [])
    sweep_data = load_json(sweep_file, {})
    cascade_rules = load_json(cascade_rules_file, [])
    ml_lrs = load_json(ml_lrs_file, {})

    print(f"   Loaded {len(threats)} threats, {len(cascade_rules)} cascade rules, {len(ml_lrs)} ML LRs")

    # ---------- 1. Process each threat ----------
    updated_count = 0
    for t in threats:
        tid = t.get('id')
        if not tid:
            continue

        # Get current SCP and prior
        current_scp = t.get('scp', 0.5)
        base_prob = t.get('base_probability', DEFAULT_PRIOR)

        # Apply decay if this threat hasn't been updated recently
        last_updated = t.get('last_updated')
        if last_updated:
            try:
                last_dt = datetime.fromisoformat(last_updated)
                days = (datetime.now() - last_dt).total_seconds() / 86400
                if days > 1:
                    current_scp = apply_scp_decay(current_scp, days)
            except:
                pass  # ignore if timestamp is malformed

        # Build likelihood ratios for this threat
        lrs = []

        # 1.1 Existing likelihood ratios from threat data
        existing_lrs = t.get('likelihood_ratios', [])
        if isinstance(existing_lrs, list):
            for lr in existing_lrs:
                if isinstance(lr, (int, float)):
                    lrs.append(lr)

        # 1.2 Cascade rules that target this threat
        for rule in cascade_rules:
            if rule.get('target') == tid:
                # Use the rule's likelihood ratio if present
                lr = rule.get('likelihood_ratio', 1.0)
                if isinstance(lr, (int, float)):
                    lrs.append(lr)

        # 1.3 ML likelihood ratio (v9) – weighted
        if tid in ml_lrs:
            ml_lr = ml_lrs[tid]
            if isinstance(ml_lr, (int, float)):
                # Weight the ML LR to avoid overfitting
                weighted_lr = 1.0 + (ml_lr - 1.0) * ML_WEIGHT
                lrs.append(weighted_lr)
                t['ml_likelihood_ratio'] = ml_lr

        # 1.4 Source credibility weighting (if sources available)
        if sweep_data.get('sources'):
            source_weights = [s.get('credibility', 0.5) for s in sweep_data['sources']]
            if source_weights:
                cred_weight = source_credibility_weighting(source_weights)
                lrs.append(1.0 + (cred_weight - 0.5) * 0.5)  # scale 0.5-1.5

        # If no LRs, use base_prob as-is
        if not lrs:
            posterior = base_prob
        else:
            # Bayesian fusion
            posterior = bayesian_log_odds(base_prob, lrs)

        # Apply decay factor (so SCP never hits 1.0 without massive evidence)
        posterior = min(0.99, posterior)

        # Update threat
        t['scp'] = round(posterior, 4)
        t['status'] = compute_threat_status(posterior, t.get('status'))
        t['base_probability'] = base_prob
        t['likelihood_ratios'] = lrs
        t['last_updated'] = datetime.now().isoformat()
        t['priority_score'] = round(posterior * 100 + len(lrs) * 2, 2)

        updated_count += 1

    # ---------- 2. Propagate cascades ----------
    # For each cascade rule, if source threat SCP exceeds threshold, propagate to target
    # We use a simple threshold model: if source SCP > 0.6, propagate with weight
    propagation_threshold = 0.6
    for rule in cascade_rules:
        source_id = rule.get('source')
        target_id = rule.get('target')
        weight = rule.get('weight', 0.3)

        source_threat = next((t for t in threats if t.get('id') == source_id), None)
        target_threat = next((t for t in threats if t.get('id') == target_id), None)

        if source_threat and target_threat:
            source_scp = source_threat.get('scp', 0.0)
            if source_scp > propagation_threshold:
                # Propagate: increase target's SCP slightly
                target_scp = target_threat.get('scp', 0.5)
                boost = weight * (source_scp - propagation_threshold) * 0.5
                new_scp = min(0.99, target_scp + boost)
                target_threat['scp'] = round(new_scp, 4)
                target_threat['status'] = compute_threat_status(new_scp, target_threat.get('status'))
                target_threat['last_updated'] = datetime.now().isoformat()

                # Log the cascade propagation
                cascade_log = load_json("cascade_log.json", [])
                cascade_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "source": source_id,
                    "target": target_id,
                    "source_scp": round(source_scp, 4),
                    "target_scp": round(new_scp, 4),
                    "boost": round(boost, 4)
                })
                save_json(cascade_log, "cascade_log.json")

    # ---------- 3. Compute global metrics ----------
    gsci = compute_gsci(threats)
    ssi = compute_ssi(threats)
    ds = compute_ds(threats)

    # Count active cascades (threats with SCP > 0.5)
    active_cascades = len([t for t in threats if t.get('scp', 0) > 0.5])
    sca_tier = compute_sca_tier(active_cascades)

    # Anomaly detection (DAS) – compare each threat's SCP to its historical baseline
    # For now, we use a simple baseline (0.5)
    anomaly_count = 0
    for t in threats:
        scp = t.get('scp', 0.5)
        das = temporal_baseline_anomaly(scp, 0.5, 0.2)
        t['das'] = round(das, 2)
        if das > 50:
            anomaly_count += 1

    # Convergence alerts (CAP)
    # Count threats in Black/Red status across domains
    black_red = [t for t in threats if t.get('status') in ('Black Acute', 'Black Structural', 'Red')]
    domains_affected = set()
    for t in black_red:
        for d in t.get('domains', []):
            domains_affected.add(d)
    cap = convergence_alert_protocol(len(black_red), len(domains_affected))

    # ---------- 4. Save results ----------
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "threats": threats,
        "gsci": round(gsci, 2),
        "ssi": round(ssi, 2),
        "ds": ds,
        "sca_tier": sca_tier,
        "anomaly_count": anomaly_count,
        "convergence_alert": cap,
        "active_cascades": active_cascades,
        "last_updated": datetime.now().isoformat()
    }

    save_json(output_data, threats_file)

    print(f"   ✅ Updated {updated_count} threats")
    print(f"   📊 GSCI: {gsci:.2f}, SSI: {ssi:.2f}, DS: {ds}")
    print(f"   🔥 Active cascades: {active_cascades}, SCA Tier: {sca_tier['label']}")
    print(f"   ⚠️ Anomalies: {anomaly_count}, CAP: {cap['level']}")

    return output_data

# ---------- CLI entry point ----------
if __name__ == "__main__":
    run_cascade_engine()

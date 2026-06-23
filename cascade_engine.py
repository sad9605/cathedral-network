#!/usr/bin/env python3
"""
cascade_engine.py – Cathedral Network Cascade Engine v8 (with v9 ML integration).
Bayesian log‑odds fusion, calibrated likelihood ratios, SCP decay, GSCI, SSI, DS, SCA tiers, DAS, and formal verification.
ML likelihood ratios from cathedral_ml.py are loaded and fused if available.
"""

import json
import math
import re
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
DEFAULT_PRIOR = 0.12
DECAY_FACTOR = 0.95
ML_WEIGHT = 0.3

# ---------- helper functions ----------
def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def normalize_rules(rules_data):
    """
    Convert various cascade_rules.json formats into a list of dicts.
    Handles:
      - List of dicts with 'source', 'target', 'weight', 'delta'
      - List of strings like "C01 -> C11"
      - Dict with keys like "rules" or "cascades"
    """
    normalized = []
    if isinstance(rules_data, list):
        for item in rules_data:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                # Try to parse "source -> target"
                if '->' in item or '→' in item:
                    parts = re.split(r'\s*->\s*|\s*→\s*', item)
                    if len(parts) == 2:
                        normalized.append({
                            "source": parts[0].strip(),
                            "target": parts[1].strip(),
                            "weight": 1.0,
                            "delta": 0.15
                        })
                elif ',' in item:
                    parts = item.split(',')
                    if len(parts) == 2:
                        normalized.append({
                            "source": parts[0].strip(),
                            "target": parts[1].strip(),
                            "weight": 1.0,
                            "delta": 0.15
                        })
    elif isinstance(rules_data, dict):
        # Try to find a list inside
        for key in ['rules', 'cascades', 'edges']:
            if key in rules_data and isinstance(rules_data[key], list):
                return normalize_rules(rules_data[key])
        # If no list found, treat as a single rule if it has source/target
        if 'source' in rules_data and 'target' in rules_data:
            normalized.append(rules_data)
    return normalized

def compute_threat_status(scp: float) -> str:
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
    return scp * (DECAY_FACTOR ** days_since_update)

# ---------- main cascade engine ----------
def run_cascade_engine(
    threats_file: str = "threats.json",
    sweep_file: str = "sweep_report.json",
    cascade_rules_file: str = "cascade_rules.json",
    ml_lrs_file: str = "ml_likelihoods.json"
) -> Dict:
    print("🏛️ Cascade Engine v8 running...")

    threats_data = load_json(threats_file, {})
    threats = threats_data.get('threats', [])
    sweep_data = load_json(sweep_file, {})
    ml_lrs = load_json(ml_lrs_file, {})

    # Load and normalize cascade rules
    cascade_rules_raw = load_json(cascade_rules_file, [])
    cascade_rules = normalize_rules(cascade_rules_raw)

    print(f"   Loaded {len(threats)} threats, {len(cascade_rules)} cascade rules, {len(ml_lrs)} ML LRs")

    # ---------- 1. Process each threat ----------
    updated_count = 0
    for t in threats:
        tid = t.get('id')
        if not tid:
            continue

        current_scp = t.get('scp', 0.5)
        base_prob = t.get('base_probability', DEFAULT_PRIOR)

        # Apply decay
        last_updated = t.get('last_updated')
        if last_updated:
            try:
                last_dt = datetime.fromisoformat(last_updated)
                days = (datetime.now() - last_dt).total_seconds() / 86400
                if days > 1:
                    current_scp = apply_scp_decay(current_scp, days)
            except:
                pass

        # Build likelihood ratios
        lrs = []

        # Existing LRs
        existing_lrs = t.get('likelihood_ratios', [])
        if isinstance(existing_lrs, list):
            for lr in existing_lrs:
                if isinstance(lr, (int, float)):
                    lrs.append(lr)

        # Cascade rules
        for rule in cascade_rules:
            if rule.get('target') == tid:
                lr = rule.get('likelihood_ratio', 1.0)
                if isinstance(lr, (int, float)):
                    lrs.append(lr)

        # ML likelihood ratio (v9)
        if tid in ml_lrs:
            ml_lr = ml_lrs[tid]
            if isinstance(ml_lr, (int, float)):
                weighted_lr = 1.0 + (ml_lr - 1.0) * ML_WEIGHT
                lrs.append(weighted_lr)
                t['ml_likelihood_ratio'] = ml_lr

        # Source credibility
        source_weights = []
        sources = sweep_data.get('sources', [])
        if sources and isinstance(sources, list):
            # Check if sources are dicts or strings
            if sources and isinstance(sources[0], dict):
                source_weights = [s.get('credibility', 0.5) for s in sources]
            else:
            # Sources are just strings (feed names) – assign default credibility
                 source_weights = [0.5 for _ in sources]
        if source_weights:
            cred_weight = source_credibility_weighting(source_weights)
            lrs.append(1.0 + (cred_weight - 0.5) * 0.5)

        # Bayesian fusion
        if not lrs:
            posterior = base_prob
        else:
            posterior = bayesian_log_odds(base_prob, lrs)

        posterior = min(0.99, posterior)

        t['scp'] = round(posterior, 4)
        t['status'] = compute_threat_status(posterior)
        t['base_probability'] = base_prob
        t['likelihood_ratios'] = lrs
        t['last_updated'] = datetime.now().isoformat()
        t['priority_score'] = round(posterior * 100 + len(lrs) * 2, 2)

        updated_count += 1

    # ---------- 2. Propagate cascades ----------
    propagation_threshold = 0.6
    for rule in cascade_rules:
        source_id = rule.get('source')
        target_id = rule.get('target')
        delta = rule.get('delta', 0.15)

        source_threat = next((t for t in threats if t.get('id') == source_id), None)
        target_threat = next((t for t in threats if t.get('id') == target_id), None)

        if source_threat and target_threat:
            source_scp = source_threat.get('scp', 0.0)
            if source_scp > propagation_threshold:
                target_scp = target_threat.get('scp', 0.5)
                boost = delta * (source_scp - propagation_threshold) * 0.5
                new_scp = min(0.99, target_scp + boost)
                target_threat['scp'] = round(new_scp, 4)
                target_threat['status'] = compute_threat_status(new_scp)
                target_threat['last_updated'] = datetime.now().isoformat()

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

    active_cascades = len([t for t in threats if t.get('scp', 0) > 0.5])
    sca_tier = compute_sca_tier(active_cascades)

    anomaly_count = 0
    for t in threats:
        scp = t.get('scp', 0.5)
        das = temporal_baseline_anomaly(scp, 0.5, 0.2)
        t['das'] = round(das, 2)
        if das > 50:
            anomaly_count += 1

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

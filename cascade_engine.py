#!/usr/bin/env python3
"""
cascade_engine.py – Cathedral Network Probability Drive v8
Full mathematical integration from Cathedral Math Compendium v1.2.
Calibrated Bayesian log-odds fusion with reduced likelihood ratios.
"""

import json
import math
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.stats import beta

# Import math functions from cathedral_math
from cathedral_math import (
    compute_ssi,
    compute_ds,
    compute_gsci,
    compute_sca_tier,
    temporal_baseline_anomaly,
    compute_scp_linear,
    nts_score,
    das_band
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
TSF_FILE = "tsf_forecasts.json"
BASELINE_FILE = "baseline_stats.json"
OUTPUT_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
GSCI_LOG = "gsci_log.json"
SSI_LOG = "ssi_log.json"

# Domain weights for GSCI
DOMAIN_WEIGHTS = {
    "Geopolitical": 1.2,
    "Energy": 1.2,
    "Food": 1.1,
    "Financial": 1.0,
    "Climate": 1.0,
    "Health": 0.9,
    "Displacement": 0.9,
    "Other": 0.8
}

# Status points for SSI
STATUS_POINTS = {
    'Green': 0,
    'Yellow': 1,
    'Orange': 2,
    'Red': 3,
    'Black Structural': 4,
    'Black Acute': 5
}

# SCP Base Probability (from compendium)
SCP_BASE = 12.0  # 4% multi-theater war + 8% other Black Swan

# ----------------------------------------------------------------------
# Utility functions
def load_json(filepath, default=None):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"{filepath} not found. Using default: {default}")
        return default if default is not None else {}
    except json.JSONDecodeError:
        logging.error(f"{filepath} is not valid JSON. Using default: {default}")
        return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_baselines():
    """Load baseline statistics for DAS calculation."""
    if Path(BASELINE_FILE).exists():
        return load_json(BASELINE_FILE)
    # Default baselines if file doesn't exist
    return {
        'brent': {'mean': 75.0, 'std': 15.0},
        'fao': {'mean': 120.0, 'std': 20.0},
        'fema': {'mean': 2.5, 'std': 0.5},
        'default': {'mean': 0.5, 'std': 0.2}
    }

# ----------------------------------------------------------------------
# Core engine functions
def bayesian_update(prior: float, likelihood_ratio: float) -> Tuple[float, float, float]:
    """
    Bayesian logit update with probability cap at 0.95 and dampening.
    Returns (posterior, lower_80, upper_80).
    """
    if prior <= 0:
        return 0.01, 0.001, 0.05
    if prior >= 1:
        return 0.95, 0.90, 0.98
    
    logit_prior = math.log(prior / (1 - prior))
    logit_posterior = logit_prior + math.log(likelihood_ratio)
    posterior = 1 / (1 + math.exp(-logit_posterior))
    
    # Apply dampening to prevent over-confidence
    dampening = 0.85
    posterior = 0.5 + (posterior - 0.5) * dampening
    
    posterior = min(0.95, max(0.01, posterior))
    
    # 80% credible interval using Beta approximation
    alpha = max(0.1, posterior * 10)
    beta_param = max(0.1, (1 - posterior) * 10)
    lower = beta.ppf(0.1, alpha, beta_param)
    upper = beta.ppf(0.9, alpha, beta_param)
    return posterior, lower, upper

def decay_scp(scp: float, half_life_days: float = 7.0) -> float:
    """Exponential decay of SCP over time."""
    decay_factor = 0.5 ** (1.0 / half_life_days)
    return scp * decay_factor

def probability_to_lr(prob_exceed: float) -> float:
    """
    Calibrated likelihood ratios – reduced to prevent over-confidence.
    """
    if prob_exceed > 0.7:
        return 1.8
    elif prob_exceed > 0.5:
        return 1.4
    elif prob_exceed > 0.3:
        return 1.1
    else:
        return 1.0

def compute_scp_from_threats(threats: List[Dict]) -> Dict:
    """
    Compute SCP using Bayesian log-odds fusion.
    Returns SCP value and contribution breakdown.
    """
    base = SCP_BASE / 100.0
    active_deltas = []
    likelihood_ratios = []
    
    for t in threats:
        delta = t.get('delta_contribution', 0)
        if delta > 0:
            active_deltas.append(delta)
            # Convert delta to likelihood ratio (simplified)
            lr = 1.0 + delta * 1.5
            likelihood_ratios.append(lr)
    
    # Linear SCP (capped)
    linear_scp = compute_scp_linear(base, active_deltas)
    
    # Bayesian SCP (log-odds)
    if likelihood_ratios:
        bayesian_scp = bayesian_update(base, np.prod(likelihood_ratios))[0] * 100
    else:
        bayesian_scp = base * 100
    
    return {
        'linear_scp': linear_scp,
        'bayesian_scp': bayesian_scp,
        'active_deltas': active_deltas,
        'delta_count': len(active_deltas)
    }

# ----------------------------------------------------------------------
# Main engine functions
def apply_temporal_decay(threats: Dict) -> Dict:
    """Apply SCP decay to all threats before cascade updates."""
    for t in threats['threats']:
        old_scp = t.get('scp', 0.5)
        t['scp'] = decay_scp(old_scp)
    return threats

def compute_das_for_threat(threat: Dict, baselines: Dict) -> float:
    """Compute DAS for a single threat using baseline statistics."""
    threat_id = threat.get('id', '')
    value = threat.get('scp', 0.5)
    baseline = baselines.get(threat_id, baselines.get('default', {'mean': 0.5, 'std': 0.2}))
    mean = baseline.get('mean', 0.5)
    std = baseline.get('std', 0.2)
    return temporal_baseline_anomaly(value, mean, std)

def apply_tsf_likelihoods(threats: Dict, tsf: Dict) -> Dict:
    """Apply Bayesian updates from TSF forecasts (Brent, FAO, FEMA)."""
    if not tsf:
        return threats
    threat_dict = {t['id']: t for t in threats['threats']}
    mapping = {
        'brent': ['C11', 'P78', 'P74'],
        'fao': ['C106', 'C03', 'P35'],
        'fema': ['D02', 'U09']
    }
    for key, targets in mapping.items():
        prob_exceed = tsf.get(key, {}).get('probability_exceed', 0.0)
        lr = probability_to_lr(prob_exceed)
        if lr == 1.0:
            continue
        for tid in targets:
            if tid in threat_dict:
                old = threat_dict[tid].get('base_probability', 0.5)
                new, low, high = bayesian_update(old, lr)
                threat_dict[tid]['base_probability'] = new
                threat_dict[tid]['prob_lower_80'] = low
                threat_dict[tid]['prob_upper_80'] = high
                logging.debug(f"Bayesian {tid}: {old:.3f} → {new:.3f}")
    threats['threats'] = list(threat_dict.values())
    return threats

def apply_cascade_rules(threats: Dict, rules: List[Dict], confidence: float = 1.0) -> Dict:
    """Propagate SCP according to cascade rules with confidence filters."""
    threat_dict = {t['id']: t for t in threats['threats']}
    log_entries = []
    
    for rule in rules:
        src_id = rule['source']
        tgt_id = rule['target']
        delta = rule['delta']
        cond = rule.get('condition', 'always')
        thresh = rule.get('threshold', 0.0)
        
        if src_id not in threat_dict:
            logging.warning(f"Source threat {src_id} not found")
            continue
        
        src = threat_dict[src_id]
        apply = False
        
        if cond == 'always':
            apply = True
        elif cond == 'scp_above' and src.get('scp', 0.0) >= thresh:
            apply = True
        elif cond == 'status_red_or_black' and src.get('status', '') in ['Red', 'Black Acute', 'Black Structural']:
            apply = True
        
        if apply and tgt_id in threat_dict:
            old_scp = threat_dict[tgt_id].get('scp', 0.5)
            adjusted_delta = delta * confidence
            new_scp = min(0.95, old_scp + adjusted_delta)
            threat_dict[tgt_id]['scp'] = new_scp
            # Store delta contribution for SCP calculation
            threat_dict[tgt_id]['delta_contribution'] = threat_dict[tgt_id].get('delta_contribution', 0) + adjusted_delta
            log_entries.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': src_id,
                'target': tgt_id,
                'delta': delta,
                'confidence': confidence,
                'adjusted_delta': adjusted_delta,
                'new_scp': new_scp
            })
    
    threats['threats'] = list(threat_dict.values())
    if log_entries:
        save_json(log_entries, CASCADE_LOG)
        logging.info(f"Cascade log saved ({len(log_entries)} updates)")
    return threats

def compute_gsci_weighted(threats: List[Dict]) -> float:
    """Compute GSCI using domain weights."""
    weighted_sum = 0.0
    total_weight = 0.0
    for t in threats:
        domains = t.get('domains', ['Other'])
        if isinstance(domains, str):
            domains = [domains]
        w = sum(DOMAIN_WEIGHTS.get(d, 1.0) for d in domains) / len(domains)
        scp = t.get('scp', 0.5)
        weighted_sum += w * scp
        total_weight += w
    if total_weight == 0:
        return 50.0
    return (weighted_sum / total_weight) * 100

def compute_priority_scores(threats: Dict, baselines: Dict) -> Dict:
    """Calculate priority score for each threat using DAS integration."""
    for t in threats['threats']:
        base = t.get('base_probability', 0.5)
        scp = t.get('scp', 0.5)
        das = compute_das_for_threat(t, baselines)
        t['das'] = das
        t['das_band'] = das_band(das)
        # Priority = base_probability * (1 + scp) * (1 + das/30)
        priority = base * (1 + scp) * (1 + das / 30)
        t['priority_score'] = round(min(100, priority * 100), 1)
    return threats

def compute_core_metrics(threats: Dict) -> Dict:
    """
    Compute all core metrics: SSI, DS, GSCI, SCA.
    """
    threat_list = threats.get('threats', [])
    
    # SSI
    ssi = compute_ssi(threat_list)
    threats['ssi'] = round(ssi, 2)
    
    # DS
    ds = compute_ds(threat_list)
    threats['ds'] = ds
    
    # GSCI
    gsci_value = compute_gsci_weighted(threat_list)
    threats['gsci'] = round(gsci_value, 2)
    
    # SCA tier
    cascade_log = load_json(CASCADE_LOG, default=[])
    sca = compute_sca_tier(len(cascade_log))
    threats['sca_tier'] = sca['tier']
    threats['sca_label'] = sca['label']
    threats['sca_count'] = sca['count']
    
    # SCP calculation
    scp_result = compute_scp_from_threats(threat_list)
    threats['scp_linear'] = round(scp_result['linear_scp'], 2)
    threats['scp_bayesian'] = round(scp_result['bayesian_scp'], 2)
    threats['scp_delta_count'] = scp_result['delta_count']
    
    return threats

# ----------------------------------------------------------------------
# Main execution
def main():
    logging.info("Cascade Engine v8 started (full mathematical integration)")
    
    # Backup original
    shutil.copy2(THREATS_FILE, THREATS_FILE.replace('.json', '.backup.json'))
    
    # Load threats
    threats = load_json(THREATS_FILE)
    if not threats or 'threats' not in threats:
        logging.error("Invalid threats.json")
        return
    
    # Apply temporal decay
    threats = apply_temporal_decay(threats)
    
    # Load cascade rules
    rules_data = load_json(RULES_FILE)
    if not rules_data or 'rules' not in rules_data:
        logging.error("cascade_rules.json missing 'rules' array")
        return
    rules = rules_data['rules']
    logging.info(f"Loaded {len(rules)} cascade rules")
    
    # Load baselines for DAS
    baselines = load_baselines()
    
    # Load TSF forecasts
    tsf = load_json(TSF_FILE, default={})
    if tsf:
        logging.info("Applying TSF likelihood ratios (Bayesian)")
        threats = apply_tsf_likelihoods(threats, tsf)
    else:
        logging.info("No TSF forecasts – skipping likelihood ratios")
    
    # Apply cascade rules with confidence filters
    confidence = 1.0
    logging.info("Applying cascade rules")
    threats = apply_cascade_rules(threats, rules, confidence)
    
    # Compute priority scores with DAS
    threats = compute_priority_scores(threats, baselines)
    
    # Compute core metrics
    threats = compute_core_metrics(threats)
    
    # Log SSI history
    ssi_log = load_json(SSI_LOG, default=[])
    ssi_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'ssi': threats['ssi'],
        'ds': threats['ds'],
        'gsci': threats['gsci'],
        'sca_tier': threats['sca_tier']
    })
    save_json(ssi_log[-100:], SSI_LOG)
    
    # Log GSCI history
    gsci_log = load_json(GSCI_LOG, default=[])
    gsci_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'gsci': threats['gsci'],
        'ssi': threats['ssi']
    })
    save_json(gsci_log[-100:], GSCI_LOG)
    
    # Update last updated timestamp
    threats['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Save results
    save_json(threats, OUTPUT_FILE)
    
    logging.info(f"Updated {len(threats['threats'])} threats saved to {OUTPUT_FILE}")
    logging.info(f"SSI: {threats['ssi']:.2f}, DS: {threats['ds']}, GSCI: {threats['gsci']:.2f}")
    logging.info(f"SCA Tier: {threats['sca_tier']} ({threats['sca_label']})")
    logging.info(f"SCP (Bayesian): {threats['scp_bayesian']:.2f}%")

if __name__ == "__main__":
    main()

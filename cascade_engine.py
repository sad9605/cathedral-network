#!/usr/bin/env python3
"""
cascade_engine_v4.py – Cathedral Network Probability Drive
Bayesian logit, TSF likelihood ratios, cascade propagation,
SCP temporal decay, uncertainty intervals (80% CI), GSCI, priority scores.
"""

import json
import math
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from scipy.stats import beta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
TSF_FILE = "tsf_forecasts.json"
BASELINE_FILE = "baseline_stats.json"
OUTPUT_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
GSCI_LOG = "gsci_log.json"

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

def load_json(filepath, default=None):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"{filepath} not found. Using default: {default}")
        return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def bayesian_update(prior: float, likelihood_ratio: float) -> Tuple[float, float, float]:
    """Return (posterior, lower_80, upper_80)."""
    if prior <= 0:
        return 0.01, 0.001, 0.05
    if prior >= 1:
        return 0.99, 0.95, 0.999
    logit_prior = math.log(prior / (1 - prior))
    logit_posterior = logit_prior + math.log(likelihood_ratio)
    posterior = 1 / (1 + math.exp(-logit_posterior))
    posterior = min(0.99, max(0.01, posterior))
    alpha = max(0.1, posterior * 10)
    beta_param = max(0.1, (1 - posterior) * 10)
    lower = beta.ppf(0.1, alpha, beta_param)
    upper = beta.ppf(0.9, alpha, beta_param)
    return posterior, lower, upper

def decay_scp(scp: float, half_life_days: float = 7.0) -> float:
    decay_factor = 0.5 ** (1.0 / half_life_days)
    return scp * decay_factor

def probability_to_lr(prob_exceed: float) -> float:
    if prob_exceed > 0.7:
        return 4.0
    elif prob_exceed > 0.5:
        return 2.5
    elif prob_exceed > 0.3:
        return 1.5
    else:
        return 1.0

def apply_temporal_decay(threats: Dict) -> Dict:
    for t in threats['threats']:
        old_scp = t.get('scp', 0.5)
        t['scp'] = decay_scp(old_scp)
    return threats

def apply_tsf_likelihoods(threats: Dict, tsf: Dict) -> Dict:
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
    threats['threats'] = list(threat_dict.values())
    return threats

def apply_cascade_rules(threats: Dict, rules: List[Dict]) -> Dict:
    threat_dict = {t['id']: t for t in threats['threats']}
    log_entries = []
    for rule in rules:
        src_id = rule['source']
        tgt_id = rule['target']
        delta = rule['delta']
        cond = rule.get('condition', 'always')
        thresh = rule.get('threshold', 0.0)
        if src_id not in threat_dict:
            logging.warning(f"Source {src_id} not found")
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
            new_scp = min(0.99, old_scp + delta)
            threat_dict[tgt_id]['scp'] = new_scp
            log_entries.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': src_id,
                'target': tgt_id,
                'delta': delta,
                'new_scp': new_scp
            })
    threats['threats'] = list(threat_dict.values())
    if log_entries:
        save_json(log_entries, CASCADE_LOG)
        logging.info(f"Cascade log saved ({len(log_entries)} updates)")
    return threats

def compute_gsci(threats: List[Dict]) -> float:
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

def compute_priority_scores(threats: Dict) -> Dict:
    for t in threats['threats']:
        base = t.get('base_probability', 0.5)
        scp = t.get('scp', 0.5)
        das = t.get('das', 0)
        priority = base * (1 + scp) * (1 + das / 30)
        t['priority_score'] = round(min(100, priority * 100), 1)
    return threats

def main():
    logging.info("Cascade Engine v4 started")
    shutil.copy2(THREATS_FILE, THREATS_FILE.replace('.json', '.backup.json'))

    threats = load_json(THREATS_FILE)
    if not threats or 'threats' not in threats:
        logging.error("Invalid threats.json")
        return

    # Apply decay first
    threats = apply_temporal_decay(threats)

    rules_data = load_json(RULES_FILE)
    if not rules_data or 'rules' not in rules_data:
        logging.error("cascade_rules.json missing 'rules' array")
        return
    rules = rules_data['rules']
    logging.info(f"Loaded {len(rules)} cascade rules")

    tsf = load_json(TSF_FILE, default={})
    if tsf:
        logging.info("Applying TSF likelihood ratios with Bayesian update")
        threats = apply_tsf_likelihoods(threats, tsf)
    else:
        logging.info("No TSF forecasts – skipping likelihood ratios")

    logging.info("Applying cascade rules")
    threats = apply_cascade_rules(threats, rules)

    gsci_value = compute_gsci(threats['threats'])
    threats['gsci'] = round(gsci_value, 2)
    logging.info(f"GSCI = {threats['gsci']}")

    gsci_log = load_json(GSCI_LOG, default=[])
    gsci_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'gsci': threats['gsci']
    })
    save_json(gsci_log[-100:], GSCI_LOG)

    threats = compute_priority_scores(threats)
    threats['last_updated'] = datetime.now(timezone.utc).isoformat()
    save_json(threats, OUTPUT_FILE)
    logging.info(f"Updated {len(threats['threats'])} threats saved")

if __name__ == "__main__":
    main()

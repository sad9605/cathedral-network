#!/usr/bin/env python3
"""
cascade_engine.py – Cathedral Network Probability Drive v7
Adds credit spread and tech valuation confidence filters.
"""

import json
import math
import logging
import shutil
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import yfinance as yf
from scipy.stats import beta
from fredapi import Fred

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
TSF_FILE = "tsf_forecasts.json"
OUTPUT_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
GSCI_LOG = "gsci_log.json"

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

# FRED API key (set environment variable)
FRED_API_KEY = os.environ.get("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

# ----------------------------------------------------------------------
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
    if prior <= 0:
        return 0.01, 0.001, 0.05
    if prior >= 1:
        return 0.95, 0.90, 0.98
    logit_prior = math.log(prior / (1 - prior))
    logit_posterior = logit_prior + math.log(likelihood_ratio)
    posterior = 1 / (1 + math.exp(-logit_posterior))
    posterior = min(0.95, max(0.01, posterior))
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
        return 5.0
    elif prob_exceed > 0.5:
        return 3.5
    elif prob_exceed > 0.3:
        return 2.2
    else:
        return 1.0

# ----------------------------------------------------------------------
# Confidence filters (reduce LR when systemic risk signals are absent)
def get_credit_spread_confidence() -> float:
    """Return confidence multiplier based on current credit spread (BAA - AAA)."""
    if not fred:
        return 1.0
    try:
        end = datetime.now()
        start = end - timedelta(days=10)
        baa = fred.get_series("BAA10Y", observation_start=start, observation_end=end)
        aaa = fred.get_series("AAA10Y", observation_start=start, observation_end=end)
        if baa.empty or aaa.empty:
            return 1.0
        spread = (baa - aaa).dropna()
        if spread.empty:
            return 1.0
        latest_spread = spread.iloc[-1]
        # Narrow spreads = low systemic risk = reduce confidence
        if latest_spread < 1.0:
            return 0.25
        elif latest_spread < 1.5:
            return 0.5
        else:
            return 1.0
    except Exception as e:
        logging.debug(f"Credit spread error: {e}")
        return 1.0

def get_tech_valuation_confidence() -> float:
    """Return confidence multiplier based on NASDAQ drawdown."""
    try:
        end = datetime.now()
        start = end - timedelta(days=30)
        data = yf.download("^IXIC", start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
        if data.empty:
            return 1.0
        col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
        prices = data[col]
        if prices.empty:
            return 1.0
        peak = prices.max()
        trough = prices.min()
        drawdown = (peak - trough) / peak if peak > 0 else 0
        if drawdown < 0.2:
            return 0.3
        elif drawdown < 0.3:
            return 0.6
        else:
            return 1.0
    except Exception as e:
        logging.debug(f"Tech valuation error: {e}")
        return 1.0

def get_bank_confidence() -> float:
    """Return confidence multiplier based on KBW Bank Index drawdown."""
    try:
        end = datetime.now()
        start = end - timedelta(days=10)
        data = yf.download("^BKX", start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
        if data.empty:
            return 1.0
        col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
        prices = data[col]
        if prices.empty:
            return 1.0
        peak = prices.max()
        trough = prices.min()
        drawdown = (peak - trough) / peak if peak > 0 else 0
        if drawdown < 0.15:
            return 0.4
        elif drawdown < 0.25:
            return 0.7
        else:
            return 1.0
    except Exception as e:
        logging.debug(f"Bank confidence error: {e}")
        return 1.0

def get_overall_confidence() -> float:
    """Combine all confidence filters."""
    credit_conf = get_credit_spread_confidence()
    tech_conf = get_tech_valuation_confidence()
    bank_conf = get_bank_confidence()
    combined = credit_conf * tech_conf * bank_conf
    logging.debug(f"Confidence multipliers: credit={credit_conf:.2f}, tech={tech_conf:.2f}, bank={bank_conf:.2f} -> overall={combined:.2f}")
    return combined

# ----------------------------------------------------------------------
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
    # Get overall confidence filter
    confidence = get_overall_confidence()
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
            # Apply confidence to delta (reduces impact when systemic risk is low)
            adjusted_delta = delta * confidence
            new_scp = min(0.95, old_scp + adjusted_delta)
            threat_dict[tgt_id]['scp'] = new_scp
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
        logging.info(f"Cascade log saved ({len(log_entries)} updates) with confidence {confidence:.2f}")
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

# ----------------------------------------------------------------------
def main():
    logging.info("Cascade Engine v7 started (with confidence filters)")
    shutil.copy2(THREATS_FILE, THREATS_FILE.replace('.json', '.backup.json'))

    threats = load_json(THREATS_FILE)
    if not threats or 'threats' not in threats:
        logging.error("Invalid threats.json")
        return

    threats = apply_temporal_decay(threats)

    rules_data = load_json(RULES_FILE)
    if not rules_data or 'rules' not in rules_data:
        logging.error("cascade_rules.json missing 'rules' array")
        return
    rules = rules_data['rules']
    logging.info(f"Loaded {len(rules)} cascade rules")

    tsf = load_json(TSF_FILE, default={})
    if tsf:
        logging.info("Applying TSF likelihood ratios")
        threats = apply_tsf_likelihoods(threats, tsf)
    else:
        logging.info("No TSF forecasts – skipping likelihood ratios")

    logging.info("Applying cascade rules with confidence filters")
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

def compute_ssi(fao_score, acled_events, unemployment, trust_score, pmi):
    """
    Compute System Stress Index from component scores.
    All inputs should be normalised 0-100.
    """
    weights = {
        'v10': 0.25,   # Food Price Index
        'v12': 0.25,   # Political Violence
        'v13': 0.20,   # Unemployment / Displacement
        'v03': 0.20,   # Institutional Trust
        'v26': 0.10    # Demand Destruction
    }
    ssi = (
        weights['v10'] * fao_score +
        weights['v12'] * acled_events +
        weights['v13'] * unemployment +
        weights['v03'] * trust_score +
        weights['v26'] * pmi
    )
    return round(ssi, 2)

if __name__ == "__main__":
    main()
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass

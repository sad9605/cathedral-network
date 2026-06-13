#!/usr/bin/env python3
"""
Cascade Engine v2 – Cathedral Network
Reads threats.json, cascade_rules.json, and tsf_forecasts.json (optional)
Outputs updated threats.json and cascade_log.json
"""

import json
import copy
import logging
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Files
THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
TSF_FILE = "tsf_forecasts.json"
OUTPUT_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"

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

def apply_likelihood_ratios(threats: Dict, tsf: Dict) -> Dict:
    """Apply TSF likelihood ratios to base probabilities."""
    if not tsf:
        return threats
    threat_dict = {t['id']: t for t in threats['threats']}
    
    # Mapping of TSF keys to target threat IDs
    mapping = {
        'brent': ['C11', 'P78', 'P74'],
        'fao': ['C106', 'C03', 'P35'],
        'fema': ['D02', 'U09']
    }
    for key, targets in mapping.items():
        lr = tsf.get(key, {}).get('likelihood_ratio', 1.0)
        if lr == 1.0:
            continue
        for tid in targets:
            if tid in threat_dict:
                old = threat_dict[tid].get('base_probability', 0.5)
                new = min(0.99, old * lr)
                threat_dict[tid]['base_probability'] = new
                logging.debug(f"LR {lr} applied to {tid}: {old:.3f} → {new:.3f}")
            else:
                logging.warning(f"Threat {tid} not found, cannot apply LR from {key}")
    threats['threats'] = list(threat_dict.values())
    return threats

def apply_cascade_rules(threats: Dict, rules: List[Dict]) -> Dict:
    """Propagate SCP increases according to cascade rules."""
    threat_dict = {t['id']: t for t in threats['threats']}
    log_entries = []
    for rule in rules:
        src_id = rule['source']
        tgt_id = rule['target']
        delta = rule['delta']
        cond = rule.get('condition', 'always')
        thresh = rule.get('threshold', 0.0)
        
        if src_id not in threat_dict:
            logging.warning(f"Source threat {src_id} not found, skipping rule")
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
        logging.info(f"Cascade log saved to {CASCADE_LOG} ({len(log_entries)} updates)")
    return threats

def compute_priority_scores(threats: Dict) -> Dict:
    for t in threats['threats']:
        base = t.get('base_probability', 0.5)
        scp = t.get('scp', 0.5)
        das = t.get('das', 0)
        priority = base * (1 + scp) * (1 + das / 30)
        t['priority_score'] = round(min(100, priority * 100), 1)
    return threats

def main():
    logging.info("Cascade Engine v2 started")
    # Backup original threats.json
    shutil.copy2(THREATS_FILE, THREATS_FILE.replace('.json', '.backup.json'))
    
    threats = load_json(THREATS_FILE)
    if not threats or 'threats' not in threats:
        logging.error("Invalid threats.json")
        return
    
    rules_data = load_json(RULES_FILE)
    if not rules_data or 'rules' not in rules_data:
        logging.error("cascade_rules.json missing or missing 'rules' array")
        return
    rules = rules_data['rules']
    logging.info(f"Loaded {len(rules)} cascade rules")
    
    tsf = load_json(TSF_FILE, default={})
    if tsf:
        logging.info("Applying TSF likelihood ratios")
        threats = apply_likelihood_ratios(threats, tsf)
    else:
        logging.info("No TSF forecasts found – skipping likelihood ratios")
    
    logging.info("Applying cascade rules")
    threats = apply_cascade_rules(threats, rules)
    
    logging.info("Computing priority scores")
    threats = compute_priority_scores(threats)
    
    threats['last_updated'] = datetime.now(timezone.utc).isoformat()
    save_json(threats, OUTPUT_FILE)
    logging.info(f"Updated {len(threats['threats'])} threats saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

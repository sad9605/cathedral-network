#!/usr/bin/env python3
"""
cascade_discovery.py – Cascade rule discovery using correlation analysis.
No pgmpy required – uses simple statistical correlation to suggest new rules.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

THREATS_FILE = "threats.json"
CASCADE_LOG = "cascade_log.json"
OUTPUT_RULES = "cascade_rules_discovered.json"

def load_threat_data():
    """Load threat data and cascade logs."""
    if not Path(THREATS_FILE).exists():
        logging.warning("threats.json not found. Using simulated data.")
        return _generate_simulated_data()
    
    with open(THREATS_FILE) as f:
        threats = json.load(f).get('threats', [])
    
    # Extract SCP values and threat IDs
    threat_scp = {t['id']: t.get('scp', 0.5) for t in threats}
    threat_names = {t['id']: t.get('name', t['id']) for t in threats}
    
    # Load cascade log if available
    if Path(CASCADE_LOG).exists():
        with open(CASCADE_LOG) as f:
            logs = json.load(f)
        # Count co-occurrences in cascade logs
        co_occurrence = defaultdict(int)
        for log in logs:
            src = log.get('source')
            tgt = log.get('target')
            if src and tgt:
                co_occurrence[(src, tgt)] += 1
    else:
        co_occurrence = defaultdict(int)
    
    return threat_scp, threat_names, co_occurrence

def _generate_simulated_data():
    """Generate simulated data for demonstration."""
    np.random.seed(42)
    threats = ['C01', 'C11', 'C03', 'C132', 'C139', 'C106', 'B02', 'C78']
    threat_scp = {t: np.random.beta(2, 5) for t in threats}
    threat_names = {t: f"Threat {t}" for t in threats}
    co_occurrence = defaultdict(int)
    for _ in range(50):
        src = np.random.choice(threats)
        tgt = np.random.choice(threats)
        if src != tgt:
            co_occurrence[(src, tgt)] += np.random.randint(1, 5)
    return threat_scp, threat_names, co_occurrence

def discover_cascade_rules(threat_scp, co_occurrence, min_occurrences=1):
    """
    Discover cascade rules from co-occurrence data.
    Rules are suggested when two threats appear together in cascade logs.
    """
    discovered = []
    for (src, tgt), count in co_occurrence.items():
        if count >= min_occurrences:
            # Calculate confidence based on occurrence frequency
            confidence = min(0.95, 0.3 + (count / 10))
            # Estimate delta based on SCP difference
            src_scp = threat_scp.get(src, 0.5)
            tgt_scp = threat_scp.get(tgt, 0.5)
            delta = max(0.05, min(0.3, abs(src_scp - tgt_scp) * 0.5))
            
            discovered.append({
                'source': src,
                'target': tgt,
                'delta': round(delta, 3),
                'condition': 'scp_above',
                'threshold': 0.5,
                'description': f'Co-occurrence discovery: {src} → {tgt} (appeared {count} times)',
                'confidence': round(confidence, 3),
                'occurrence_count': count
            })
    
    # Sort by confidence
    discovered.sort(key=lambda x: x['confidence'], reverse=True)
    return discovered

def main():
    logging.info("Loading threat data...")
    threat_scp, threat_names, co_occurrence = load_threat_data()
    
    logging.info(f"Loaded {len(threat_scp)} threats, {len(co_occurrence)} co-occurrence pairs")
    
    logging.info("Discovering cascade rules from co-occurrence...")
    discovered = discover_cascade_rules(threat_scp, co_occurrence)
    
    # Save discovered rules
    with open(OUTPUT_RULES, 'w') as f:
        json.dump(discovered, f, indent=2)
    
    logging.info(f"Discovered {len(discovered)} cascade rules. Saved to {OUTPUT_RULES}")
    
    print("\n=== Suggested New Cascade Rules ===")
    for rule in discovered[:10]:
        print(f"  {rule['source']} → {rule['target']}  (delta: {rule['delta']}, confidence: {rule['confidence']})")
        print(f"    {rule['description']}")
    
    if len(discovered) > 10:
        print(f"  ... and {len(discovered) - 10} more (see {OUTPUT_RULES})")
    
    print("\nTo apply these rules, review and merge into cascade_rules.json")

if __name__ == "__main__":
    main()

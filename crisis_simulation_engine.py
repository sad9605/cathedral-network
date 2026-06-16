#!/usr/bin/env python3
"""
crisis_simulation_engine.py – Monte Carlo cascade simulations.
Estimates trigger probabilities and GSCI distributions over time.
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
SIMULATION_RUNS = 10000
SIMULATION_DAYS = 30
DAILY_TRIGGER_PROB_MULTIPLIER = 0.1   # how SCP translates to daily trigger prob

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def simulate_cascade(initial_threats: List[Dict], rules: List[Dict], days: int) -> Dict:
    """
    Run one Monte Carlo simulation.
    Returns: {
        'triggered_ids': set of threats that triggered at least once,
        'final_scp': dict of threat id -> final SCP,
        'final_gsci': float,
        'cascade_chain': list of (day, src, tgt)
    }
    """
    # Create mutable copies
    threats = {t['id']: {'scp': t.get('scp', 0.5), 'triggered': False} for t in initial_threats}
    cascade_chain = []
    # Simulate day by day
    for day in range(1, days+1):
        # Determine which threats trigger today (based on SCP)
        triggered_today = []
        for tid, data in threats.items():
            # Daily trigger probability = SCP * multiplier, capped at 0.5
            prob = min(0.5, data['scp'] * DAILY_TRIGGER_PROB_MULTIPLIER)
            if random.random() < prob and not data['triggered']:
                triggered_today.append(tid)
                data['triggered'] = True
        # Apply cascade rules for each trigger
        for src_id in triggered_today:
            for rule in rules:
                if rule.get('source') == src_id:
                    tgt_id = rule['target']
                    delta = rule['delta']
                    cond = rule.get('condition', 'always')
                    # simplified condition check – you can expand
                    if cond == 'always' or (cond == 'scp_above' and threats[src_id]['scp'] >= rule.get('threshold', 0)):
                        old_scp = threats[tgt_id]['scp']
                        new_scp = min(0.99, old_scp + delta)
                        threats[tgt_id]['scp'] = new_scp
                        cascade_chain.append((day, src_id, tgt_id))
    # Compute final GSCI (simple average of SCPs, or use domain weights from cascade_engine)
    scp_values = [data['scp'] for data in threats.values()]
    final_gsci = np.mean(scp_values) * 100  # simplistic, replace with domain-weighted later
    triggered_ids = [tid for tid, data in threats.items() if data['triggered']]
    return {
        'triggered_ids': set(triggered_ids),
        'final_scp': {tid: data['scp'] for tid, data in threats.items()},
        'final_gsci': final_gsci,
        'cascade_chain': cascade_chain
    }

def main():
    logging.info("Loading threats and cascade rules...")
    threats_data = load_json(THREATS_FILE)
    rules_data = load_json(RULES_FILE)
    threats = threats_data.get('threats', [])
    rules = rules_data.get('rules', [])
    logging.info(f"Loaded {len(threats)} threats, {len(rules)} rules")

    results = []
    trigger_counts = defaultdict(int)
    gsci_list = []
    all_cascade_chains = []

    for i in range(SIMULATION_RUNS):
        if i % 1000 == 0:
            logging.info(f"Simulation {i}/{SIMULATION_RUNS}")
        outcome = simulate_cascade(threats, rules, SIMULATION_DAYS)
        results.append(outcome)
        for tid in outcome['triggered_ids']:
            trigger_counts[tid] += 1
        gsci_list.append(outcome['final_gsci'])
        all_cascade_chains.extend(outcome['cascade_chain'])

    # Compute probabilities
    trigger_prob = {tid: count / SIMULATION_RUNS for tid, count in trigger_counts.items()}

    # Statistics
    mean_gsci = np.mean(gsci_list)
    std_gsci = np.std(gsci_list)
    percentiles = np.percentile(gsci_list, [10, 50, 90])

    logging.info(f"GSCI: mean={mean_gsci:.2f}, std={std_gsci:.2f}, 10th={percentiles[0]:.2f}, median={percentiles[1]:.2f}, 90th={percentiles[2]:.2f}")

    # Save results
    report = {
        'simulation_runs': SIMULATION_RUNS,
        'simulation_days': SIMULATION_DAYS,
        'trigger_probabilities': trigger_prob,
        'gsci_stats': {
            'mean': mean_gsci,
            'std': std_gsci,
            '10th_percentile': percentiles[0],
            'median': percentiles[1],
            '90th_percentile': percentiles[2]
        },
        'most_common_cascades': sorted(all_cascade_chains, key=lambda x: x[1])[:20]  # simplistic
    }
    with open('crisis_simulation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    logging.info("Saved crisis_simulation_report.json")

if __name__ == "__main__":
    main()
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass

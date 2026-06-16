#!/usr/bin/env python3
"""
Monte Carlo Crisis Simulation Engine – Cathedral Network
"""

import json
import numpy as np
from datetime import datetime, timezone

N_SIMULATIONS = 10000
THREATS_FILE = "threats.json"
RULES_FILE = "cascade_rules.json"
OUTPUT_FILE = "monte_carlo_results.json"

def load_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def run_simulation(threats, rules):
    # Convert threats to dictionary for easy update
    threat_dict = {t['id']: t.copy() for t in threats['threats']}
    # Random initial probabilities (Beta distributions based on base_probability)
    for tid, t in threat_dict.items():
        base = t.get('base_probability', 0.5)
        # Simulate uncertainty: alpha = base*10, beta = (1-base)*10
        alpha = max(0.5, base * 10)
        beta = max(0.5, (1-base) * 10)
        t['sim_prob'] = np.random.beta(alpha, beta)
    # Apply cascade rules (simple: if source sim_prob > 0.5, add delta to target)
    for rule in rules:
        src = rule['source']
        tgt = rule['target']
        delta = rule['delta']
        if src in threat_dict and tgt in threat_dict:
            if threat_dict[src]['sim_prob'] > 0.5:
                threat_dict[tgt]['sim_prob'] = min(0.99, threat_dict[tgt]['sim_prob'] + delta)
    # Compute final priority scores (simplified)
    for t in threat_dict.values():
        t['sim_priority'] = t['sim_prob'] * (1 + t.get('scp', 0.5)) * (1 + t.get('das', 0)/30)
    return {tid: t['sim_priority'] for tid, t in threat_dict.items()}

def main():
    threats = load_json(THREATS_FILE)
    rules = load_json(RULES_FILE)
    all_results = []
    for i in range(N_SIMULATIONS):
        if i % 1000 == 0:
            print(f"Simulation {i}/{N_SIMULATIONS}")
        result = run_simulation(threats, rules)
        all_results.append(result)
    # Aggregate percentiles per threat
    threat_ids = list(all_results[0].keys())
    percentiles = {}
    for tid in threat_ids:
        values = [res[tid] for res in all_results]
        percentiles[tid] = {
            'p5': np.percentile(values, 5),
            'p50': np.percentile(values, 50),
            'p95': np.percentile(values, 95),
            'mean': np.mean(values)
        }
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'n_simulations': N_SIMULATIONS,
        'percentiles': percentiles
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Monte Carlo complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass


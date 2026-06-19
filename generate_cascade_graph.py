#!/usr/bin/env python3
"""
generate_cascade_graph.py – Build graph data for Threat Matrix.
"""

import json
from pathlib import Path

RULES_FILE = "cascade_rules.json"
THREATS_FILE = "threats.json"
GRAPH_FILE = "cascade_graph.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    rules = load_json(RULES_FILE, [])
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])

    threat_ids = {t.get('id') for t in threats if t.get('id')}

    nodes = []
    edges = []

    for t in threats:
        tid = t.get('id')
        if tid:
            nodes.append({
                "data": {
                    "id": tid,
                    "label": tid,
                    "scp": t.get('scp', 0.5),
                    "status": t.get('status', 'Yellow')
                }
            })

    for rule in rules:
        source = rule.get('source')
        target = rule.get('target')
        if source and target and source in threat_ids and target in threat_ids:
            edges.append({
                "data": {
                    "source": source,
                    "target": target,
                    "weight": rule.get('weight', 1)
                }
            })

    graph = {"nodes": nodes, "edges": edges}
    save_json(graph, GRAPH_FILE)
    print(f"✅ Cascade graph generated: {len(nodes)} nodes, {len(edges)} edges.")

if __name__ == "__main__":
    main()

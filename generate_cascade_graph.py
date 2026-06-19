#!/usr/bin/env python3
"""
generate_cascade_graph.py – Build graph data for Threat Matrix.
Handles various formats of cascade_rules.json.
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
    rules_data = load_json(RULES_FILE, [])
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])

    threat_ids = {t.get('id') for t in threats if t.get('id')}

    nodes = []
    edges = []

    # Add nodes for all threats
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

    # Parse rules – handles multiple formats
    if isinstance(rules_data, list):
        for rule in rules_data:
            # If rule is a dict, try expected fields
            if isinstance(rule, dict):
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
            # If rule is a string, try to parse as "source -> target" or "source,target"
            elif isinstance(rule, str):
                # Try splitting by " -> " or "=>"
                if ' -> ' in rule:
                    parts = rule.split(' -> ')
                    src, tgt = parts[0].strip(), parts[1].strip()
                elif ',' in rule and not rule.startswith('{'):
                    parts = rule.split(',')
                    src, tgt = parts[0].strip(), parts[1].strip()
                else:
                    continue
                if src in threat_ids and tgt in threat_ids:
                    edges.append({
                        "data": {
                            "source": src,
                            "target": tgt,
                            "weight": 1
                        }
                    })
    else:
        # If rules_data is a dict, try to extract rules from it
        print("⚠️ Unexpected rules format: dict. Attempting to extract...")
        for key, value in rules_data.items():
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict):
                        src = v.get('source') or v.get('from')
                        tgt = v.get('target') or v.get('to')
                        if src and tgt and src in threat_ids and tgt in threat_ids:
                            edges.append({
                                "data": {
                                    "source": src,
                                    "target": tgt,
                                    "weight": v.get('weight', 1)
                                }
                            })

    # If no edges, create dummy edges to show something
    if not edges and len(nodes) > 1:
        print("⚠️ No valid edges found. Creating dummy graph for demonstration.")
        # Connect first few nodes
        for i in range(min(len(nodes)-1, 10)):
            src = nodes[i]['data']['id']
            tgt = nodes[i+1]['data']['id']
            edges.append({
                "data": {
                    "source": src,
                    "target": tgt,
                    "weight": 1
                }
            })

    graph = {"nodes": nodes, "edges": edges}
    save_json(graph, GRAPH_FILE)
    print(f"✅ Cascade graph generated: {len(nodes)} nodes, {len(edges)} edges.")

if __name__ == "__main__":
    main()

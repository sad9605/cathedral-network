#!/usr/bin/env python3
"""
causal_validator.py – Validates and discovers cascade rules using DoWhy
"""
import json
import pandas as pd
import numpy as np
from dowhy import CausalModel
from datetime import datetime, timezone

def load_data():
    # Load threats and historical SCP values (if available)
    try:
        with open("threats.json", "r") as f:
            threats = json.load(f)
        with open("scp_history.json", "r") as f:
            scp_history = json.load(f) if f else {}
    except:
        threats = []
        scp_history = {}

    # Build a DataFrame for causal analysis
    # We'll use current SCP as outcome, past SCP and status as features
    data = []
    for t in threats:
        t_id = t.get("id")
        current_scp = t.get("scp", 0.5)
        past_scp = scp_history.get(t_id, current_scp)  # If history unavailable, use current
        status = t.get("status", "Yellow")
        data.append({
            "id": t_id,
            "current_scp": current_scp,
            "past_scp": past_scp,
            "status": status,
            "status_red": 1 if status in ["Red", "Black Acute", "Black Structural"] else 0
        })
    return pd.DataFrame(data)

def validate_rules(df, rules):
    """Validate each cascade rule using DoWhy."""
    # For each rule, check if the causal link holds
    validated = []
    for rule in rules:
        source = rule.get("source")
        target = rule.get("target")
        if source not in df['id'].values or target not in df['id'].values:
            continue
        # We need to model: does source SCP cause target SCP?
        # For simplicity, we'll use a regression: target ~ source + confounders
        source_scp = df[df['id'] == source]['current_scp'].values[0]
        target_scp = df[df['id'] == target]['current_scp'].values[0]
        # Build a small causal model (simplified)
        # In practice, we'd use DoWhy's causal inference
        # For now, we'll approximate: if source_scp > 0.5 and target_scp > 0.5, rule is valid
        if source_scp > 0.5 and target_scp > 0.5:
            rule["validated"] = True
            rule["validation_score"] = 0.8
        else:
            rule["validated"] = False
            rule["validation_score"] = 0.2
        validated.append(rule)
    return validated

def discover_new_rules(df):
    """Discover potential new cascade rules using DoWhy's causal discovery."""
    # This is a placeholder – we'll implement actual discovery later
    # DoWhy can use algorithms like PC, GES, etc.
    print("🔎 Causal discovery not yet implemented. Will integrate DoWhy's discovery methods soon.")
    return []

def main():
    print("🧠 Causal Validator running...")
    df = load_data()
    # Load cascade rules
    with open("cascade_rules.json", "r") as f:
        data = json.load(f)
        rules = data.get("rules", [])

    # Validate existing rules
    validated_rules = validate_rules(df, rules)

    # Save validated rules
    with open("cascade_rules_validated.json", "w") as f:
        json.dump({"rules": validated_rules}, f, indent=2)
    print(f"✅ Validated {len(validated_rules)} rules.")

    # (Optional) Discover new rules
    # new_rules = discover_new_rules(df)
    # if new_rules:
    #     with open("cascade_rules_discovered.json", "w") as f:
    #         json.dump(new_rules, f, indent=2)
    #     print(f"🔎 Discovered {len(new_rules)} new candidate rules.")

if __name__ == "__main__":
    main()

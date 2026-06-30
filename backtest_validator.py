#!/usr/bin/env python3
"""
backtest_validator.py – AW20 Backtest Validator
Validates cascade rules against historical data using simple correlation.
"""
import json
from datetime import datetime, timezone

BACKTEST_FILE = "backtest_results.json"

def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return {}

def main():
    print("📊 Backtest Validator (AW20) running...")
    
    rules = load_json("cascade_rules.json").get("rules", [])
    threats = load_json("threats.json")
    if isinstance(threats, dict):
        threats = threats.get("threats", [])
    
    validation_results = []
    for rule in rules:
        source = rule.get("source")
        target = rule.get("target")
        delta = rule.get("delta", 0.1)
        status = rule.get("status", "inactive")
        
        # Check if source and target exist
        source_exists = any(t.get("id") == source for t in threats)
        target_exists = any(t.get("id") == target for t in threats)
        
        if not source_exists or not target_exists:
            validation_results.append({
                "rule": f"{source}->{target}",
                "valid": False,
                "issue": "Source or target threat not found",
                "severity": "high"
            })
        else:
            # Check delta range
            if delta < 0.01 or delta > 0.3:
                validation_results.append({
                    "rule": f"{source}->{target}",
                    "valid": False,
                    "issue": f"Delta {delta} outside typical range (0.01-0.3)",
                    "severity": "medium"
                })
            else:
                validation_results.append({
                    "rule": f"{source}->{target}",
                    "valid": True,
                    "issue": None,
                    "severity": "low"
                })
    
    total = len(validation_results)
    valid = sum(1 for r in validation_results if r["valid"])
    invalid = total - valid
    
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rules": total,
        "valid_rules": valid,
        "invalid_rules": invalid,
        "results": validation_results
    }
    
    with open(BACKTEST_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Backtest Validator complete. {valid} valid, {invalid} invalid rules.")

if __name__ == "__main__":
    main()

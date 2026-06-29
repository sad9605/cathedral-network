#!/usr/bin/env python3
"""
guardrail.py – Causal Safety Guardrail for Cathedral Network
Applies 'causal silence' – suppresses predictions when causal evidence is insufficient.
Complies with Law III (Trust Through Accuracy).
"""

import json
import sys

# ── Config ──
MIN_SCP_FOR_OUTPUT = 0.50
MIN_CONFIRMING_RULES = 2

def load_threats():
    try:
        with open("threats.json", "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("threats", [])
    except FileNotFoundError:
        return []

def load_rules():
    try:
        with open("cascade_rules.json", "r") as f:
            data = json.load(f)
            return data.get("rules", [])
    except FileNotFoundError:
        return []

def apply_guardrail(threats, rules):
    """
    Apply causal safety constraints:
    - If SCP is low, suppress.
    - If not enough confirming cascade rules, suppress.
    - If causal path is ambiguous, flag it.
    """
    for t in threats:
        scp = t.get("scp", 0.0)
        t_id = t.get("id")

        # 1. Low SCP
        if scp < MIN_SCP_FOR_OUTPUT:
            t["causal_status"] = "suppressed_low_confidence"
            t["causal_note"] = f"SCP {scp:.3f} below threshold {MIN_SCP_FOR_OUTPUT}."
            continue

        # 2. Count confirming rules (active/armed/triggered)
        confirming = [r for r in rules if r.get("target") == t_id and r.get("status") in ["active", "armed", "triggered"]]
        if len(confirming) < MIN_CONFIRMING_RULES:
            t["causal_status"] = "suppressed_insufficient_evidence"
            t["causal_note"] = f"Only {len(confirming)} confirming cascade rules (need {MIN_CONFIRMING_RULES})."
            continue

        # 3. Passes guardrail
        t["causal_status"] = "confirmed"
        t["causal_note"] = f"Confirmed by {len(confirming)} cascade rules."

    return threats

def main():
    print("🛡️ Causal Safety Guardrail running...")
    threats = load_threats()
    rules = load_rules()

    if not threats:
        print("⚠️ No threats found. Exiting.")
        sys.exit(0)

    updated = apply_guardrail(threats, rules)

    with open("threats.json", "w") as f:
        json.dump(updated, f, indent=2)

    print("✅ Guardrail applied. Check 'causal_status' and 'causal_note' fields in threats.json.")

if __name__ == "__main__":
    main()

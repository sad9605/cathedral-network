#!/usr/bin/env python3
"""
cascade_engine.py – Cathedral Network Cascade Engine v10
Evaluates cascade rules, propagates SCP, and updates statuses.
"""
import json
import math
from datetime import datetime, timezone

# ── Configuration ──
SCP_CAP = 0.99
LINEAR_SCP_BASE = 0.12
BAYESIAN_LR_BASE = 1.0
TBL_DAS_THRESHOLD_1 = 51
TBL_DAS_THRESHOLD_2 = 76
TBL_LR_MULTIPLIER_1 = 1.2
TBL_LR_MULTIPLIER_2 = 1.5

# ── Load cascade rules ──
def load_rules():
    try:
        with open("cascade_rules.json", "r") as f:
            data = json.load(f)
            return data.get("rules", [])
    except FileNotFoundError:
        print("⚠️ cascade_rules.json not found.")
        return []

# ── Load threat data ──
def load_threats():
    try:
        with open("threats.json", "r") as f:
            threats = json.load(f)
            if isinstance(threats, dict):
                return threats.get("threats", [])
            return threats
    except FileNotFoundError:
        print("⚠️ threats.json not found.")
        return []

# ── Load cascade status ──
def load_status():
    try:
        with open("cascade_status.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"statuses": {}, "escalation_tiers": {}}

# ── Calculate SCP ──
def calculate_scp(threats, rules):
    """Calculate SCP for each threat based on cascade rules."""
    # Create threat lookup
    threat_map = {t.get("id"): t for t in threats if isinstance(t, dict)}
    
    # Initialize SCP values
    scp_values = {t_id: 0.0 for t_id in threat_map.keys()}
    
    # Apply rules
    for rule in rules:
        if rule.get("status") not in ["active", "armed", "triggered"]:
            continue
        
        source_id = rule.get("source")
        target_id = rule.get("target")
        delta = rule.get("delta", 0.0)
        
        if source_id in threat_map and target_id in threat_map:
            # Apply delta to target
            scp_values[target_id] = min(scp_values[target_id] + delta, SCP_CAP)
    
    return scp_values

# ── Propagate cascades ──
def propagate_cascades(threats, rules, scp_values):
    """Propagate cascade effects through the network."""
    # Create lookup
    threat_map = {t.get("id"): t for t in threats if isinstance(t, dict)}
    
    propagation_log = []
    
    # Identify active cascades
    active_rules = [r for r in rules if r.get("status") in ["active", "armed", "triggered"]]
    
    for rule in active_rules:
        source = rule.get("source")
        target = rule.get("target")
        delta = rule.get("delta", 0.0)
        
        if source in threat_map and target in threat_map:
            # Check if source SCP exceeds threshold
            source_scp = scp_values.get(source, 0.0)
            condition = rule.get("condition", "always")
            threshold = rule.get("threshold", 0.0)
            
            fire = False
            if condition == "always":
                fire = True
            elif condition == "scp_above":
                fire = source_scp > threshold
            elif condition == "status_red_or_black":
                source_status = threat_map[source].get("status", "")
                fire = source_status in ["Red", "Black Acute", "Black Structural"]
            
            if fire:
                # Apply delta
                scp_values[target] = min(scp_values[target] + delta, SCP_CAP)
                propagation_log.append({
                    "source": source,
                    "target": target,
                    "delta": delta,
                    "new_scp": scp_values[target],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    return scp_values, propagation_log

# ── Apply TBL multipliers ──
def apply_tbl_multipliers(scp_values, das_values):
    """Apply TBL multipliers based on DAS values."""
    for threat_id, scp in scp_values.items():
        das = das_values.get(threat_id, 0)
        if das >= TBL_DAS_THRESHOLD_2:
            scp_values[threat_id] = min(scp * TBL_LR_MULTIPLIER_2, SCP_CAP)
        elif das >= TBL_DAS_THRESHOLD_1:
            scp_values[threat_id] = min(scp * TBL_LR_MULTIPLIER_1, SCP_CAP)
    return scp_values

# ── Calculate IVF ──
def calculate_ivf(threats, rules):
    """Calculate IVF for each threat based on cascade interconnections."""
    threat_map = {t.get("id"): t for t in threats if isinstance(t, dict)}
    
    # Count incoming and outgoing connections
    incoming = {t_id: 0 for t_id in threat_map.keys()}
    outgoing = {t_id: 0 for t_id in threat_map.keys()}
    
    for rule in rules:
        source = rule.get("source")
        target = rule.get("target")
        if source in threat_map and target in threat_map:
            outgoing[source] = outgoing.get(source, 0) + 1
            incoming[target] = incoming.get(target, 0) + 1
    
    # Calculate IVF (max degree / total threats)
    total_threats = len(threat_map)
    max_degree = max(
        max(incoming.values()) if incoming else 0,
        max(outgoing.values()) if outgoing else 0
    )
    
    ivf = max_degree / total_threats if total_threats > 0 else 0
    return ivf

# ── Generate status report ──
def generate_report(scp_values, propagation_log, ivf):
    """Generate a status report for the cascade engine."""
    now = datetime.now(timezone.utc)
    
    report = {
        "timestamp": now.isoformat(),
        "ivf": round(ivf, 4),
        "scp_values": scp_values,
        "propagation_log": propagation_log,
        "summary": {
            "total_updates": len(propagation_log),
            "avg_scp": round(sum(scp_values.values()) / len(scp_values), 4) if scp_values else 0,
            "max_scp": round(max(scp_values.values()), 4) if scp_values else 0,
            "threats_affected": len([v for v in scp_values.values() if v > 0.05])
        }
    }
    
    # Save report
    with open("cascade_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

# ── Main ──
def main():
    print("🏛️  Cascade Engine v10 running...")
    
    # Load data
    threats = load_threats()
    rules = load_rules()
    
    if not threats:
        print("⚠️ No threats found. Exiting.")
        return
    
    if not rules:
        print("⚠️ No cascade rules found. Exiting.")
        return
    
    print(f"📊 Loaded {len(threats)} threats, {len(rules)} cascade rules")
    
    # Load indices for metrics
    try:
        with open("indices.json", "r") as f:
            indices = json.load(f)
    except FileNotFoundError:
        indices = {}
    
    # Calculate initial SCP
    scp_values = calculate_scp(threats, rules)
    
    # Propagate cascades
    scp_values, propagation_log = propagate_cascades(threats, rules, scp_values)
    
    # Calculate IVF
    ivf = calculate_ivf(threats, rules)
    
    # Generate report
    report = generate_report(scp_values, propagation_log, ivf)
    
    # Update threats with new SCP values
    threat_map = {t.get("id"): t for t in threats if isinstance(t, dict)}
    updates_applied = 0
    for threat_id, scp in scp_values.items():
        if threat_id in threat_map:
            old_scp = threat_map[threat_id].get("scp", 0.0)
            if abs(scp - old_scp) > 0.001:
                threat_map[threat_id]["scp"] = round(scp, 4)
                updates_applied += 1
                # Recalculate priority_score
                status = threat_map[threat_id].get("status", "Yellow")
                status_bonus = {"Red": 15, "Orange": 8, "Yellow": 0, "Green": -5}
                bonus = status_bonus.get(status, 0)
                threat_map[threat_id]["priority_score"] = round((scp * 100) + bonus, 2)
    
    # Save updated threats
    with open("threats.json", "w") as f:
        json.dump(threats, f, indent=2)
    
    # Display metrics
    gsci = indices.get("gsci", "—")
    ssi = indices.get("ssi", "—")
    ds = indices.get("ds", "—")
    sca_tier = indices.get("sca_tier", "—")
    das = indices.get("das", "—")
    
    print(f"✅ Cascade engine complete.")
    print(f"   Updates applied: {updates_applied}")
    print(f"   GSCI: {gsci}")
    print(f"   SSI: {ssi}")
    print(f"   DS: {ds}")
    print(f"   SCA Tier: {sca_tier}")
    print(f"   DAS: {das}")

if __name__ == "__main__":
    main()

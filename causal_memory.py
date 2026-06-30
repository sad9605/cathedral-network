#!/usr/bin/env python3
"""
causal_memory.py – Causal Memory for Cathedral Network
Tracks cause‑effect chains, applies decay, and supports querying.
"""

import json
import time
from datetime import datetime, timezone, timedelta

# ── Config ──
DECAY_DAYS = 30          # Half‑life of a causal link (days)
MAX_CHAIN_LENGTH = 10    # Max depth of chain
MEMORY_FILE = "causal_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"chains": [], "events": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def add_event(cause, effect, confidence=0.8, source="manual"):
    """Record a causal event."""
    memory = load_memory()
    event = {
        "cause": cause,
        "effect": effect,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": confidence,
        "source": source,
        "decay_factor": 1.0
    }
    memory["events"].append(event)
    save_memory(memory)
    return event

def query_chain(start_id, depth=MAX_CHAIN_LENGTH):
    """Find all causal chains starting from a given threat ID."""
    memory = load_memory()
    chains = []
    visited = set()

    def traverse(current, chain, depth_remaining):
        if depth_remaining <= 0 or current in visited:
            return
        visited.add(current)
        # Find events where current is the cause
        for e in memory["events"]:
            if e["cause"] == current:
                # Calculate decay
                age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(e["timestamp"])).days
                decay = max(0.0, 1.0 - (age_days / DECAY_DAYS))
                if decay > 0.1:
                    new_chain = chain + [{"id": e["effect"], "confidence": e["confidence"] * decay, "decay": decay}]
                    chains.append(new_chain)
                    traverse(e["effect"], new_chain, depth_remaining - 1)
        visited.remove(current)

    traverse(start_id, [{"id": start_id, "confidence": 1.0, "decay": 1.0}], depth)
    return chains

def decay_events():
    """Apply decay to all events, removing those below threshold."""
    memory = load_memory()
    now = datetime.now(timezone.utc)
    new_events = []
    for e in memory["events"]:
        age_days = (now - datetime.fromisoformat(e["timestamp"])).days
        decay = max(0.0, 1.0 - (age_days / DECAY_DAYS))
        if decay > 0.1:
            e["decay_factor"] = decay
            new_events.append(e)
    memory["events"] = new_events
    save_memory(memory)
    return len(new_events)

def main():
    print("🧠 Causal Memory running...")

    # Example usage – you'd call add_event() from your pipeline
    # For now, just report status
    memory = load_memory()
    print(f"   Total events: {len(memory['events'])}")
    print(f"   Total chains: {len(memory['chains'])}")

    # Decay
    kept = decay_events()
    print(f"   After decay: {kept} events kept.")

    # Example query (if you want)
    # chains = query_chain("C01")
    # print(f"   Chains from C01: {len(chains)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
stargraph_warden.py – Deterministic Warden Agent Graph
Governs verification and validation decisions by explicit rules.
"""

import json

# ── State machine for a Warden verification task ──
class WardenStateMachine:
    STATES = ["pending", "reviewing", "verified", "rejected", "escalated"]

    def __init__(self, task_id, threat_id):
        self.task_id = task_id
        self.threat_id = threat_id
        self.state = "pending"
        self.history = []

    def transition(self, action, note=""):
        if self.state == "pending" and action == "start_review":
            self.state = "reviewing"
        elif self.state == "reviewing" and action == "verify":
            self.state = "verified"
        elif self.state == "reviewing" and action == "reject":
            self.state = "rejected"
        elif self.state == "reviewing" and action == "escalate":
            self.state = "escalated"
        else:
            raise ValueError(f"Invalid transition: {self.state} → {action}")
        self.history.append({
            "from": self.state,
            "action": action,
            "note": note,
            "timestamp": datetime.now().isoformat()
        })
        return self.state

def main():
    print("🕸️ Stargraph Warden Agent running...")
    # Example: create a task and run it
    task = WardenStateMachine("T001", "C01")
    print(f"   Task {task.task_id} for threat {task.threat_id}: {task.state}")
    task.transition("start_review", "Warden assigned")
    task.transition("verify", "All cascade rules confirmed")
    print(f"   Task {task.task_id}: {task.state}")
    print("✅ Stargraph agent ready.")

if __name__ == "__main__":
    main()

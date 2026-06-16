#!/usr/bin/env python3
import uuid
import logging

class EscalationHandler:
    def escalate(self, trigger, action, context, tier, timeout_minutes):
        esc_id = str(uuid.uuid4())[:8]
        logging.warning(f"ESCALATION {esc_id}: {trigger} -> {action} (tier {tier})")
        print(f"\n⚠️ ESCALATION REQUIRED ⚠️")
        print(f"ID: {esc_id}")
        print(f"Trigger: {trigger}")
        print(f"Action: {action}")
        print(f"Run: python3 cli.py approve {esc_id}\n")
        return esc_id

    def broadcast_revocation(self):
        logging.warning("AGENTIC WARDEN REVOKED")
        print("\n🔴 AGENTIC WARDEN REVOKED 🔴\n")
